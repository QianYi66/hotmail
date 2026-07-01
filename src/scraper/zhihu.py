# -*- coding: utf-8 -*-
"""
知乎热搜抓取

支持渠道：
1. 知乎热榜 API (api.zhihu.com - 无需认证)
2. 热榜页面 HTML 解析 (备用，有时需要 Cookie)
"""

import json
import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from . import BaseHotScraper, HotItem


class ZhihuHotScraper(BaseHotScraper):
    """
    知乎热搜抓取

    支持渠道：
    1. 知乎热榜 API (api.zhihu.com 子域名，无需登录)
    2. 热榜页面 HTML 解析 (备用)
    """

    source_name = "知乎热榜"
    source_key = "zhihu"

    # API（api.zhihu.com 无需认证即可访问）
    API_URL = "https://api.zhihu.com/topstory/hot-lists/total"
    # 热榜页面（备用）
    HTML_URL = "https://www.zhihu.com/hot"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.zhihu.com/",
            "Accept": "application/json, text/plain, */*",
        })

    # ---------- 渠道一：官方 API ----------

    def _fetch_from_api(self) -> Optional[List[HotItem]]:
        """从 api.zhihu.com 获取热榜（无需登录）"""
        resp = self.session.get(self.API_URL, timeout=self.timeout)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            return None

        data = resp.json()
        entries = data.get("data", [])
        if not entries:
            return None

        items = []
        for i, entry in enumerate(entries, start=1):
            target = entry.get("target", {})
            title = target.get("title", "")
            if not title:
                continue

            # 链接：将 api.zhihu.com 转为 www.zhihu.com（注意路径单复数）
            api_url = target.get("url", "")
            if api_url:
                link = api_url.replace("https://api.zhihu.com", "https://www.zhihu.com")
                link = link.replace("/questions/", "/question/")  # api 返回的是复数
            else:
                question_id = target.get("id", "")
                link = f"https://www.zhihu.com/question/{question_id}" if question_id else "https://www.zhihu.com/hot"

            # 热度标签
            tag = "热"
            card_label = entry.get("card_label", {})
            if isinstance(card_label, dict):
                label_type = card_label.get("type", "")
                # "boiling" = 沸, "hot" = 热, "new" = 新
                tag_map = {"boiling": "沸", "hot": "热", "new": "新", "explosive": "爆"}
                tag = tag_map.get(label_type, "热")

            # 热度指标：回答数 + 关注数
            answer_count = target.get("answer_count", 0)
            follower_count = target.get("follower_count", 0)
            hot = f"{answer_count} 回答" if answer_count else ""
            if follower_count:
                hot = f"{hot} · {follower_count} 关注" if hot else f"{follower_count} 关注"

            items.append(HotItem(
                rank=i,
                title=title,
                link=link,
                hot=hot,
                tag=tag,
            ))

        return items

    # ---------- 渠道二：页面解析 ----------

    def _fetch_from_page(self) -> Optional[List[HotItem]]:
        """解析知乎热榜页面"""
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
            if "window.__INITIAL_STATE__" in text:
                match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", text, re.DOTALL)
                if match:
                    try:
                        state = json.loads(match.group(1))
                        topstory = state.get("topstory", {})
                        hot_list = topstory.get("hotList", []) or topstory.get("recommendList", [])
                        for i, entry in enumerate(hot_list, start=1):
                            card = entry.get("card", entry)
                            target = card.get("target", card)
                            title = target.get("titleArea", {}).get("text", "") or target.get("title", "")
                            if not title:
                                continue
                            link = target.get("link", {}).get("url", "")
                            if link and not link.startswith("http"):
                                link = f"https://www.zhihu.com{link}"
                            items.append(HotItem(
                                rank=i,
                                title=title,
                                link=link or "https://www.zhihu.com/hot",
                            ))
                    except (json.JSONDecodeError, KeyError):
                        pass
                break

        # 兜底：用 CSS 选择器解析页面结构
        if not items:
            card_items = soup.select(".HotList-item, .TopstoryItem-hot")
            for i, card in enumerate(card_items, start=1):
                title_el = card.select_one(".HotList-itemTitle, .TopstoryItem-title")
                link_el = card.select_one("a")
                if title_el:
                    title = title_el.get_text(strip=True)
                    link = ""
                    if link_el and link_el.get("href"):
                        href = link_el["href"]
                        link = href if href.startswith("http") else f"https://www.zhihu.com{href}"
                    items.append(HotItem(
                        rank=i,
                        title=title,
                        link=link or "https://www.zhihu.com/hot",
                    ))

        return items if items else None

    # ---------- 主入口 ----------

    def fetch(self) -> List[HotItem]:
        """抓取知乎热搜"""
        items = self._fetch_from_api()
        if items:
            print(f"  [OK] 知乎热榜: 获取 {len(items)} 条")
            return items

        items = self._fetch_from_page()
        if items:
            print(f"  [OK] 知乎热榜 (页面): 获取 {len(items)} 条")
            return items

        raise RuntimeError("所有渠道均失败")
