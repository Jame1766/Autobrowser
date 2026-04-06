# AutoBrowser

自动爬取 X/Twitter、Reddit 的 AI 相关内容，并发布到小红书的自动化工具。

## 功能

- 每3小时自动爬取 AI 相关新闻
- AI 审核筛选优质内容
- AI 修改适配小红书格式
- 自动发布到小红书

## 技术栈

- OpenCLI: 爬取 X/Twitter、Reddit 内容
- 小红书自动化技能: 发布内容
- Python: 核心逻辑

## 目录结构

```
├── src/
│   ├── crawler/      # 爬取模块
│   ├── processor/    # 内容处理模块（AI审核/修改）
│   ├── publisher/    # 发布模块
│   ├── scheduler/    # 定时调度
│   └── config/       # 配置管理
├── data/             # 数据存储
├── logs/             # 日志文件
└── main.py           # 主入口
```

## 使用

```bash
python main.py
```

## 配置

编辑 `config/settings.yaml` 进行配置。
