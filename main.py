# -*- coding: utf-8 -*-
"""
今日热闻 - 定时邮件推送

把微博热搜、知乎热搜等内容定时发送到指定邮箱。

使用方法:
    # 先编辑 config.yaml 配置邮箱信息
    python main.py              # 按配置文件中的定时设置运行
    python main.py --now        # 立即发送一次
    python main.py --dry        # 仅抓取预览，不发送邮件
"""

import logging
import os
import sys
from functools import partial
from typing import List

# 确保引用本项目的路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import beijing_now
from src.config import AppConfig
from src.mail import MailSender
from src.mail.template import build_html, build_text
from src.scheduler import TaskScheduler
from src.scraper.weibo import WeiboHotScraper
from src.scraper.zhihu import ZhihuHotScraper
from src.scraper.baidu import BaiduHotScraper
from src.scraper.douyin import DouyinHotScraper


def setup_logger():
    """配置日志"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("hotmail")
    logger.setLevel(logging.DEBUG)

    # 格式
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 控制台
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    # Windows GBK 兼容
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logger.addHandler(ch)

    # 文件
    log_file = os.path.join(log_dir, f"hotmail_{beijing_now().strftime('%Y%m%d')}.log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


logger = setup_logger()


def fetch_all_hot(limit: int) -> dict[str, list]:
    """
    抓取所有开启的热搜来源

    Returns:
        {"微博热搜": [HotItem, ...], "知乎热榜": [HotItem, ...]}
    """
    sources = {}
    items_by_source = {}

    config = AppConfig.load()

    if config.content.weibo:
        sources["微博热搜"] = WeiboHotScraper()

    if config.content.zhihu:
        sources["知乎热榜"] = ZhihuHotScraper()

    if config.content.baidu:
        sources["百度热搜"] = BaiduHotScraper()

    if config.content.douyin:
        sources["抖音热搜"] = DouyinHotScraper()

    for name, scraper in sources.items():
        try:
            items = scraper.fetch_safe()
            if items:
                items_by_source[name] = items[:limit]
                logger.info(f"  ✓ {name}: {len(items)} 条")
            else:
                logger.warning(f"  ⚠ {name}: 未获取到数据")
        except Exception as e:
            logger.error(f"  ✗ {name}: {e}")

    return items_by_source


def format_timestamp() -> str:
    """格式化的时间戳"""
    now = beijing_now()
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return now.strftime(f"%Y-%m-%d %H:%M {weekday[now.weekday()]}")


def send_email(items_by_source: dict) -> bool:
    """
    发送邮件

    Returns:
        bool: 是否成功
    """
    config = AppConfig.load()

    sender = MailSender(
        smtp_server=config.mail.smtp_server,
        smtp_port=config.mail.smtp_port,
        sender_email=config.mail.sender_email,
        sender_password=config.mail.sender_password,
        sender_name=config.mail.sender_name,
    )

    # 标题
    now = beijing_now()
    date_str = now.strftime("%Y-%m-%d %H:%M")
    subject = f"今日热闻 | {date_str}"

    # 构建 HTML
    html = build_html(items_by_source)
    result = sender.send_html(subject, html, config.mail.recipients)

    if result["success"]:
        logger.info(f"  ✓ 邮件发送成功 → {', '.join(result['sent_to'])}")
    else:
        logger.error(f"  ✗ 邮件发送失败: {result['failed']}")

    return result["success"]


def preview(items_by_source: dict):
    """终端预览"""
    now = beijing_now()
    date_str = now.strftime("%Y-%m-%d %H:%M")

    print(f"\n{'=' * 60}")
    print(f"  今日热闻 | {date_str}")
    print(f"{'=' * 60}")

    for source_name, items in items_by_source.items():
        print(f"\n  【{source_name}】")
        print(f"  {'-' * 40}")
        for item in items:
            tag = f" [{item.tag}]" if item.tag else ""
            hot = f" ({item.hot})" if item.hot else ""
            print(f"  #{item.rank:<3} {item.title}{tag}{hot}")
        print()

    total = sum(len(v) for v in items_by_source.values())
    print(f"{'=' * 60}")
    print(f"  共 {total} 条热点")
    print(f"{'=' * 60}\n")


def do_send(config: AppConfig):
    """执行一次抓取 + 发送"""
    logger.info(f"📥 开始抓取热搜...")
    items_by_source = fetch_all_hot(config.content.limit)

    if not items_by_source:
        logger.warning("⚠ 没有获取到任何内容，跳过发送")
        return

    logger.info(f"📤 正在发送邮件...")
    send_email(items_by_source)


def print_banner(config: AppConfig):
    """打印启动信息"""
    print(f"""
{'=' * 50}
  == 今日热闻 - 定时邮件推送 ==
{'=' * 50}
  邮箱:    {config.mail.sender_email} -> {', '.join(config.mail.recipients)}
  SMTP:    {config.mail.smtp_server}:{config.mail.smtp_port}
  内容:    {'微博 ' if config.content.weibo else ''}{'知乎 ' if config.content.zhihu else ''}{'百度 ' if config.content.baidu else ''}{'抖音 ' if config.content.douyin else ''}
  定时:    {', '.join(config.schedule.times) if config.schedule.enabled else '手动模式'}
{'=' * 50}
""")


# ==============================================================
# 主入口
# ==============================================================

def main():
    config = AppConfig.load()

    # 解析简单参数
    args = [a.lower() for a in sys.argv[1:]]
    dry_run = "--dry" in args
    now_mode = "--now" in args

    if dry_run:
        # 预览模式
        print_banner(config)
        logger.info("🔍 预览模式：抓取热搜并打印到终端")
        items_by_source = fetch_all_hot(config.content.limit)
        preview(items_by_source)
        logger.info("✅ 预览完成（未发送邮件）")
        return

    # 验证邮箱配置
    if not config.mail.valid:
        logger.error("✗ 邮箱配置不完整，请先编辑 config.yaml")
        logger.error("   必须填写: sender_email, sender_password, recipients")
        print("\n   💡 快速配置:")
        print("      1. 编辑 config.yaml")
        print("      2. 填入你的邮箱和 SMTP 授权码")
        print("      3. 运行 python main.py --dry 先测试抓取")
        print("      4. 运行 python main.py --now 测试发送")
        sys.exit(1)

    print_banner(config)

    if now_mode:
        # 立即发送模式
        logger.info("📬 立即发送模式")
        do_send(config)
        logger.info("✅ 发送完成")
        return

    # 定时模式
    scheduler = TaskScheduler()
    scheduler.setup(
        times=config.schedule.times,
        job_func=partial(do_send, config),
    )

    logger.info(f"⏰ 定时模式已启动")
    if scheduler.next_run:
        logger.info(f"   下次发送: {scheduler.next_run}")

    # 启动前立即执行一次（便于验证）
    if config.schedule.enabled:
        scheduler.run_once(partial(do_send, config))

    # 进入循环
    scheduler.start()


if __name__ == "__main__":
    main()
