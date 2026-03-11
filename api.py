# -*- coding: utf-8 -*-
"""
Product Hunt API 客户端 / Product Hunt API Client
负责与 Product Hunt API 交互 / Responsible for interacting with Product Hunt API
"""

import json
import time
import requests
from typing import Dict, List, Optional, Any
import config


class ProductHuntAPIError(Exception):
    """API 错误异常 / API Error Exception"""
    pass


class RateLimitError(Exception):
    """速率限制异常 / Rate Limit Exception"""
    pass


class APIClient:
    """
    Product Hunt API 客户端类 / Product Hunt API Client Class
    提供 GraphQL API 调用方法 / Provides GraphQL API call methods
    """

    def __init__(self, token: Optional[str] = None):
        """
        初始化 API 客户端 / Initialize API Client

        Args:
            token: Product Hunt API token，如果为 None 则使用配置中的 token
                   Product Hunt API token, uses config token if None
        """
        self.token = token or config.PRODUCT_HUNT_TOKEN
        self.url = config.PRODUCT_HUNT_API_URL
        self.timeout = config.REQUEST_TIMEOUT
        self.max_retries = config.MAX_RETRIES
        self.proxy = self._get_proxy()

        if not self.token:
            print("警告: 未设置 Product Hunt API Token，请设置 PRODUCT_HUNT_TOKEN 环境变量")
            print("Warning: Product Hunt API Token not set, please set PRODUCT_HUNT_TOKEN env variable")

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """
        获取代理配置 / Get Proxy Configuration

        Returns:
            代理字典，None 表示不使用代理 / Proxy dictionary, None means no proxy
        """
        http_proxy = config.HTTP_PROXY
        https_proxy = config.HTTPS_PROXY

        if not http_proxy and not https_proxy:
            return None

        proxies = {}
        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy

        return proxies if proxies else None

    def _get_headers(self) -> Dict[str, str]:
        """
        获取请求头 / Get Request Headers

        Returns:
            请求头字典 / Request header dictionary
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

    def _make_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        retries: int = 0
    ) -> Dict[str, Any]:
        """
        发起 GraphQL 请求 / Make GraphQL Request

        Args:
            query: GraphQL 查询语句 / GraphQL query statement
            variables: 查询变量 / Query variables
            retries: 当前重试次数 / Current retry count

        Returns:
            API 响应数据 / API response data

        Raises:
            ProductHuntAPIError: API 错误 / API Error
            RateLimitError: 速率限制 / Rate Limit
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }

        try:
            response = requests.post(
                self.url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
                proxies=self.proxy
            )

            # 检查 HTTP 状态码 / Check HTTP status code
            if response.status_code == 429:
                if retries < self.max_retries:
                    wait_time = 2 ** retries  # 指数退避 / Exponential backoff
                    print(f"触发速率限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    return self._make_request(query, variables, retries + 1)
                raise RateLimitError("请求频率过高，请稍后再试")

            if response.status_code != 200:
                raise ProductHuntAPIError(f"API 请求失败: {response.status_code} - {response.text}")

            data = response.json()

            # 检查 GraphQL 错误 / Check GraphQL errors
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "未知错误")
                raise ProductHuntAPIError(f"GraphQL 错误: {error_msg}")

            return data.get("data", {})

        except requests.exceptions.Timeout:
            if retries < self.max_retries:
                return self._make_request(query, variables, retries + 1)
            raise ProductHuntAPIError("请求超时")

        except requests.exceptions.RequestException as e:
            raise ProductHuntAPIError(f"网络请求错误: {str(e)}")

    def get_today_products(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取今日产品列表 / Get Today's Products List

        Args:
            limit: 返回数量限制 / Return quantity limit

        Returns:
            产品列表 / Products list
        """
        query = config.GET_TODAY_PRODUCTS_QUERY.replace("first: 20", f"first: {limit}")
        data = self._make_request(query)

        products = []
        edges = data.get("posts", {}).get("edges", [])

        for edge in edges:
            node = edge.get("node", {})
            products.append(node)

        return products

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取产品详情 / Get Product Details by ID

        Args:
            product_id: 产品 ID / Product ID

        Returns:
            产品详情，失败返回 None / Product details, returns None on failure
        """
        query = """
        query GetProduct($id: ID!) {
            post(id: $id) {
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
            }
        }
        """

        try:
            data = self._make_request(query, {"id": product_id})
            return data.get("post")
        except ProductHuntAPIError:
            return None

    def search_products(
        self,
        search_term: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索产品 / Search Products

        Args:
            search_term: 搜索关键词 / Search keyword
            category: 分类（可选）/ Category (optional)
            limit: 返回数量限制 / Return quantity limit

        Returns:
            产品列表 / Products list
        """
        # 构建搜索查询 / Build search query
        query = """
        query SearchPosts($term: String!, $first: Int!) {
            searchPosts(query: $term, first: $first) {
                edges {
                    node {
                        id
                        name
                        tagline
                        url
                        votesCount
                        thumbnail {
                            url
                        }
                    }
                }
            }
        }
        """

        try:
            data = self._make_request(query, {"term": search_term, "first": limit})
            edges = data.get("searchPosts", {}).get("edges", [])
            return [edge.get("node", {}) for edge in edges]
        except ProductHuntAPIError:
            return []

    def get_products_by_date(self, date: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取指定日期的产品列表 / Get products for a specific date

        Args:
            date: 日期字符串 (YYYY-MM-DD) / Date string (YYYY-MM-DD)
            limit: 返回数量限制 / Return quantity limit

        Returns:
            产品列表 / Products list
        """
        # 构建日期范围 / Build date range
        from datetime import datetime, timedelta
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            next_date = target_date + timedelta(days=1)
            date_after = target_date.strftime("%Y-%m-%dT00:00:00Z")
            date_before = next_date.strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            raise ProductHuntAPIError("日期格式错误，请使用 YYYY-MM-DD 格式")

        query = """
        query GetPostsByDate($dateAfter: Datetime!, $dateBefore: Datetime!, $first: Int!) {
            posts(postedAfter: $dateAfter, postedBefore: $dateBefore, order: VOTES, first: $first) {
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

        try:
            data = self._make_request(query, {
                "dateAfter": date_after,
                "dateBefore": date_before,
                "first": limit
            })

            products = []
            edges = data.get("posts", {}).get("edges", [])

            for edge in edges:
                node = edge.get("node", {})
                products.append(node)

            return products
        except ProductHuntAPIError:
            return []

    def get_categories(self) -> List[Dict[str, Any]]:
        """
        获取产品分类列表 / Get categories list

        Returns:
            分类列表 / Categories list
        """
        query = """
        query {
            topics(first: 50) {
                edges {
                    node {
                        id
                        name
                        slug
                    }
                }
            }
        }
        """

        try:
            data = self._make_request(query)
            edges = data.get("topics", {}).get("edges", [])
            return [edge.get("node", {}) for edge in edges]
        except ProductHuntAPIError:
            return []

    def get_products_by_date_range(self, start_date: str, end_date: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取指定日期范围的产品列表 / Get products for a date range

        Args:
            start_date: 开始日期 (YYYY-MM-DD) / Start date (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD) / End date (YYYY-MM-DD)
            limit: 返回数量限制 / Return quantity limit

        Returns:
            产品列表 / Products list
        """
        from datetime import datetime, timedelta
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            date_after = start.strftime("%Y-%m-%dT00:00:00Z")
            date_before = (end + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            raise ProductHuntAPIError("日期格式错误，请使用 YYYY-MM-DD 格式")

        query = """
        query GetPostsByDateRange($dateAfter: Datetime!, $dateBefore: Datetime!, $first: Int!) {
            posts(postedAfter: $dateAfter, postedBefore: $dateBefore, order: VOTES, first: $first) {
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

        try:
            data = self._make_request(query, {
                "dateAfter": date_after,
                "dateBefore": date_before,
                "first": limit
            })

            products = []
            edges = data.get("posts", {}).get("edges", [])

            for edge in edges:
                node = edge.get("node", {})
                products.append(node)

            return products
        except ProductHuntAPIError:
            return []
