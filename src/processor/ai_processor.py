"""
AI 处理模块（支持多模型：Kimi/DeepSeek）
统一的 AI 内容处理接口
"""
import json
import logging
import os
import requests
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from src.config import config

logger = logging.getLogger(__name__)


class BaseAIProcessor(ABC):
    """AI 处理器基类"""

    def __init__(self, provider: str):
        self.provider = provider
        self.api_key = self._get_api_key()
        self.api_base = self._get_api_base()
        self.model = self._get_model()
        self.temperature = self._get_temperature()

    def _get_api_key(self) -> str:
        """获取 API Key（优先环境变量）"""
        env_var = f"{self.provider.upper()}_API_KEY"
        return os.environ.get(env_var, config.get(f'ai.{self.provider}.api_key', ''))

    def _get_api_base(self) -> str:
        """获取 API Base URL"""
        return config.get(f'ai.{self.provider}.api_base', '')

    def _get_model(self) -> str:
        """获取模型名称"""
        return config.get(f'ai.{self.provider}.model', '')

    def _get_temperature(self) -> float:
        """获取 temperature"""
        return config.get(f'ai.{self.provider}.temperature', 1.0)

    def process_content(self, content: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        处理内容，生成小红书标题和正文

        Args:
            content: 原始内容

        Returns:
            处理后的标题、正文、封面文字
        """
        if not self.api_key:
            logger.error(f"{self.provider} API Key 未配置")
            return None

        try:
            prompt = self._build_prompt(content)
            response = self._call_api(prompt)

            if not response:
                return None

            result = self._parse_response(response)
            result = self._format_result(result)

            logger.info(f"{self.provider} 处理完成")
            logger.info(f"  标题: {result['title']}")
            logger.info(f"  正文长度: {len(result['content'])} 字符")

            return result

        except Exception as e:
            logger.exception(f"{self.provider} 处理失败: {e}")
            return None

    def _build_prompt(self, content: Dict[str, Any]) -> str:
        """构建 Prompt"""
        original_title = content.get('title', '')
        original_content = content.get('content', '')
        platform = content.get('platform', '')
        author = content.get('author', '')
        engagement = content.get('engagement', {})

        # 构建互动信息
        engagement_info = ""
        if platform == 'twitter':
            likes = engagement.get('likes', 0)
            retweets = engagement.get('retweets', 0)
            engagement_info = f"点赞: {likes}, 转发: {retweets}"
        elif platform == 'reddit':
            upvotes = engagement.get('upvotes', 0)
            comments = engagement.get('comments', 0)
            engagement_info = f"赞同: {upvotes}, 评论: {comments}"

        return f"""你是一位专业的小红书内容运营专家。请将以下{platform}上的AI相关内容转化为适合小红书平台的中文笔记。

## 原始内容

**原标题（英文）**: {original_title}

**正文内容**:
{original_content[:1000]}

**来源**: {platform}
**作者**: {author}
**互动数据**: {engagement_info}

## 小红书转化要求

请严格按照以下规则生成内容：

### 1. 标题要求（必须遵守）
- 长度：最多20个字（含emoji）
- 风格：吸引眼球、有爆款潜质
- 必须包含emoji（如🔥、💡、🚀、⚡️、🎯等）
- 使用以下一种模板风格：
  * 🔥 AI重磅发布！AI圈都炸了
  * 💡 救命！这个AI工具让我效率翻倍
  * 🚀 AI必备！大厂都在用的黑科技
  * ⚡️ 别再直接问AI了！试试这个Prompt
  * 🎯 反直觉！AI的正确打开方式

### 2. 正文要求（必须遵守）
- 总长度控制在200个字符以内（确保能自动发布成功）
- 结构清晰，使用emoji分隔
- 语言风格：口语化、亲切、短句
- 必须包含以下部分：
  * 🔥 Hook: 引起兴趣（1句）
  * 📌 核心内容（2-3句，总结要点）
  * ✨ 价值点（1句）
  * 💬 CTA引导互动（1句）
  * 🏷️ 话题标签（必须包含：#AI资讯 #人工智能 #科技前沿）
  * 🔗 来源提示（"详情见评论"）

### 3. 输出格式（必须严格遵守）
请按照以下JSON格式输出，不要添加任何其他内容：

```json
{{
  "title": "生成的标题（20字以内，带emoji）",
  "content": "生成的正文（200字以内，使用\\n换行）",
  "cover_text": "用于封面的文字（4-8个字，提炼标题核心）"
}}
```

注意：
1. 只输出JSON，不要有任何解释文字
2. 确保JSON格式正确，可以被解析
3. 标题和正文必须中文
4. cover_text 用于生成封面图片，要简洁有力
"""

    @abstractmethod
    def _call_api(self, prompt: str) -> Optional[str]:
        """调用 AI API（子类实现）"""
        pass

    def _parse_response(self, response: str) -> Dict[str, str]:
        """解析 AI 响应"""
        try:
            # 尝试直接解析 JSON
            try:
                data = json.loads(response)
                return data
            except json.JSONDecodeError:
                pass

            # 尝试从 markdown 代码块中提取
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data

            # 如果都没找到，返回原始内容
            logger.warning(f"无法解析 {self.provider} 响应为 JSON，返回原始内容")
            return {
                'title': response[:20] if len(response) > 20 else response,
                'content': response[:200] if len(response) > 200 else response,
                'cover_text': 'AI资讯'
            }

        except Exception as e:
            logger.exception(f"解析 {self.provider} 响应失败: {e}")
            return {
                'title': '🔥 AI资讯',
                'content': '内容生成失败',
                'cover_text': 'AI资讯'
            }

    def _format_result(self, data: dict) -> Dict[str, str]:
        """格式化结果，确保长度限制"""
        title = data.get('title', '🔥 AI资讯')
        content = data.get('content', '')
        cover_text = data.get('cover_text', 'AI资讯')

        # 确保标题不超过20字
        if len(title) >= 20:
            title = title[:18] + '…'

        # 确保内容不超过200字
        if len(content) > 200:
            content = content[:197] + '...'

        # 确保封面文字不超过10字
        if len(cover_text) > 10:
            cover_text = cover_text[:9] + '…'

        return {
            'title': title,
            'content': content,
            'cover_text': cover_text
        }


class KimiProcessor(BaseAIProcessor):
    """Kimi AI 处理器"""

    def __init__(self):
        super().__init__('kimi')
        # 设置默认值
        if not self.api_base:
            self.api_base = 'https://api.moonshot.cn/v1'
        if not self.model:
            self.model = 'kimi-k2.5'

    def _call_api(self, prompt: str) -> Optional[str]:
        """调用 Kimi API"""
        try:
            # 优先使用 OpenAI SDK
            try:
                from openai import OpenAI

                client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                )

                completion = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是小红书内容运营专家，擅长将 AI 资讯转化为小红书爆款笔记格式。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature
                )

                return completion.choices[0].message.content

            except ImportError:
                logger.warning("未安装 openai sdk，使用 requests 调用")

            # 使用 requests 直接调用
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
                "temperature": self.temperature
            }

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
                logger.error(f"Kimi API 错误: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.exception(f"调用 Kimi API 失败: {e}")
            return None


class DeepSeekProcessor(BaseAIProcessor):
    """DeepSeek AI 处理器"""

    def __init__(self):
        super().__init__('deepseek')
        # 设置默认值
        if not self.api_base:
            self.api_base = 'https://api.deepseek.com'
        if not self.model:
            self.model = 'deepseek-chat'

    def _call_api(self, prompt: str) -> Optional[str]:
        """调用 DeepSeek API"""
        try:
            # 优先使用 OpenAI SDK（DeepSeek 兼容 OpenAI 接口）
            try:
                from openai import OpenAI

                client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                )

                completion = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是小红书内容运营专家，擅长将 AI 资讯转化为小红书爆款笔记格式。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    stream=False
                )

                return completion.choices[0].message.content

            except ImportError:
                logger.warning("未安装 openai sdk，使用 requests 调用")

            # 使用 requests 直接调用（DeepSeek 格式）
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


class AIProcessorFactory:
    """AI 处理器工厂"""

    _processors = {
        'kimi': KimiProcessor,
        'deepseek': DeepSeekProcessor,
    }

    @classmethod
    def get_processor(cls, provider: str = None) -> BaseAIProcessor:
        """
        获取 AI 处理器

        Args:
            provider: 模型提供商（kimi/deepseek），默认从配置读取

        Returns:
            AI 处理器实例
        """
        if not provider:
            provider = config.get('ai.provider', 'kimi')

        provider = provider.lower()

        if provider not in cls._processors:
            logger.error(f"不支持的 AI 提供商: {provider}，使用默认 Kimi")
            provider = 'kimi'

        logger.info(f"使用 AI 处理器: {provider}")
        return cls._processors[provider]()

    @classmethod
    def register_processor(cls, name: str, processor_class: type):
        """注册新的处理器"""
        cls._processors[name.lower()] = processor_class


# 兼容旧代码的导入
# 使用工厂方法获取处理器实例
def get_ai_processor(provider: str = None) -> BaseAIProcessor:
    """获取 AI 处理器（兼容旧代码）"""
    return AIProcessorFactory.get_processor(provider)


# 为了向后兼容，保留 KimiProcessor 的直接导入
__all__ = ['BaseAIProcessor', 'KimiProcessor', 'DeepSeekProcessor', 'AIProcessorFactory', 'get_ai_processor']
