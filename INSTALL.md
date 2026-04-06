# AutoBrowser

## 安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装 OpenCLI
npm install -g @jackwener/opencli

# 3. 配置小红书技能路径（如需要）
```

## 配置

编辑 `config/settings.yaml`：

```yaml
crawler:
  keywords:
    - "AI"
    - "OpenAI"
    - "Claude"
  sources:
    - twitter
    - reddit
  limit: 10
  interval_hours: 3
```

## 使用

```bash
# 立即执行一次
python main.py --run-once

# 启动定时任务（每3小时）
python main.py --start

# 小红书登录
python main.py --login
```

## 依赖

- Python 3.8+
- Node.js + OpenCLI
- Chrome 浏览器
- 小红书自动化技能
