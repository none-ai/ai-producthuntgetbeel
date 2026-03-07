# -*- coding: utf-8 -*-
"""
数据解析器 / Data Parser
负责解析和格式化 Product Hunt 数据 / Responsible for parsing and formatting Product Hunt data
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from typing import TypedDict


class Product(TypedDict):
    """产品数据类型定义 / Product data type definition"""
    id: str
    name: str
    tagline: str
    description: Optional[str]
    url: str
    votes_count: int
    comments_count: int
    thumbnail_url: str
    makers: List[Dict[str, str]]
    published_at: str
    topics: List[str]
    day: str


class Parser:
    """
    数据解析器类 / Data Parser Class
    解析原始 API 数据为结构化格式 / Parses raw API data to structured format
    """

    @staticmethod
    def parse_product(product: Dict[str, Any]) -> Product:
        """
        解析单个产品数据 / Parse single product data

        Args:
            product: 原始产品数据 / Raw product data

        Returns:
            解析后的产品数据 / Parsed product data
        """
        # 解析缩略图 URL / Parse thumbnail URL
        thumbnail_url = ""
        thumbnail = product.get("thumbnail", {})
        if thumbnail:
            thumbnail_url = thumbnail.get("url", "")

        # 解析创作者信息 / Parse maker information
        makers = []
        maker_list = product.get("maker", [])
        if isinstance(maker_list, list):
            for maker in maker_list:
                if isinstance(maker, dict):
                    makers.append({
                        "name": maker.get("name", ""),
                        "username": maker.get("username", "")
                    })
        elif isinstance(maker_list, dict):
            # 单个创作者 / Single maker
            makers.append({
                "name": maker_list.get("name", ""),
                "username": maker_list.get("username", "")
            })

        # 解析话题/分类 / Parse topics/categories
        topics = []
        topics_edges = product.get("topics", {}).get("edges", [])
        for edge in topics_edges:
            topic = edge.get("node", {})
            if isinstance(topic, dict):
                topics.append(topic.get("name", ""))

        # 解析发布日期 / Parse published date
        published_at = product.get("publishedAt", "")
        day = ""
        if published_at:
            try:
                dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                day = dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                day = published_at[:10] if published_at else ""

        return Product(
            id=str(product.get("id", "")),
            name=product.get("name", ""),
            tagline=product.get("tagline", ""),
            description=product.get("description"),
            url=product.get("url", ""),
            votes_count=product.get("votesCount", 0),
            comments_count=product.get("commentsCount", 0),
            thumbnail_url=thumbnail_url,
            makers=makers,
            published_at=published_at,
            topics=topics,
            day=day
        )

    @staticmethod
    def parse_products(products: List[Dict[str, Any]]) -> List[Product]:
        """
        解析产品列表 / Parse products list

        Args:
            products: 原始产品列表 / Raw products list

        Returns:
            解析后的产品列表 / Parsed products list
        """
        return [Parser.parse_product(p) for p in products]

    @staticmethod
    def format_product_for_display(product: Product) -> Dict[str, str]:
        """
        格式化产品数据用于显示 / Format product data for display

        Args:
            product: 解析后的产品数据 / Parsed product data

        Returns:
            用于显示的产品数据 / Product data for display
        """
        # 格式化投票数 / Format votes count
        votes = product["votes_count"]
        if votes >= 1000:
            votes_display = f"{votes / 1000:.1f}k"
        else:
            votes_display = str(votes)

        # 格式化评论数 / Format comments count
        comments = product["comments_count"]
        if comments >= 1000:
            comments_display = f"{comments / 1000:.1f}k"
        else:
            comments_display = str(comments)

        # 格式化创作者 / Format makers
        makers_names = [m["name"] for m in product["makers"] if m.get("name")]
        makers_display = ", ".join(makers_names) if makers_names else "未知"

        return {
            "id": product["id"],
            "name": product["name"],
            "tagline": product["tagline"],
            "description": product.get("description", "") or product["tagline"],
            "url": product["url"],
            "votes_count": votes_display,
            "votes_raw": product["votes_count"],
            "comments_count": comments_display,
            "comments_raw": product["comments_count"],
            "thumbnail_url": product["thumbnail_url"],
            "makers": makers_display,
            "topics": ", ".join(product["topics"]) if product["topics"] else "",
            "published_at": product["published_at"],
            "day": product["day"]
        }

    @staticmethod
    def sort_products(
        products: List[Product],
        sort_by: str = "votes",
        reverse: bool = True
    ) -> List[Product]:
        """
        对产品列表排序 / Sort products list

        Args:
            products: 产品列表 / Products list
            sort_by: 排序字段 (votes, comments, name) / Sort field
            reverse: 是否倒序 / Whether to reverse order

        Returns:
            排序后的产品列表 / Sorted products list
        """
        if sort_by == "votes":
            return sorted(products, key=lambda p: p["votes_count"], reverse=reverse)
        elif sort_by == "comments":
            return sorted(products, key=lambda p: p["comments_count"], reverse=reverse)
        elif sort_by == "name":
            return sorted(products, key=lambda p: p["name"].lower(), reverse=False)
        else:
            return products

    @staticmethod
    def filter_products(
        products: List[Product],
        min_votes: int = 0,
        topics: Optional[List[str]] = None
    ) -> List[Product]:
        """
        过滤产品列表 / Filter products list

        Args:
            products: 产品列表 / Products list
            min_votes: 最小投票数 / Minimum votes
            topics: 话题过滤列表 / Topics filter list

        Returns:
            过滤后的产品列表 / Filtered products list
        """
        filtered = products

        # 按投票数过滤 / Filter by votes count
        if min_votes > 0:
            filtered = [p for p in filtered if p["votes_count"] >= min_votes]

        # 按话题过滤 / Filter by topics
        if topics:
            filtered = [
                p for p in filtered
                if any(topic.lower() in [t.lower() for t in p["topics"]] for topic in topics)
            ]

        return filtered
