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

            # 检查默认图片是否存在
            default_image = '/Users/wangzihan/Autobrowser/assets/default.jpg'
            if not Path(default_image).exists():
                logger.warning(f"默认图片不存在: {default_image}")
                images = []
            else:
                images = [default_image]

            # 构建话题标签
            topics = "AI,人工智能,科技前沿,AIGC"

            # 构建 opencli 命令
            cmd = [
                'opencli', 'xiaohongshu', 'publish', content,
                '--title', title,
                '--topics', topics,
            ]

            if images:
                img_paths = ','.join(images)
                cmd.extend(['--images', img_paths])
                logger.info(f"使用图片: {img_paths}")

            if draft:
                cmd.extend(['--draft', 'true'])

            cmd.extend(['--format', 'json', '--verbose'])

            logger.info(f"执行发布命令: opencli xiaohongshu publish...")
            logger.info(f"标题: {title}")
            logger.info(f"话题: {topics}")

            # 执行发布
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 增加超时时间到3分钟
            )

            # 记录完整输出用于调试
            logger.info(f"OpenCLI stdout: {result.stdout}")
            logger.info(f"OpenCLI stderr: {result.stderr}")
            logger.info(f"OpenCLI returncode: {result.returncode}")

            if result.returncode == 0:
                # 解析 JSON 输出检查 isSuccess
                try:
                    import json
                    output_data = json.loads(result.stdout)
                    is_success = output_data.get('isSuccess', False)
                    detail = output_data.get('detail', '')

                    if is_success:
                        logger.info(f"发布成功: {title}")
                        return {
                            'success': True,
                            'message': '发布成功',
                            'output': result.stdout,
                            'detail': detail
                        }
                    else:
                        logger.error(f"发布失败 (isSuccess=false): {detail}")
                        return {
                            'success': False,
                            'message': f'发布失败: {detail}',
                            'output': result.stdout
                        }
                except json.JSONDecodeError:
                    logger.warning("无法解析 JSON 输出，按返回码判断成功")
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
