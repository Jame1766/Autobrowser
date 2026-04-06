"""
定时任务调度器
每3小时执行一次爬取和发布流程
"""
import logging
import time
from datetime import datetime
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = []

    def add_job(self, func: Callable, interval_hours: int = 3, **kwargs):
        """
        添加定时任务

        Args:
            func: 要执行的函数
            interval_hours: 执行间隔（小时）
            **kwargs: 传递给函数的参数
        """
        trigger = IntervalTrigger(hours=interval_hours)
        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            kwargs=kwargs,
            id='crawl_and_publish',
            replace_existing=True
        )
        self.jobs.append(job)
        logger.info(f"添加定时任务: 每 {interval_hours} 小时执行")

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("调度器已启动")

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("调度器已关闭")

    def run_once(self, func: Callable, **kwargs):
        """立即执行一次任务"""
        logger.info("立即执行任务...")
        func(**kwargs)
