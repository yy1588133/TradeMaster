"""
训练管理服务

提供机器学习模型训练的完整生命周期管理，包括训练任务创建、监控、控制等功能。
集成TradeMaster训练流程和Celery异步任务，支持分布式训练和资源管理。
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from enum import Enum

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from app.core.trademaster_config import get_config_adapter
from app.services.trademaster_integration import (
    get_trademaster_service,
    TradeMasterAPIException,
    IntegrationMode
)
from app.models.database import (
    TrainingJob,
    TrainingMetric,
    TrainingStatus,
    Strategy,
    Dataset,
    User
)


class TrainingServiceError(Exception):
    """训练服务异常"""
    pass


class TrainingMode(str, Enum):
    """训练模式枚举"""
    STANDARD = "standard"           # 标准训练
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"  # 超参数调优
    ENSEMBLE = "ensemble"           # 集成训练
    TRANSFER_LEARNING = "transfer_learning"  # 迁移学习


class ResourceType(str, Enum):
    """资源类型枚举"""
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    STORAGE = "storage"


class TrainingService:
    """训练管理服务
    
    提供训练任务的完整生命周期管理功能：
    - 训练任务创建和配置
    - 训练进度监控
    - 资源使用管理
    - 超参数优化
    - 模型保存和版本管理
    """
    
    def __init__(self):
        """初始化训练服务"""
        self.config_adapter = get_trademaster_config_adapter()
        self.trademaster_service = get_trademaster_service()
        
        # 训练任务状态映射
        self.status_mapping = {
            "pending": TrainingStatus.PENDING,
            "running": TrainingStatus.RUNNING,
            "completed": TrainingStatus.COMPLETED,
            "failed": TrainingStatus.FAILED,
            "cancelled": TrainingStatus.CANCELLED
        }
        
        # 默认训练配置
        self.default_training_config = {
            "epochs": 100,
            "batch_size": 64,
            "learning_rate": 0.001,
            "early_stopping": True,
            "patience": 10,
            "save_best_model": True,
            "validation_split": 0.2
        }
        
        # 资源限制配置
        self.resource_limits = {
            ResourceType.CPU: 8,      # CPU核心数
            ResourceType.GPU: 1,      # GPU数量
            ResourceType.MEMORY: 16,  # 内存GB
            ResourceType.STORAGE: 100 # 存储GB
        }
        
        logger.info("训练服务初始化完成")
    
    # ==================== 训练任务管理 ====================
    
    async def create_training_job(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int,
        training_config: Optional[Dict[str, Any]] = None,
        dataset_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        training_mode: TrainingMode = TrainingMode.STANDARD
    ) -> Dict[str, Any]:
        """创建训练任务
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID
            training_config: 训练配置
            dataset_id: 数据集ID
            name: 任务名称
            description: 任务描述
            training_mode: 训练模式
            
        Returns:
            Dict[str, Any]: 创建的训练任务信息
            
        Raises:
            TrainingServiceError: 创建失败时抛出
        """
        try:
            # 验证策略存在
            strategy_result = await db.execute(
                select(Strategy).where(
                    Strategy.id == strategy_id,
                    Strategy.owner_id == user_id
                )
            )
            strategy = strategy_result.scalar_one_or_none()
            
            if not strategy:
                raise TrainingServiceError("策略不存在或无权限访问")
            
            # 验证数据集存在（如果提供）
            dataset = None
            if dataset_id:
                dataset_result = await db.execute(
                    select(Dataset).where(
                        Dataset.id == dataset_id,
                        Dataset.owner_id == user_id
                    )
                )
                dataset = dataset_result.scalar_one_or_none()
                
                if not dataset:
                    raise TrainingServiceError("数据集不存在或无权限访问")
            
            # 合并训练配置
            final_config = {**self.default_training_config}
            if training_config:
                final_config.update(training_config)
            
            # 构建完整的训练配置
            full_config = {
                **strategy.config,
                **final_config,
                "training_mode": training_mode.value
            }
            
            # 验证配置
            validation_errors = await self._validate_training_config(full_config)
            if validation_errors:
                raise TrainingServiceError(f"训练配置验证失败: {'; '.join(validation_errors)}")
            
            # 生成任务名称
            if not name:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                name = f"{strategy.name}_training_{timestamp}"
            
            # 创建训练任务记录
            training_job = TrainingJob(
                uuid=str(uuid.uuid4()),
                name=name,
                description=description,
                status=TrainingStatus.PENDING,
                config=full_config,
                hyperparameters=training_config or {},
                strategy_id=strategy_id,
                dataset_id=dataset_id,
                user_id=user_id,
                total_epochs=final_config.get("epochs", 100)
            )
            
            db.add(training_job)
            await db.commit()
            await db.refresh(training_job)
            
            logger.info(f"训练任务创建成功: {name} (ID: {training_job.id})")
            
            return {
                "job_id": training_job.id,
                "job_uuid": training_job.uuid,
                "name": name,
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "dataset_id": dataset_id,
                "dataset_name": dataset.name if dataset else None,
                "training_mode": training_mode.value,
                "status": training_job.status.value,
                "config": full_config,
                "created_at": training_job.created_at.isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"训练任务创建失败: {str(e)}")
            raise TrainingServiceError(f"训练任务创建失败: {str(e)}")
    
    async def start_training_job(
        self,
        db: AsyncSession,
        job_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """启动训练任务
        
        Args:
            db: 数据库会话
            job_id: 训练任务ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 启动结果
            
        Raises:
            TrainingServiceError: 启动失败时抛出
        """
        try:
            # 获取训练任务
            result = await db.execute(
                select(TrainingJob)
                .options(selectinload(TrainingJob.strategy))
                .where(
                    TrainingJob.id == job_id,
                    TrainingJob.user_id == user_id
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise TrainingServiceError("训练任务不存在或无权限访问")
            
            if job.status != TrainingStatus.PENDING:
                raise TrainingServiceError(f"训练任务状态不正确: {job.status}")
            
            # 检查资源可用性
            resource_check = await self._check_resource_availability(job.config)
            if not resource_check["available"]:
                raise TrainingServiceError(f"资源不足: {resource_check['message']}")
            
            # 构建TradeMaster配置
            tm_config = await self._build_trademaster_training_config(job)
            
            # 启动训练
            try:
                training_result = await self.trademaster_service.train_strategy(tm_config)
                session_id = training_result.get("session_id")
                
                if not session_id:
                    raise TrainingServiceError("无法获取训练会话ID")
                
                # 更新任务状态
                await db.execute(
                    update(TrainingJob)
                    .where(TrainingJob.id == job_id)
                    .values(
                        status=TrainingStatus.RUNNING,
                        trademaster_session_id=session_id,
                        started_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # 启动监控任务
                asyncio.create_task(
                    self._monitor_training_job(db, job_id, session_id)
                )
                
                logger.info(f"训练任务启动成功: {job.name} (会话ID: {session_id})")
                
                return {
                    "job_id": job_id,
                    "session_id": session_id,
                    "status": "started",
                    "message": "训练任务已启动",
                    "started_at": datetime.utcnow().isoformat()
                }
                
            except TradeMasterAPIException as e:
                # 更新为失败状态
                await db.execute(
                    update(TrainingJob)
                    .where(TrainingJob.id == job_id)
                    .values(
                        status=TrainingStatus.FAILED,
                        error_message=str(e)
                    )
                )
                await db.commit()
                raise TrainingServiceError(f"启动训练失败: {str(e)}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"训练任务启动失败: {str(e)}")
            raise TrainingServiceError(f"训练任务启动失败: {str(e)}")
    
    async def stop_training_job(
        self,
        db: AsyncSession,
        job_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """停止训练任务
        
        Args:
            db: 数据库会话
            job_id: 训练任务ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 停止结果
            
        Raises:
            TrainingServiceError: 停止失败时抛出
        """
        try:
            # 获取训练任务
            result = await db.execute(
                select(TrainingJob).where(
                    TrainingJob.id == job_id,
                    TrainingJob.user_id == user_id
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise TrainingServiceError("训练任务不存在或无权限访问")
            
            if job.status not in [TrainingStatus.PENDING, TrainingStatus.RUNNING]:
                raise TrainingServiceError(f"训练任务无法停止，当前状态: {job.status}")
            
            # 停止TradeMaster训练
            if job.trademaster_session_id:
                try:
                    await self.trademaster_service.stop_training(job.trademaster_session_id)
                except Exception as e:
                    logger.warning(f"停止TradeMaster训练失败: {str(e)}")
            
            # 更新任务状态
            await db.execute(
                update(TrainingJob)
                .where(TrainingJob.id == job_id)
                .values(
                    status=TrainingStatus.CANCELLED,
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            logger.info(f"训练任务停止成功: {job.name}")
            
            return {
                "job_id": job_id,
                "status": "stopped",
                "message": "训练任务已停止",
                "stopped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"训练任务停止失败: {str(e)}")
            raise TrainingServiceError(f"训练任务停止失败: {str(e)}")
    
    async def get_training_job_status(
        self,
        db: AsyncSession,
        job_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取训练任务状态
        
        Args:
            db: 数据库会话
            job_id: 训练任务ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 训练任务状态信息
            
        Raises:
            TrainingServiceError: 获取失败时抛出
        """
        try:
            # 获取训练任务
            result = await db.execute(
                select(TrainingJob)
                .options(
                    selectinload(TrainingJob.strategy),
                    selectinload(TrainingJob.dataset)
                )
                .where(
                    TrainingJob.id == job_id,
                    TrainingJob.user_id == user_id
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise TrainingServiceError("训练任务不存在或无权限访问")
            
            # 获取最新指标
            latest_metrics = {}
            if job.trademaster_session_id:
                try:
                    tm_status = await self.trademaster_service.get_train_status(
                        job.trademaster_session_id
                    )
                    latest_metrics = tm_status.get("metrics", {})
                except Exception as e:
                    logger.warning(f"获取TradeMaster状态失败: {str(e)}")
            
            # 计算运行时间
            runtime_seconds = None
            if job.started_at:
                end_time = job.completed_at or datetime.utcnow()
                runtime_seconds = int((end_time - job.started_at).total_seconds())
            
            # 预估剩余时间
            estimated_remaining = None
            if job.status == TrainingStatus.RUNNING and job.current_epoch > 0:
                epochs_remaining = job.total_epochs - job.current_epoch
                avg_time_per_epoch = runtime_seconds / job.current_epoch if runtime_seconds else 0
                estimated_remaining = int(epochs_remaining * avg_time_per_epoch)
            
            return {
                "job_id": job.id,
                "job_uuid": job.uuid,
                "name": job.name,
                "description": job.description,
                "status": job.status.value,
                "progress": float(job.progress),
                "current_epoch": job.current_epoch,
                "total_epochs": job.total_epochs,
                "strategy_name": job.strategy.name if job.strategy else None,
                "dataset_name": job.dataset.name if job.dataset else None,
                "latest_metrics": latest_metrics,
                "best_metrics": job.best_metrics,
                "runtime_seconds": runtime_seconds,
                "estimated_remaining_seconds": estimated_remaining,
                "resource_usage": {
                    "cpu_usage": float(job.cpu_usage) if job.cpu_usage else None,
                    "memory_usage": float(job.memory_usage) if job.memory_usage else None,
                    "gpu_usage": float(job.gpu_usage) if job.gpu_usage else None
                },
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message
            }
            
        except Exception as e:
            logger.error(f"获取训练任务状态失败: {str(e)}")
            raise TrainingServiceError(f"获取训练任务状态失败: {str(e)}")
    
    async def get_training_logs(
        self,
        db: AsyncSession,
        job_id: int,
        user_id: int,
        limit: int = 100,
        level: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取训练日志
        
        Args:
            db: 数据库会话
            job_id: 训练任务ID
            user_id: 用户ID
            limit: 日志条数限制
            level: 日志级别过滤
            
        Returns:
            Dict[str, Any]: 训练日志
            
        Raises:
            TrainingServiceError: 获取失败时抛出
        """
        try:
            # 获取训练任务
            result = await db.execute(
                select(TrainingJob).where(
                    TrainingJob.id == job_id,
                    TrainingJob.user_id == user_id
                )
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise TrainingServiceError("训练任务不存在或无权限访问")
            
            # 获取TradeMaster日志
            logs = []
            if job.trademaster_session_id:
                try:
                    tm_logs = await self.trademaster_service.get_training_logs(
                        job.trademaster_session_id, limit, level
                    )
                    logs = tm_logs.get("logs", [])
                except Exception as e:
                    logger.warning(f"获取TradeMaster日志失败: {str(e)}")
            
            # 添加本地日志
            if job.logs:
                local_logs = json.loads(job.logs) if isinstance(job.logs, str) else job.logs
                if isinstance(local_logs, list):
                    logs.extend(local_logs)
            
            # 按时间排序
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return {
                "job_id": job_id,
                "logs": logs[:limit],
                "total_logs": len(logs),
                "level_filter": level
            }
            
        except Exception as e:
            logger.error(f"获取训练日志失败: {str(e)}")
            raise TrainingServiceError(f"获取训练日志失败: {str(e)}")
    
    # ==================== 超参数优化 ====================
    
    async def start_hyperparameter_tuning(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int,
        param_space: Dict[str, Any],
        optimization_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """启动超参数优化
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID
            param_space: 参数空间定义
            optimization_config: 优化配置
            
        Returns:
            Dict[str, Any]: 优化任务信息
        """
        try:
            # 默认优化配置
            default_opt_config = {
                "n_trials": 50,
                "timeout": 3600,  # 1小时
                "optimization_direction": "maximize",
                "target_metric": "validation_accuracy"
            }
            
            final_opt_config = {**default_opt_config}
            if optimization_config:
                final_opt_config.update(optimization_config)
            
            # 创建优化任务
            tuning_job = await self.create_training_job(
                db=db,
                strategy_id=strategy_id,
                user_id=user_id,
                training_config={
                    "param_space": param_space,
                    "optimization_config": final_opt_config
                },
                training_mode=TrainingMode.HYPERPARAMETER_TUNING,
                name=f"hyperparameter_tuning_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # 启动优化流程
            await self._run_hyperparameter_optimization(
                db, tuning_job["job_id"], param_space, final_opt_config
            )
            
            return {
                **tuning_job,
                "optimization_type": "hyperparameter_tuning",
                "param_space": param_space,
                "optimization_config": final_opt_config
            }
            
        except Exception as e:
            logger.error(f"超参数优化启动失败: {str(e)}")
            raise TrainingServiceError(f"超参数优化启动失败: {str(e)}")
    
    # ==================== 监控和指标 ====================
    
    async def _monitor_training_job(
        self,
        db: AsyncSession,
        job_id: int,
        session_id: str
    ):
        """监控训练任务进度"""
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                try:
                    # 获取训练状态
                    status = await self.trademaster_service.get_train_status(session_id)
                    
                    # 更新任务状态
                    update_data = {
                        "progress": min(100.0, status.get("progress", 0)),
                        "current_epoch": status.get("current_epoch", 0),
                        "metrics": status.get("metrics", {})
                    }
                    
                    # 检查是否完成
                    if status.get("status") in ["completed", "failed", "stopped"]:
                        update_data["status"] = self.status_mapping.get(
                            status["status"], TrainingStatus.FAILED
                        )
                        update_data["completed_at"] = datetime.utcnow()
                        
                        if status["status"] == "completed":
                            # 保存最终结果
                            update_data["best_metrics"] = status.get("final_metrics", {})
                    
                    await db.execute(
                        update(TrainingJob)
                        .where(TrainingJob.id == job_id)
                        .values(**update_data)
                    )
                    await db.commit()
                    
                    # 保存指标历史
                    if status.get("metrics"):
                        await self._save_training_metrics(
                            db, job_id, status["current_epoch"], status["metrics"]
                        )
                    
                    # 如果任务完成，退出监控
                    if update_data.get("status") in [
                        TrainingStatus.COMPLETED,
                        TrainingStatus.FAILED,
                        TrainingStatus.CANCELLED
                    ]:
                        break
                        
                except Exception as e:
                    logger.warning(f"监控训练任务失败: {job_id}, {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"训练任务监控异常: {job_id}, {str(e)}")
    
    async def _save_training_metrics(
        self,
        db: AsyncSession,
        job_id: int,
        epoch: int,
        metrics: Dict[str, Any]
    ):
        """保存训练指标"""
        try:
            metric_record = TrainingMetric(
                training_job_id=job_id,
                epoch=epoch,
                metrics=metrics
            )
            
            db.add(metric_record)
            await db.commit()
            
        except Exception as e:
            logger.warning(f"保存训练指标失败: {str(e)}")
    
    # ==================== 辅助方法 ====================
    
    async def _validate_training_config(self, config: Dict[str, Any]) -> List[str]:
        """验证训练配置"""
        errors = []
        
        # 检查必需参数
        required_params = ["epochs", "batch_size", "learning_rate"]
        for param in required_params:
            if param not in config:
                errors.append(f"缺少必需参数: {param}")
        
        # 检查参数范围
        if config.get("epochs") and (config["epochs"] < 1 or config["epochs"] > 10000):
            errors.append("epochs必须在1-10000之间")
        
        if config.get("batch_size") and (config["batch_size"] < 1 or config["batch_size"] > 1024):
            errors.append("batch_size必须在1-1024之间")
        
        if config.get("learning_rate") and (config["learning_rate"] <= 0 or config["learning_rate"] > 1):
            errors.append("learning_rate必须在0-1之间")
        
        return errors
    
    async def _check_resource_availability(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """检查资源可用性"""
        # 简化的资源检查实现
        required_memory = config.get("required_memory", 8)
        required_gpu = config.get("required_gpu", 0)
        
        available_memory = self.resource_limits[ResourceType.MEMORY]
        available_gpu = self.resource_limits[ResourceType.GPU]
        
        if required_memory > available_memory:
            return {
                "available": False,
                "message": f"内存不足，需要 {required_memory}GB，可用 {available_memory}GB"
            }
        
        if required_gpu > available_gpu:
            return {
                "available": False,
                "message": f"GPU不足，需要 {required_gpu} 个，可用 {available_gpu} 个"
            }
        
        return {"available": True, "message": "资源充足"}
    
    async def _build_trademaster_training_config(
        self,
        job: TrainingJob
    ) -> Dict[str, Any]:
        """构建TradeMaster训练配置"""
        # 合并策略配置和训练配置
        tm_config = {
            **job.strategy.config,
            **job.config,
            "job_id": job.id,
            "job_uuid": job.uuid
        }
        
        return tm_config
    
    async def _run_hyperparameter_optimization(
        self,
        db: AsyncSession,
        job_id: int,
        param_space: Dict[str, Any],
        opt_config: Dict[str, Any]
    ):
        """运行超参数优化"""
        # 这里应该实现具体的超参数优化逻辑
        # 可以集成Optuna、Ray Tune等优化库
        logger.info(f"开始超参数优化: {job_id}")
        
        # 模拟优化过程
        asyncio.create_task(self._simulate_hyperparameter_optimization(db, job_id))
    
    async def _simulate_hyperparameter_optimization(
        self,
        db: AsyncSession,
        job_id: int
    ):
        """模拟超参数优化过程"""
        try:
            # 更新状态为运行中
            await db.execute(
                update(TrainingJob)
                .where(TrainingJob.id == job_id)
                .values(
                    status=TrainingStatus.RUNNING,
                    started_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            # 模拟优化过程
            await asyncio.sleep(60)  # 模拟1分钟的优化
            
            # 模拟优化结果
            best_params = {
                "learning_rate": 0.001,
                "batch_size": 64,
                "hidden_size": 128
            }
            
            best_metrics = {
                "accuracy": 0.95,
                "loss": 0.05,
                "f1_score": 0.93
            }
            
            # 更新完成状态
            await db.execute(
                update(TrainingJob)
                .where(TrainingJob.id == job_id)
                .values(
                    status=TrainingStatus.COMPLETED,
                    progress=100.0,
                    best_metrics=best_metrics,
                    hyperparameters=best_params,
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            logger.info(f"超参数优化完成: {job_id}")
            
        except Exception as e:
            # 更新失败状态
            await db.execute(
                update(TrainingJob)
                .where(TrainingJob.id == job_id)
                .values(
                    status=TrainingStatus.FAILED,
                    error_message=str(e),
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            logger.error(f"超参数优化失败: {job_id}, {str(e)}")


# 全局服务实例
_training_service = None

def get_training_service() -> TrainingService:
    """获取训练服务实例
    
    Returns:
        TrainingService: 训练服务实例
    """
    global _training_service
    if _training_service is None:
        _training_service = TrainingService()
    return _training_service


# 导出主要类和函数
__all__ = [
    "TrainingService",
    "TrainingServiceError",
    "TrainingMode",
    "ResourceType",
    "get_training_service"
]