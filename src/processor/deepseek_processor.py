"""
DeepSeek AI 处理模块
调用 DeepSeek API 进行内容处理
"""
import json
import logging
import os
import requests
from typing import Dict, Any, Optional

from src.processor.base_ai_processor import BaseAIProcessor

logger = logging.getLogger(__name__)


class DeepSeekProcessor(BaseAIProcessor):
    """DeepSeek AI 内容处理器"""

    def __init__(self, config: dict = None):
        # 默认配置
        default_config = {
            'api_key': os.environ.get('DEEPSEEK_API_KEY', ''),
            'api_base': 'https://api.deepseek.com',
            'model': 'deepseek-chat',
            'temperature': 1.0
        }

        # 合并配置
        if config:
            default_config.update(config)

        super().__init__(default_config)

        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置，请设置环境变量 DEEPSEEK_API_KEY")

    def process_content(self, content: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        使用 DeepSeek AI 处理内容，生成小红书标题和正文

        Args:
            content: 原始内容（包含 title, content, platform 等）

        Returns:
            处理后的标题和正文
        """
        if not self.api_key:
            logger.error("DeepSeek API Key 未配置")
            return None

        try:
            # 构建 prompt
            prompt = self._build_prompt(content)

            # 调用 DeepSeek API
            response = self._call_api(prompt)

            if not response:
                return None

            # 解析响应
            result = self._parse_response(response)

            logger.info(f"DeepSeek 处理完成")
            logger.info(f"  标题: {result['title']}")
            logger.info(f"  正文长度: {len(result['content'])} 字符")

            return result

        except Exception as e:
            logger.exception(f"DeepSeek 处理失败: {e}")
            return None

    def _call_api(self, prompt: str) -> Optional[str]:
        """调用 DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是小红书内容运营专家，擅长将 AI 资讯转化为小红书爆款笔记格式。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "stream": False
            }

            logger.info(f"调用 DeepSeek API: {self.api_base}/chat/completions")
            logger.info(f"模型: {self.model}")

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"DeepSeek API 错误: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.exception(f"调用 DeepSeek API 失败: {e}")
            return None
