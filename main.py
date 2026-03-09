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


def fetch_products(limit: int = 20, save: bool = True):
    """
    获取产品数据（命令行模式）/ Fetch products (CLI mode)

    Args:
        limit: 获取数量限制 / Fetch quantity limit
        save: 是否保存到缓存 / Whether to save to cache

    Returns:
    """
    print(f"正在获取 Product Hunt 今日热门产品 (最多 {limit} 个)...")

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
        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        # 显示产品列表 / Display products list
        print("\n" + "=" * 60)
        print("Product Hunt 今日热门产品")
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


def run_web(debug: bool = False):
    """
    运行 Web 服务器 / Run Web server

    Args:
        debug: 是否开启调试模式 / Whether to enable debug mode
    """
    from web import run_server

    print(f"启动 GetBeel Web 服务 (调试模式: {debug})")
    run_server(debug=debug)


def fetch_historical_products(date: str, limit: int = 20):
    """
    获取历史产品数据 / Fetch historical products data

    Args:
        date: 日期字符串 (YYYY-MM-DD) / Date string (YYYY-MM-DD)
        limit: 获取数量限制 / Fetch quantity limit
    """
    print(f"正在获取 {date} 的 Product Hunt 产品...")

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
        formatted_products = [
            Parser.format_product_for_display(p) for p in parsed_products
        ]

        # 显示产品列表 / Display products list
        print("\n" + "=" * 60)
        print(f"Product Hunt {date} 热门产品")
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


def run_scheduler():
    """运行定时任务 / Run scheduler"""
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
        "--list",
        action="store_true",
        help="列出所有历史数据"
    )

    # scheduler 命令 / scheduler command
    scheduler_parser = subparsers.add_parser("scheduler", help="启动定时任务")

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
        print(f"{config.APP_NAME} v{config.APP_VERSION}")

    elif args.command == "fetch":
        fetch_products(limit=args.limit, save=not args.no_save)

    elif args.command == "export":
        export_products(format=args.format, output=args.output)

    elif args.command == "history":
        if args.list:
            list_historical_products()
        elif args.date:
            fetch_historical_products(date=args.date, limit=args.limit)
        else:
            parser.print_help()

    elif args.command == "scheduler":
        run_scheduler()

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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
