# -*- coding: utf-8 -*-
"""
配置加载模块
"""

import os
from pathlib import Path
from typing import List, Optional

import yaml


class MailConfig:
    """邮箱配置"""

    def __init__(self, data: dict):
        self.smtp_server: str = data.get("smtp_server", "smtp.qq.com")
        self.smtp_port: int = data.get("smtp_port", 465)
        self.sender_email: str = data.get("sender_email", "")
        self.sender_password: str = data.get("sender_password", "")
        self.recipients: List[str] = data.get("recipients", [])
        self.sender_name: str = data.get("sender_name", "今日热闻")

    @property
    def valid(self) -> bool:
        """配置是否有效"""
        return bool(self.sender_email and self.sender_password and self.recipients)


class ContentConfig:
    """内容配置"""

    def __init__(self, data: dict):
        self.weibo: bool = data.get("weibo", True)
        self.zhihu: bool = data.get("zhihu", True)
        self.baidu: bool = data.get("baidu", False)
        self.limit: int = data.get("limit", 20)


class ScheduleConfig:
    """定时配置"""

    def __init__(self, data: dict):
        self.enabled: bool = data.get("enabled", True)
        self.times: List[str] = data.get("times", ["09:00"])


class AppConfig:
    """应用配置"""

    def __init__(self, data: dict):
        self.mail = MailConfig(data.get("mail", {}))
        self.content = ContentConfig(data.get("content", {}))
        self.schedule = ScheduleConfig(data.get("schedule", {}))

    @classmethod
    def load(cls, path: Optional[str] = None) -> "AppConfig":
        """从 YAML 文件加载配置"""
        if path is None:
            path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config.yaml",
            )

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(data)
