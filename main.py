# -*- coding: utf-8 -*-
"""
GetBeel 主入口文件 / GetBeel Main Entry Point
提供命令行和 Web 服务两种运行方式 / Provides both CLI and Web service run methods
"""

import sys
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


def fetch_products(limit: int = 20, save: bool = True, topic: str = None):
    """
    获取产品数据（命令行模式）/ Fetch products (CLI mode)

    Args:
        limit: 获取数量限制 / Fetch quantity limit
        save: 是否保存到缓存 / Whether to save to cache
        topic: 话题过滤 / Topic filter

    Returns:
    """
    print(f"正在获取 Product Hunt 今日热门产品 (最多 {limit} 个)...")

    if topic:
        print(f"话题过滤: {topic}")

    try:
        # 初始化 API 客户端 / Initialize API client
        api_client = APIClient()
        storage = Storage()

        # 获取产品数据 / Fetch products data
        products = api_client.get_today_products(limit=limit)

        if not products:
            print("未获取到任何产品数据")
            return

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
            print(f"话题过滤后剩余 {len(parsed_products)} 个产品")

        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        # 显示产品列表 / Display products list
        print("\n" + "=" * 60)
        print(f"Product Hunt 今日热门产品{f' - {topic}' if topic else ''}")
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
            print("\n数据已保存到缓存")

    except ProductHuntAPIError as e:
        print(f"API 错误: {e}")
    except RateLimitError as e:
        print(f"速率限制: {e}")
    except Exception as e:
        print(f"未知错误: {e}")


def export_products(format: str = "json", output: str = "products.json"):
    """
    导出产品数据 / Export products data

    Args:
        format: 导出格式 (json/csv) / Export format
        output: 输出文件名 / Output filename
    """
    print(f"正在导出产品数据到 {output}...")

    try:
        storage = Storage()
        products = storage.get_products("today")

        if not products:
            print("缓存中没有产品数据，请先运行 fetch 命令获取数据")
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


def fetch_historical_products(date: str, limit: int = 20, topic: str = None):
    """
    获取历史产品数据 / Fetch historical products data

    Args:
        date: 日期字符串 (YYYY-MM-DD) / Date string (YYYY-MM-DD)
        limit: 获取数量限制 / Fetch quantity limit
        topic: 话题过滤 / Topic filter
    """
    print(f"正在获取 {date} 的 Product Hunt 产品...")

    if topic:
        print(f"话题过滤: {topic}")

    try:
        api_client = APIClient()
        storage = Storage()

        # 获取历史产品数据 / Fetch historical products data
        products = api_client.get_products_by_date(date, limit=limit)

        if not products:
            print(f"未获取到 {date} 的产品数据")
            return

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
            print(f"话题过滤后剩余 {len(parsed_products)} 个产品")

        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        # 显示产品列表 / Display products list
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


def search_products(query: str, limit: int = 20):
    """
    搜索产品 / Search products

    Args:
        query: 搜索关键词 / Search query
        limit: 结果数量限制 / Results limit
    """
    if not query:
        print("请输入搜索关键词")
        return

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
            print("未找到匹配的产品")
            print("提示: 请先运行 fetch 命令获取产品数据")
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


def show_status():
    """
    显示应用状态 / Show application status
    显示 API 配置、缓存、定时任务等信息 / Display API configuration, cache, scheduler and other information
    """
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
    try:
        storage = Storage()
        cache_info = storage.get_cache_info()
        if cache_info:
            for category, data in cache_info.items():
                print(f"   - {category}: {data['count']} 个产品 (更新于: {data['updated_at']})")
        else:
            print("   暂无缓存数据")
    except Exception as e:
        print(f"   获取缓存信息失败: {e}")

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


def show_statistics():
    """
    显示产品统计数据 / Show product statistics
    """
    from statistics import Statistics

    print(f"\n{'=' * 50}")
    print(f"产品统计数据")
    print(f"{'=' * 50}\n")

    try:
        stats = Statistics()

        # 总体统计 / Total statistics
        total_stats = stats.get_total_stats()
        print("总体统计:")
        print(f"   总获取次数: {total_stats['total_fetches']}")
        print(f"   总产品数: {total_stats['total_products']}")
        print(f"   平均每次获取产品数: {total_stats['avg_products_per_fetch']:.1f}")

        # 每日统计 / Daily statistics
        daily_stats = stats.get_daily_stats(days=7)
        if daily_stats:
            print("\n最近7天获取统计:")
            for day in daily_stats:
                print(f"   {day['date']}: {day['products']} 个产品 ({day['fetches']} 次)")

        # 热门产品 / Top products
        top_products = stats.get_top_products(limit=5)
        if top_products:
            print("\n热门产品 (按投票数):")
            for i, p in enumerate(top_products, 1):
                print(f"   {i}. {p['name']}: {p['votes']} 票, {p['comments']} 评论")

        # 分类分布 / Category distribution
        category_dist = stats.get_category_distribution()
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


def show_version():
    """
    显示版本信息 / Show version information
    包括应用版本、Python 版本和依赖版本 / Includes app version, Python version and dependency versions
    """
    import platform

    print(f"\n{config.APP_NAME} v{config.APP_VERSION}")
    print(f"Python: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")

    # 显示依赖版本 / Show dependency versions
    deps = {
        "requests": "requests",
        "flask": "flask",
        "beautifulsoup4": "beautifulsoup4",
    }

    for dep, import_name in deps.items():
        try:
            from importlib.metadata import version
            deps[dep] = version(import_name)
        except Exception:
            deps[dep] = "not installed"

    print("\n依赖版本 / Dependencies:")
    for dep, version in deps.items():
        status = "✓" if version and version != "not installed" else "✗"
        print(f"   {status} {dep}: {version}")


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

    # status 命令 / status command
    status_parser = subparsers.add_parser("status", help="显示应用状态")

    # stats 命令 / stats command
    stats_parser = subparsers.add_parser("stats", help="显示产品统计数据")

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

    # 添加版本参数 / Add version argument
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{config.APP_NAME} v{config.APP_VERSION}"
    )

    # 解析参数 / Parse arguments
    args = parser.parse_args()

    # 如果没有指定命令，默认启动 Web 服务器 / If no command specified, start Web server by default
    if args.command is None:
        run_web()
        return

    # 执行相应命令 / Execute corresponding command
    if args.command == "version":
        show_version()

    elif args.command == "status":
        show_status()

    elif args.command == "stats":
        show_statistics()

    elif args.command == "fetch":
        fetch_products(limit=args.limit, save=not args.no_save, topic=args.topic)

    elif args.command == "export":
        export_products(format=args.format, output=args.output)

    elif args.command == "history":
        if args.list:
            list_historical_products()
        elif args.date:
            fetch_historical_products(date=args.date, limit=args.limit, topic=args.topic)
        else:
            parser.print_help()

    elif args.command == "scheduler":
        run_scheduler()

    elif args.command == "search":
        if args.query:
            search_products(query=args.query, limit=args.limit)
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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
