# -*- coding: utf-8 -*-
"""
GetBeel Maker 模块 / Maker Module
提供产品创作者/开发者信息功能 / Provides product maker/creator information functionality
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
import config


class Maker:
    """Maker/创作者类 / Maker Class"""

    def __init__(self):
        """初始化 Maker 模块 / Initialize Maker module"""
        pass

    @staticmethod
    def extract_makers_from_products(products: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        从产品列表中提取创作者信息 / Extract maker info from products list

        Args:
            products: 产品列表 / Products list

        Returns:
            创作者字典 / Makers dictionary
        """
        makers = {}

        for product in products:
            # 获取创作者信息 / Get maker info
            maker_data = product.get('maker', {})
            if not maker_data:
                continue

            maker_name = maker_data.get('name', 'Unknown')
            maker_username = maker_data.get('username', '')

            if not maker_username:
                continue

            if maker_username not in makers:
                makers[maker_username] = {
                    'name': maker_name,
                    'username': maker_username,
                    'products': [],
                    'total_votes': 0,
                    'total_comments': 0,
                    'product_count': 0
                }

            # 添加产品信息 / Add product info
            makers[maker_username]['products'].append({
                'id': product.get('id'),
                'name': product.get('name'),
                'tagline': product.get('tagline'),
                'url': product.get('url'),
                'votes': product.get('votesCount', 0),
                'comments': product.get('commentsCount', 0),
                'thumbnail': product.get('thumbnail', {}).get('url')
            })

            # 更新统计数据 / Update statistics
            makers[maker_username]['total_votes'] += product.get('votesCount', 0)
            makers[maker_username]['total_comments'] += product.get('commentsCount', 0)
            makers[maker_username]['product_count'] += 1

        return makers

    @staticmethod
    def get_maker_profile(maker_username: str, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        获取创作者个人资料 / Get maker profile

        Args:
            maker_username: 创作者用户名 / Maker username
            products: 产品列表 / Products list

        Returns:
            创作者资料 / Maker profile
        """
        for product in products:
            maker_data = product.get('maker', {})
            if maker_data.get('username') == maker_username:
                return {
                    'username': maker_username,
                    'name': maker_data.get('name'),
                    'products': [],
                    'total_votes': 0,
                    'total_comments': 0,
                    'product_count': 0
                }

        return None

    @staticmethod
    def get_top_makers(products: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最热门创作者排行 / Get top makers ranking

        Args:
            products: 产品列表 / Products list
            limit: 返回数量 / Return count

        Returns:
            热门创作者列表 / Top makers list
        """
        makers = Maker.extract_makers_from_products(products)

        # 转换为列表并排序 / Convert to list and sort
        makers_list = list(makers.values())
        makers_list.sort(key=lambda x: x['total_votes'], reverse=True)

        return makers_list[:limit]


class ProductComparison:
    """产品比较类 / Product Comparison Class"""

    @staticmethod
    def compare_products(product_ids: List[str], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        比较多个产品 / Compare multiple products

        Args:
            product_ids: 产品 ID 列表 / Product IDs list
            products: 产品列表 / Products list

        Returns:
            比较结果列表 / Comparison results list
        """
        comparison = []

        for product_id in product_ids:
            product = next(
                (p for p in products if str(p.get('id')) == str(product_id)),
                None
            )
            if product:
                comparison.append({
                    'id': product.get('id'),
                    'name': product.get('name'),
                    'tagline': product.get('tagline'),
                    'votes': product.get('votesCount', 0),
                    'comments': product.get('commentsCount', 0),
                    'thumbnail': product.get('thumbnail', {}).get('url'),
                    'url': product.get('url'),
                    'topics': product.get('topics', {}).get('edges', [])
                })

        return comparison

    @staticmethod
    def get_statistics(products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取产品列表统计信息 / Get products list statistics

        Args:
            products: 产品列表 / Products list

        Returns:
            统计数据 / Statistics
        """
        if not products:
            return {
                'total_products': 0,
                'total_votes': 0,
                'total_comments': 0,
                'avg_votes': 0,
                'avg_comments': 0,
                'max_votes': 0,
                'min_votes': 0
            }

        votes = [p.get('votesCount', 0) for p in products]
        comments = [p.get('commentsCount', 0) for p in products]

        return {
            'total_products': len(products),
            'total_votes': sum(votes),
            'total_comments': sum(comments),
            'avg_votes': sum(votes) / len(votes) if votes else 0,
            'avg_comments': sum(comments) / len(comments) if comments else 0,
            'max_votes': max(votes) if votes else 0,
            'min_votes': min(votes) if votes else 0,
            'max_comments': max(comments) if comments else 0,
            'min_comments': min(comments) if comments else 0
        }


class TrendingProducts:
    """热门趋势类 / Trending Products Class"""

    def __init__(self):
        """初始化趋势模块 / Initialize trending module"""
        self.storage = None
        try:
            from storage import Storage
            self.storage = Storage()
        except ImportError:
            pass

    def get_weekly_trending(self) -> List[Dict[str, Any]]:
        """
        获取本周热门产品 / Get weekly trending products

        Returns:
            本周热门产品列表 / Weekly trending products list
        """
        return self._get_trending_products(days=7)

    def get_monthly_trending(self) -> List[Dict[str, Any]]:
        """
        获取本月热门产品 / Get monthly trending products

        Returns:
            本月热门产品列表 / Monthly trending products list
        """
        return self._get_trending_products(days=30)

    def _get_trending_products(self, days: int) -> List[Dict[str, Any]]:
        """
        获取指定天数内的热门产品 / Get trending products within specified days

        Args:
            days: 天数 / Number of days

        Returns:
            热门产品列表 / Trending products list
        """
        if not self.storage:
            return []

        all_products = []
        dates = self.storage.get_all_historical_dates()

        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # 收集指定天数内的产品 / Collect products within specified days
        for date in dates:
            if date >= cutoff_date:
                products = self.storage.get_historical_products(date)
                all_products.extend(products)

        # 如果没有历史数据，使用今日数据 / If no historical data, use today's data
        if not all_products:
            all_products = self.storage.get_products("today")

        # 按投票数排序 / Sort by votes
        all_products.sort(key=lambda x: x.get('votesCount', 0), reverse=True)

        # 去重 / Remove duplicates
        seen = set()
        unique_products = []
        for p in all_products:
            if p.get('id') not in seen:
                seen.add(p.get('id'))
                unique_products.append(p)

        return unique_products[:20]

    def get_trending_topics(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取热门话题/分类 / Get trending topics

        Args:
            days: 天数 / Number of days

        Returns:
            热门话题列表 / Trending topics list
        """
        if not self.storage:
            return []

        topic_counts = defaultdict(int)
        dates = self.storage.get_all_historical_dates()

        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        for date in dates:
            if date >= cutoff_date:
                products = self.storage.get_historical_products(date)
                for product in products:
                    topics = product.get('topics', {}).get('edges', [])
                    for edge in topics:
                        topic = edge.get('node', {})
                        name = topic.get('name', '')
                        if name:
                            topic_counts[name] += 1

        # 转换为列表并排序 / Convert to list and sort
        topics_list = [
            {'name': name, 'count': count}
            for name, count in topic_counts.items()
        ]
        topics_list.sort(key=lambda x: x['count'], reverse=True)

        return topics_list[:10]
