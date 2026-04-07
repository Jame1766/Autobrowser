#!/usr/bin/env python3
"""
小红书发布详细测试 - 捕获完整输出
"""
import subprocess
import json

print("=" * 70)
print("小红书发布详细测试")
print("=" * 70)

# 构建命令
title = "🧪 测试"
content = "测试内容"
images = "/Users/wangzihan/Autobrowser/assets/default.jpg"
topics = "AI,人工智能,科技前沿"

cmd = [
    'opencli', 'xiaohongshu', 'publish', content,
    '--title', title,
    '--images', images,
    '--topics', topics,
    '--format', 'json',
    '--verbose'
]

print(f"\n执行命令:")
print(f"  {' '.join(cmd)}")
print(f"\n等待执行（约30-60秒）...\n")

result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=180
)

print("=" * 70)
print("返回码:", result.returncode)
print("=" * 70)

print("\n【标准输出 stdout】")
print(result.stdout)

print("\n【标准错误 stderr】")
print(result.stderr)

print("\n【JSON 解析】")
try:
    data = json.loads(result.stdout)
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"解析失败: {e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
