# -*- coding: utf-8 -*-
"""
GetBeel 邮件通知模块 / Email Notification Module
提供邮件通知功能 / Provides email notification functionality
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
import config


class EmailNotifier:
    """邮件通知类 / Email Notifier Class"""

    def __init__(self):
        """初始化邮件通知 / Initialize email notification"""
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.to_email = os.getenv("TO_EMAIL", "")

    def is_configured(self) -> bool:
        """
        检查邮件配置是否完整 / Check if email configuration is complete

        Returns:
            是否已配置 / Whether configured
        """
        return bool(
            self.smtp_host and
            self.smtp_user and
            self.smtp_password and
            self.to_email
        )

    def send_email(
        self,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        发送邮件 / Send email

        Args:
            subject: 邮件主题 / Email subject
            body: 邮件正文 / Email body
            html_body: HTML 格式正文 / HTML body

        Returns:
            是否发送成功 / Whether sent successfully
        """
        if not self.is_configured():
            print("邮件配置不完整，请检查环境变量")
            return False

        try:
            # 创建邮件 / Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.to_email

            # 添加纯文本正文 / Add plain text body
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)

            # 添加 HTML 正文（如果有）/ Add HTML body (if available)
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)

            # 连接 SMTP 服务器并发送 / Connect to SMTP server and send
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            print(f"邮件发送成功: {subject}")
            return True

        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

    def send_products_notification(self, products: List[Dict[str, Any]]) -> bool:
        """
        发送产品更新通知 / Send products update notification

        Args:
            products: 产品列表 / Products list

        Returns:
            是否发送成功 / Whether sent successfully
        """
        if not products:
            return False

        subject = f"Product Hunt 热门产品更新 - {len(products)} 个新产品"

        # 构建纯文本正文 / Build plain text body
        body = "今日 Product Hunt 热门产品：\n\n"
        for i, product in enumerate(products[:10], 1):
            body += f"{i}. {product.get('name')}\n"
            body += f"   {product.get('tagline')}\n"
            body += f"   投票: {product.get('votesCount', 0)} | 评论: {product.get('commentsCount', 0)}\n"
            body += f"   链接: {product.get('url')}\n\n"

        # 构建 HTML 正文 / Build HTML body
        html_body = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .product { margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }
                .product-name { font-size: 18px; font-weight: bold; color: #333; }
                .product-tagline { color: #666; margin: 5px 0; }
                .product-stats { color: #888; font-size: 14px; }
                .product-link a { color: #0066cc; }
            </style>
        </head>
        <body>
            <h2>Product Hunt 热门产品更新</h2>
        """

        for product in products[:10]:
            html_body += f"""
            <div class="product">
                <div class="product-name">{product.get('name')}</div>
                <div class="product-tagline">{product.get('tagline')}</div>
                <div class="product-stats">
                    投票: {product.get('votesCount', 0)} | 评论: {product.get('commentsCount', 0)}
                </div>
                <div class="product-link">
                    <a href="{product.get('url')}">查看产品</a>
                </div>
            </div>
            """

        html_body += "</body></html>"

        return self.send_email(subject, body, html_body)


class ProductAlert:
    """产品提醒类 / Product Alert Class"""

    def __init__(self):
        """初始化产品提醒 / Initialize product alert"""
        self.alerts_file = config.DATA_DIR / "alerts.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保提醒文件存在 / Ensure alerts file exists"""
        if not self.alerts_file.exists():
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_alerts([])

    def _load_alerts(self) -> List[Dict[str, Any]]:
        """加载提醒配置 / Load alerts"""
        import json
        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_alerts(self, alerts: List[Dict[str, Any]]):
        """保存提醒配置 / Save alerts"""
        import json
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)

    def add_alert(
        self,
        product_name: str,
        threshold: int,
        alert_type: str = "votes"
    ) -> bool:
        """
        添加产品提醒 / Add product alert

        Args:
            product_name: 产品名称 / Product name
            threshold: 阈值 / Threshold
            alert_type: 提醒类型 (votes/comments) / Alert type

        Returns:
            是否添加成功 / Whether added successfully
        """
        alerts = self._load_alerts()

        # 检查是否已存在 / Check if already exists
        for alert in alerts:
            if alert['product_name'] == product_name and alert['alert_type'] == alert_type:
                return False

        alerts.append({
            'product_name': product_name,
            'threshold': threshold,
            'alert_type': alert_type,
            'created_at': self._get_timestamp()
        })

        self._save_alerts(alerts)
        return True

    def remove_alert(self, product_name: str, alert_type: str = "votes") -> bool:
        """
        移除产品提醒 / Remove product alert

        Args:
            product_name: 产品名称 / Product name
            alert_type: 提醒类型 / Alert type

        Returns:
            是否移除成功 / Whether removed successfully
        """
        alerts = self._load_alerts()
        original_count = len(alerts)

        alerts = [
            a for a in alerts
            if not (a['product_name'] == product_name and a['alert_type'] == alert_type)
        ]

        if len(alerts) < original_count:
            self._save_alerts(alerts)
            return True
        return False

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        获取所有提醒 / Get all alerts

        Returns:
            提醒列表 / Alerts list
        """
        return self._load_alerts()

    def check_alerts(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检查产品是否达到提醒阈值 / Check if products reached alert threshold

        Args:
            products: 产品列表 / Products list

        Returns:
            触发的提醒列表 / Triggered alerts list
        """
        alerts = self._load_alerts()
        triggered = []

        for product in products:
            product_name = product.get('name', '')
            votes = product.get('votesCount', 0)
            comments = product.get('commentsCount', 0)

            for alert in alerts:
                if alert['product_name'].lower() in product_name.lower():
                    threshold = alert['threshold']
                    alert_type = alert['alert_type']

                    if alert_type == "votes" and votes >= threshold:
                        triggered.append({
                            'product': product,
                            'alert': alert,
                            'current_value': votes
                        })
                    elif alert_type == "comments" and comments >= threshold:
                        triggered.append({
                            'product': product,
                            'alert': alert,
                            'current_value': comments
                        })

        return triggered

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳 / Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
