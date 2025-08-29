"""
Celery应用配置

配置异步任务队列，支持训练、回测等长时间运行的任务。
"""

import os
from celery import Celery
from kombu import Queue

from app.core.config import settings


# 创建Celery实例
celery_app = Celery(
    "trademaster",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.training_tasks",
        "app.tasks.backtest_tasks", 
        "app.tasks.monitoring_tasks"
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # 任务路由
    task_routes={
        "training.*": {"queue": "training"},
        "backtest.*": {"queue": "backtest"},
        "monitoring.*": {"queue": "monitoring"}
    },
    
    # 队列定义
    task_queues=(
        Queue("training", routing_key="training"),
        Queue("backtest", routing_key="backtest"),
        Queue("monitoring", routing_key="monitoring"),
        Queue("default", routing_key="default")
    ),
    
    # 任务执行配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=7200,  # 2小时任务超时
    task_soft_time_limit=6600,  # 1.8小时软超时
    
    # 结果配置
    result_expires=86400,  # 结果保存1天
    result_backend_transport_options={"master_name": "mymaster"},
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # 错误处理
    task_reject_on_worker_lost=True,
    task_ignore_result=False
)

# 配置环境变量
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10
)


if __name__ == "__main__":
    celery_app.start()