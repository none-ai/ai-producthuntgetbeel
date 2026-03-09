# -*- coding: utf-8 -*-
"""
GetBeel 统计模块 / Statistics Module
提供产品数据分析功能 / Provides product data analysis functionality
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import config


class Statistics:
    """统计类 / Statistics Class"""

    def __init__(self):
        """初始化统计模块 / Initialize statistics"""
        self.stats_file = config.DATA_DIR / "statistics.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保统计文件存在 / Ensure statistics file exists"""
        if not self.stats_file.exists():
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_stats({})

    def _load_stats(self) -> Dict[str, Any]:
        """加载统计数据 / Load statistics data"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_stats(self, stats: Dict[str, Any]):
        """保存统计数据 / Save statistics data"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

    def record_fetch(self, product_count: int):
        """记录一次数据获取 / Record a data fetch"""
        stats = self._load_stats()

        today = datetime.now().strftime("%Y-%m-%d")

        if 'fetches' not in stats:
            stats['fetches'] = []

        stats['fetches'].append({
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'count': product_count
        })

        # 保留最近30天的记录 / Keep last 30 days records
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        stats['fetches'] = [
            f for f in stats['fetches'] if f['date'] >= cutoff_date
        ]

        self._save_stats(stats)

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取每日统计数据 / Get daily statistics

        Args:
            days: 天数 / Number of days

        Returns:
            每日统计数据列表 / Daily statistics list
        """
        stats = self._load_stats()
        fetches = stats.get('fetches', [])

        # 按日期分组 / Group by date
        daily_data = {}
        for fetch in fetches:
            date = fetch['date']
            if date not in daily_data:
                daily_data[date] = {'count': 0, 'fetches': 0}
            daily_data[date]['count'] += fetch['count']
            daily_data[date]['fetches'] += 1

        # 转换为列表 / Convert to list
        result = [
            {'date': date, 'products': data['count'], 'fetches': data['fetches']}
            for date, data in sorted(daily_data.items(), reverse=True)
        ]

        return result[:days]

    def get_total_stats(self) -> Dict[str, Any]:
        """
        获取总体统计 / Get total statistics

        Returns:
            总体统计数据 / Total statistics
        """
        stats = self._load_stats()
        fetches = stats.get('fetches', [])

        total_products = sum(f['count'] for f in fetches)
        total_fetches = len(fetches)

        return {
            'total_products': total_products,
            'total_fetches': total_fetches,
            'avg_products_per_fetch': total_products / total_fetches if total_fetches > 0 else 0
        }

    def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门产品排行 / Get top products ranking

        Args:
            limit: 返回数量 / Return count

        Returns:
            热门产品列表 / Top products list
        """
        storage = config.storage if hasattr(config, 'storage') else None

        if not storage:
            from storage import Storage
            storage = Storage()

        # 从缓存中获取历史产品 / Get historical products from cache
        all_products = []

        # 获取今日产品 / Get today's products
        today_products = storage.get_products("today")
        if today_products:
            for p in today_products:
                all_products.append({
                    'name': p.get('name'),
                    'votes': p.get('votesCount', 0),
                    'comments': p.get('commentsCount', 0)
                })

        # 排序 / Sort
        all_products.sort(key=lambda x: x['votes'], reverse=True)

        return all_products[:limit]

    def get_category_distribution(self) -> Dict[str, int]:
        """
        获取分类分布 / Get category distribution

        Returns:
            分类统计数据 / Category statistics
        """
        storage = None
        try:
            from storage import Storage
            storage = Storage()
        except ImportError:
            return {}

        distribution = {}
        products = storage.get_products("today") if storage else []

        for product in products:
            topics = product.get('topics', {}).get('edges', [])
            for edge in topics:
                topic = edge.get('node', {})
                name = topic.get('name', 'Unknown')
                distribution[name] = distribution.get(name, 0) + 1

        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
