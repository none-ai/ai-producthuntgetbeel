# -*- coding: utf-8 -*-
"""
RSS 订阅源模块 / RSS Feed Module
生成 Product Hunt 热门产品的 RSS 订阅源 / Generate RSS feed for Product Hunt popular products
"""

from datetime import datetime
from typing import List, Dict, Any
import config


class RSSFeed:
    """
    RSS 订阅源类 / RSS Feed Class
    生成符合 RSS 2.0 规范的订阅源 / Generate RSS 2.0 compliant feed
    """

    def __init__(self, title: str = None, description: str = None, link: str = None):
        """
        初始化 RSS 订阅源 / Initialize RSS Feed

        Args:
            title: 订阅源标题 / Feed title
            description: 订阅源描述 / Feed description
            link: 订阅源链接 / Feed link
        """
        self.title = title or config.RSS_FEED_TITLE
        self.description = description or config.RSS_FEED_DESCRIPTION
        self.link = link or "https://www.producthunt.com"
        self.items: List[Dict[str, str]] = []

    def add_item(self, product: Dict[str, Any]):
        """
        添加订阅项 / Add feed item

        Args:
            product: 产品数据 / Product data
        """
        item = {
            "title": product.get("name", ""),
            "link": product.get("url", ""),
            "description": product.get("tagline", ""),
            "guid": product.get("id", ""),
            "pubDate": product.get("published_at", ""),
            "votes": product.get("votes_count", ""),
            "comments": product.get("comments_count", ""),
            "makers": product.get("makers", ""),
            "topics": product.get("topics", "")
        }
        self.items.append(item)

    def add_products(self, products: List[Dict[str, Any]]):
        """
        添加多个产品 / Add multiple products

        Args:
            products: 产品列表 / Products list
        """
        for product in products:
            self.add_item(product)

    def generate(self) -> str:
        """
        生成 RSS XML / Generate RSS XML

        Returns:
            RSS XML 字符串 / RSS XML string
        """
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
            '  <channel>',
            f'    <title>{self._escape_xml(self.title)}</title>',
            f'    <description>{self._escape_xml(self.description)}</description>',
            f'    <link>{self._escape_xml(self.link)}</link>',
            f'    <pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")}</pubDate>',
            f'    <generator>GetBeel</generator>',
            '    <atom:link href="https://getbeel.example.com/rss" rel="self" type="application/rss+xml"/>'
        ]

        for item in self.items:
            xml_parts.extend([
                '    <item>',
                f'      <title>{self._escape_xml(item["title"])}</title>',
                f'      <link>{self._escape_xml(item["link"])}</link>',
                f'      <description><![CDATA[{item["description"]}]]></description>',
                f'      <guid isPermaLink="false">{self._escape_xml(item["guid"])}</guid>',
                f'      <pubDate>{self._format_date(item["pubDate"])}</pubDate>',
                f'      <votes>{item["votes"]}</votes>',
                f'      <comments>{item["comments"]}</comments>',
                '    </item>'
            ])

        xml_parts.extend([
            '  </channel>',
            '</rss>'
        ])

        return '\n'.join(xml_parts)

    @staticmethod
    def _escape_xml(text: str) -> str:
        """转义 XML 特殊字符 / Escape XML special characters"""
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    @staticmethod
    def _format_date(date_str: str) -> str:
        """格式化日期 / Format date"""
        if not date_str:
            return datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except (ValueError, AttributeError):
            return datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

    def get_atom_feed(self) -> str:
        """
        获取 Atom 格式订阅源 / Get Atom format feed

        Returns:
            Atom XML 字符串 / Atom XML string
        """
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<feed xmlns="http://www.w3.org/2005/Atom">',
            f'  <title>{self._escape_xml(self.title)}</title>',
            f'  <subtitle>{self._escape_xml(self.description)}</subtitle>',
            f'  <updated>{datetime.now().isoformat()}</updated>',
            f'  <id>urn:getbeel:feed</id>',
            '  <link href="https://getbeel.example.com/rss" rel="self"/>',
            '  <link href="https://www.producthunt.com"/>'
        ]

        for item in self.items:
            xml_parts.extend([
                '  <entry>',
                f'    <title>{self._escape_xml(item["title"])}</title>',
                f'    <link href="{self._escape_xml(item["link"])}"/>',
                f'    <id>urn:getbeel:product:{item["guid"]}</id>',
                f'    <updated>{self._format_date(item["pubDate"])}</updated>',
                f'    <summary>{self._escape_xml(item["description"])}</summary>',
                '  </entry>'
            ])

        xml_parts.append('</feed>')
        return '\n'.join(xml_parts)
