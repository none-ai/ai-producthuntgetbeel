# GetBeel - Product Hunt 数据获取工具

[English](./README_en.md) | 中文

## 项目简介

GetBeel 是一个用于获取和展示 Product Hunt 每日热门产品的 Python 工具。它提供命令行界面和 Web 界面两种使用方式，帮助用户快速获取 Product Hunt 上的热门产品信息。

## 功能特性

- 获取 Product Hunt 今日热门产品
- 支持历史产品数据获取（指定日期）
- 支持数据缓存，提高访问速度
- Web 界面展示，友好用户体验
- 支持数据导出（JSON、CSV 格式）
- RSS 订阅源支持
- 支持话题/分类过滤
- 命令行和 Web 两种运行模式
- 定时自动数据采集
- Webhook 通知支持

## 项目结构

```
getbeel/
├── main.py              # 主入口文件
├── config.py            # 配置文件
├── api.py               # Product Hunt API 客户端
├── parser.py            # 数据解析器
├── storage.py           # 数据存储模块
├── web.py               # Flask Web 应用
├── rss.py               # RSS 订阅源生成器
├── webhook.py           # Webhook 通知模块
├── requirements.txt     # 项目依赖
├── templates/          # HTML 模板目录
│   ├── index.html
│   ├── products.html
│   ├── product.html
│   ├── error.html
│   ├── cache.html
│   └── history.html
└── data/               # 数据存储目录（自动创建）
    └── cache.json
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 API Token

1. 访问 [Product Hunt API](https://api.producthunt.com/v2/docs) 获取 API Token
2. 设置环境变量：

```bash
export PRODUCT_HUNT_TOKEN="你的API_Token"
```

或者在 `.env` 文件中配置：

```
PRODUCT_HUNT_TOKEN=你的API_Token
```

### 使用方式

#### 1. 命令行模式

```bash
# 获取今日热门产品
python main.py fetch

# 获取更多产品
python main.py fetch --limit 50

# 导出数据到 JSON
python main.py export

# 导出到指定文件
python main.py export -o mydata.json

# 清除缓存
python main.py cache clear
```

#### 2. Web 服务器模式

```bash
# 启动 Web 服务器
python main.py web

# 调试模式启动
python main.py web --debug
```

启动后访问 `http://localhost:5000`

#### 3. 直接运行 Python 脚本

```bash
python web.py
```

## 命令行参数

| 命令 | 说明 |
|------|------|
| `fetch` | 获取 Product Hunt 热门产品 |
| `fetch -l 50` | 获取50个产品 |
| `fetch --no-save` | 获取但不保存到缓存 |
| `fetch -t AI` | 按话题过滤获取产品 |
| `fetch --topic design` | 按话题过滤获取产品 |
| `fetch -q` | 静默模式，减少输出 |
| `export` | 导出产品数据到 JSON |
| `export -f csv` | 导出为 CSV 格式 |
| `export -o file.json` | 指定输出文件名 |
| `export --json` | 以 JSON 格式输出到标准输出 |
| `history -d 2024-01-15` | 获取指定日期的历史产品 |
| `history --list` | 列出所有历史数据 |
| `yesterday` | 获取昨日热门产品 |
| `yesterday -l 20` | 获取昨日20个产品 |
| `yesterday --json` | JSON格式输出昨日产品 |
| `search <keyword>` | 搜索产品 |
| `search <keyword> -l 10` | 搜索并限制结果数量 |
| `search <keyword> --json` | 以 JSON 格式输出搜索结果 |
| `build-index` | 构建搜索索引 |
| `scheduler` | 启动定时数据采集任务 |
| `stats` | 显示产品统计数据 |
| `web` | 启动 Web 服务器 |
| `web -d` | 调试模式启动 |
| `cache clear` | 清除所有缓存 |
| `cache info` | 查看缓存信息 |
| `favorites list` | 查看收藏列表 |
| `favorites add` | 添加产品到收藏 |
| `favorites add -i <id>` | 根据ID添加收藏 |
| `favorites remove -i <id>` | 移除收藏 |
| `maker top` | 热门创作者排行 |
| `maker top -l 20` | 获取前20名创作者 |
| `maker top --json` | JSON格式输出创作者排行 |
| `maker trending` | 热门话题排行 |
| `maker trending -d 30` | 最近30天话题 |
| `maker trending --json` | JSON格式输出话题排行 |

## 新增功能

### RSS 订阅源
访问 `http://localhost:5000/rss` 获取 RSS 订阅源
- 支持 RSS 2.0 格式
- 支持 Atom 格式（`?format=atom`）

### Webhook 通知
配置环境变量启用 Webhook 通知：
```bash
export WEBHOOK_URL="your-webhook-url"
export WEBHOOK_ENABLED="true"
```

### 话题过滤
在产品列表页面可以使用话题过滤：
```
/products?topic=AI
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PRODUCT_HUNT_TOKEN` | Product Hunt API Token | - |
| `DEBUG` | 调试模式 | `False` |
| `HOST` | Web 服务器地址 | `0.0.0.0` |
| `PORT` | Web 服务器端口 | `5000` |
| `SECRET_KEY` | Flask 密钥（生产环境请修改） | - |
| `WEBHOOK_URL` | Webhook 通知 URL | - |
| `WEBHOOK_ENABLED` | 启用 Webhook | `False` |
| `SCHEDULER_ENABLED` | 启用定时任务 | `False` |
| `SCHEDULER_INTERVAL_HOURS` | 定时任务间隔（小时） | `6` |

## API 说明

### 模块功能

- **api.py**: Product Hunt GraphQL API 客户端，包含请求重试、速率限制处理等功能
- **parser.py**: 数据解析器，将原始 API 数据转换为结构化格式
- **storage.py**: 本地存储模块，提供缓存和数据导出功能
- **web.py**: Flask Web 应用，提供 Web 界面
- **rss.py**: RSS 订阅源生成器
- **webhook.py**: Webhook 通知模块

### 主要类

- `APIClient`: Product Hunt API 客户端类
- `Parser`: 数据解析器类
- `Storage`: 数据存储类
- `RSSFeed`: RSS 订阅源生成类
- `WebhookNotifier`: Webhook 通知类

## 依赖

- Python >= 3.8
- requests >= 2.28.0
- flask >= 2.3.0
- python-dotenv >= 1.0.0
- schedule >= 1.2.0
- beautifulsoup4 >= 4.12.0 (可选)

## 注意事项

1. 使用 API 功能需要 Product Hunt API Token，未配置时只能使用 Web 界面的演示数据
2. 缓存有效期为 24 小时
3. 建议在生产环境修改 `config.py` 中的 `SECRET_KEY`

作者: stlin256的openclaw
