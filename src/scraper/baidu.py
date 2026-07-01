# -*- coding: utf-8 -*-
"""
百度热搜抓取

支持两个渠道，自动降级：
1. 百度热搜 API（已验证：https://top.baidu.com/api/board?tab=realtime）
2. 热搜榜页面 HTML 解析（备用）
"""

import json
import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from . import BaseHotScraper, HotItem


class BaiduHotScraper(BaseHotScraper):
    """
    百度热搜抓取

    支持渠道：
    1. 百度热搜 API
    2. 热搜榜页面 HTML 解析 (备用)
    """

    source_name = "百度热搜"
    source_key = "baidu"

    # API 地址（已验证可用）
    API_URL = "https://top.baidu.com/api/board?tab=realtime"
    # 热搜榜页面（备用）
    HTML_URL = "https://top.baidu.com/board?tab=realtime"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://top.baidu.com/",
            "Accept": "application/json, text/plain, */*",
        })

    # ---------- 渠道一：百度热搜 API ----------

    def _fetch_from_api(self) -> Optional[List[HotItem]]:
        """从百度热搜 API 获取"""
        resp = self.session.get(self.API_URL, timeout=self.timeout)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            return None

        data = resp.json()
        if not data.get("success"):
            return None

        cards = data.get("data", {}).get("cards", [])
        if not cards:
            return None

        # 主列表
        content = cards[0].get("content", [])
        if not content:
            return None

        items = []
        for entry in content:
            title = entry.get("word", "") or entry.get("query", "")
            if not title:
                continue

            rank = entry.get("index", 0) + 1  # API 中 index 从 0 开始

            # 链接
            link = entry.get("rawUrl", "") or entry.get("url", "")

            # 热度值
            hot_score = entry.get("hotScore", "")

            # 标签：使用 hotTag 作为热度标签（0=无标签, 1/3=有特殊标识）
            tag = ""
            hot_tag = entry.get("hotTag", "")
            if hot_tag and hot_tag not in ("0", ""):
                tag = "热"

            items.append(HotItem(
                rank=rank,
                title=title,
                link=link or f"https://www.baidu.com/s?wd={title}",
                hot=str(hot_score) if hot_score else "",
                tag=tag,
            ))

        return items if items else None

    # ---------- 渠道二：热搜榜页面解析 ----------

    def _fetch_from_page(self) -> Optional[List[HotItem]]:
        """从热搜榜页面解析 HTML"""
        headers = self.session.headers.copy()
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        resp = self.session.get(self.HTML_URL, timeout=self.timeout, headers=headers)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "lxml")
        items = []

        # 尝试从页面内嵌数据中提取
        for script in soup.find_all("script"):
            text = script.string or ""

            # __NEXT_DATA__ (Next.js 内嵌数据)
            if script.get("id") == "__NEXT_DATA__" and script.get("type") == "application/json":
                try:
                    state = json.loads(text)
                    # Next.js 数据结构可能不同，尝试多种路径
                    props = state.get("props", {}).get("pageProps", {})
                    board_data = props.get("boardData", props)
                    cards = board_data.get("data", {}).get("cards", []) or board_data.get("cards", [])
                    if cards:
                        content = cards[0].get("content", []) if isinstance(cards[0], dict) else []
                        for i, entry in enumerate(content, start=1):
                            title = entry.get("word", "") or entry.get("query", "")
                            if not title:
                                continue
                            link = entry.get("rawUrl", "") or entry.get("url", "")
                            hot_score = entry.get("hotScore", "")
                            items.append(HotItem(
                                rank=i,
                                title=title,
                                link=link or f"https://www.baidu.com/s?wd={title}",
                                hot=str(hot_score) if hot_score else "",
                            ))
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
                break

            # window.__INITIAL_STATE__
            if "window.__INITIAL_STATE__" in text:
                match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", text, re.DOTALL)
                if match:
                    try:
                        state = json.loads(match.group(1))
                        board_data = state.get("boardData", state)
                        cards = board_data.get("data", {}).get("cards", []) or board_data.get("cards", [])
                        if cards:
                            content = cards[0].get("content", []) if isinstance(cards[0], dict) else []
                            for i, entry in enumerate(content, start=1):
                                title = entry.get("word", "") or entry.get("query", "")
                                if not title:
                                    continue
                                link = entry.get("rawUrl", "") or entry.get("url", "")
                                hot_score = entry.get("hotScore", "")
                                items.append(HotItem(
                                    rank=i,
                                    title=title,
                                    link=link or f"https://www.baidu.com/s?wd={title}",
                                    hot=str(hot_score) if hot_score else "",
                                ))
                    except (json.JSONDecodeError, KeyError, TypeError):
                        pass
                break

        # 兜底：CSS 选择器解析页面
        if not items:
            # 尝试匹配常见的百度热搜条目选择器
            for selector in [
                ".category-wrap .content_1YWBm",
                ".hot-list-item",
                "[class*=\"hot-item\"]",
                "[class*=\"content-item\"]",
                "a[class*=\"title\"]",
            ]:
                elements = soup.select(selector)
                if elements:
                    for i, el in enumerate(elements, start=1):
                        title = el.get_text(strip=True)
                        if title and len(title) > 2:  # 过滤过短文本
                            link = ""
                            parent_a = el.find_parent("a") or (el if el.name == "a" else None)
                            if parent_a and parent_a.get("href"):
                                href = parent_a["href"]
                                link = href if href.startswith("http") else f"https://top.baidu.com{href}"
                            items.append(HotItem(
                                rank=i,
                                title=title,
                                link=link or f"https://www.baidu.com/s?wd={title}",
                            ))
                    if items:
                        break

        return items if items else None

    # ---------- 主入口 ----------

    def fetch(self) -> List[HotItem]:
        """抓取百度热搜"""
        items = self._fetch_from_api()
        if items:
            print(f"  [OK] 百度热搜: 获取 {len(items)} 条")
            return items

        items = self._fetch_from_page()
        if items:
            print(f"  [OK] 百度热搜 (页面): 获取 {len(items)} 条")
            return items

        raise RuntimeError("所有渠道均失败")
