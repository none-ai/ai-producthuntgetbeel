# -*- coding: utf-8 -*-
"""
GetBeel 主入口文件 / GetBeel Main Entry Point
提供命令行和 Web 服务两种运行方式 / Provides both CLI and Web service run methods
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径 / Add project root to Python path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

import config
from api import APIClient, ProductHuntAPIError, RateLimitError
from storage import Storage, StorageError
from parser import Parser
from favorites import Favorites
from search import SearchEngine
from maker import Maker, TrendingProducts
from notification import EmailNotifier, ProductAlert


def fetch_products(limit: int = 20, save: bool = True, topic: str = None, quiet: bool = False, json_output: bool = False, min_votes: int = 0, sort: str = "votes"):
    """
    获取产品数据（命令行模式）/ Fetch products (CLI mode)

    Args:
        limit: 获取数量限制 / Fetch quantity limit
        save: 是否保存到缓存 / Whether to save to cache
        topic: 话题过滤 / Topic filter
        quiet: 静默模式，减少输出 / Quiet mode, reduce output
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
        min_votes: 最低投票数过滤 / Minimum votes filter
        sort: 排序方式 / Sort method (votes, comments, date)

    Returns:
    """
    import json
    if not quiet:
        print(f"正在获取 Product Hunt 今日热门产品 (最多 {limit} 个)...")

    if topic and not quiet:
        print(f"话题过滤: {topic}")

    if min_votes > 0 and not quiet:
        print(f"最低投票数过滤: {min_votes}")

    try:
        # 初始化 API 客户端 / Initialize API client
        api_client = APIClient()
        storage = Storage()

        # 获取产品数据 / Fetch products data
        products = api_client.get_today_products(limit=limit)

        if not products:
            if not quiet:
                print("未获取到任何产品数据")
            return

        if not quiet:
            print(f"成功获取 {len(products)} 个产品")

        # 解析产品数据 / Parse products data
        parsed_products = Parser.parse_products(products)

        # 按话题过滤 / Filter by topic
        if topic:
            topic_lower = topic.lower()
            filtered = []
            for p in parsed_products:
                topics = p.get('topics', [])
                if any(topic_lower in t.lower() for t in topics):
                    filtered.append(p)
            parsed_products = filtered
            if not quiet:
                print(f"话题过滤后剩余 {len(parsed_products)} 个产品")

        # 按最低投票数过滤 / Filter by minimum votes
        if min_votes > 0:
            filtered = [p for p in parsed_products if p.get('votes_count', 0) >= min_votes]
            parsed_products = filtered
            if not quiet:
                print(f"最低投票数过滤后剩余 {len(parsed_products)} 个产品")

        # 排序 / Sort products
        if sort == "votes":
            parsed_products.sort(key=lambda p: p.get('votes_count', 0), reverse=True)
        elif sort == "comments":
            parsed_products.sort(key=lambda p: p.get('comments_count', 0), reverse=True)
        elif sort == "date":
            parsed_products.sort(key=lambda p: p.get('published_at', ''), reverse=True)

        if sort and not quiet:
            sort_desc = {"votes": "投票数", "comments": "评论数", "date": "日期"}
            print(f"排序方式: {sort_desc.get(sort, sort)}")

        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        # JSON 格式输出 / JSON output
        if json_output:
            output_data = {
                "date": "today",
                "topic": topic,
                "min_votes": min_votes,
                "sort": sort,
                "count": len(formatted_products),
                "products": formatted_products
            }
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
            return

        # 显示产品列表 / Display products list
        if not quiet:
            filter_desc = ""
            if topic:
                filter_desc += f" - {topic}"
            if min_votes > 0:
                filter_desc += f" (投票数≥{min_votes})"
            print("\n" + "=" * 60)
            print(f"Product Hunt 今日热门产品{filter_desc}")
            print("=" * 60)

            for i, product in enumerate(formatted_products, 1):
                print(f"\n{i}. {product['name']}")
                print(f"   描述: {product['tagline']}")
                print(f"   🔥 投票: {product['votes_count']} | 💬 评论: {product['comments_count']}")
                print(f"   创作者: {product['makers']}")
                print(f"   链接: {product['url']}")

        # 保存到缓存 / Save to cache
        if save:
            storage.save_products(products)
            if not quiet:
                print("\n数据已保存到缓存")

    except ProductHuntAPIError as e:
        print(f"API 错误: {e}")
    except RateLimitError as e:
        print(f"速率限制: {e}")
    except Exception as e:
        print(f"未知错误: {e}")


def export_products(format: str = "json", output: str = "products.json", json_output: bool = False):
    """
    导出产品数据 / Export products data

    Args:
        format: 导出格式 (json/csv) / Export format
        output: 输出文件名 / Output filename
        json_output: 是否以 JSON 格式输出到标准输出 / Whether to output JSON to stdout
    """
    import json

    if not json_output:
        print(f"正在导出产品数据到 {output}...")

    try:
        storage = Storage()
        products = storage.get_products("today")

        if not products:
            print("缓存中没有产品数据，请先运行 fetch 命令获取数据")
            return

        # JSON 格式输出到标准输出 / JSON output to stdout
        if json_output:
            output_data = {
                "date": "today",
                "count": len(products),
                "products": products
            }
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
            return

        output_path = BASE_DIR / output

        if format == "csv":
            storage.export_to_csv(output_path)
        else:
            storage.export_to_json(output_path)

    except StorageError as e:
        print(f"导出错误: {e}")


def clear_cache():
    """清除所有缓存 / Clear all cache"""
    print("正在清除缓存...")

    try:
        storage = Storage()
        storage.clear_cache()
        print("缓存已清除")

    except StorageError as e:
        print(f"清除缓存错误: {e}")


def list_favorites():
    """列出所有收藏的产品 / List all favorited products"""
    try:
        favorites = Favorites()
        fav_list = favorites.get_favorites()

        if not fav_list:
            print("暂无收藏产品")
            return

        print("\n" + "=" * 60)
        print("收藏的产品列表")
        print("=" * 60)

        for i, fav in enumerate(fav_list, 1):
            print(f"\n{i}. {fav['name']}")
            print(f"   描述: {fav.get('tagline', 'N/A')}")
            print(f"   🔥 投票: {fav.get('votes_count', 0)}")
            print(f"   链接: {fav.get('url', 'N/A')}")
            print(f"   收藏时间: {fav.get('added_at', 'N/A')}")

        print(f"\n共收藏 {len(fav_list)} 个产品")

    except Exception as e:
        print(f"错误: {e}")


def add_favorite(product_id: str = None):
    """
    添加产品到收藏 / Add product to favorites

    Args:
        product_id: 产品 ID / Product ID
    """
    try:
        favorites = Favorites()
        storage = Storage()

        # 如果没有提供 ID，从缓存中选择 / If no ID provided, select from cache
        if not product_id:
            products = storage.get_products("today")
            if not products:
                print("缓存中没有产品数据，请先运行 fetch 命令获取数据")
                return

            print("请选择要收藏的产品:")
            for i, p in enumerate(products, 1):
                print(f"  {i}. {p.get('name', 'N/A')} - {p.get('tagline', 'N/A')}")

            try:
                choice = int(input("\n请输入产品编号: ")) - 1
                if choice < 0 or choice >= len(products):
                    print("无效的选择")
                    return
                product = products[choice]
            except ValueError:
                print("请输入有效的数字")
                return
        else:
            # 从缓存中查找产品 / Find product from cache
            products = storage.get_products("today")
            product = None
            for p in products:
                if str(p.get('id')) == str(product_id):
                    product = p
                    break

            if not product:
                print(f"未找到 ID 为 {product_id} 的产品")
                return

        if favorites.add_favorite(product):
            print(f"已将 {product.get('name')} 添加到收藏")
        else:
            print(f"{product.get('name')} 已经存在于收藏中")

    except Exception as e:
        print(f"错误: {e}")


def remove_favorite(product_id: str):
    """移除收藏 / Remove from favorites"""
    try:
        favorites = Favorites()

        if favorites.remove_favorite(product_id):
            print(f"已从收藏中移除产品")
        else:
            print(f"未找到 ID 为 {product_id} 的收藏")

    except Exception as e:
        print(f"错误: {e}")


def run_web(debug: bool = False):
    """
    运行 Web 服务器 / Run Web server

    Args:
        debug: 是否开启调试模式 / Whether to enable debug mode
    """
    from web import run_server

    print(f"启动 GetBeel Web 服务 (调试模式: {debug})")
    run_server(debug=debug)


def fetch_yesterday_products(limit: int = 20, topic: str = None, quiet: bool = False, json_output: bool = False):
    """
    获取昨日产品数据 / Fetch yesterday's products data

    Args:
        limit: 获取数量限制 / Fetch quantity limit
        topic: 话题过滤 / Topic filter
        quiet: 静默模式，减少输出 / Quiet mode, reduce output
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    from datetime import datetime, timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    fetch_historical_products(date=yesterday, limit=limit, topic=topic, quiet=quiet, json_output=json_output)


def fetch_weekly_products(limit: int = 50, topic: str = None, quiet: bool = False, json_output: bool = False):
    """
    获取过去7天的产品数据 / Fetch products from the past 7 days

    Args:
        limit: 获取数量限制 / Fetch quantity limit
        topic: 话题过滤 / Topic filter
        quiet: 静默模式，减少输出 / Quiet mode, reduce output
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    from datetime import datetime, timedelta
    import json

    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    if not quiet:
        print(f"正在获取过去7天 ({start_str} - {end_str}) 的 Product Hunt 产品...")

    if topic and not quiet:
        print(f"话题过滤: {topic}")

    try:
        api_client = APIClient()
        storage = Storage()

        # 获取过去7天的产品数据 / Fetch products from past 7 days
        products = api_client.get_products_by_date_range(start_str, end_str, limit=limit)

        if not products:
            if not quiet:
                print("未获取到任何产品数据")
            return

        if not quiet:
            print(f"成功获取 {len(products)} 个产品")

        # 解析产品数据 / Parse products data
        parsed_products = Parser.parse_products(products)

        # 按话题过滤 / Filter by topic
        if topic:
            topic_lower = topic.lower()
            filtered = []
            for p in parsed_products:
                topics = p.get('topics', [])
                if any(topic_lower in t.lower() for t in topics):
                    filtered.append(p)
            parsed_products = filtered
            if not quiet:
                print(f"话题过滤后剩余 {len(parsed_products)} 个产品")

        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        # 按投票数排序 / Sort by votes
        formatted_products.sort(key=lambda x: x['votes_count'], reverse=True)

        # JSON 格式输出 / JSON output
        if json_output:
            output_data = {
                "start_date": start_str,
                "end_date": end_str,
                "topic": topic,
                "count": len(formatted_products),
                "products": formatted_products
            }
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
            return

        # 显示产品列表 / Display products list
        if not quiet:
            print("\n" + "=" * 60)
            print(f"Product Hunt 过去7天热门产品{f' - {topic}' if topic else ''}")
            print(f"({start_str} - {end_str})")
            print("=" * 60)

            for i, product in enumerate(formatted_products, 1):
                print(f"\n{i}. {product['name']}")
                print(f"   描述: {product['tagline']}")
                print(f"   🔥 投票: {product['votes_count']} | 💬 评论: {product['comments_count']}")
                print(f"   创作者: {product['makers']}")
                print(f"   链接: {product['url']}")

    except ProductHuntAPIError as e:
        print(f"API 错误: {e}")
    except RateLimitError as e:
        print(f"速率限制: {e}")
    except Exception as e:
        print(f"未知错误: {e}")


def fetch_monthly_products(limit: int = 100, topic: str = None, quiet: bool = False, json_output: bool = False):
    """
    获取过去30天的产品数据 / Fetch products from the past 30 days

    Args:
        limit: 获取数量限制 / Fetch quantity limit
        topic: 话题过滤 / Topic filter
        quiet: 静默模式，减少输出 / Quiet mode, reduce output
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    from datetime import datetime, timedelta
    import json

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    if not quiet:
        print(f"正在获取过去30天 ({start_str} - {end_str}) 的 Product Hunt 产品...")

    if topic and not quiet:
        print(f"话题过滤: {topic}")

    try:
        api_client = APIClient()
        storage = Storage()

        # 获取过去30天的产品数据 / Fetch products from past 30 days
        products = api_client.get_products_by_date_range(start_str, end_str, limit=limit)

        if not products:
            if not quiet:
                print("未获取到任何产品数据")
            return

        if not quiet:
            print(f"成功获取 {len(products)} 个产品")

        # 解析产品数据 / Parse products data
        parsed_products = Parser.parse_products(products)

        # 按话题过滤 / Filter by topic
        if topic:
            topic_lower = topic.lower()
            filtered = []
            for p in parsed_products:
                topics = p.get('topics', [])
                if any(topic_lower in t.lower() for t in topics):
                    filtered.append(p)
            parsed_products = filtered
            if not quiet:
                print(f"话题过滤后剩余 {len(parsed_products)} 个产品")

        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        # 按投票数排序 / Sort by votes
        formatted_products.sort(key=lambda x: x['votes_count'], reverse=True)

        # JSON 格式输出 / JSON output
        if json_output:
            output_data = {
                "start_date": start_str,
                "end_date": end_str,
                "topic": topic,
                "count": len(formatted_products),
                "products": formatted_products
            }
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
            return

        # 显示产品列表 / Display products list
        if not quiet:
            print("\n" + "=" * 60)
            print(f"Product Hunt 过去30天热门产品{f' - {topic}' if topic else ''}")
            print(f"({start_str} - {end_str})")
            print("=" * 60)

            for i, product in enumerate(formatted_products, 1):
                print(f"\n{i}. {product['name']}")
                print(f"   描述: {product['tagline']}")
                print(f"   🔥 投票: {product['votes_count']} | 💬 评论: {product['comments_count']}")
                print(f"   创作者: {product['makers']}")
                print(f"   链接: {product['url']}")

    except ProductHuntAPIError as e:
        print(f"API 错误: {e}")
    except RateLimitError as e:
        print(f"速率限制: {e}")
    except Exception as e:
        print(f"未知错误: {e}")


def fetch_historical_products(date: str, limit: int = 20, topic: str = None, quiet: bool = False, json_output: bool = False):
    """
    获取历史产品数据 / Fetch historical products data

    Args:
        date: 日期字符串 (YYYY-MM-DD) / Date string (YYYY-MM-DD)
        limit: 获取数量限制 / Fetch quantity limit
        topic: 话题过滤 / Topic filter
        quiet: 静默模式，减少输出 / Quiet mode, reduce output
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    import json
    if not quiet:
        print(f"正在获取 {date} 的 Product Hunt 产品...")

    if topic and not quiet:
        print(f"话题过滤: {topic}")

    try:
        api_client = APIClient()
        storage = Storage()

        # 获取历史产品数据 / Fetch historical products data
        products = api_client.get_products_by_date(date, limit=limit)

        if not products:
            if not quiet:
                print(f"未获取到 {date} 的产品数据")
            return

        if not quiet:
            print(f"成功获取 {len(products)} 个产品")

        # 解析产品数据 / Parse products data
        parsed_products = Parser.parse_products(products)

        # 按话题过滤 / Filter by topic
        if topic:
            topic_lower = topic.lower()
            filtered = []
            for p in parsed_products:
                topics = p.get('topics', [])
                if any(topic_lower in t.lower() for t in topics):
                    filtered.append(p)
            parsed_products = filtered
            if not quiet:
                print(f"话题过滤后剩余 {len(parsed_products)} 个产品")

        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        # JSON 格式输出 / JSON output
        if json_output:
            output_data = {
                "date": date,
                "topic": topic,
                "count": len(formatted_products),
                "products": formatted_products
            }
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
            # 保存到缓存 / Save to cache
            storage.save_historical_products(products, date)
            return

        # 显示产品列表 / Display products list
        if not quiet:
            print("\n" + "=" * 60)
            print(f"Product Hunt {date} 热门产品{f' - {topic}' if topic else ''}")
            print("=" * 60)

            for i, product in enumerate(formatted_products, 1):
                print(f"\n{i}. {product['name']}")
                print(f"   描述: {product['tagline']}")
                print(f"   投票: {product['votes_count']} | 评论: {product['comments_count']}")
                print(f"   创作者: {product['makers']}")
                print(f"   链接: {product['url']}")

        # 保存到缓存 / Save to cache
        storage.save_historical_products(products, date)
        if not quiet:
            print(f"\n历史数据已保存到缓存 ({date})")

    except ProductHuntAPIError as e:
        print(f"API 错误: {e}")
    except RateLimitError as e:
        print(f"速率限制: {e}")
    except Exception as e:
        print(f"未知错误: {e}")


def list_historical_products():
    """列出所有历史数据 / List all historical data"""
    try:
        storage = Storage()
        dates = storage.get_all_historical_dates()

        if not dates:
            print("暂无历史数据")
            return

        print("历史数据日期列表:")
        for date in dates:
            products = storage.get_historical_products(date)
            print(f"  {date}: {len(products)} 个产品")

    except Exception as e:
        print(f"错误: {e}")


def build_search_index():
    """构建搜索索引 / Build search index"""
    try:
        storage = Storage()
        search_engine = SearchEngine()

        # 获取今日产品数据 / Get today's products data
        products = storage.get_products("today")
        if not products:
            print("缓存中没有产品数据，请先运行 fetch 命令获取数据")
            return False

        search_engine.build_index(products)
        print(f"搜索索引已构建，包含 {len(products)} 个产品")
        return True

    except Exception as e:
        print(f"构建搜索索引失败: {e}")
        return False


def search_products(query: str, limit: int = 20, json_output: bool = False):
    """
    搜索产品 / Search products

    Args:
        query: 搜索关键词 / Search query
        limit: 结果数量限制 / Results limit
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    import json
    if not query:
        print("请输入搜索关键词")
        return

    if not json_output:
        print(f"正在搜索: {query}")

    try:
        search_engine = SearchEngine()

        # 先尝试从缓存构建索引 / Try to build index from cache first
        products = Storage().get_products("today")
        if products:
            search_engine.build_index(products)

        # 执行搜索 / Execute search
        results = search_engine.search(query, limit=limit)

        if not results:
            if json_output:
                print(json.dumps({"query": query, "count": 0, "results": []}, ensure_ascii=False, indent=2))
            else:
                print("未找到匹配的产品")
                print("提示: 请先运行 fetch 命令获取产品数据")
            return

        # JSON 格式输出 / JSON output
        if json_output:
            output_data = {
                "query": query,
                "count": len(results),
                "results": results
            }
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
            return

        print(f"\n找到 {len(results)} 个匹配结果:")
        print("=" * 60)

        for i, product in enumerate(results, 1):
            print(f"\n{i}. {product['name']}")
            print(f"   描述: {product['tagline']}")
            print(f"   🔥 投票: {product['votes']} | 💬 评论: {product['comments']}")
            print(f"   链接: {product['url']}")

    except Exception as e:
        print(f"搜索失败: {e}")


def show_status(json_output: bool = False):
    """
    显示应用状态 / Show application status
    显示 API 配置、缓存、定时任务等信息 / Display API configuration, cache, scheduler and other information

    Args:
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    import json

    # 缓存状态 / Cache status
    cache_info = {}
    try:
        storage = Storage()
        cache_data = storage.get_cache_info()
        if cache_data:
            for category, data in cache_data.items():
                cache_info[category] = {
                    "count": data['count'],
                    "updated_at": data['updated_at']
                }
    except Exception as e:
        pass

    status_data = {
        "app_name": config.APP_NAME,
        "version": config.APP_VERSION,
        "api": {
            "token_configured": bool(config.PRODUCT_HUNT_TOKEN),
            "token_preview": config.PRODUCT_HUNT_TOKEN[:10] + "..." if config.PRODUCT_HUNT_TOKEN and len(config.PRODUCT_HUNT_TOKEN) > 10 else (config.PRODUCT_HUNT_TOKEN if config.PRODUCT_HUNT_TOKEN else None)
        },
        "cache": cache_info if cache_info else None,
        "scheduler": {
            "enabled": config.SCHEDULER_ENABLED,
            "interval_hours": config.SCHEDULER_INTERVAL_HOURS
        },
        "webhook": {
            "enabled": config.WEBHOOK_ENABLED,
            "url_configured": bool(config.WEBHOOK_URL)
        },
        "service": {
            "host": config.HOST,
            "port": config.PORT,
            "debug": config.DEBUG
        }
    }

    if json_output:
        print(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    print(f"\n{'=' * 50}")
    print(f"{config.APP_NAME} v{config.APP_VERSION} 状态信息")
    print(f"{'=' * 50}\n")

    # API 配置状态 / API configuration status
    print("API 配置:")
    if config.PRODUCT_HUNT_TOKEN:
        token_preview = config.PRODUCT_HUNT_TOKEN[:10] + "..." if len(config.PRODUCT_HUNT_TOKEN) > 10 else config.PRODUCT_HUNT_TOKEN
        print(f"   API Token: 已配置 ({token_preview})")
    else:
        print(f"   API Token: 未配置")
        print(f"   请设置环境变量 PRODUCT_HUNT_TOKEN")

    # 缓存状态 / Cache status
    print("\n缓存状态:")
    if cache_info:
        for category, data in cache_info.items():
            print(f"   - {category}: {data['count']} 个产品 (更新于: {data['updated_at']})")
    else:
        print("   暂无缓存数据")

    # 定时任务状态 / Scheduler status
    print("\n定时任务:")
    print(f"   启用状态: {'是' if config.SCHEDULER_ENABLED else '否'}")
    if config.SCHEDULER_ENABLED:
        print(f"   采集间隔: {config.SCHEDULER_INTERVAL_HOURS} 小时")

    # Webhook 状态 / Webhook status
    print("\nWebhook:")
    print(f"   启用状态: {'是' if config.WEBHOOK_ENABLED else '否'}")
    if config.WEBHOOK_URL:
        url_preview = config.WEBHOOK_URL[:30] + "..." if len(config.WEBHOOK_URL) > 30 else config.WEBHOOK_URL
        print(f"   Webhook URL: {url_preview}")

    # 服务配置 / Service configuration
    print("\n服务配置:")
    print(f"   Host: {config.HOST}")
    print(f"   Port: {config.PORT}")
    print(f"   Debug: {'是' if config.DEBUG else '否'}")

    print(f"\n{'=' * 50}\n")


def show_config(json_output: bool = False, validate: bool = False):
    """
    显示和验证配置 / Show and validate configuration
    显示当前配置信息并可选择验证配置是否有效 / Display current configuration and optionally validate if it's valid

    Args:
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
        validate: 是否验证配置 / Whether to validate configuration
    """
    import json

    # 获取 SMTP 配置 / Get SMTP configuration
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_user = os.environ.get("SMTP_USER", "")
    from_email = os.environ.get("FROM_EMAIL", "")
    to_email = os.environ.get("TO_EMAIL", "")

    config_data = {
        "app": {
            "name": config.APP_NAME,
            "version": config.APP_VERSION,
            "debug": config.DEBUG
        },
        "api": {
            "product_hunt_token": "已配置" if config.PRODUCT_HUNT_TOKEN else "未配置",
            "api_url": config.PRODUCT_HUNT_API_URL,
            "timeout": config.REQUEST_TIMEOUT,
            "max_retries": config.MAX_RETRIES
        },
        "storage": {
            "cache_file": str(config.CACHE_FILE),
            "data_dir": str(config.DATA_DIR)
        },
        "scheduler": {
            "enabled": config.SCHEDULER_ENABLED,
            "interval_hours": config.SCHEDULER_INTERVAL_HOURS
        },
        "webhook": {
            "enabled": config.WEBHOOK_ENABLED,
            "url_configured": bool(config.WEBHOOK_URL)
        },
        "smtp": {
            "host_configured": bool(smtp_host),
            "user_configured": bool(smtp_user),
            "from_email_configured": bool(from_email),
            "to_email_configured": bool(to_email)
        },
        "web": {
            "host": config.HOST,
            "port": config.PORT,
            "secret_key_configured": bool(config.SECRET_KEY and config.SECRET_KEY != "getbeel-secret-key-change-in-production")
        }
    }

    if json_output:
        print(json.dumps(config_data, ensure_ascii=False, indent=2))
        return

    print(f"\n{'=' * 50}")
    print(f"GetBeel 配置信息")
    print(f"{'=' * 50}")

    # 应用信息 / App info
    print(f"\n应用信息:")
    print(f"   名称: {config_data['app']['name']}")
    print(f"   版本: {config_data['app']['version']}")
    print(f"   调试模式: {'是' if config_data['app']['debug'] else '否'}")

    # API 配置 / API configuration
    print(f"\nAPI 配置:")
    print(f"   Product Hunt Token: {config_data['api']['product_hunt_token']}")
    print(f"   API URL: {config_data['api']['api_url']}")
    print(f"   请求超时: {config_data['api']['timeout']} 秒")
    print(f"   最大重试: {config_data['api']['max_retries']} 次")

    # 存储配置 / Storage configuration
    print(f"\n存储配置:")
    print(f"   缓存文件: {config_data['storage']['cache_file']}")
    print(f"   数据目录: {config_data['storage']['data_dir']}")

    # 定时任务配置 / Scheduler configuration
    print(f"\n定时任务:")
    print(f"   启用: {'是' if config_data['scheduler']['enabled'] else '否'}")
    if config_data['scheduler']['enabled']:
        print(f"   采集间隔: {config_data['scheduler']['interval_hours']} 小时")

    # Webhook 配置 / Webhook configuration
    print(f"\nWebhook:")
    print(f"   启用: {'是' if config_data['webhook']['enabled'] else '否'}")
    print(f"   URL已配置: {'是' if config_data['webhook']['url_configured'] else '否'}")

    # SMTP 配置 / SMTP configuration
    print(f"\n邮件通知 (SMTP):")
    print(f"   SMTP主机: {'已配置' if config_data['smtp']['host_configured'] else '未配置'}")
    print(f"   SMTP用户: {'已配置' if config_data['smtp']['user_configured'] else '未配置'}")
    print(f"   发件人: {'已配置' if config_data['smtp']['from_email_configured'] else '未配置'}")
    print(f"   收件人: {'已配置' if config_data['smtp']['to_email_configured'] else '未配置'}")

    # Web 配置 / Web configuration
    print(f"\nWeb 服务:")
    print(f"   Host: {config_data['web']['host']}")
    print(f"   Port: {config_data['web']['port']}")
    print(f"   Secret Key: {'已修改' if config_data['web']['secret_key_configured'] else '默认 (建议修改)'}")

    # 验证配置 / Validate configuration
    if validate:
        print(f"\n{'=' * 50}")
        print(f"配置验证结果")
        print(f"{'=' * 50}")

        issues = []

        if not config.PRODUCT_HUNT_TOKEN:
            issues.append("未配置 Product Hunt API Token，部分功能将无法使用")

        if config.SCHEDULER_ENABLED and not config.PRODUCT_HUNT_TOKEN:
            issues.append("定时任务已启用但未配置 API Token，将无法正常工作")

        if config.WEBHOOK_ENABLED and not config.WEBHOOK_URL:
            issues.append("Webhook 已启用但未配置 URL")

        if config.DEBUG:
            issues.append("调试模式已启用，生产环境建议关闭")

        if issues:
            print(f"\n发现 {len(issues)} 个问题:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print(f"\n配置验证通过！")

    print(f"\n{'=' * 50}\n")


def show_statistics(json_output: bool = False):
    """
    显示产品统计数据 / Show product statistics

    Args:
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    import json
    from statistics import Statistics

    try:
        stats = Statistics()

        # 总体统计 / Total statistics
        total_stats = stats.get_total_stats()
        # 每日统计 / Daily statistics
        daily_stats = stats.get_daily_stats(days=7)
        # 热门产品 / Top products
        top_products = stats.get_top_products(limit=5)
        # 分类分布 / Category distribution
        category_dist = stats.get_category_distribution()

        stats_data = {
            "total": {
                "total_fetches": total_stats['total_fetches'],
                "total_products": total_stats['total_products'],
                "avg_products_per_fetch": total_stats['avg_products_per_fetch']
            },
            "daily": daily_stats,
            "top_products": top_products,
            "category_distribution": dict(list(category_dist.items())[:5]) if category_dist else {}
        }

        if json_output:
            print(json.dumps(stats_data, ensure_ascii=False, indent=2))
            return

        print(f"\n{'=' * 50}")
        print(f"产品统计数据")
        print(f"{'=' * 50}\n")

        print("总体统计:")
        print(f"   总获取次数: {total_stats['total_fetches']}")
        print(f"   总产品数: {total_stats['total_products']}")
        print(f"   平均每次获取产品数: {total_stats['avg_products_per_fetch']:.1f}")

        # 每日统计 / Daily statistics
        if daily_stats:
            print("\n最近7天获取统计:")
            for day in daily_stats:
                print(f"   {day['date']}: {day['products']} 个产品 ({day['fetches']} 次)")

        # 热门产品 / Top products
        if top_products:
            print("\n热门产品 (按投票数):")
            for i, p in enumerate(top_products, 1):
                print(f"   {i}. {p['name']}: {p['votes']} 票, {p['comments']} 评论")

        # 分类分布 / Category distribution
        if category_dist:
            print("\n话题分布 (Top 5):")
            for i, (cat, count) in enumerate(list(category_dist.items())[:5], 1):
                print(f"   {i}. {cat}: {count} 个产品")

    except Exception as e:
        print(f"获取统计数据失败: {e}")

    print(f"\n{'=' * 50}\n")


def run_scheduler():
    """
    运行定时任务 / Run scheduler
    """
    try:
        import schedule
        import time as time_module

        print("启动定时数据采集任务...")
        print(f"采集间隔: {config.SCHEDULER_INTERVAL_HOURS} 小时")

        # 定时获取今日热门产品 / Scheduled fetch today's popular products
        def fetch_task():
            print("\n执行定时任务: 获取今日热门产品")
            fetch_products(limit=30, save=True)

        # 设置定时任务 / Set schedule
        schedule.every(config.SCHEDULER_INTERVAL_HOURS).hours.do(fetch_task)

        # 立即执行一次 / Execute once immediately
        fetch_task()

        while True:
            schedule.run_pending()
            time_module.sleep(60)

    except ImportError:
        print("请安装 schedule 库: pip install schedule")
    except Exception as e:
        print(f"定时任务错误: {e}")


def show_welcome():
    """
    显示欢迎信息和快速开始提示 / Show welcome message and quick start tips
    """
    print(f"\n{'=' * 60}")
    print(f"欢迎使用 {config.APP_NAME} v{config.APP_VERSION}")
    print(f"{'=' * 60}")
    print("\n快速开始:")
    print("  python main.py fetch           获取今日热门产品")
    print("  python main.py web             启动 Web 服务器")
    print("  python main.py --help          查看所有命令")
    print("\n其他命令:")
    print("  python main.py status          查看应用状态")
    print("  python main.py stats           查看统计数据")
    print("  python main.py version         查看版本信息")
    print("  python main.py cache info      查看缓存信息")
    print(f"\n{'=' * 60}\n")
    print("提示: 直接运行 python main.py 也可启动 Web 服务器\n")


def show_version(json_output: bool = False):
    """
    显示版本信息 / Show version information
    包括应用版本、Python 版本和依赖版本 / Includes app version, Python version and dependency versions

    Args:
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    import json
    import platform
    from importlib.metadata import version, PackageNotFoundError

    # 读取 requirements.txt 并显示所有依赖版本 / Read requirements.txt and show all dependency versions
    requirements_file = BASE_DIR / "requirements.txt"
    deps = {}

    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行 / Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # 跳过 Python 版本要求 / Skip Python version requirement
                if line.startswith('python'):
                    continue
                # 解析依赖名称（去除版本号）/ Parse dependency name (remove version)
                dep_name = line.split('>=')[0].split('==')[0].split('~=')[0].strip()
                if dep_name:
                    deps[dep_name] = None  # Placeholder, will be filled with actual version

    # 获取每个依赖的实际版本 / Get actual version for each dependency
    for dep in deps:
        try:
            deps[dep] = version(dep)
        except PackageNotFoundError:
            deps[dep] = "not installed"

    version_data = {
        "app_name": config.APP_NAME,
        "version": config.APP_VERSION,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": deps
    }

    if json_output:
        print(json.dumps(version_data, ensure_ascii=False, indent=2))
        return

    print(f"\n{config.APP_NAME} v{config.APP_VERSION}")
    print(f"Python: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")

    print("\n依赖版本 / Dependencies:")
    for dep, ver in sorted(deps.items()):
        status = "✓" if ver and ver != "not installed" else "✗"
        print(f"   {status} {dep}: {ver}")


def show_makers(limit: int = 10, json_output: bool = False):
    """
    显示热门创作者排行 / Show top makers

    Args:
        limit: 返回数量 / Return count
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    import json
    try:
        storage = Storage()
        products = storage.get_products("today")

        if not products:
            print("缓存中没有产品数据，请先运行 fetch 命令获取数据")
            return

        maker = Maker()
        top_makers = maker.get_top_makers(products, limit=limit)

        if not top_makers:
            print("未找到创作者信息")
            return

        if json_output:
            output_data = {
                "count": len(top_makers),
                "makers": top_makers
            }
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
            return

        print(f"\n{'=' * 60}")
        print(f"热门创作者排行 (Top {limit})")
        print(f"{'=' * 60}\n")

        for i, m in enumerate(top_makers, 1):
            print(f"{i}. {m['name']} (@{m['username']})")
            print(f"   产品数: {m['product_count']} | 总投票: {m['total_votes']} | 总评论: {m['total_comments']}")
            print()

    except Exception as e:
        print(f"获取创作者信息失败: {e}")


def show_trending_topics(days: int = 7, json_output: bool = False):
    """
    显示热门话题/分类 / Show trending topics

    Args:
        days: 统计天数 / Number of days
        json_output: 是否以 JSON 格式输出 / Whether to output in JSON format
    """
    import json
    try:
        trending = TrendingProducts()
        topics = trending.get_trending_topics(days=days)

        if not topics:
            print("暂无热门话题数据")
            print("提示: 请先运行 fetch 命令获取产品数据")
            return

        if json_output:
            output_data = {
                "days": days,
                "count": len(topics),
                "topics": topics
            }
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
            return

        print(f"\n{'=' * 60}")
        print(f"热门话题 (最近 {days} 天)")
        print(f"{'=' * 60}\n")

        for i, t in enumerate(topics, 1):
            print(f"{i}. {t['name']}: {t['count']} 个产品")

    except Exception as e:
        print(f"获取热门话题失败: {e}")


def send_email_notification(products_limit: int = 10):
    """
    发送产品邮件通知 / Send product email notification

    Args:
        products_limit: 产品数量限制 / Products limit
    """
    try:
        notifier = EmailNotifier()

        if not notifier.is_configured():
            print("邮件配置不完整，请检查以下环境变量:")
            print("  - SMTP_HOST")
            print("  - SMTP_USER")
            print("  - SMTP_PASSWORD")
            print("  - TO_EMAIL")
            return

        # 获取今日热门产品 / Fetch today's products
        api_client = APIClient()
        products = api_client.get_today_products(limit=products_limit)

        if not products:
            print("未获取到产品数据")
            return

        # 解析产品数据 / Parse products data
        parser = Parser()
        parsed_products = parser.parse_products(products)

        # 发送邮件通知 / Send email notification
        success = notifier.send_products_notification(parsed_products)

        if success:
            print(f"邮件通知已发送，包含 {len(parsed_products)} 个产品")
        else:
            print("邮件通知发送失败")

    except Exception as e:
        print(f"发送邮件通知失败: {e}")


def list_alerts():
    """列出所有产品提醒 / List all product alerts"""
    try:
        alert_system = ProductAlert()
        alerts = alert_system.get_alerts()

        if not alerts:
            print("暂无产品提醒")
            print("使用 'alert add' 命令添加提醒")
            return

        print(f"\n{'=' * 60}")
        print(f"产品提醒列表 (共 {len(alerts)} 个)")
        print(f"{'=' * 60}\n")

        for i, alert in enumerate(alerts, 1):
            print(f"{i}. 产品: {alert['product_name']}")
            print(f"   类型: {alert['alert_type']}")
            print(f"   阈值: {alert['threshold']}")
            print(f"   创建时间: {alert['created_at']}")
            print()

    except Exception as e:
        print(f"获取提醒列表失败: {e}")


def add_alert(product_name: str, threshold: int, alert_type: str = "votes"):
    """
    添加产品提醒 / Add product alert

    Args:
        product_name: 产品名称 / Product name
        threshold: 阈值 / Threshold
        alert_type: 提醒类型 (votes/comments) / Alert type
    """
    try:
        alert_system = ProductAlert()
        success = alert_system.add_alert(product_name, threshold, alert_type)

        if success:
            print(f"提醒添加成功: {product_name} (阈值: {threshold}, 类型: {alert_type})")
        else:
            print(f"提醒已存在: {product_name} ({alert_type})")

    except Exception as e:
        print(f"添加提醒失败: {e}")


def remove_alert(product_name: str, alert_type: str = "votes"):
    """
    移除产品提醒 / Remove product alert

    Args:
        product_name: 产品名称 / Product name
        alert_type: 提醒类型 / Alert type
    """
    try:
        alert_system = ProductAlert()
        success = alert_system.remove_alert(product_name, alert_type)

        if success:
            print(f"提醒移除成功: {product_name} ({alert_type})")
        else:
            print(f"提醒不存在: {product_name} ({alert_type})")

    except Exception as e:
        print(f"移除提醒失败: {e}")


def check_alerts():
    """检查产品提醒 / Check product alerts"""
    try:
        alert_system = ProductAlert()

        # 获取今日热门产品 / Fetch today's products
        api_client = APIClient()
        products = api_client.get_today_products(limit=50)

        if not products:
            print("未获取到产品数据")
            return

        # 解析产品数据 / Parse products data
        parser = Parser()
        parsed_products = parser.parse_products(products)

        # 检查提醒 / Check alerts
        triggered = alert_system.check_alerts(parsed_products)

        if not triggered:
            print("暂无触发的提醒")
            return

        print(f"\n{'=' * 60}")
        print(f"触发的提醒 (共 {len(triggered)} 个)")
        print(f"{'=' * 60}\n")

        for item in triggered:
            product = item['product']
            alert = item['alert']
            current = item['current_value']

            print(f"产品: {product.get('name')}")
            print(f"  阈值: {alert['threshold']} | 当前: {current}")
            print(f"  链接: {product.get('url')}")
            print()

    except Exception as e:
        print(f"检查提醒失败: {e}")


def main():
    """
    主函数 / Main function
    解析命令行参数并执行相应操作 / Parse command line arguments and execute corresponding operations
    """
    parser = argparse.ArgumentParser(
        description="GetBeel - Product Hunt 数据获取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py fetch                    获取今日热门产品
  python main.py fetch --limit 50         获取50个产品
  python main.py export                    导出产品数据到 JSON
  python main.py export -o mydata.json    指定输出文件名
  python main.py web                       启动 Web 服务器
  python main.py web --debug               调试模式启动
  python main.py cache-clear               清除缓存
        """
    )

    # 添加子命令 / Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # version 命令 / version command
    version_parser = subparsers.add_parser("version", help="显示版本信息")
    version_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出版本信息"
    )

    # status 命令 / status command
    status_parser = subparsers.add_parser("status", help="显示应用状态")
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出状态信息"
    )

    # config 命令 / config command
    config_parser = subparsers.add_parser("config", help="显示和验证配置")
    config_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出配置信息"
    )
    config_parser.add_argument(
        "--validate",
        action="store_true",
        help="验证配置是否有效"
    )

    # stats 命令 / stats command
    stats_parser = subparsers.add_parser("stats", help="显示产品统计数据")
    stats_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出统计数据"
    )

    # fetch 命令 / fetch command
    fetch_parser = subparsers.add_parser("fetch", help="获取 Product Hunt 热门产品")
    fetch_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=20,
        help="获取产品数量 (默认: 20)"
    )
    fetch_parser.add_argument(
        "--no-save",
        action="store_true",
        help="不保存到缓存"
    )
    fetch_parser.add_argument(
        "-t", "--topic",
        type=str,
        help="按话题过滤 (例如: AI, design, productivity)"
    )
    fetch_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，减少输出"
    )
    fetch_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出产品数据"
    )
    fetch_parser.add_argument(
        "-v", "--min-votes",
        type=int,
        default=0,
        help="按最低投票数过滤 (默认: 0，不过滤)"
    )
    fetch_parser.add_argument(
        "-s", "--sort",
        type=str,
        choices=["votes", "comments", "date"],
        default="votes",
        help="排序方式: votes(投票数), comments(评论数), date(日期) (默认: votes)"
    )

    # export 命令 / export command
    export_parser = subparsers.add_parser("export", help="导出产品数据")
    export_parser.add_argument(
        "-o", "--output",
        type=str,
        default="products.json",
        help="输出文件名 (默认: products.json)"
    )
    export_parser.add_argument(
        "-f", "--format",
        type=str,
        choices=["json", "csv"],
        default="json",
        help="导出格式 (默认: json)"
    )
    export_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出到标准输出"
    )

    # history 命令 / history command
    history_parser = subparsers.add_parser("history", help="历史产品数据管理")
    history_parser.add_argument(
        "-d", "--date",
        type=str,
        help="指定日期 (YYYY-MM-DD)"
    )
    history_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=20,
        help="获取产品数量 (默认: 20)"
    )
    history_parser.add_argument(
        "-t", "--topic",
        type=str,
        help="按话题过滤 (例如: AI, design, productivity)"
    )
    history_parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有历史数据"
    )
    history_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，减少输出"
    )
    history_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出产品数据"
    )

    # yesterday 命令 / yesterday command
    yesterday_parser = subparsers.add_parser("yesterday", help="获取昨日热门产品")
    yesterday_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=20,
        help="获取产品数量 (默认: 20)"
    )
    yesterday_parser.add_argument(
        "-t", "--topic",
        type=str,
        help="按话题过滤 (例如: AI, design, productivity)"
    )
    yesterday_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，减少输出"
    )
    yesterday_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出产品数据"
    )

    # week 命令 / week command
    week_parser = subparsers.add_parser("week", help="获取过去7天热门产品")
    week_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=50,
        help="获取产品数量 (默认: 50)"
    )
    week_parser.add_argument(
        "-t", "--topic",
        type=str,
        help="按话题过滤 (例如: AI, design, productivity)"
    )
    week_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，减少输出"
    )
    week_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出产品数据"
    )

    # month 命令 / month command
    month_parser = subparsers.add_parser("month", help="获取过去30天热门产品")
    month_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=100,
        help="获取产品数量 (默认: 100)"
    )
    month_parser.add_argument(
        "-t", "--topic",
        type=str,
        help="按话题过滤 (例如: AI, design, productivity)"
    )
    month_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，减少输出"
    )
    month_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出产品数据"
    )

    # scheduler 命令 / scheduler command
    scheduler_parser = subparsers.add_parser("scheduler", help="启动定时任务")

    # search 命令 / search command
    search_parser = subparsers.add_parser("search", help="搜索产品")
    search_parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="搜索关键词"
    )
    search_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=20,
        help="结果数量限制 (默认: 20)"
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出搜索结果"
    )

    # build-index 命令 / build-index command
    index_parser = subparsers.add_parser("build-index", help="构建搜索索引")

    # web 命令 / web command
    web_parser = subparsers.add_parser("web", help="启动 Web 服务器")
    web_parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="开启调试模式"
    )

    # cache 命令 / cache command
    cache_parser = subparsers.add_parser("cache", help="缓存管理")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_action")

    clear_cache_parser = cache_subparsers.add_parser("clear", help="清除缓存")
    info_cache_parser = cache_subparsers.add_parser("info", help="查看缓存信息")

    # favorites 命令 / favorites command
    favorites_parser = subparsers.add_parser("favorites", help="收藏管理")
    favorites_subparsers = favorites_parser.add_subparsers(dest="favorites_action")

    list_favorites_parser = favorites_subparsers.add_parser("list", help="列出收藏的产品")
    add_favorites_parser = favorites_subparsers.add_parser("add", help="添加收藏")
    add_favorites_parser.add_argument(
        "-i", "--id",
        type=str,
        help="产品 ID"
    )
    remove_favorites_parser = favorites_subparsers.add_parser("remove", help="移除收藏")
    remove_favorites_parser.add_argument(
        "-i", "--id",
        type=str,
        required=True,
        help="产品 ID"
    )

    # maker 命令 / maker command
    maker_parser = subparsers.add_parser("maker", help="创作者信息")
    maker_subparsers = maker_parser.add_subparsers(dest="maker_action")

    top_makers_parser = maker_subparsers.add_parser("top", help="热门创作者排行")
    top_makers_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="返回数量 (默认: 10)"
    )
    top_makers_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出"
    )

    trending_parser = maker_subparsers.add_parser("trending", help="热门话题")
    trending_parser.add_argument(
        "-d", "--days",
        type=int,
        default=7,
        help="统计天数 (默认: 7)"
    )
    trending_parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出"
    )

    # email 命令 / email command
    email_parser = subparsers.add_parser("email", help="邮件通知")
    email_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="产品数量限制 (默认: 10)"
    )

    # alert 命令 / alert command
    alert_parser = subparsers.add_parser("alert", help="产品提醒管理")
    alert_subparsers = alert_parser.add_subparsers(dest="alert_action")

    list_alert_parser = alert_subparsers.add_parser("list", help="列出所有提醒")

    add_alert_parser = alert_subparsers.add_parser("add", help="添加提醒")
    add_alert_parser.add_argument(
        "product_name",
        type=str,
        help="产品名称"
    )
    add_alert_parser.add_argument(
        "-t", "--threshold",
        type=int,
        required=True,
        help="阈值 (投票数或评论数)"
    )
    add_alert_parser.add_argument(
        "-type", "--type",
        type=str,
        choices=["votes", "comments"],
        default="votes",
        help="提醒类型 (默认: votes)"
    )

    remove_alert_parser = alert_subparsers.add_parser("remove", help="移除提醒")
    remove_alert_parser.add_argument(
        "product_name",
        type=str,
        help="产品名称"
    )
    remove_alert_parser.add_argument(
        "-type", "--type",
        type=str,
        choices=["votes", "comments"],
        default="votes",
        help="提醒类型 (默认: votes)"
    )

    check_alert_parser = alert_subparsers.add_parser("check", help="检查提醒")

    # 添加版本参数 / Add version argument
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{config.APP_NAME} v{config.APP_VERSION}"
    )

    # 解析参数 / Parse arguments
    args = parser.parse_args()

    # 如果没有指定命令，显示欢迎信息 / If no command specified, show welcome message
    if args.command is None:
        show_welcome()
        return

    # 执行相应命令 / Execute corresponding command
    if args.command == "version":
        show_version(json_output=args.json)

    elif args.command == "status":
        show_status(json_output=args.json)

    elif args.command == "config":
        show_config(json_output=args.json, validate=args.validate)

    elif args.command == "stats":
        show_statistics(json_output=args.json)

    elif args.command == "fetch":
        fetch_products(limit=args.limit, save=not args.no_save, topic=args.topic, quiet=args.quiet, json_output=args.json, min_votes=args.min_votes, sort=args.sort)

    elif args.command == "export":
        export_products(format=args.format, output=args.output, json_output=args.json)

    elif args.command == "history":
        if args.list:
            list_historical_products()
        elif args.date:
            fetch_historical_products(date=args.date, limit=args.limit, topic=args.topic, quiet=args.quiet, json_output=args.json)
        else:
            parser.print_help()

    elif args.command == "yesterday":
        fetch_yesterday_products(limit=args.limit, topic=args.topic, quiet=args.quiet, json_output=args.json)

    elif args.command == "week":
        fetch_weekly_products(limit=args.limit, topic=args.topic, quiet=args.quiet, json_output=args.json)

    elif args.command == "month":
        fetch_monthly_products(limit=args.limit, topic=args.topic, quiet=args.quiet, json_output=args.json)

    elif args.command == "scheduler":
        run_scheduler()

    elif args.command == "search":
        if args.query:
            search_products(query=args.query, limit=args.limit, json_output=args.json)
        else:
            parser.parse_args(["search", "-h"])

    elif args.command == "build-index":
        build_search_index()

    elif args.command == "web":
        run_web(debug=args.debug)

    elif args.command == "cache":
        if args.cache_action == "clear":
            clear_cache()
        elif args.cache_action == "info":
            storage = Storage()
            info = storage.get_cache_info()
            if info:
                print("缓存信息:")
                for category, data in info.items():
                    print(f"  {category}: {data['count']} 个产品 (更新时间: {data['updated_at']})")
            else:
                print("暂无缓存数据")
        else:
            parser.print_help()

    elif args.command == "favorites":
        if args.favorites_action == "list":
            list_favorites()
        elif args.favorites_action == "add":
            add_favorite(product_id=args.id)
        elif args.favorites_action == "remove":
            remove_favorite(product_id=args.id)
        else:
            parser.print_help()

    elif args.command == "maker":
        if args.maker_action == "top":
            show_makers(limit=args.limit, json_output=args.json)
        elif args.maker_action == "trending":
            show_trending_topics(days=args.days, json_output=args.json)
        else:
            parser.print_help()

    elif args.command == "email":
        send_email_notification(products_limit=args.limit)

    elif args.command == "alert":
        if args.alert_action == "list":
            list_alerts()
        elif args.alert_action == "add":
            add_alert(args.product_name, args.threshold, args.type)
        elif args.alert_action == "remove":
            remove_alert(args.product_name, args.type)
        elif args.alert_action == "check":
            check_alerts()
        else:
            parser.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
