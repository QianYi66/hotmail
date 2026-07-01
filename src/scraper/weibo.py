# -*- coding: utf-8 -*-
"""
微博热搜抓取
"""

import json
import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from . import BaseHotScraper, HotItem


class WeiboHotScraper(BaseHotScraper):
    """
    微博热搜抓取

    支持两个获取渠道，自动降级：
    1. 微博热搜 API (ajax 接口)
    2. 热搜榜页面 HTML 解析 (备用)
    """

    source_name = "微博热搜"
    source_key = "weibo"

    # API 地址
    API_URL = "https://weibo.com/ajax/side/hotSearch"
    # 热搜榜页面（备用）
    HTML_URL = "https://s.weibo.com/top/summary?cate=realtimehot"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://weibo.com/",
        })

    # ---------- 渠道一：API 接口 ----------

    def _fetch_from_api(self) -> Optional[List[HotItem]]:
        """从微博 ajax 接口获取热搜"""
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = self.session.get(url, timeout=self.timeout)
        resp.encoding = "utf-8"
        data = resp.json()

        realtime = data.get("data", {}).get("realtime", [])
        if not realtime:
            return None

        items = []
        for i, entry in enumerate(realtime, start=1):
            raw_word = entry.get("raw_word", "") or entry.get("word", "")
            if not raw_word:
                continue

            # 热度标签（爆/沸/新/荐）
            tag = ""
            flag = entry.get("flag", "")  # "爆"、"沸"、"新"
            label = entry.get("label_name", "")  # 有时用 label
            icon_desc = entry.get("icon_desc", "")
            tag = flag or label or icon_desc or ""

            # 热度数值
            num = entry.get("num", "")  # 热度值

            # 热搜榜链接
            scheme = entry.get("scheme", "")
            link = f"https://weibo.com{scheme}" if scheme else ""

            items.append(HotItem(
                rank=i,
                title=raw_word,
                link=link or f"https://s.weibo.com/weibo?q={raw_word}",
                hot=num,
                tag=tag,
            ))

        return items

    # ---------- 渠道二：热搜榜页面解析 ----------

    def _fetch_from_page(self) -> Optional[List[HotItem]]:
        """从热搜榜页面解析 HTML（备用渠道）"""
        headers = self.session.headers.copy()
        headers["Accept"] = (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/webp,*/*;q=0.8"
        )
        resp = self.session.get(self.HTML_URL, timeout=self.timeout, headers=headers)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "lxml")
        items = []

        # 尝试从内嵌 JSON 中提取
        for script in soup.find_all("script"):
            text = script.string or ""
            # 搜索 __INITIAL_STATE__ 或 __DATA__
            for pattern in [
                r"window\.__INITIAL_STATE__\s*=\s*({.*?});",
                r"window\.__DATA__\s*=\s*({.*?});",
            ]:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    try:
                        state = json.loads(match.group(1))
                        # 尝试多种路径找到热搜列表
                        for path in [
                            ["realtime", "list"],
                            ["hotSearch", "list"],
                            ["data", "list"],
                        ]:
                            data = state
                            for key in path:
                                data = data.get(key, {}) if isinstance(data, dict) else {}
                            if isinstance(data, (list, tuple)):
                                for i, entry in enumerate(data, start=1):
                                    if isinstance(entry, dict):
                                        title = entry.get("word", "") or entry.get("title", "")
                                        if title:
                                            items.append(HotItem(
                                                rank=i,
                                                title=title,
                                                link=entry.get("link", ""),
                                                hot=str(entry.get("num", "")),
                                                tag=str(entry.get("flag", "") or entry.get("label", "")),
                                            ))
                                break
                    except (json.JSONDecodeError, KeyError, TypeError):
                        pass
                    break
            if items:
                break

        # 兜底：从 HTML 表格解析
        if not items:
            # 热搜榜页面是表格结构
            rows = soup.select("tr")
            for i, row in enumerate(rows, start=1):
                # 找到包含排名、标题、热度的单元格
                tds = row.find_all("td")
                if len(tds) >= 2:
                    title_td = tds[0]
                    hot_td = tds[1] if len(tds) > 1 else None

                    # 标题
                    title_link = title_td.find("a")
                    title = title_link.get_text(strip=True) if title_link else title_td.get_text(strip=True)
                    if not title:
                        continue

                    # 标签
                    tag = ""
                    tag_span = title_td.find("span", class_=re.compile(r"tag|icon"))
                    if tag_span:
                        tag = tag_span.get_text(strip=True)

                    # 链接
                    link = ""
                    if title_link and title_link.get("href"):
                        href = title_link["href"]
                        link = href if href.startswith("http") else f"https:{href}"

                    # 热度
                    hot = hot_td.get_text(strip=True) if hot_td else ""

                    items.append(HotItem(
                        rank=i,
                        title=title.strip(),
                        link=link,
                        hot=hot,
                        tag=tag.strip(),
                    ))

            # 如果表格没取到，尝试 CSS 列表
            if not items:
                card_items = soup.select("[class*=\"card\"], [class*=\"item\"], [class*=\"list\"] li")
                for i, card in enumerate(card_items, start=1):
                    title_el = card.select_one("a[href*=\"weibo\"]") or card.select_one("a")
                    if title_el:
                        title = title_el.get_text(strip=True)
                        if title and len(title) > 2:
                            link = title_el.get("href", "")
                            if link and not link.startswith("http"):
                                link = f"https:{link}" if link.startswith("//") else f"https://s.weibo.com{link}"
                            items.append(HotItem(
                                rank=i,
                                title=title,
                                link=link,
                            ))

        return items if items else None

    # ---------- 主入口 ----------

    def fetch(self) -> List[HotItem]:
        """抓取微博热搜"""
        items = self._fetch_from_api()
        if items:
            print(f"  [OK] 微博热搜: 获取 {len(items)} 条")
            return items

        items = self._fetch_from_page()
        if items:
            print(f"  [OK] 微博热搜 (页面): 获取 {len(items)} 条")
            return items

        raise RuntimeError("所有渠道均失败")
