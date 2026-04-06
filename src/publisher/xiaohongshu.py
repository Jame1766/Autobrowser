"""
小红书发布模块
调用 xiaohongshu-skills 发布内容
"""
import subprocess
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class XiaohongshuPublisher:
    """小红书发布器"""

    def __init__(self, chrome_port: int = 9222):
        self.chrome_port = chrome_port
        self.skill_path = self._find_skill_path()

    def _find_skill_path(self) -> Path:
        """查找小红书技能路径"""
        # 尝试查找 xiaohongshu-skills
        possible_paths = [
            Path.home() / ".claude" / "skills" / "xiaohongshu-skills",
            Path("/Users/wangzihan/.claude/skills/xiaohongshu-skills"),
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return Path("xiaohongshu-skills")  # 默认名称

    def publish(self, title: str, content: str, images: Optional[list] = None) -> dict:
        """
        发布图文到小红书

        Args:
            title: 标题
            content: 内容
            images: 图片路径列表（可选）

        Returns:
            发布结果
        """
        try:
            # 保存标题和内容到临时文件
            temp_dir = Path("data/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            title_file = temp_dir / "title.txt"
            content_file = temp_dir / "content.txt"

            title_file.write_text(title, encoding='utf-8')
            content_file.write_text(content, encoding='utf-8')

            # 构建发布命令
            cmd = [
                'python', 'scripts/cli.py', 'publish',
                '--title-file', str(title_file),
                '--content-file', str(content_file),
            ]

            if images:
                for img in images:
                    cmd.extend(['--images', img])

            # 执行发布
            result = subprocess.run(
                cmd,
                cwd=self.skill_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                logger.info(f"发布成功: {title[:50]}...")
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
        """检查小红书登录状态"""
        try:
            cmd = ['python', 'scripts/cli.py', 'check-login']
            result = subprocess.run(
                cmd,
                cwd=self.skill_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0 and '登录' in result.stdout
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    def login(self) -> dict:
        """获取登录二维码"""
        try:
            cmd = ['python', 'scripts/cli.py', 'login']
            result = subprocess.run(
                cmd,
                cwd=self.skill_path,
                capture_output=True,
                text=True,
                timeout=60
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
