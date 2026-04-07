"""
Kimi AI 处理模块
调用 Moonshot AI API 进行内容处理
"""
import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from src.config import config

logger = logging.getLogger(__name__)

class KimiProcessor:
    """Kimi AI 内容处理器"""

    def __init__(self):
        self.api_key = config.get('kimi.api_key', '')
        self.api_base = config.get('kimi.api_base', 'https://api.moonshot.cn/v1')
        self.model = config.get('kimi.model', 'moonshot-v1-8k')
        self.temperature = config.get('kimi.temperature', 0.7)

        if not self.api_key:
            logger.warning("Kimi API Key 未配置，请在 config/settings.yaml 中设置")

    def process_content(self, content: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        使用 Kimi AI 处理内容，生成小红书标题和正文

        Args:
            content: 原始内容（包含 title, content, platform 等）

        Returns:
            处理后的标题和正文
        """
        if not self.api_key:
            logger.error("Kimi API Key 未配置")
            return None

        try:
            # 构建 prompt
            prompt = self._build_prompt(content)

            # 调用 Kimi API
            response = self._call_api(prompt)

            if not response:
                return None

            # 解析响应
            result = self._parse_response(response)

            logger.info(f"Kimi 处理完成")
            logger.info(f"  标题: {result['title']}")
            logger.info(f"  正文长度: {len(result['content'])} 字符")

            return result

        except Exception as e:
            logger.exception(f"Kimi 处理失败: {e}")
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

        prompt = f"""你是一位专业的小红书内容运营专家。请将以下{platform}上的AI相关内容转化为适合小红书平台的中文笔记。

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
  * 🔥 {话题}重磅发布！AI圈都炸了
  * 💡 救命！这个{话题}让我效率翻倍
  * 🚀 {话题}必备！大厂都在用的黑科技
  * ⚡️ 别再直接问AI了！试试这个{话题}
  * 🎯 反直觉！{话题}的正确打开方式

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

        return prompt

    def _call_api(self, prompt: str) -> Optional[str]:
        """调用 Kimi API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
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

    def _parse_response(self, response: str) -> Dict[str, str]:
        """解析 Kimi 响应"""
        try:
            # 尝试提取 JSON
            # 先尝试直接解析
            try:
                data = json.loads(response)
                return {
                    'title': data.get('title', ''),
                    'content': data.get('content', ''),
                    'cover_text': data.get('cover_text', '')
                }
            except json.JSONDecodeError:
                pass

            # 尝试从 markdown 代码块中提取
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return {
                    'title': data.get('title', ''),
                    'content': data.get('content', ''),
                    'cover_text': data.get('cover_text', '')
                }

            # 如果都没找到，返回原始内容
            logger.warning("无法解析 Kimi 响应为 JSON，返回原始内容")
            return {
                'title': response[:20] if len(response) > 20 else response,
                'content': response[:200] if len(response) > 200 else response,
                'cover_text': 'AI资讯'
            }

        except Exception as e:
            logger.exception(f"解析 Kimi 响应失败: {e}")
            return {
                'title': '🔥 AI资讯',
                'content': '内容生成失败',
                'cover_text': 'AI资讯'
            }
