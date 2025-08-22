"""
任务队列管理系统

提供异步任务队列管理，支持训练任务、数据处理任务、分析任务的排队、执行和监控。
集成Redis作为消息队列，支持任务优先级、重试机制和状态跟踪。
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
import traceback

import redis.asyncio as redis
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 等待中
    RUNNING = "running"           # 运行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"       # 已取消
    RETRYING = "retrying"        # 重试中


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"                  # 低优先级
    NORMAL = "normal"            # 普通优先级
    HIGH = "high"                # 高优先级
    URGENT = "urgent"            # 紧急优先级


class TaskType(str, Enum):
    """任务类型枚举"""
    STRATEGY_TRAINING = "strategy_training"       # 策略训练
    DATA_PROCESSING = "data_processing"           # 数据处理
    BACKTEST_ANALYSIS = "backtest_analysis"       # 回测分析
    PERFORMANCE_EVALUATION = "performance_evaluation"  # 性能评估
    RISK_ANALYSIS = "risk_analysis"               # 风险分析
    TOOL_EXECUTION = "tool_execution"             # 工具执行
    CUSTOM = "custom"                             # 自定义任务


@dataclass
class TaskConfig:
    """任务配置"""
    max_retries: int = 3              # 最大重试次数
    retry_delay: int = 5              # 重试延迟（秒）
    timeout: int = 3600               # 任务超时时间（秒）
    heartbeat_interval: int = 30      # 心跳间隔（秒）
    result_ttl: int = 86400          # 结果存储时间（秒）


class TaskResult(BaseModel):
    """任务结果模型"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    error_traceback: Optional[str] = Field(None, description="错误堆栈")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    retry_count: int = Field(0, description="重试次数")
    progress: float = Field(0.0, description="执行进度（0-1）")
    metadata: Dict[str, Any] = Field({}, description="元数据")


class Task(BaseModel):
    """任务模型"""
    task_id: str = Field(..., description="任务ID")
    task_type: TaskType = Field(..., description="任务类型")
    task_name: str = Field(..., description="任务名称")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="任务优先级")
    status: TaskStatus = Field(TaskStatus.PENDING, description="任务状态")
    
    # 任务参数
    parameters: Dict[str, Any] = Field({}, description="任务参数")
    config: TaskConfig = Field(default_factory=TaskConfig, description="任务配置")
    
    # 执行信息
    user_id: Optional[str] = Field(None, description="用户ID")
    queue_name: str = Field("default", description="队列名称")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 执行状态
    worker_id: Optional[str] = Field(None, description="执行器ID")
    retry_count: int = Field(0, description="重试次数")
    progress: float = Field(0.0, description="执行进度（0-1）")
    last_heartbeat: Optional[datetime] = Field(None, description="最后心跳时间")
    
    # 结果和错误
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    error_traceback: Optional[str] = Field(None, description="错误堆栈")
    
    # 元数据
    metadata: Dict[str, Any] = Field({}, description="元数据")


class TaskQueueError(Exception):
    """任务队列异常"""
    pass


class TaskQueue:
    """任务队列管理器
    
    基于Redis实现的异步任务队列，支持：
    - 任务优先级排序
    - 任务状态跟踪
    - 失败重试机制
    - 任务超时处理
    - 工作进程心跳监控
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """初始化任务队列
        
        Args:
            redis_url: Redis连接URL
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        
        # 队列前缀
        self.queue_prefix = "trademaster:queue"
        self.task_prefix = "trademaster:task"
        self.result_prefix = "trademaster:result"
        self.worker_prefix = "trademaster:worker"
        
        # 优先级权重映射
        self.priority_weights = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4
        }
        
        # 任务处理器注册表
        self.task_handlers: Dict[TaskType, Callable] = {}
        
        logger.info("任务队列管理器初始化完成")
    
    async def connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise TaskQueueError(f"Redis连接失败: {str(e)}")
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis连接已断开")
    
    # ==================== 任务提交 ====================
    
    async def submit_task(
        self,
        task_type: TaskType,
        task_name: str,
        parameters: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        queue_name: str = "default",
        user_id: Optional[str] = None,
        config: Optional[TaskConfig] = None,
        scheduled_at: Optional[datetime] = None
    ) -> str:
        """提交任务到队列
        
        Args:
            task_type: 任务类型
            task_name: 任务名称
            parameters: 任务参数
            priority: 任务优先级
            queue_name: 队列名称
            user_id: 用户ID
            config: 任务配置
            scheduled_at: 计划执行时间
            
        Returns:
            str: 任务ID
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务对象
            task = Task(
                task_id=task_id,
                task_type=task_type,
                task_name=task_name,
                priority=priority,
                parameters=parameters,
                config=config or TaskConfig(),
                user_id=user_id,
                queue_name=queue_name,
                scheduled_at=scheduled_at
            )
            
            # 存储任务信息
            task_key = f"{self.task_prefix}:{task_id}"
            await self.redis_client.hset(
                task_key,
                mapping={
                    "data": json.dumps(task.dict(), default=str),
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "created_at": task.created_at.isoformat()
                }
            )
            
            # 设置任务过期时间
            await self.redis_client.expire(task_key, task.config.result_ttl)
            
            # 添加到队列
            if scheduled_at and scheduled_at > datetime.utcnow():
                # 延迟任务
                await self._add_to_delayed_queue(task)
            else:
                # 立即执行的任务
                await self._add_to_ready_queue(task)
            
            logger.info(f"任务提交成功: {task_id} ({task_name})")
            
            return task_id
            
        except Exception as e:
            logger.error(f"任务提交失败: {str(e)}")
            raise TaskQueueError(f"任务提交失败: {str(e)}")
    
    async def _add_to_ready_queue(self, task: Task):
        """添加任务到就绪队列"""
        queue_key = f"{self.queue_prefix}:ready:{task.queue_name}"
        priority_score = self.priority_weights[task.priority]
        
        # 使用有序集合实现优先级队列
        await self.redis_client.zadd(
            queue_key,
            {task.task_id: priority_score}
        )
    
    async def _add_to_delayed_queue(self, task: Task):
        """添加任务到延迟队列"""
        delayed_key = f"{self.queue_prefix}:delayed"
        timestamp = task.scheduled_at.timestamp()
        
        await self.redis_client.zadd(
            delayed_key,
            {task.task_id: timestamp}
        )
    
    # ==================== 任务获取和执行 ====================
    
    async def get_next_task(
        self,
        queue_name: str = "default",
        worker_id: Optional[str] = None
    ) -> Optional[Task]:
        """获取下一个待执行任务
        
        Args:
            queue_name: 队列名称
            worker_id: 工作进程ID
            
        Returns:
            Optional[Task]: 任务对象，如果没有任务则返回None
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            # 处理延迟任务
            await self._process_delayed_tasks()
            
            # 从就绪队列获取最高优先级任务
            queue_key = f"{self.queue_prefix}:ready:{queue_name}"
            
            # 使用ZREVRANGE获取最高分数的任务（最高优先级）
            task_ids = await self.redis_client.zrevrange(queue_key, 0, 0)
            
            if not task_ids:
                return None
            
            task_id = task_ids[0]
            
            # 从队列中移除任务
            await self.redis_client.zrem(queue_key, task_id)
            
            # 获取任务详情
            task = await self.get_task(task_id)
            if not task:
                return None
            
            # 更新任务状态为运行中
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            task.worker_id = worker_id
            task.last_heartbeat = datetime.utcnow()
            
            await self._update_task(task)
            
            # 添加到运行队列
            running_key = f"{self.queue_prefix}:running:{queue_name}"
            await self.redis_client.zadd(
                running_key,
                {task_id: datetime.utcnow().timestamp()}
            )
            
            logger.info(f"任务开始执行: {task_id} ({task.task_name})")
            
            return task
            
        except Exception as e:
            logger.error(f"获取任务失败: {str(e)}")
            raise TaskQueueError(f"获取任务失败: {str(e)}")
    
    async def _process_delayed_tasks(self):
        """处理延迟任务"""
        delayed_key = f"{self.queue_prefix}:delayed"
        current_time = datetime.utcnow().timestamp()
        
        # 获取到期的延迟任务
        expired_tasks = await self.redis_client.zrangebyscore(
            delayed_key, 0, current_time
        )
        
        for task_id in expired_tasks:
            # 获取任务信息
            task = await self.get_task(task_id)
            if task:
                # 移动到就绪队列
                await self._add_to_ready_queue(task)
                
            # 从延迟队列中移除
            await self.redis_client.zrem(delayed_key, task_id)
    
    # ==================== 任务状态管理 ====================
    
    async def update_task_progress(
        self,
        task_id: str,
        progress: float,
        message: Optional[str] = None
    ):
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度（0-1）
            message: 进度消息
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            task = await self.get_task(task_id)
            if not task:
                raise TaskQueueError(f"任务不存在: {task_id}")
            
            task.progress = max(0.0, min(1.0, progress))
            task.last_heartbeat = datetime.utcnow()
            
            if message:
                task.extra_metadata["progress_message"] = message
            
            await self._update_task(task)
            
            logger.debug(f"任务进度更新: {task_id} -> {progress:.2%}")
            
        except Exception as e:
            logger.error(f"更新任务进度失败: {task_id}, {str(e)}")
            raise TaskQueueError(f"更新任务进度失败: {str(e)}")
    
    async def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """完成任务
        
        Args:
            task_id: 任务ID
            result: 任务结果
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            task = await self.get_task(task_id)
            if not task:
                raise TaskQueueError(f"任务不存在: {task_id}")
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.progress = 1.0
            task.result = result
            
            # 计算执行时长
            if task.started_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                task.extra_metadata["duration"] = duration
            
            await self._update_task(task)
            
            # 从运行队列中移除
            await self._remove_from_running_queue(task_id, task.queue_name)
            
            # 存储结果
            await self._store_task_result(task)
            
            logger.info(f"任务完成: {task_id} ({task.task_name})")
            
        except Exception as e:
            logger.error(f"完成任务失败: {task_id}, {str(e)}")
            raise TaskQueueError(f"完成任务失败: {str(e)}")
    
    async def fail_task(
        self,
        task_id: str,
        error: str,
        error_traceback: Optional[str] = None,
        retry: bool = True
    ):
        """标记任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
            error_traceback: 错误堆栈
            retry: 是否重试
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            task = await self.get_task(task_id)
            if not task:
                raise TaskQueueError(f"任务不存在: {task_id}")
            
            task.error = error
            task.error_traceback = error_traceback
            task.retry_count += 1
            
            # 判断是否需要重试
            if retry and task.retry_count <= task.config.max_retries:
                # 重试任务
                task.status = TaskStatus.RETRYING
                task.progress = 0.0
                task.worker_id = None
                task.last_heartbeat = None
                
                # 添加重试延迟
                retry_at = datetime.utcnow() + timedelta(seconds=task.config.retry_delay)
                task.scheduled_at = retry_at
                
                await self._update_task(task)
                await self._add_to_delayed_queue(task)
                
                logger.warning(f"任务重试: {task_id} (第{task.retry_count}次)")
                
            else:
                # 任务最终失败
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                
                await self._update_task(task)
                await self._store_task_result(task)
                
                logger.error(f"任务失败: {task_id} ({task.task_name}) - {error}")
            
            # 从运行队列中移除
            await self._remove_from_running_queue(task_id, task.queue_name)
            
        except Exception as e:
            logger.error(f"标记任务失败异常: {task_id}, {str(e)}")
            raise TaskQueueError(f"标记任务失败异常: {str(e)}")
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            task = await self.get_task(task_id)
            if not task:
                return False
            
            # 只有等待中或重试中的任务可以取消
            if task.status not in [TaskStatus.PENDING, TaskStatus.RETRYING]:
                return False
            
            # 更新任务状态
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            
            await self._update_task(task)
            
            # 从相关队列中移除
            await self._remove_from_all_queues(task_id, task.queue_name)
            
            logger.info(f"任务已取消: {task_id} ({task.task_name})")
            
            return True
            
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, {str(e)}")
            raise TaskQueueError(f"取消任务失败: {str(e)}")
    
    # ==================== 任务查询 ====================
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            task_key = f"{self.task_prefix}:{task_id}"
            task_data = await self.redis_client.hget(task_key, "data")
            
            if not task_data:
                return None
            
            task_dict = json.loads(task_data)
            return Task(**task_dict)
            
        except Exception as e:
            logger.error(f"获取任务信息失败: {task_id}, {str(e)}")
            return None
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskResult]: 任务结果
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            result_key = f"{self.result_prefix}:{task_id}"
            result_data = await self.redis_client.get(result_key)
            
            if not result_data:
                # 如果没有结果，检查任务状态
                task = await self.get_task(task_id)
                if task:
                    return TaskResult(
                        task_id=task_id,
                        status=task.status,
                        result=task.result,
                        error=task.error,
                        error_traceback=task.error_traceback,
                        started_at=task.started_at,
                        completed_at=task.completed_at,
                        retry_count=task.retry_count,
                        progress=task.progress,
                        metadata=task.extra_metadata
                    )
                return None
            
            result_dict = json.loads(result_data)
            return TaskResult(**result_dict)
            
        except Exception as e:
            logger.error(f"获取任务结果失败: {task_id}, {str(e)}")
            return None
    
    async def list_tasks(
        self,
        queue_name: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Task]:
        """列出任务
        
        Args:
            queue_name: 队列名称筛选
            status: 状态筛选
            user_id: 用户ID筛选
            limit: 结果数量限制
            
        Returns:
            List[Task]: 任务列表
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            # 获取所有任务键
            pattern = f"{self.task_prefix}:*"
            task_keys = await self.redis_client.scan_iter(match=pattern)
            
            tasks = []
            count = 0
            
            async for task_key in task_keys:
                if count >= limit:
                    break
                
                task_id = task_key.split(":")[-1]
                task = await self.get_task(task_id)
                
                if not task:
                    continue
                
                # 应用筛选条件
                if queue_name and task.queue_name != queue_name:
                    continue
                
                if status and task.status != status:
                    continue
                
                if user_id and task.user_id != user_id:
                    continue
                
                tasks.append(task)
                count += 1
            
            # 按创建时间排序
            tasks.sort(key=lambda x: x.created_at, reverse=True)
            
            return tasks
            
        except Exception as e:
            logger.error(f"列出任务失败: {str(e)}")
            raise TaskQueueError(f"列出任务失败: {str(e)}")
    
    # ==================== 队列统计 ====================
    
    async def get_queue_stats(self, queue_name: str = "default") -> Dict[str, Any]:
        """获取队列统计信息
        
        Args:
            queue_name: 队列名称
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.redis_client:
            await self.connect()
        
        try:
            # 获取各队列长度
            ready_key = f"{self.queue_prefix}:ready:{queue_name}"
            running_key = f"{self.queue_prefix}:running:{queue_name}"
            delayed_key = f"{self.queue_prefix}:delayed"
            
            ready_count = await self.redis_client.zcard(ready_key)
            running_count = await self.redis_client.zcard(running_key)
            delayed_count = await self.redis_client.zcard(delayed_key)
            
            # 获取各状态任务统计
            all_tasks = await self.list_tasks(queue_name=queue_name, limit=1000)
            
            status_counts = {}
            for status in TaskStatus:
                status_counts[status.value] = len([
                    t for t in all_tasks if t.status == status
                ])
            
            return {
                "queue_name": queue_name,
                "ready_tasks": ready_count,
                "running_tasks": running_count,
                "delayed_tasks": delayed_count,
                "total_tasks": len(all_tasks),
                "status_counts": status_counts,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取队列统计失败: {queue_name}, {str(e)}")
            raise TaskQueueError(f"获取队列统计失败: {str(e)}")
    
    # ==================== 私有方法 ====================
    
    async def _update_task(self, task: Task):
        """更新任务信息"""
        task_key = f"{self.task_prefix}:{task.task_id}"
        await self.redis_client.hset(
            task_key,
            mapping={
                "data": json.dumps(task.dict(), default=str),
                "status": task.status.value,
                "updated_at": datetime.utcnow().isoformat()
            }
        )
    
    async def _store_task_result(self, task: Task):
        """存储任务结果"""
        result = TaskResult(
            task_id=task.task_id,
            status=task.status,
            result=task.result,
            error=task.error,
            error_traceback=task.error_traceback,
            started_at=task.started_at,
            completed_at=task.completed_at,
            duration=(task.completed_at - task.started_at).total_seconds() if task.started_at and task.completed_at else None,
            retry_count=task.retry_count,
            progress=task.progress,
            metadata=task.extra_metadata
        )
        
        result_key = f"{self.result_prefix}:{task.task_id}"
        await self.redis_client.setex(
            result_key,
            task.config.result_ttl,
            json.dumps(result.dict(), default=str)
        )
    
    async def _remove_from_running_queue(self, task_id: str, queue_name: str):
        """从运行队列中移除任务"""
        running_key = f"{self.queue_prefix}:running:{queue_name}"
        await self.redis_client.zrem(running_key, task_id)
    
    async def _remove_from_all_queues(self, task_id: str, queue_name: str):
        """从所有队列中移除任务"""
        ready_key = f"{self.queue_prefix}:ready:{queue_name}"
        running_key = f"{self.queue_prefix}:running:{queue_name}"
        delayed_key = f"{self.queue_prefix}:delayed"
        
        await self.redis_client.zrem(ready_key, task_id)
        await self.redis_client.zrem(running_key, task_id)
        await self.redis_client.zrem(delayed_key, task_id)


# 全局任务队列实例
_task_queue = None

async def get_task_queue() -> TaskQueue:
    """获取任务队列实例
    
    Returns:
        TaskQueue: 任务队列实例
    """
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
        await _task_queue.connect()
    return _task_queue


# 导出主要类和函数
__all__ = [
    "TaskQueue",
    "Task",
    "TaskResult",
    "TaskConfig",
    "TaskStatus",
    "TaskPriority", 
    "TaskType",
    "TaskQueueError",
    "get_task_queue"
]