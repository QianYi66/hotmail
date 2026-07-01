# -*- coding: utf-8 -*-
"""
今日热闻 - 定时邮件推送
把微博热搜、知乎热搜等内容定时发送到邮箱。
"""

from datetime import datetime, timezone, timedelta


def beijing_now() -> datetime:
    """返回北京时区（UTC+8）的当前时间"""
    return datetime.now(timezone(timedelta(hours=8)))
