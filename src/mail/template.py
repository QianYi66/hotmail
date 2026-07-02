# -*- coding: utf-8 -*-
"""
邮件模板 - HTML 格式
"""

from html import escape
from typing import List

from .. import beijing_now
from ..scraper import HotItem


def build_html(
    items_by_source: dict[str, List[HotItem]],
    custom_title: str = "",
) -> str:
    """
    构建 HTML 邮件内容

    Args:
        items_by_source: {"微博热搜": [HotItem, ...], ...}
        title: 邮件标题（覆盖自动生成）

    Returns:
        HTML 字符串
    """
    now = beijing_now()
    date_str = now.strftime("%Y年%m月%d日")
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_map[now.weekday()]
    time_str = now.strftime("%H:%M")

    title = custom_title or f"📰 今日热闻 | {date_str} {weekday}"

    sections_html = ""
    total_items = 0
    for source_name, items in items_by_source.items():
        if not items:
            continue
        total_items += len(items)

        # 用 emoji 做来源图标
        icon = {"微博热搜": "🔴", "知乎热榜": "💡", "百度热搜": "🔵"}.get(source_name, "📌")

        rows = ""
        for item in items:
            rank = item.rank
            title_text = escape(str(item.title))
            link = escape(str(item.link or ""))
            hot = escape(str(item.hot or ""))
            tag = escape(str(item.tag or ""))

            # 标签着色
            tag_badge = ""
            if tag:
                tag_colors = {"爆": "#FF2D2D", "沸": "#FF6B35", "新": "#00B368", "热": "#FF8C00", "荐": "#1E90FF"}
                tag_color = tag_colors.get(tag, "#999")
                tag_badge = f'<span class="tag" style="background:{tag_color}">{tag}</span>'

            hot_badge = f'<span class="hot">{hot}</span>' if hot else ""

            if link:
                row = (
                    f'<tr>'
                    f'  <td class="rank">#{rank}</td>'
                    f'  <td class="title">'
                    f'    <a href="{link}" target="_blank">{title_text}</a>'
                    f'    {tag_badge}'
                    f'  </td>'
                    f'  <td class="hot-col">{hot_badge}</td>'
                    f'</tr>'
                )
            else:
                row = (
                    f'<tr>'
                    f'  <td class="rank">#{rank}</td>'
                    f'  <td class="title">'
                    f'    {title_text}'
                    f'    {tag_badge}'
                    f'  </td>'
                    f'  <td class="hot-col">{hot_badge}</td>'
                    f'</tr>'
                )
            rows += row

        section = f"""
        <div class="section">
            <h2>{icon} {source_name} <span class="count">共 {len(items)} 条</span></h2>
            <table class="table">
                <thead>
                    <tr><th>排名</th><th>标题</th><th>热度</th></tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """
        sections_html += section

    # 邮箱底部信息
    footer = f"""
    <div class="footer">
        <p>📅 {date_str} {weekday} {time_str} · 自动发送</p>
        <p>数据来源: 微博 · 知乎 · 百度</p>
        <hr>
        <p class="note">本邮件由「今日热闻」自动生成，仅供个人参考</p>
    </div>
    """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif;
        background: #f5f6f8;
        padding: 20px;
        color: #1a1a1a;
    }}
    .container {{
        max-width: 680px;
        margin: 0 auto;
        background: #ffffff;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }}
    .header {{
        background: linear-gradient(135deg, #FF4D4F, #FF6B35);
        color: white;
        padding: 32px 28px;
    }}
    .header h1 {{
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 6px;
    }}
    .header p {{
        font-size: 14px;
        opacity: 0.9;
    }}
    .body {{ padding: 24px 28px; }}
    .section {{ margin-bottom: 28px; }}
    .section h2 {{
        font-size: 18px;
        color: #333;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #f0f0f0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .count {{
        font-size: 13px;
        color: #999;
        font-weight: 400;
    }}
    .table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }}
    .table th {{
        text-align: left;
        padding: 8px 10px;
        color: #888;
        font-weight: 500;
        font-size: 13px;
        border-bottom: 1px solid #eee;
    }}
    .table td {{
        padding: 10px;
        border-bottom: 1px solid #f5f5f5;
        vertical-align: middle;
    }}
    .table tr:hover td {{
        background: #fafafa;
    }}
    .rank {{
        color: #999;
        width: 40px;
        font-weight: 600;
        font-size: 13px;
    }}
    .title a {{
        color: #1a1a1a;
        text-decoration: none;
    }}
    .title a:hover {{
        color: #FF4D4F;
        text-decoration: underline;
    }}
    .tag {{
        display: inline-block;
        color: white;
        font-size: 11px;
        padding: 1px 6px;
        border-radius: 4px;
        margin-left: 6px;
        vertical-align: middle;
        font-weight: 600;
    }}
    .hot-col {{ width: 80px; text-align: right; }}
    .hot {{
        font-size: 12px;
        color: #999;
    }}
    .footer {{
        text-align: center;
        padding: 20px 28px;
        background: #fafafa;
        color: #aaa;
        font-size: 12px;
        line-height: 1.8;
    }}
    .footer hr {{
        border: none;
        border-top: 1px solid #eee;
        margin: 10px 0;
    }}
    .note {{
        color: #ccc;
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📰 今日热闻</h1>
        <p>{date_str} {weekday} · {time_str} · 共 {total_items} 条热点</p>
    </div>
    <div class="body">
        {sections_html}
    </div>
    {footer}
</div>
</body>
</html>"""

    return html


def build_text(items_by_source: dict[str, List[HotItem]], title: str = "") -> str:
    """
    构建纯文本邮件内容（备选）

    Args:
        items_by_source: {"微博热搜": [HotItem, ...], ...}
        title: 邮件标题

    Returns:
        纯文本字符串
    """
    now = beijing_now()
    date_str = now.strftime("%Y-%m-%d")
    lines = [
        "=" * 60,
        f"  今日热闻 | {date_str}",
        "=" * 60,
        "",
    ]

    for source_name, items in items_by_source.items():
        if not items:
            continue
        lines.append(f"【{source_name}】")
        lines.append("-" * 40)
        for item in items:
            tag = f" [{item.tag}]" if item.tag else ""
            hot = f" ({item.hot})" if item.hot else ""
            line = f"  #{item.rank:<3} {item.title}{tag}{hot}"
            if item.link:
                line += f"\n         ↳ {item.link}"
            lines.append(line)
        lines.append("")

    lines.extend([
        "-" * 60,
        f"  {date_str} · 自动发送",
        "-" * 60,
    ])

    return "\n".join(lines)
