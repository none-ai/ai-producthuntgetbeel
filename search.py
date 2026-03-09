# -*- coding: utf-8 -*-
"""
Search Module - Provides product search functionality
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import config


class SearchEngine:
    """Search engine for products"""

    def __init__(self):
        """Initialize search engine"""
        self.index_file = config.DATA_DIR / "search_index.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Ensure index file exists"""
        if not self.index_file.exists():
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_index({})

    def _load_index(self) -> Dict[str, Any]:
        """Load search index"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_index(self, index: Dict[str, Any]):
        """Save search index"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def build_index(self, products: List[Dict[str, Any]]):
        """Build search index from products"""
        index = {}

        for product in products:
            product_id = str(product.get('id', ''))
            if not product_id:
                continue

            # Create searchable text
            name = product.get('name', '').lower()
            tagline = product.get('tagline', '').lower()
            description = product.get('description', '').lower()
            topics = product.get('topics', '')

            # Handle topics as string or dict
            if isinstance(topics, dict):
                topics_list = []
                edges = topics.get('edges', [])
                for edge in edges:
                    if isinstance(edge, dict) and 'node' in edge:
                        topics_list.append(edge['node'].get('name', '').lower())
                topics = ' '.join(topics_list)

            searchable_text = f"{name} {tagline} {description} {topics}"

            index[product_id] = {
                'name': product.get('name'),
                'tagline': product.get('tagline'),
                'url': product.get('url'),
                'votes': product.get('votesCount', 0),
                'comments': product.get('commentsCount', 0),
                'thumbnail': product.get('thumbnail', {}).get('url'),
                'topics': topics,
                'searchable': searchable_text
            }

        self._save_index(index)

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search products by query

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching products
        """
        if not query:
            return []

        index = self._load_index()
        query_lower = query.lower()

        results = []
        for product_id, product_data in index.items():
            if query_lower in product_data.get('searchable', ''):
                results.append({
                    'id': product_id,
                    'name': product_data.get('name'),
                    'tagline': product_data.get('tagline'),
                    'url': product_data.get('url'),
                    'votes': product_data.get('votes'),
                    'comments': product_data.get('comments'),
                    'thumbnail': product_data.get('thumbnail'),
                    'topics': product_data.get('topics')
                })

        # Sort by votes
        results.sort(key=lambda x: x.get('votes', 0), reverse=True)
        return results[:limit]

    def get_all_indexed(self) -> List[Dict[str, Any]]:
        """Get all indexed products"""
        index = self._load_index()
        return list(index.values())
