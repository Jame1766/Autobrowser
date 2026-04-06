"""
AI 内容处理模块
根据产品经理制定的规则实现内容审核和修改
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIContentProcessor:
    """AI 内容处理器 - 实现产品经理制定的评分和改写规则"""

    # 权威性来源关键词
    AUTHORITATIVE_SOURCES = [
        'openai', 'anthropic', 'claude', 'google', 'deepmind',
        'microsoft', 'meta', 'nvidia', 'stability ai',
        'mistral', 'cohere', 'ai2'
    ]

    # 爆款话题关键词
    TRENDING_TOPICS = [
        'gpt', 'claude', 'llama', 'gemini', 'midjourney',
        'stable diffusion', 'sora', 'agent', 'rag', 'fine-tuning',
        'multimodal', 'reasoning', 'code generation'
    ]

    # 标题模板
    TITLE_TEMPLATES = [
        "🔥 {topic}重磅发布！AI圈都炸了",
        "💡 救命！这个{topic}技巧让我效率翻倍",
        "🚀 {topic}必备！大厂都在用的黑科技",
        "⚡️ 别再直接问AI了！试试这个{topic}方法",
        "🎯 反直觉！{topic}的正确打开方式"
    ]

    def __init__(self):
        self.name = "AIContentProcessor"

    def review_and_select(self, contents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        AI 审核评分（产品经理规则）

        评分标准（满分11分）：
        - 时效性（24-48小时内）：+3分
        - 来源权威性（大厂/官方）：+3分
        - 话题热度（互动量）：+2分
        - 实用价值：+2分
        - 独家性：+1分

        入选门槛：≥5分，且必须有时效性
        发布决策：≥6分立即发布，4-6分可选发布，<4分跳过

        Args:
            contents: 待审核的内容列表

        Returns:
            选中的最佳内容，如果没有合适的返回 None
        """
        if not contents:
            logger.info("没有内容需要审核")
            return None

        scored_contents = []
        for content in contents:
            score, details = self._calculate_detailed_score(content)
            scored_contents.append({
                'score': score,
                'details': details,
                'content': content
            })

        # 按分数排序
        scored_contents.sort(key=lambda x: x['score'], reverse=True)

        # 选择最高分
        best = scored_contents[0]
        best_score = best['score']
        best_content = best['content']

        logger.info(f"AI 审核评分排名:")
        for i, item in enumerate(scored_contents[:3], 1):
            logger.info(f"  {i}. {item['content']['title'][:40]}... - {item['score']}分")

        # 入选门槛：≥5分，且必须有时效性
        if best_score >= 5.0 and best['details']['timeliness'] > 0:
            decision = "立即发布" if best_score >= 6 else "可选发布"
            logger.info(f"✅ 选中内容（{decision}）: {best_score}分")
            return best_content
        else:
            logger.info(f"❌ 没有内容达到发布标准（最高分: {best_score}分）")
            return None

    def _calculate_detailed_score(self, content: Dict[str, Any]) -> tuple:
        """
        计算详细评分

        Returns:
            (总分, 评分详情)
        """
        score = 0.0
        details = {
            'timeliness': 0,
            'authority': 0,
            'engagement': 0,
            'utility': 0,
            'exclusivity': 0
        }

        text = (content.get('title', '') + ' ' + content.get('content', '')).lower()
        engagement = content.get('engagement', {})

        # 1. 时效性（24-48小时内）：+3分
        created_at = content.get('created_at', '')
        if created_at:
            try:
                # 尝试解析时间
                content_time = self._parse_time(created_at)
                if content_time:
                    hours_ago = (datetime.now() - content_time).total_seconds() / 3600
                    if hours_ago <= 24:
                        details['timeliness'] = 3
                    elif hours_ago <= 48:
                        details['timeliness'] = 2
                    elif hours_ago <= 72:
                        details['timeliness'] = 1
            except Exception:
                pass
        score += details['timeliness']

        # 2. 来源权威性（大厂/官方）：+3分
        author = content.get('author', '').lower()
        for source in self.AUTHORITATIVE_SOURCES:
            if source in text or source in author:
                details['authority'] = 3
                break
        score += details['authority']

        # 3. 话题热度（互动量）：+2分
        if content['platform'] == 'twitter':
            likes = engagement.get('likes', 0)
            retweets = engagement.get('retweets', 0)
            total = likes + retweets * 2
            if total > 1000:
                details['engagement'] = 2
            elif total > 100:
                details['engagement'] = 1
        elif content['platform'] == 'reddit':
            upvotes = engagement.get('upvotes', 0)
            comments = engagement.get('comments', 0)
            if upvotes > 500 or comments > 50:
                details['engagement'] = 2
            elif upvotes > 100 or comments > 10:
                details['engagement'] = 1
        score += details['engagement']

        # 4. 实用价值（关键词匹配）：+2分
        utility_keywords = ['tutorial', 'guide', 'how to', 'tips', 'tricks',
                          'workflow', 'prompt', 'hack', '技巧', '教程']
        for kw in utility_keywords:
            if kw in text:
                details['utility'] = 2
                break
        if details['utility'] == 0:
            for topic in self.TRENDING_TOPICS:
                if topic in text:
                    details['utility'] = 1
                    break
        score += details['utility']

        # 5. 独家性（较少见的关键词组合）：+1分
        rare_keywords = ['breakthrough', 'exclusive', 'first look', '泄露', '首发']
        for kw in rare_keywords:
            if kw in text:
                details['exclusivity'] = 1
                break
        score += details['exclusivity']

        return score, details

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """解析时间字符串"""
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%a %b %d %H:%M:%S +0000 %Y',
            '%Y-%m-%d %H:%M:%S'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        return None

    def modify_for_xiaohongshu(self, content: Dict[str, Any]) -> Dict[str, str]:
        """
        将内容修改为适合小红书的格式

        改写规则（产品经理规则）：
        1. 标题设计（4种爆款模板）
        2. 正文结构：Hook → What → Why → How → CTA → Tags
        3. 语言风格：口语化、亲切、短句、适度情感表达
        4. 去除外链，替换为"详情见评论"

        Args:
            content: 原始内容

        Returns:
            修改后的标题和内容
        """
        original_title = content.get('title', '')
        original_content = content.get('content', '')
        platform = content.get('platform', '')

        # 生成标题
        modified_title = self._generate_title(original_title, original_content)

        # 生成正文
        modified_content = self._generate_body(original_title, original_content, platform)

        logger.info(f"✏️ AI 改写完成")
        logger.info(f"   原标题: {original_title[:50]}...")
        logger.info(f"   新标题: {modified_title}")

        return {
            'title': modified_title,
            'content': modified_content,
            'original_url': content.get('url', '')
        }

    def _generate_title(self, title: str, content: str) -> str:
        """生成爆款标题"""
        text = (title + ' ' + content).lower()

        # 提取核心话题
        topic = "AI"
        for t in self.TRENDING_TOPICS:
            if t in text:
                topic = t.title()
                break

        # 选择模板
        import random
        template = random.choice(self.TITLE_TEMPLATES)

        # 生成标题（控制在20字以内）
        new_title = template.format(topic=topic)
        if len(new_title) > 20:
            new_title = new_title[:19] + "…"

        return new_title

    def _generate_body(self, title: str, content: str, platform: str) -> str:
        """生成小红书正文"""
        # 清理内容
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        main_content = ' '.join(paragraphs[:3])  # 取前3段

        # 如果内容太长，截断
        if len(main_content) > 500:
            main_content = main_content[:497] + "..."

        # 构建正文结构
        body_parts = []

        # 1. Hook（引起兴趣）
        platform_name = "推特" if platform == "twitter" else "Reddit"
        body_parts.append(f"🔥 这个在 {platform_name} 上火了！")

        # 2. What（是什么）
        body_parts.append(f"\n📌 {title}")

        # 3. Why（为什么重要）
        body_parts.append(f"\n💡 核心看点：")
        body_parts.append(main_content[:200] + "..." if len(main_content) > 200 else main_content)

        # 4. Key Insight（关键洞察）
        body_parts.append("\n✨ 为什么值得关注：")
        body_parts.append("• 这是最新的 AI 进展")
        body_parts.append("• 对普通用户也有实用价值")
        body_parts.append("• 可能会改变未来的工作方式")

        # 5. CTA（引导互动）
        body_parts.append("\n💬 你怎么看？")
        body_parts.append("觉得这个技术有用吗？")
        body_parts.append("评论区聊聊你的想法～")

        # 6. Tags（话题标签）
        body_parts.append("\n🏷️ #AI资讯 #人工智能 #科技前沿 #AIGC #AI工具")

        # 7. 来源提示
        body_parts.append("\n🔗 详情见评论")

        return '\n'.join(body_parts)
