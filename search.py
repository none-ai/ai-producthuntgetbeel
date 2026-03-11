# -*- coding: utf-8 -*-
"""
Search Module - Provides product search functionality with enhanced relevance scoring
"""

import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import config


class SearchEngine:
    """Search engine for products with TF-IDF style relevance scoring"""

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

    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into words"""
        if not text:
            return set()
        # Simple tokenization: split on whitespace and punctuation
        words = text.lower().split()
        # Filter out short words and common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                     'to', 'of', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'as'}
        return {w.strip('.,!?;:()[]{}') for w in words if len(w) > 2 and w not in stopwords}

    def _calculate_tf(self, tokens: Set[str], document_tokens: List[str]) -> Dict[str, float]:
        """Calculate term frequency for each token"""
        if not document_tokens:
            return {}
        tf = {}
        for token in tokens:
            count = document_tokens.count(token)
            if count > 0:
                tf[token] = 1 + math.log(count)  # Logarithmic TF
        return tf

    def _calculate_idf(self, tokens: Set[str], all_documents: List[str]) -> Dict[str, float]:
        """Calculate inverse document frequency for each token"""
        n_docs = len(all_documents)
        if n_docs == 0:
            return {t: 0 for t in tokens}

        idf = {}
        for token in tokens:
            # Count documents containing the token
            doc_count = sum(1 for doc in all_documents if token in doc.lower().split())
            if doc_count > 0:
                idf[token] = math.log(n_docs / doc_count)
            else:
                idf[token] = 0
        return idf

    def _calculate_relevance_score(self, query: str, product_data: Dict[str, Any]) -> float:
        """Calculate relevance score using TF-IDF style approach"""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return 0

        searchable = product_data.get('searchable', '')
        doc_tokens = searchable.split()

        # Get all documents for IDF calculation
        index = self._load_index()
        all_docs = [p.get('searchable', '') for p in index.values()]

        # Calculate TF and IDF
        tf = self._calculate_tf(query_tokens, doc_tokens)
        idf = self._calculate_idf(query_tokens, all_docs)

        # Calculate TF-IDF score
        score = 0
        for token in query_tokens:
            tf_val = tf.get(token, 0)
            idf_val = idf.get(token, 0)
            score += tf_val * idf_val

        # Boost for exact name match
        name = product_data.get('name', '').lower()
        query_lower = query.lower()
        if query_lower in name:
            score += 10
        # Boost for exact tagline match
        tagline = product_data.get('tagline', '').lower()
        if query_lower in tagline:
            score += 5
        # Boost for topic match
        topics = product_data.get('topics', '').lower()
        if query_lower in topics:
            score += 3

        # Add votes as a factor
        score += math.log(product_data.get('votes', 0) + 1) * 0.1

        return score

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search products by query with enhanced relevance scoring

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching products sorted by relevance
        """
        if not query:
            return []

        index = self._load_index()
        query_lower = query.lower()

        results = []
        for product_id, product_data in index.items():
            if query_lower in product_data.get('searchable', ''):
                # Calculate relevance score
                score = self._calculate_relevance_score(query, product_data)
                results.append({
                    'id': product_id,
                    'name': product_data.get('name'),
                    'tagline': product_data.get('tagline'),
                    'url': product_data.get('url'),
                    'votes': product_data.get('votes'),
                    'comments': product_data.get('comments'),
                    'thumbnail': product_data.get('thumbnail'),
                    'topics': product_data.get('topics'),
                    'score': round(score, 2)
                })

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:limit]

    def get_all_indexed(self) -> List[Dict[str, Any]]:
        """Get all indexed products"""
        index = self._load_index()
        return list(index.values())
