#!/usr/bin/env python3
"""
AutoBrowser 主程序
自动爬取 X/Reddit AI 内容，使用 Kimi AI 处理，生成封面，发布到小红书
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.crawler.opencli_crawler import ContentCrawler
from src.storage.content_store import ContentStore
from src.processor.ai_processor import AIContentProcessor
from src.processor.kimi_processor import KimiProcessor
from src.publisher.xiaohongshu import XiaohongshuPublisher
from src.scheduler.task_scheduler import TaskScheduler

# 封面生成（可选）
try:
    from src.utils.cover_generator import generate_cover
    COVER_GENERATION_AVAILABLE = True
except ImportError:
    COVER_GENERATION_AVAILABLE = False

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
        self.kimi_processor = KimiProcessor()
        self.publisher = XiaohongshuPublisher(
            chrome_port=config.xiaohongshu.get('chrome_port', 9222)
        )
        self.scheduler = TaskScheduler()
        self.cover_enabled = config.get('cover.enabled', True)
        self.cover_dir = Path(config.get('cover.output_dir', 'assets/covers'))

    def run_once(self):
        """执行一次完整流程"""
        logger.info("=" * 60)
        logger.info("开始执行自动化流程")
        logger.info("=" * 60)

        try:
            # 1. 爬取内容
            logger.info("步骤 1/6: 爬取内容")
            contents = self.crawler.crawl_all()
            if not contents:
                logger.warning("没有爬取到内容，流程结束")
                return

            # 保存到数据库
            self.store.save_contents(contents)
            logger.info(f"爬取完成: {len(contents)} 条内容")

            # 2. AI 审核选择
            logger.info("步骤 2/6: AI 审核选择")
            selected_content = self.ai_processor.review_and_select(contents)
            if not selected_content:
                logger.info("没有内容通过 AI 审核，流程结束")
                return

            # 更新选中内容状态
            self.store.update_content_status(
                selected_content['id'],
                'selected'
            )
            logger.info(f"选中内容: {selected_content['title'][:50]}...")

            # 3. Kimi AI 处理
            logger.info("步骤 3/6: Kimi AI 处理")
            kimi_result = self.kimi_processor.process_content(selected_content)
            if not kimi_result:
                logger.error("Kimi 处理失败，使用备用方案")
                kimi_result = self.ai_processor.modify_for_xiaohongshu(selected_content)
                kimi_result['cover_text'] = kimi_result['title'][:10]

            logger.info(f"Kimi 生成标题: {kimi_result['title']}")
            logger.info(f"封面文字: {kimi_result.get('cover_text', 'AI资讯')}")

            # 4. 生成封面图片（如果启用）
            cover_path = None
            if self.cover_enabled and COVER_GENERATION_AVAILABLE:
                logger.info("步骤 4/6: 生成封面图片")
                cover_text = kimi_result.get('cover_text', kimi_result['title'][:10])
                cover_path = self._generate_cover_image(cover_text)
                if cover_path:
                    logger.info(f"封面生成成功: {cover_path}")
                else:
                    logger.warning("封面生成失败，使用默认图片")
            else:
                logger.info("步骤 4/6: 跳过封面生成")

            # 5. 发布到小红书
            logger.info("步骤 5/6: 发布到小红书")

            # 检查今日发布数量
            today_count = self.store.get_today_publication_count()
            max_daily = self.config.publisher.get('max_daily_posts', 8)

            if today_count >= max_daily:
                logger.warning(f"今日已发布 {today_count} 条，达到上限")
                return

            # 准备图片（优先使用生成的封面）
            if cover_path and Path(cover_path).exists():
                images = [cover_path]
            else:
                images = ['/Users/wangzihan/Autobrowser/assets/default.jpg']

            # 执行发布
            result = self.publisher.publish(
                title=kimi_result['title'],
                content=kimi_result['content'],
                images=images,
                draft=False
            )

            # 6. 记录结果
            logger.info("步骤 6/6: 记录发布结果")
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

    def _generate_cover_image(self, text: str) -> str:
        """生成封面图片"""
        try:
            # 确保目录存在
            self.cover_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.cover_dir / f"cover_{timestamp}.png"

            # 调用封面生成函数
            result = generate_cover(text, str(output_path))
            return result

        except Exception as e:
            logger.exception(f"生成封面失败: {e}")
            return None

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

        # 检查 Kimi API Key
        if not self.kimi_processor.api_key:
            logger.warning("Kimi API Key 未配置，请在 config/settings.yaml 中设置")
            logger.warning("将使用本地 AI 处理作为备用方案")

        logger.info("环境检查通过")
        return True

def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description='AutoBrowser - AI 内容自动化发布工具')
    parser.add_argument('--run-once', action='store_true', help='立即执行一次')
    parser.add_argument('--start', action='store_true', help='启动定时任务')
    parser.add_argument('--login', action='store_true', help='小红书登录')
    parser.add_argument('--test-kimi', action='store_true', help='测试 Kimi AI 处理')
    parser.add_argument('--test-cover', action='store_true', help='测试封面生成')

    args = parser.parse_args()

    app = AutoBrowserApp()

    if args.login:
        result = app.publisher.login()
        print(result['output'])
        return

    if args.test_kimi:
        # 测试 Kimi 处理
        test_content = {
            'id': 'test',
            'platform': 'twitter',
            'title': 'OpenAI releases GPT-5 with breakthrough capabilities',
            'content': 'The new model shows significant improvements in reasoning and coding tasks.',
            'author': 'OpenAI',
            'created_at': '2026-04-07',
            'engagement': {'likes': 5000, 'retweets': 2000}
        }
        result = app.kimi_processor.process_content(test_content)
        if result:
            print("Kimi 处理结果:")
            print(f"标题: {result['title']}")
            print(f"内容: {result['content']}")
            print(f"封面文字: {result.get('cover_text', '')}")
        return

    if args.test_cover:
        # 测试封面生成
        cover_path = app._generate_cover_image("AI资讯日报")
        if cover_path:
            print(f"封面生成成功: {cover_path}")
        else:
            print("封面生成失败")
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
    print("  python main.py --run-once      # 立即执行一次")
    print("  python main.py --start         # 启动定时任务")
    print("  python main.py --login         # 小红书登录")
    print("  python main.py --test-kimi     # 测试 Kimi AI")
    print("  python main.py --test-cover    # 测试封面生成")

if __name__ == '__main__':
    main()
