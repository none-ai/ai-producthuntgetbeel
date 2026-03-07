# -*- coding: utf-8 -*-
"""
Web 应用模块 / Web Application Module
使用 Flask 构建的 Web 界面 / Web interface built with Flask
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from typing import Dict, Any, List, Optional
import config
from api import APIClient, ProductHuntAPIError, RateLimitError
from storage import Storage
from parser import Parser, Product

# 创建 Flask 应用 / Create Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "getbeel-secret-key-change-in-production"

# 初始化 API 客户端和存储 / Initialize API client and storage
api_client = APIClient()
storage = Storage()


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
        min_votes=min_votes
    )


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
