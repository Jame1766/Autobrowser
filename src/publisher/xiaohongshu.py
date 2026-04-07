"""
小红书发布模块
使用 OpenCLI 发布内容
"""
import os
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
            # 确保标题不超过20字（严格限制）
            if len(title) >= 20:
                title = title[:18] + "…"

            # 检查图片路径
            if images:
                # 使用传入的图片
                valid_images = []
                for img in images:
                    if Path(img).exists():
                        valid_images.append(img)
                    else:
                        logger.warning(f"图片不存在: {img}")
                images = valid_images

            # 如果没有有效图片，使用默认图片
            if not images:
                default_image = '/Users/wangzihan/Autobrowser/assets/default.jpg'
                if Path(default_image).exists():
                    images = [default_image]
                else:
                    logger.warning(f"默认图片不存在: {default_image}")
                    images = []

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
            # 设置更长的超时时间（3分钟）
            env = os.environ.copy()
            env['OPENCLI_BROWSER_COMMAND_TIMEOUT'] = '180'

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=200,  # 增加超时时间到3分20秒
                env=env
            )

            # 记录完整输出用于调试
            logger.info(f"OpenCLI stdout: {result.stdout}")
            logger.info(f"OpenCLI stderr: {result.stderr}")
            logger.info(f"OpenCLI returncode: {result.returncode}")

            if result.returncode == 0:
                # 解析 JSON 输出检查是否成功
                try:
                    import json
                    output_data = json.loads(result.stdout)
                    logger.info(f"OpenCLI 返回数据: {json.dumps(output_data, ensure_ascii=False, indent=2)}")

                    # OpenCLI 返回的是数组格式
                    if isinstance(output_data, list) and len(output_data) > 0:
                        item = output_data[0]
                        status = item.get('status', '')
                        detail = item.get('detail', '')

                        # 判断是否成功：状态包含"成功"或"✅"
                        is_success = '成功' in status or '✅' in status

                        if is_success:
                            logger.info(f"发布成功: {title}")
                            return {
                                'success': True,
                                'message': status,
                                'output': result.stdout,
                                'detail': detail
                            }
                        else:
                            logger.warning(f"发布状态异常: {status} - {detail}")
                            return {
                                'success': False,
                                'message': status,
                                'output': result.stdout,
                                'detail': detail
                            }
                    else:
                        logger.warning(f"意外的输出格式: {output_data}")
                        return {
                            'success': True,
                            'message': '命令执行成功但格式异常',
                            'output': result.stdout
                        }
                except json.JSONDecodeError as e:
                    logger.warning(f"无法解析 JSON 输出: {e}")
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
