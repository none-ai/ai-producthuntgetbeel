# -*- coding: utf-8 -*-
"""
Webhook 通知模块 / Webhook Notification Module
发送产品更新通知 / Send product update notifications
"""

import json
import requests
from typing import List, Dict, Any, Optional
import config


class WebhookNotifier:
    """
    Webhook 通知类 / Webhook Notification Class
    通过 Webhook 发送产品更新通知 / Send product update notifications via Webhook
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """
        初始化 Webhook 通知器 / Initialize Webhook Notifier

        Args:
            webhook_url: Webhook URL
        """
        self.webhook_url = webhook_url or config.WEBHOOK_URL
        self.enabled = config.WEBHOOK_ENABLED and bool(self.webhook_url)

    def send_notification(self, products: List[Dict[str, Any]], title: str = None) -> bool:
        """
        发送产品更新通知 / Send product update notification

        Args:
            products: 产品列表 / Products list
            title: 通知标题 / Notification title

        Returns:
            是否发送成功 / Whether sent successfully
        """
        if not self.enabled:
            print("Webhook 通知未启用")
            return False

        if not self.webhook_url:
            print("未配置 Webhook URL")
            return False

        try:
            payload = {
                "title": title or "Product Hunt 热门产品更新",
                "description": f"今日热门产品已更新，共 {len(products)} 个产品",
                "products": [
                    {
                        "name": p.get("name", ""),
                        "tagline": p.get("tagline", ""),
                        "votes": p.get("votes_raw", p.get("votes_count", "")),
                        "url": p.get("url", "")
                    }
                    for p in products[:10]  # 只发送前10个
                ],
                "total_count": len(products),
                "timestamp": self._get_timestamp()
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in (200, 201, 204):
                print(f"Webhook 通知发送成功")
                return True
            else:
                print(f"Webhook 通知发送失败: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Webhook 请求错误: {e}")
            return False

    def send_new_product_alert(self, product: Dict[str, Any], min_votes: int = 100) -> bool:
        """
        发送新产品提醒 / Send new product alert

        Args:
            product: 产品数据 / Product data
            min_votes: 最小投票数阈值 / Minimum votes threshold

        Returns:
            是否发送成功 / Whether sent successfully
        """
        votes = product.get("votes_raw", product.get("votes_count", 0))

        if votes < min_votes:
            return False

        if not self.enabled:
            return False

        try:
            payload = {
                "title": f"🔥 热门产品提醒: {product.get('name', '')}",
                "description": product.get("tagline", ""),
                "product": {
                    "name": product.get("name", ""),
                    "tagline": product.get("tagline", ""),
                    "votes": votes,
                    "comments": product.get("comments_raw", product.get("comments_count", 0)),
                    "makers": product.get("makers", ""),
                    "url": product.get("url", "")
                },
                "timestamp": self._get_timestamp()
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            return response.status_code in (200, 201, 204)

        except requests.exceptions.RequestException as e:
            print(f"Webhook 请求错误: {e}")
            return False

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳 / Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


def test_webhook(webhook_url: str) -> bool:
    """
    测试 Webhook / Test Webhook

    Args:
        webhook_url: Webhook URL

    Returns:
        是否成功 / Whether successful
    """
    try:
        payload = {
            "title": "GetBeel Webhook 测试",
            "description": "这是一条测试消息",
            "timestamp": WebhookNotifier._get_timestamp()
        }

        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code in (200, 201, 204):
            print("Webhook 测试成功!")
            return True
        else:
            print(f"Webhook 测试失败: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Webhook 请求错误: {e}")
        return False
