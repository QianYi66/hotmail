# -*- coding: utf-8 -*-
"""
热搜抓取基类
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HotItem:
    """一条热搜"""
    rank: int                   # 排名
    title: str                  # 标题
    hot: Optional[str] = None   # 热度值
    link: Optional[str] = None  # 链接
    tag: Optional[str] = None   # 标签（如"新"、"沸"、"爆"、"热"）

    def __str__(self):
        return f"#{self.rank}. {self.title}"


class BaseHotScraper:
    """热搜抓取基类"""

    source_name: str = "未知"       # 来源名称（中文）
    source_key: str = "unknown"     # 来源标识

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.source_name

    def fetch(self) -> List[HotItem]:
        """抓取热搜列表，子类必须实现"""
        raise NotImplementedError

    def fetch_safe(self) -> List[HotItem]:
        """安全抓取，失败时返回空列表"""
        try:
            result = self.fetch()
            if not result:
                print(f"  [!] {self.source_name}: 未获取到数据")
                return []
            return result
        except Exception as e:
            print(f"  [X] {self.source_name}: 抓取失败 - {e}")
            return []
