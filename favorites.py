# -*- coding: utf-8 -*-
"""
GetBeel 收藏模块 / Favorites Module
提供产品收藏功能 / Provides product favorites functionality
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import config


class Favorites:
    """收藏夹类 / Favorites Class"""

    def __init__(self):
        """初始化收藏夹 / Initialize favorites"""
        self.favorites_file = config.DATA_DIR / "favorites.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保收藏文件存在 / Ensure favorites file exists"""
        if not self.favorites_file.exists():
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_favorites([])

    def _load_favorites(self) -> List[Dict[str, Any]]:
        """加载收藏数据 / Load favorites data"""
        try:
            with open(self.favorites_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_favorites(self, favorites: List[Dict[str, Any]]):
        """保存收藏数据 / Save favorites data"""
        with open(self.favorites_file, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)

    def add_favorite(self, product: Dict[str, Any]) -> bool:
        """
        添加收藏 / Add favorite

        Args:
            product: 产品数据 / Product data

        Returns:
            是否成功添加 / Whether successfully added
        """
        favorites = self._load_favorites()

        # 检查是否已收藏 / Check if already favorited
        product_id = product.get('id')
        if any(f.get('id') == product_id for f in favorites):
            return False

        # 添加收藏 / Add favorite
        favorites.append({
            'id': product_id,
            'name': product.get('name'),
            'tagline': product.get('tagline'),
            'url': product.get('url'),
            'votes_count': product.get('votesCount', 0),
            'thumbnail': product.get('thumbnail', {}).get('url'),
            'added_at': self._get_timestamp()
        })

        self._save_favorites(favorites)
        return True

    def remove_favorite(self, product_id: str) -> bool:
        """
        移除收藏 / Remove favorite

        Args:
            product_id: 产品 ID / Product ID

        Returns:
            是否成功移除 / Whether successfully removed
        """
        favorites = self._load_favorites()
        original_count = len(favorites)

        favorites = [f for f in favorites if f.get('id') != product_id]

        if len(favorites) < original_count:
            self._save_favorites(favorites)
            return True
        return False

    def get_favorites(self) -> List[Dict[str, Any]]:
        """
        获取所有收藏 / Get all favorites

        Returns:
            收藏列表 / Favorites list
        """
        return self._load_favorites()

    def is_favorited(self, product_id: str) -> bool:
        """
        检查产品是否已收藏 / Check if product is favorited

        Args:
            product_id: 产品 ID / Product ID

        Returns:
            是否已收藏 / Whether favorited
        """
        favorites = self._load_favorites()
        return any(f.get('id') == product_id for f in favorites)

    def clear_favorites(self):
        """清空所有收藏 / Clear all favorites"""
        self._save_favorites([])

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳 / Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
