"""
监控任务

定期监控训练会话状态并推送实时数据到WebSocket客户端。
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from loguru import logger
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import get_async_db_session
from app.models.database import StrategySession, SessionStatus
from app.services.websocket_service import get_websocket_manager


@celery_app.task(name="monitoring.session_monitor")
def monitor_active_sessions():
    """监控活跃会话并推送实时数据"""
    logger.info("开始监控活跃会话")
    
    try:
        # 使用异步包装器
        asyncio.run(_monitor_sessions_async())
    except Exception as e:
        logger.error(f"监控会话时发生错误: {str(e)}")


async def _monitor_sessions_async():
    """异步监控会话"""
    try:
        ws_manager = get_websocket_manager()
        
        # 获取所有活跃会话
        async with get_async_db_session() as db:
            query = select(StrategySession).where(
                StrategySession.status.in_([
                    SessionStatus.RUNNING, 
                    SessionStatus.PENDING
                ])
            )
            
            result = await db.execute(query)
            active_sessions = result.scalars().all()
        
        logger.info(f"找到 {len(active_sessions)} 个活跃会话")
        
        # 为每个会话推送状态更新
        for session in active_sessions:
            try:
                await _push_session_updates(session, ws_manager)
            except Exception as e:
                logger.error(f"推送会话 {session.id} 更新失败: {str(e)}")
        
        # 清理不活跃连接
        await ws_manager.cleanup_inactive_connections()
        
    except Exception as e:
        logger.error(f"异步监控会话失败: {str(e)}")


async def _push_session_updates(session: StrategySession, ws_manager):
    """推送单个会话的更新"""
    try:
        # 检查是否有订阅者
        subscriber_count = ws_manager.get_session_subscriber_count(session.id)
        if subscriber_count == 0:
            return
        
        # 构建状态数据
        status_data = {
            "session_id": session.id,
            "status": session.status.value,
            "progress": float(session.progress),
            "current_epoch": session.current_epoch,
            "total_epochs": session.total_epochs,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "last_update": datetime.now().isoformat()
        }
        
        # 推送状态更新
        await ws_manager.push_session_status_update(session.id, status_data)
        
        # 如果是运行状态，推送进度更新
        if session.status == SessionStatus.RUNNING:
            progress_data = {
                "current_epoch": session.current_epoch,
                "total_epochs": session.total_epochs,
                "progress_percentage": float(session.progress),
                "estimated_remaining": _estimate_remaining_time(session)
            }
            
            await ws_manager.push_training_progress(session.id, progress_data)
        
        logger.debug(f"已推送会话 {session.id} 的状态更新给 {subscriber_count} 个订阅者")
        
    except Exception as e:
        logger.error(f"推送会话 {session.id} 更新失败: {str(e)}")


def _estimate_remaining_time(session: StrategySession) -> int:
    """估算剩余时间（秒）"""
    try:
        if not session.started_at or session.current_epoch <= 0 or not session.total_epochs:
            return 0
        
        # 计算已用时间
        elapsed_time = (datetime.now() - session.started_at).total_seconds()
        
        # 计算每轮平均时间
        avg_time_per_epoch = elapsed_time / session.current_epoch
        
        # 估算剩余时间
        remaining_epochs = session.total_epochs - session.current_epoch
        estimated_remaining = int(remaining_epochs * avg_time_per_epoch)
        
        return max(0, estimated_remaining)
        
    except Exception:
        return 0


# 定期任务：每5秒监控一次活跃会话
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """设置定期任务"""
    # 每5秒监控一次活跃会话
    sender.add_periodic_task(
        5.0,  # 5秒间隔
        monitor_active_sessions.s(),
        name='monitor active sessions every 5 seconds'
    )
    
    logger.info("已设置定期会话监控任务")


@celery_app.task(name="monitoring.cleanup_connections")
def cleanup_inactive_connections():
    """清理不活跃的WebSocket连接"""
    logger.info("开始清理不活跃连接")
    
    try:
        asyncio.run(_cleanup_connections_async())
    except Exception as e:
        logger.error(f"清理连接时发生错误: {str(e)}")


async def _cleanup_connections_async():
    """异步清理连接"""
    ws_manager = get_websocket_manager()
    await ws_manager.cleanup_inactive_connections()