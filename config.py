# -*- coding: utf-8 -*-
"""
GetBeel 配置文件 / Configuration file
提供应用所需的配置参数 / Provides configuration parameters for the application
"""

import os
from pathlib import Path

# 项目根目录 / Project root directory
BASE_DIR = Path(__file__).parent

# Product Hunt API 配置 / Product Hunt API Configuration
# 请在 https://api.producthunt.com/v2/docs 获取 API 密钥
# Please get API key from https://api.producthunt.com/v2/docs
PRODUCT_HUNT_API_URL = "https://api.producthunt.com/v2/api/graphql"
PRODUCT_HUNT_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN", "")

# 应用配置 / Application Configuration
APP_NAME = "GetBeel"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Flask 配置 / Flask Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

# 数据配置 / Data Configuration
CACHE_FILE = BASE_DIR / "data" / "cache.json"
DATA_DIR = BASE_DIR / "data"

# API 请求配置 / API Request Configuration
REQUEST_TIMEOUT = 30  # 超时时间（秒）/ Timeout in seconds
MAX_RETRIES = 3  # 最大重试次数 / Maximum retry attempts

# GraphQL 查询 / GraphQL Queries
GET_TODAY_PRODUCTS_QUERY = """
query {
    posts(order: VOTES, first: 20) {
        edges {
            node {
                id
                name
                tagline
                description
                url
                votesCount
                commentsCount
                thumbnail {
                    url
                }
                maker {
                    name
                    username
                }
                publishedAt
                topics {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
        }
    }
}
"""

# 分页配置 / Pagination Configuration
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
