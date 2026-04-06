"""
小红书发布模块
使用 OpenCLI 发布内容
"""
import subprocess
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class XiaohongshuPublisher:
    """小红书发布器 - 使用 OpenCLI"""

    def __init__(self, chrome_port: int = 9222):
        self.chrome_port = chrome_port

    def publish(self, title: str, content: str, images: Optional[list] = None, draft: bool = False) -> dict:
        """
        发布图文到小红书

        Args:
            title: 标题（最多20字）
            content: 内容正文
            images: 图片路径列表（可选，最多9张）
            draft: 是否保存为草稿

        Returns:
            发布结果
        """
        try:
            # 确保标题不超过20字
            if len(title) > 20:
                title = title[:19] + "…"

            # 构建 opencli 命令
            cmd = [
                'opencli', 'xiaohongshu', 'publish', content,
                '--title', title,
            ]

            if images:
                img_paths = ','.join(images)
                cmd.extend(['--images', img_paths])

            if draft:
                cmd.extend(['--draft', 'true'])

            cmd.extend(['--format', 'json'])

            logger.info(f"执行发布命令: opencli xiaohongshu publish...")
            logger.info(f"标题: {title}")

            # 执行发布
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                logger.info(f"发布成功: {title}")
                return {
                    'success': True,
                    'message': '发布成功',
                    'output': result.stdout
                }
            else:
                logger.error(f"发布失败: {result.stderr}")
                return {
                    'success': False,
                    'message': result.stderr,
                    'output': result.stdout
                }

        except Exception as e:
            logger.error(f"发布异常: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def check_login(self) -> bool:
        """检查小红书登录状态（通过尝试获取用户信息）"""
        try:
            # opencli xiaohongshu 没有直接的 check-login 命令
            # 通过尝试获取创作者数据来判断是否登录
            cmd = ['opencli', 'xiaohongshu', 'creator-profile', '--format', 'json']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            # 如果能成功获取数据，说明已登录
            return result.returncode == 0 and 'error' not in result.stderr.lower()
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    def get_login_status(self) -> dict:
        """获取登录状态详情"""
        try:
            cmd = ['opencli', 'xiaohongshu', 'creator-profile', '--format', 'json']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
