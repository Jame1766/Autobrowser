#!/usr/bin/env python3
"""
小红书发布测试 - 使用 OpenCLI
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.publisher.xiaohongshu import XiaohongshuPublisher

print("=" * 60)
print("小红书发布测试 (OpenCLI)")
print("=" * 60)

# 初始化发布器
publisher = XiaohongshuPublisher()

# 1. 检查登录状态
print("\n1. 检查登录状态...")
status = publisher.get_login_status()
if status['success']:
    print("   ✅ 已登录")
    print(f"   用户信息: {status['output'][:200]}...")
else:
    print("   ❌ 未登录或检查失败")
    print(f"   错误: {status.get('error', 'Unknown')}")
    print("\n   请先在小红书创作者中心登录")
    print("   步骤:")
    print("   1. 启动 Chrome: python scripts/chrome_launcher.py")
    print("   2. 访问 https://creator.xiaohongshu.com")
    print("   3. 扫码登录")

# 2. 发布测试内容
print("\n2. 发布测试内容...")
test_title = "🧪 AI自动化测试"
test_content = "这是一篇测试内容，验证自动化发布流程是否正常。\n\n今天测试了自动爬取和发布系统 ✅"

print(f"   标题: {test_title}")
print(f"   内容: {test_content[:50]}...")

result = publisher.publish(
    title=test_title,
    content=test_content,
    images=['/Users/wangzihan/Autobrowser/assets/default.jpg'],
    draft=True
)

if result['success']:
    print("\n   ✅ 发布成功！")
    print(f"   输出: {result['output'][:300]}...")
else:
    print("\n   ❌ 发布失败")
    print(f"   错误: {result['message']}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
