# -*- coding: utf-8 -*-
"""
定时调度模块
"""

import logging
import time
from datetime import datetime
from functools import partial
from typing import Callable, List, Optional

import schedule

logger = logging.getLogger("hotmail")


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self):
        self._jobs: List[str] = []
        self._running = False

    def setup(self, times: List[str], job_func: Callable):
        """
        配置定时任务

        Args:
            times: 发送时间列表，如 ["09:00", "18:00"]
            job_func: 要执行的函数
        """
        self.clear()

        for t in times:
            schedule.every().day.at(t).do(job_func)
            self._jobs.append(t)
            logger.info(f"  已设置定时发送: 每天 {t}")

    def run_once(self, job_func: Callable):
        """立即执行一次"""
        logger.info("立即执行一次...")
        job_func()

    def start(self, run_immediately: bool = False, job_func: Optional[Callable] = None):
        """
        启动定时循环

        Args:
            run_immediately: 是否先立即执行一次
            job_func: 任务函数
        """
        if run_immediately and job_func:
            self.run_once(job_func)

        if not self._jobs:
            logger.warning("未设置任何定时任务")
            return

        self._running = True
        logger.info(f"⏰ 定时调度已启动 (共 {len(self._jobs)} 个任务)")
        logger.info(f"   下次发送: {schedule.next_run()}")

        try:
            while self._running:
                schedule.run_pending()
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("收到终止信号，调度停止")
            self.stop()

    def stop(self):
        """停止调度"""
        self._running = False
        self.clear()
        logger.info("调度已停止")

    def clear(self):
        """清除所有任务"""
        schedule.clear()
        self._jobs.clear()

    @property
    def next_run(self) -> Optional[str]:
        """下次运行时间"""
        n = schedule.next_run()
        return n.strftime("%Y-%m-%d %H:%M:%S") if n else None
