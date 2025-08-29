"""
任务初始化模块

导入所有任务模块，确保Celery能够发现和注册任务。
"""

from app.tasks.training_tasks import execute_training_task, stop_training_task
from app.tasks.backtest_tasks import execute_backtest_task

__all__ = [
    "execute_training_task",
    "stop_training_task", 
    "execute_backtest_task"
]