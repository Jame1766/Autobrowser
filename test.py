#!/usr/bin/env python3
"""
测试脚本 - 验证各模块功能
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.crawler.opencli_crawler import ContentCrawler
from src.storage.content_store import ContentStore
from src.processor.ai_processor import AIContentProcessor

print("=" * 60)
print("AutoBrowser 模块测试")
print("=" * 60)

# 1. 测试配置
print("\n✅ 配置模块测试")
print(f"   爬取关键词: {config.crawler.get('keywords')}")
print(f"   爬取间隔: {config.crawler.get('interval_hours')} 小时")
print(f"   爬取数量: {config.crawler.get('limit')}")

# 2. 测试存储
print("\n✅ 存储模块测试")
store = ContentStore(db_path="data/test.db")
print(f"   数据库路径: data/test.db")

# 3. 测试 AI 处理器
print("\n✅ AI 处理器测试")
ai = AIContentProcessor()
test_content = {
    'id': 'test123',
    'platform': 'twitter',
    'title': 'OpenAI releases GPT-5 with breakthrough capabilities',
    'content': 'The new model shows significant improvements in reasoning and coding tasks.',
    'url': 'https://twitter.com/test',
    'author': 'OpenAI',
    'created_at': 'Sun Apr 06 20:00:00 +0000 2026',
    'engagement': {'likes': 5000, 'retweets': 2000}
}
score, details = ai._calculate_detailed_score(test_content)
print(f"   测试内容评分: {score}分")
print(f"   评分详情: {details}")

# 4. 测试爬取（少量）
print("\n✅ 爬取模块测试")
crawler = ContentCrawler(config)
print("   爬取 Twitter 'AI' 关键词（2条）...")
contents = crawler.opencli.crawl('twitter', 'AI', 2)
print(f"   爬取成功: {len(contents)} 条")
if contents:
    print(f"   示例: {contents[0]['title'][:50]}...")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
