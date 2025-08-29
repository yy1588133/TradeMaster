"""
训练任务辅助函数

提供数据库操作、实时数据推送、进度更新等支持功能。
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger
from sqlalchemy import select

from app.core.database import get_db_session
from app.models.database import (
    StrategySession, SessionStatus, PerformanceMetric, 
    ResourceUsage, User
)
from app.services.websocket_service import get_websocket_manager


# ==================== 进度更新和数据推送 ====================

async def _update_training_progress(
    session_id: int,
    progress: float,
    epoch: int,
    metrics: Dict[str, Any]
):
    """更新训练进度并推送实时数据"""
    try:
        async with get_db_session() as db:
            session = await db.get(StrategySession, session_id)
            if not session:
                logger.error(f"会话不存在: {session_id}")
                return
            
            # 更新会话进度
            session.progress = progress
            session.current_epoch = epoch
            session.updated_at = datetime.now()
            await db.commit()
            
            # 获取WebSocket管理器
            ws_manager = get_websocket_manager()
            
            # 推送进度更新
            await ws_manager.push_training_progress(session_id, {
                "progress": progress,
                "epoch": epoch,
                "total_epochs": session.total_epochs,
                "status": session.status.value
            })
            
            # 如果有新的指标数据，也推送指标更新
            if metrics:
                await ws_manager.push_performance_metrics(session_id, metrics)
                
            logger.debug(f"Session {session_id}: 进度更新 {progress}%, 轮次 {epoch}")
            
    except Exception as e:
        logger.error(f"更新训练进度失败: session_id={session_id}, error={str(e)}")


async def _record_performance_metrics(
    session_id: int,
    metrics: Dict[str, Any],
    epoch: int
):
    """记录性能指标到数据库"""
    try:
        async with get_db_session() as db:
            # 批量插入性能指标
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)):
                    metric = PerformanceMetric(
                        session_id=session_id,
                        metric_name=metric_name,
                        metric_value=float(metric_value),
                        epoch=epoch,
                        metadata={"source": "training_callback"}
                    )
                    db.add(metric)
            
            await db.commit()
            logger.debug(f"Session {session_id}: 记录性能指标 epoch={epoch}")
            
    except Exception as e:
        logger.error(f"记录性能指标失败: session_id={session_id}, error={str(e)}")


async def _update_session_final_status(
    session_id: int, 
    final_status: SessionStatus, 
    result: Dict[str, Any]
):
    """更新会话最终状态和结果"""
    try:
        async with get_db_session() as db:
            session = await db.get(StrategySession, session_id)
            if not session:
                return
            
            # 更新状态
            session.status = final_status
            session.completed_at = datetime.now()
            session.updated_at = datetime.now()
            
            # 保存结果数据
            if result.get("success"):
                session.result_data = {
                    "final_metrics": result.get("final_metrics", {}),
                    "evaluation_results": result.get("evaluation_results", {}),
                    "duration": result.get("duration", 0),
                    "success": True
                }
                session.progress = 100.0
            else:
                session.error_message = result.get("error_message", "训练失败")
                session.result_data = {
                    "success": False,
                    "error_type": result.get("error_type", "unknown"),
                    "error_details": result.get("error_message", "")
                }
            
            await db.commit()
            
            # 推送最终状态更新
            ws_manager = get_websocket_manager()
            await ws_manager.push_session_status_update(session_id, {
                "status": session.status.value,
                "progress": float(session.progress),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "result_data": session.result_data,
                "success": result.get("success", False)
            })
            
            logger.info(f"Session {session_id}: 最终状态更新为 {final_status.value}")
            
    except Exception as e:
        logger.error(f"更新最终状态失败: session_id={session_id}, error={str(e)}")


# ==================== 会话进度管理 ====================

async def _update_session_progress(session_id: int, current_epoch: int, progress: float):
    """更新会话训练进度"""
    try:
        async with get_db_session() as db:
            session = await db.get(StrategySession, session_id)
            if session:
                session.current_epoch = current_epoch
                session.progress = progress
                session.updated_at = datetime.now()
                await db.commit()
                
                # 推送进度更新
                ws_manager = get_websocket_manager()
                await ws_manager.push_training_progress(session_id, {
                    "progress": progress,
                    "epoch": current_epoch,
                    "total_epochs": session.total_epochs,
                    "status": session.status.value
                })
                
    except Exception as e:
        logger.error(f"更新会话进度失败: {str(e)}")


async def _save_performance_metrics(
    session_id: int, 
    metrics: Dict[str, Any], 
    epoch: int
):
    """保存性能指标"""
    try:
        async with get_db_session() as db:
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)):
                    metric = PerformanceMetric(
                        session_id=session_id,
                        metric_name=metric_name,
                        metric_value=float(metric_value),
                        epoch=epoch,
                        metadata={"source": "training_monitor"}
                    )
                    db.add(metric)
            
            await db.commit()
            
            # 推送性能指标更新
            ws_manager = get_websocket_manager()
            await ws_manager.push_performance_metrics(session_id, metrics)
            
    except Exception as e:
        logger.error(f"保存性能指标失败: {str(e)}")


async def _save_resource_usage(session_id: int, resource_info: Dict[str, Any]):
    """保存资源使用情况"""
    try:
        async with get_db_session() as db:
            usage = ResourceUsage(
                session_id=session_id,
                cpu_percent=resource_info.get("cpu_percent"),
                memory_mb=resource_info.get("memory_mb"),
                gpu_percent=resource_info.get("gpu_percent"),
                gpu_memory_mb=resource_info.get("gpu_memory_mb"),
                disk_io_mb=resource_info.get("disk_io_mb"),
                network_io_mb=resource_info.get("network_io_mb")
            )
            db.add(usage)
            await db.commit()
            
            # 推送资源使用更新
            ws_manager = get_websocket_manager()
            await ws_manager.push_resource_usage(session_id, resource_info)
            
    except Exception as e:
        logger.error(f"保存资源使用失败: {str(e)}")


async def _save_final_metrics(session_id: int, final_metrics: Dict[str, Any]):
    """保存最终训练指标"""
    try:
        async with get_db_session() as db:
            session = await db.get(StrategySession, session_id)
            if session:
                # 更新会话的最终指标
                if session.result_data is None:
                    session.result_data = {}
                session.result_data["final_metrics"] = final_metrics
                session.updated_at = datetime.now()
                await db.commit()
                
                # 推送最终指标
                ws_manager = get_websocket_manager()
                await ws_manager.push_performance_metrics(session_id, {
                    "final": True,
                    **final_metrics
                })
                
    except Exception as e:
        logger.error(f"保存最终指标失败: {str(e)}")


async def _collect_final_metrics(session_id: int) -> Dict[str, Any]:
    """收集最终训练指标"""
    try:
        async with get_db_session() as db:
            # 获取最新的性能指标
            query = select(PerformanceMetric).where(
                PerformanceMetric.session_id == session_id
            ).order_by(PerformanceMetric.recorded_at.desc()).limit(10)
            
            result = await db.execute(query)
            metrics = result.scalars().all()
            
            final_metrics = {}
            for metric in metrics:
                final_metrics[metric.metric_name] = float(metric.metric_value)
            
            return final_metrics
            
    except Exception as e:
        logger.error(f"收集最终指标失败: {str(e)}")
        return {}


# ==================== 错误处理和通知 ====================

async def push_error_notification(session_id: int, error_message: str, error_type: str = "unknown"):
    """推送错误通知"""
    try:
        ws_manager = get_websocket_manager()
        await ws_manager.push_error_notification(session_id, {
            "error_message": error_message,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.error(f"Session {session_id}: 错误通知 - {error_message}")
        
    except Exception as e:
        logger.error(f"推送错误通知失败: {str(e)}")


# ==================== 导出函数 ====================

__all__ = [
    "_update_training_progress",
    "_record_performance_metrics", 
    "_update_session_final_status",
    "_update_session_progress",
    "_save_performance_metrics",
    "_save_resource_usage",
    "_save_final_metrics",
    "_collect_final_metrics",
    "push_error_notification"
]