# GetBeel - Product Hunt 数据获取工具

[English](./README_en.md) | 中文

## 项目简介

GetBeel 是一个用于获取和展示 Product Hunt 每日热门产品的 Python 工具。它提供命令行界面和 Web 界面两种使用方式，帮助用户快速获取 Product Hunt 上的热门产品信息。

## 功能特性

- 获取 Product Hunt 今日热门产品
- 支持数据缓存，提高访问速度
- Web 界面展示，友好用户体验
- 支持数据导出（JSON 格式）
- 命令行和 Web 两种运行模式

## 项目结构

```
getbeel/
├── main.py              # 主入口文件
├── config.py            # 配置文件
├── api.py               # Product Hunt API 客户端
├── parser.py            # 数据解析器
├── storage.py           # 数据存储模块
├── web.py               # Flask Web 应用
├── requirements.txt     # 项目依赖
├── templates/          # HTML 模板目录
│   ├── index.html
│   ├── products.html
│   ├── product.html
│   ├── error.html
│   └── cache.html
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
| `export` | 导出产品数据到 JSON |
| `export -o file.json` | 指定输出文件名 |
| `web` | 启动 Web 服务器 |
| `web -d` | 调试模式启动 |
| `cache clear` | 清除所有缓存 |
| `cache info` | 查看缓存信息 |

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PRODUCT_HUNT_TOKEN` | Product Hunt API Token | - |
| `DEBUG` | 调试模式 | `False` |
| `HOST` | Web 服务器地址 | `0.0.0.0` |
| `PORT` | Web 服务器端口 | `5000` |

## API 说明

### 模块功能

- **api.py**: Product Hunt GraphQL API 客户端，包含请求重试、速率限制处理等功能
- **parser.py**: 数据解析器，将原始 API 数据转换为结构化格式
- **storage.py**: 本地存储模块，提供缓存和数据导出功能
- **web.py**: Flask Web 应用，提供 Web 界面

### 主要类

- `APIClient`: Product Hunt API 客户端类
- `Parser`: 数据解析器类
- `Storage`: 数据存储类

## 依赖

- Python >= 3.8
- requests >= 2.28.0
- flask >= 2.3.0
- python-dotenv >= 1.0.0
- beautifulsoup4 >= 4.12.0 (可选)

## 注意事项

1. 使用 API 功能需要 Product Hunt API Token，未配置时只能使用 Web 界面的演示数据
2. 缓存有效期为 24 小时
3. 建议在生产环境修改 `config.py` 中的 `SECRET_KEY`

## 许可证

MIT License
