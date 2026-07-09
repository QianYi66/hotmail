# -*- coding: utf-8 -*-
"""
抖音热搜抓取

渠道：
1. 抖音热搜 API (aweme/v1/web/hot/search/list/ - 无需认证)
"""

from typing import List, Optional
import urllib.parse

import requests

from . import BaseHotScraper, HotItem


class DouyinHotScraper(BaseHotScraper):
    """
    抖音热搜抓取

    使用抖音官方热搜 API，无需 Cookie 或登录。
    """

    source_name = "抖音热搜"
    source_key = "douyin"

    # 热搜 API（无需 Cookie）
    API_URL = "https://www.douyin.com/aweme/v1/web/hot/search/list/"

    # 标签映射（抖音 label 字段为数字，这里做常用映射）
    LABEL_MAP = {
        0: "",
        1: "爆",
        2: "沸",
        3: "热",
        4: "新",
        5: "荐",
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
        })

    def _fetch_from_api(self) -> Optional[List[HotItem]]:
        """从抖音热搜 API 获取"""
        resp = self.session.get(self.API_URL, timeout=self.timeout)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            return None

        data = resp.json()

        # 检查状态码
        if data.get("status_code") != 0:
            return None

        word_list = data.get("data", {}).get("word_list", [])
        if not word_list:
            return None

        items = []
        for entry in word_list:
            title = entry.get("word", "")
            if not title:
                continue

            rank = entry.get("position", 0)

            # 热值
            hot_value = entry.get("hot_value", 0)

            # 标签
            label_num = entry.get("label", 0)
            tag = self.LABEL_MAP.get(label_num, "")

            # 链接：抖音热搜词本质是搜索关键词，跳转到搜索结果页
            keyword = urllib.parse.quote(title, safe='')
            link = f"https://www.douyin.com/search/{keyword}"

            items.append(HotItem(
                rank=rank,
                title=title,
                link=link,
                hot=str(hot_value) if hot_value else "",
                tag=tag,
            ))

        return items if items else None

    def fetch(self) -> List[HotItem]:
        """抓取抖音热搜"""
        items = self._fetch_from_api()
        if items:
            return items

        raise RuntimeError("抖音热搜 API 返回为空")
