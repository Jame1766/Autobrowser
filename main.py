#!/usr/bin/env python3
"""
AutoBrowser 主程序
自动爬取 X/Reddit AI 内容并发布到小红书
"""
import sys
import logging
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.crawler.opencli_crawler import ContentCrawler
from src.storage.content_store import ContentStore
from src.processor.ai_processor import AIContentProcessor
from src.publisher.xiaohongshu import XiaohongshuPublisher
from src.scheduler.task_scheduler import TaskScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoBrowserApp:
    """主应用类"""

    def __init__(self):
        self.config = config
        self.crawler = ContentCrawler(config)
        self.store = ContentStore()
        self.ai_processor = AIContentProcessor()
        self.publisher = XiaohongshuPublisher(
            chrome_port=config.xiaohongshu.get('chrome_port', 9222)
        )
        self.scheduler = TaskScheduler()

    def run_once(self):
        """执行一次完整流程"""
        logger.info("=" * 50)
        logger.info("开始执行自动化流程")
        logger.info("=" * 50)

        try:
            # 1. 爬取内容
            logger.info("步骤 1/5: 爬取内容")
            contents = self.crawler.crawl_all()
            if not contents:
                logger.warning("没有爬取到内容，流程结束")
                return

            # 保存到数据库
            self.store.save_contents(contents)
            logger.info(f"爬取完成: {len(contents)} 条内容")

            # 2. AI 审核选择
            logger.info("步骤 2/5: AI 审核选择")
            selected_content = self.ai_processor.review_and_select(contents)
            if not selected_content:
                logger.info("没有内容通过 AI 审核，流程结束")
                return

            # 更新选中内容状态
            self.store.update_content_status(
                selected_content['id'],
                'selected'
            )

            # 3. AI 内容修改
            logger.info("步骤 3/5: AI 内容修改")
            modified = self.ai_processor.modify_for_xiaohongshu(selected_content)
            logger.info(f"修改后标题: {modified['title']}")

            # 4. 发布到小红书
            logger.info("步骤 4/5: 发布到小红书")

            # 检查今日发布数量
            today_count = self.store.get_today_publication_count()
            max_daily = self.config.publisher.get('max_daily_posts', 8)

            if today_count >= max_daily:
                logger.warning(f"今日已发布 {today_count} 条，达到上限")
                return

            # 准备图片（使用默认图片或从内容中提取）
            images = ['/Users/wangzihan/Autobrowser/assets/default.jpg']

            # 执行发布
            result = self.publisher.publish(
                title=modified['title'],
                content=modified['content'],
                images=images,
                draft=False
            )

            # 5. 记录结果
            logger.info("步骤 5/5: 记录发布结果")
            if result['success']:
                self.store.update_content_status(
                    selected_content['id'],
                    'published'
                )
                self.store.log_publication(
                    content_id=selected_content['id'],
                    platform='xiaohongshu',
                    status='success',
                    message='发布成功'
                )
                logger.info("✅ 流程完成: 内容已发布")
            else:
                self.store.update_content_status(
                    selected_content['id'],
                    'failed'
                )
                self.store.log_publication(
                    content_id=selected_content['id'],
                    platform='xiaohongshu',
                    status='failed',
                    message=result['message']
                )
                logger.error(f"❌ 发布失败: {result['message']}")

        except Exception as e:
            logger.exception("流程执行异常")

    def start_scheduler(self):
        """启动定时调度"""
        interval = self.config.crawler.get('interval_hours', 3)
        self.scheduler.add_job(self.run_once, interval_hours=interval)
        self.scheduler.start()
        logger.info(f"定时任务已启动，每 {interval} 小时执行一次")

        # 保持程序运行
        try:
            import threading
            event = threading.Event()
            event.wait()
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
            self.scheduler.shutdown()

    def check_setup(self) -> bool:
        """检查环境配置"""
        logger.info("检查环境配置...")

        # 检查小红书登录状态
        if not self.publisher.check_login():
            logger.warning("小红书未登录，请先执行登录流程")
            return False

        logger.info("环境检查通过")
        return True

def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description='AutoBrowser - AI 内容自动化发布工具')
    parser.add_argument('--run-once', action='store_true', help='立即执行一次')
    parser.add_argument('--start', action='store_true', help='启动定时任务')
    parser.add_argument('--login', action='store_true', help='小红书登录')

    args = parser.parse_args()

    app = AutoBrowserApp()

    if args.login:
        result = app.publisher.login()
        print(result['output'])
        return

    if args.run_once:
        if app.check_setup():
            app.run_once()
        return

    if args.start:
        if app.check_setup():
            app.start_scheduler()
        return

    # 默认：执行一次
    parser.print_help()
    print("\n示例:")
    print("  python main.py --run-once    # 立即执行一次")
    print("  python main.py --start       # 启动定时任务")
    print("  python main.py --login       # 小红书登录")

if __name__ == '__main__':
    main()
