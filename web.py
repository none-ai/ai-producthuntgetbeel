# -*- coding: utf-8 -*-
"""
Web 应用模块 / Web Application Module
使用 Flask 构建的 Web 界面 / Web interface built with Flask
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, Response
from typing import Dict, Any, List, Optional
import config
from api import APIClient, ProductHuntAPIError, RateLimitError
from storage import Storage
from parser import Parser, Product
from rss import RSSFeed
from webhook import WebhookNotifier
from favorites import Favorites
from statistics import Statistics

# 创建 Flask 应用 / Create Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

# 初始化 API 客户端和存储 / Initialize API client and storage
api_client = APIClient()
storage = Storage()
webhook_notifier = WebhookNotifier()


@app.route("/health")
def health_check():
    """
    健康检查端点 / Health check endpoint
    检查 API 配置和缓存状态 / Check API configuration and cache status
    """
    health_status = {
        "status": "healthy",
        "api_configured": bool(config.PRODUCT_HUNT_TOKEN),
        "cache": {},
        "version": config.APP_VERSION
    }

    # 检查缓存状态 / Check cache status
    try:
        cache_info = storage.get_cache_info()
        health_status["cache"] = cache_info
    except Exception as e:
        health_status["cache"] = {"error": str(e)}
        health_status["status"] = "degraded"

    # 如果未配置 API Token，返回警告状态 / Return warning status if API token not configured
    if not config.PRODUCT_HUNT_TOKEN:
        health_status["status"] = "warning"
        health_status["message"] = "API Token 未配置，部分功能可能不可用"

    status_code = 200 if health_status["status"] == "healthy" else 206
    return jsonify(health_status), status_code


@app.route("/")
def index():
    """
    首页 - 显示今日产品 / Home page - Shows today's products
    """
    return render_template("index.html")


@app.route("/products")
def products():
    """
    产品列表页面 / Products list page
    支持排序和过滤 / Supports sorting and filtering
    """
    # 获取查询参数 / Get query parameters
    sort_by = request.args.get("sort", "votes")
    min_votes = int(request.args.get("min_votes", "0"))
    category = request.args.get("category", "today")
    topic = request.args.get("topic", "")

    # 从缓存获取数据 / Get data from cache
    products = storage.get_products(category)

    # 如果缓存为空，尝试获取新数据 / If cache is empty, try to get new data
    if not products:
        try:
            raw_products = api_client.get_today_products(limit=30)
            storage.save_products(raw_products, category="today")
            products = storage.get_products("today")
        except (ProductHuntAPIError, RateLimitError) as e:
            return render_template(
                "error.html",
                error_message=f"获取产品数据失败: {str(e)}"
            )

    # 按话题过滤 / Filter by topic
    if topic:
        products = [p for p in products if topic.lower() in p.get("topics", "").lower()]

    # 排序 / Sort
    if sort_by == "votes":
        products = sorted(products, key=lambda x: x.get("votes_raw", 0), reverse=True)
    elif sort_by == "comments":
        products = sorted(products, key=lambda x: x.get("comments_raw", 0), reverse=True)
    elif sort_by == "name":
        products = sorted(products, key=lambda x: x.get("name", "").lower())

    # 过滤 / Filter
    if min_votes > 0:
        products = [p for p in products if p.get("votes_raw", 0) >= min_votes]

    return render_template(
        "products.html",
        products=products,
        sort_by=sort_by,
        min_votes=min_votes,
        current_topic=topic
    )


@app.route("/history")
def history():
    """
    历史产品页面 / Historical products page
    """
    # 获取所有历史日期 / Get all historical dates
    dates = storage.get_all_historical_dates()
    selected_date = request.args.get("date", "")

    products = []
    if selected_date:
        products = storage.get_historical_products(selected_date)

    return render_template(
        "history.html",
        dates=dates,
        selected_date=selected_date,
        products=products
    )


@app.route("/rss")
def rss_feed():
    """
    RSS 订阅源 / RSS Feed
    """
    # 获取产品数据 / Get products data
    products = storage.get_products("today")

    if not products:
        try:
            raw_products = api_client.get_today_products(limit=20)
            storage.save_products(raw_products, category="today")
            products = storage.get_products("today")
        except (ProductHuntAPIError, RateLimitError):
            products = []

    # 生成 RSS / Generate RSS
    feed = RSSFeed()
    feed.add_products(products)

    format_type = request.args.get("format", "rss")
    if format_type == "atom":
        xml = feed.get_atom_feed()
    else:
        xml = feed.generate()

    return Response(xml, mimetype="application/rss+xml")


@app.route("/api/products")
def api_products():
    """
    API 端点 - 获取产品列表 / API endpoint - Get products list
    """
    try:
        # 尝试从缓存获取 / Try to get from cache
        products = storage.get_products("today")

        if not products:
            # 获取新产品数据 / Get new product data
            raw_products = api_client.get_today_products(limit=20)
            storage.save_products(raw_products, "today")
            products = storage.get_products("today")

        return jsonify({
            "success": True,
            "data": products,
            "count": len(products)
        })

    except (ProductHuntAPIError, RateLimitError) as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/refresh")
def api_refresh():
    """
    API 端点 - 刷新产品数据 / API endpoint - Refresh product data
    """
    try:
        # 清除缓存并获取新数据 / Clear cache and get new data
        storage.clear_cache("today")
        raw_products = api_client.get_today_products(limit=20)
        storage.save_products(raw_products, "today")

        # 发送 webhook 通知 / Send webhook notification
        products = storage.get_products("today")
        webhook_notifier.send_notification(products)

        return jsonify({
            "success": True,
            "message": "数据刷新成功",
            "count": len(raw_products)
        })

    except (ProductHuntAPIError, RateLimitError) as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/webhook/test", methods=["POST"])
def api_webhook_test():
    """
    测试 Webhook / Test Webhook
    """
    data = request.get_json() or {}
    webhook_url = data.get("webhook_url", config.WEBHOOK_URL)

    if not webhook_url:
        return jsonify({
            "success": False,
            "error": "未提供 Webhook URL"
        }), 400

    from webhook import test_webhook
    success = test_webhook(webhook_url)

    return jsonify({
        "success": success,
        "message": "测试成功" if success else "测试失败"
    })


@app.route("/product/<product_id>")
def product_detail(product_id: str):
    """
    产品详情页面 / Product detail page
    """
    try:
        # 尝试从 API 获取详情 / Try to get details from API
        product = api_client.get_product_by_id(product_id)

        if not product:
            # 如果 API 失败，从缓存中查找 / If API fails, search in cache
            products = storage.get_products("today")
            product = next((p for p in products if str(p.get("id")) == product_id), None)

        if not product:
            return render_template(
                "error.html",
                error_message="未找到产品"
            )

        return render_template("product.html", product=product)

    except ProductHuntAPIError as e:
        return render_template(
            "error.html",
            error_message=f"获取产品详情失败: {str(e)}"
        )


@app.route("/cache/info")
def cache_info():
    """
    缓存信息页面 / Cache information page
    """
    info = storage.get_cache_info()
    return render_template("cache.html", cache_info=info)


@app.route("/cache/clear")
def cache_clear():
    """
    清除缓存页面 / Clear cache page
    """
    storage.clear_cache()
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(error):
    """404 错误处理 / 404 error handler"""
    return render_template("error.html", error_message="页面未找到"), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理 / 500 error handler"""
    return render_template("error.html", error_message="服务器内部错误"), 500


def create_app() -> Flask:
    """
    创建并配置 Flask 应用 / Create and configure Flask application

    Returns:
        配置好的 Flask 应用 / Configured Flask application
    """
    return app


def run_server(host: Optional[str] = None, port: Optional[int] = None, debug: bool = False):
    """
    运行 Flask 服务器 / Run Flask server

    Args:
        host: 主机地址 / Host address
        port: 端口号 / Port number
        debug: 是否开启调试模式 / Whether to enable debug mode
    """
    host = host or config.HOST
    port = port or config.PORT
    debug = debug or config.DEBUG

    print(f"启动 GetBeel 服务: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)
