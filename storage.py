# -*- coding: utf-8 -*-
"""
数据存储模块 / Data Storage Module
负责产品数据的本地存储和缓存 / Responsible for local storage and caching of product data
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import config
from parser import Product, Parser


class StorageError(Exception):
    """存储错误异常 / Storage Error Exception"""
    pass


class Storage:
    """
    数据存储类 / Data Storage Class
    提供数据持久化和缓存功能 / Provides data persistence and caching functionality
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化存储 / Initialize Storage

        Args:
            data_dir: 数据目录路径 / Data directory path
        """
        self.data_dir = data_dir or config.DATA_DIR
        self.cache_file = config.CACHE_FILE
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """确保数据目录存在 / Ensure data directory exists"""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_cache_file(self) -> None:
        """确保缓存文件存在 / Ensure cache file exists"""
        if not self.cache_file.exists():
            self._save_cache({})

    def _load_cache(self) -> Dict[str, Any]:
        """
        加载缓存数据 / Load cache data

        Returns:
            缓存数据字典 / Cache data dictionary
        """
        try:
            self._ensure_cache_file()
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载缓存失败: {e}")
            return {}

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """
        保存缓存数据 / Save cache data

        Args:
            data: 要保存的数据 / Data to save
        """
        try:
            self._ensure_data_dir()
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise StorageError(f"保存缓存失败: {e}")

    def save_products(self, products: List[Product], category: str = "today") -> None:
        """
        保存产品数据到缓存 / Save products data to cache

        Args:
            products: 产品列表 / Products list
            category: 数据分类 / Data category
        """
        cache = self._load_cache()

        # 解析并保存产品数据 / Parse and save products data
        parsed_products = Parser.parse_products(products)
        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        cache[category] = {
            "data": formatted_products,
            "updated_at": datetime.now().isoformat(),
            "count": len(formatted_products)
        }

        self._save_cache(cache)
        print(f"已保存 {len(formatted_products)} 个产品到缓存")

    def get_products(self, category: str = "today") -> List[Dict[str, Any]]:
        """
        从缓存获取产品数据 / Get products data from cache

        Args:
            category: 数据分类 / Data category

        Returns:
            产品列表 / Products list
        """
        cache = self._load_cache()
        category_data = cache.get(category, {})

        if not category_data:
            return []

        # 检查缓存是否过期（24小时）/ Check if cache is expired (24 hours)
        updated_at = category_data.get("updated_at", "")
        if updated_at:
            try:
                updated_time = datetime.fromisoformat(updated_at)
                age = datetime.now() - updated_time
                if age.total_seconds() > 24 * 3600:
                    print("缓存已过期")
                    return []
            except (ValueError, AttributeError):
                pass

        return category_data.get("data", [])

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息 / Get cache information

        Returns:
            缓存信息字典 / Cache information dictionary
        """
        cache = self._load_cache()
        info = {}

        for category, data in cache.items():
            if isinstance(data, dict):
                info[category] = {
                    "count": data.get("count", 0),
                    "updated_at": data.get("updated_at", "")
                }

        return info

    def clear_cache(self, category: Optional[str] = None) -> None:
        """
        清除缓存 / Clear cache

        Args:
            category: 要清除的分类，None 表示清除所有 / Category to clear, None means clear all
        """
        if category is None:
            self._save_cache({})
            print("已清除所有缓存")
        else:
            cache = self._load_cache()
            if category in cache:
                del cache[category]
                self._save_cache(cache)
                print(f"已清除 {category} 缓存")

    def export_to_json(self, filepath: Path, category: str = "today") -> None:
        """
        导出数据到 JSON 文件 / Export data to JSON file

        Args:
            filepath: 导出文件路径 / Export file path
            category: 数据分类 / Data category
        """
        products = self.get_products(category)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            print(f"已导出 {len(products)} 个产品到 {filepath}")
        except IOError as e:
            raise StorageError(f"导出失败: {e}")

    def import_from_json(self, filepath: Path, category: str = "imported") -> int:
        """
        从 JSON 文件导入数据 / Import data from JSON file

        Args:
            filepath: 导入文件路径 / Import file path
            category: 数据分类 / Data category

        Returns:
            导入的产品数量 / Number of imported products
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                products = json.load(f)

            if not isinstance(products, list):
                raise StorageError("JSON 文件格式错误，应为产品数组")

            cache = self._load_cache()
            cache[category] = {
                "data": products,
                "updated_at": datetime.now().isoformat(),
                "count": len(products)
            }
            self._save_cache(cache)

            print(f"已从 {filepath} 导入 {len(products)} 个产品")
            return len(products)

        except (json.JSONDecodeError, IOError) as e:
            raise StorageError(f"导入失败: {e}")
