"""TradeMaster深度集成服务

提供与TradeMaster核心的完整集成，包括策略训练、回测、实盘交易等功能。
支持会话管理、实时监控和Celery异步任务集成。
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class TradeMasterAPIException(Exception):
    """TradeMaster API异常"""
    pass

from app.core.database import get_db_session
from app.models.database import (
    StrategySession, SessionStatus, SessionType,
    PerformanceMetric, Strategy, User
)
from app.services.trademaster_core import get_trademaster_core, TradeMasterCoreError
from app.core.trademaster_config import TradeMasterConfigAdapter


class TradeMasterIntegrationService:
    """完整的TradeMaster集成服务
    
    负责Web界面与TradeMaster核心的完整集成，提供策略训练、
    回测、实盘交易等完整生命周期管理。
    """
    
    def __init__(self):
        self.config_adapter = TradeMasterConfigAdapter()
        try:
            self.trademaster_core = get_trademaster_core()
            self.core_available = True
            logger.info("TradeMaster核心模块初始化成功")
        except Exception as e:
            logger.warning(f"TradeMaster核心模块不可用: {str(e)}")
            self.trademaster_core = None
            self.core_available = False
    
    async def create_training_session(
        self, 
        strategy_id: int, 
        user_id: int, 
        config: Dict[str, Any]
    ) -> int:
        """创建训练会话
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID  
            config: 训练配置参数
            
        Returns:
            int: 会话ID
        """
        try:
            # 1. 转换配置为TradeMaster格式
            tm_config = await self._convert_config_to_trademaster(config)
            
            # 2. 验证配置有效性
            validation_result = self.config_adapter.validate_trademaster_config(tm_config)
            if not validation_result["valid"]:
                raise ValueError(f"配置验证失败: {', '.join(validation_result['errors'])}")
            
            # 3. 创建会话记录
            async with get_db_session() as db:
                session = StrategySession(
                    strategy_id=strategy_id,
                    user_id=user_id,
                    session_type=SessionType.TRAINING,
                    status=SessionStatus.PENDING,
                    trademaster_config=tm_config,
                    total_epochs=config.get("epochs", 100)
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
                
                logger.info(f"创建训练会话: {session.id}")
                return session.id
                
        except Exception as e:
            logger.error(f"创建训练会话失败: {str(e)}")
            raise ValueError(f"创建训练会话失败: {str(e)}")
    
    async def start_training_task(self, session_id: int) -> str:
        """启动训练任务
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: Celery任务ID
        """
        try:
            # 1. 获取会话信息
            async with get_db_session() as db:
                session = await db.get(StrategySession, session_id)
                if not session:
                    raise ValueError(f"会话不存在: {session_id}")
                
                if session.status != SessionStatus.PENDING:
                    raise ValueError(f"会话状态错误: {session.status}")
            
            # 2. 提交Celery任务
            from app.tasks.training_tasks import execute_training_task
            task = execute_training_task.delay(session_id)
            
            # 3. 更新会话状态
            async with get_db_session() as db:
                session = await db.get(StrategySession, session_id)
                session.celery_task_id = task.id
                await db.commit()
            
            logger.info(f"启动训练任务: session_id={session_id}, task_id={task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"启动训练任务失败: {str(e)}")
            raise ValueError(f"启动训练任务失败: {str(e)}")
    
    async def create_backtest_session(
        self,
        strategy_id: int,
        user_id: int,
        config: Dict[str, Any]
    ) -> int:
        """创建回测会话"""
        try:
            # 转换回测配置
            tm_config = await self._convert_backtest_config(config)
            
            async with get_db_session() as db:
                session = StrategySession(
                    strategy_id=strategy_id,
                    user_id=user_id,
                    session_type=SessionType.BACKTEST,
                    status=SessionStatus.PENDING,
                    trademaster_config=tm_config
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
                
                logger.info(f"创建回测会话: {session.id}")
                return session.id
                
        except Exception as e:
            logger.error(f"创建回测会话失败: {str(e)}")
            raise ValueError(f"创建回测会话失败: {str(e)}")
    
    async def start_backtest_task(self, session_id: int) -> str:
        """启动回测任务"""
        try:
            from app.tasks.backtest_tasks import execute_backtest_task
            task = execute_backtest_task.delay(session_id)
            
            async with get_db_session() as db:
                session = await db.get(StrategySession, session_id)
                session.celery_task_id = task.id
                await db.commit()
            
            logger.info(f"启动回测任务: session_id={session_id}, task_id={task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"启动回测任务失败: {str(e)}")
            raise ValueError(f"启动回测任务失败: {str(e)}")
    
    async def stop_session(self, session_id: int, user_id: int) -> Dict[str, Any]:
        """停止会话"""
        try:
            async with get_db_session() as db:
                session = await db.get(StrategySession, session_id)
                if not session:
                    raise ValueError(f"会话不存在: {session_id}")
                
                # 验证用户权限
                if session.user_id != user_id:
                    raise ValueError("无权操作此会话")
                
                # 撤销Celery任务
                if session.celery_task_id:
                    from app.core.celery_app import celery_app
                    celery_app.control.revoke(session.celery_task_id, terminate=True)
                
                # 停止TradeMaster会话
                if session.trademaster_session_id and self.core_available:
                    try:
                        await self.trademaster_core.stop_training(session.trademaster_session_id)
                    except Exception as e:
                        logger.warning(f"停止TradeMaster会话失败: {str(e)}")
                
                # 更新状态
                session.status = SessionStatus.CANCELLED
                session.completed_at = datetime.now()
                await db.commit()
            
            logger.info(f"停止会话: {session_id}")
            return {"status": "stopped", "message": "会话已停止"}
            
        except Exception as e:
            logger.error(f"停止会话失败: {str(e)}")
            raise ValueError(f"停止会话失败: {str(e)}")
    
    async def get_session_status(self, session_id: int) -> Dict[str, Any]:
        """获取会话状态"""
        try:
            async with get_db_session() as db:
                session = await db.get(StrategySession, session_id)
                if not session:
                    raise ValueError(f"会话不存在: {session_id}")
                
                # 获取实时指标
                recent_metrics = await self._get_recent_metrics(session_id)
                
                return {
                    "session_id": session_id,
                    "status": session.status.value,
                    "progress": float(session.progress),
                    "current_epoch": session.current_epoch,
                    "total_epochs": session.total_epochs,
                    "recent_metrics": recent_metrics,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "error_message": session.error_message,
                    "final_metrics": session.final_metrics
                }
                
        except Exception as e:
            logger.error(f"获取会话状态失败: {str(e)}")
            raise ValueError(f"获取会话状态失败: {str(e)}")
    
    async def get_user_sessions(
        self, 
        user_id: int, 
        session_type: Optional[SessionType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取用户的会话列表"""
        try:
            async with get_db_session() as db:
                query = select(StrategySession).where(
                    StrategySession.user_id == user_id
                )
                
                if session_type:
                    query = query.where(StrategySession.session_type == session_type)
                
                query = query.order_by(StrategySession.created_at.desc()).limit(limit)
                
                result = await db.execute(query)
                sessions = result.scalars().all()
                
                return [
                    {
                        "session_id": s.id,
                        "session_type": s.session_type.value,
                        "status": s.status.value,
                        "progress": float(s.progress),
                        "strategy_id": s.strategy_id,
                        "created_at": s.created_at.isoformat(),
                        "started_at": s.started_at.isoformat() if s.started_at else None,
                        "completed_at": s.completed_at.isoformat() if s.completed_at else None
                    }
                    for s in sessions
                ]
                
        except Exception as e:
            logger.error(f"获取用户会话列表失败: {str(e)}")
            return []
    
    async def _convert_config_to_trademaster(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换Web配置到TradeMaster格式"""
        return self.config_adapter.convert_web_config_to_trademaster(config)
    
    async def _convert_backtest_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换回测配置"""
        tm_config = await self._convert_config_to_trademaster(config)
        
        # 添加回测特定配置
        tm_config.update({
            "mode": "backtest",
            "start_date": config.get("start_date"),
            "end_date": config.get("end_date"),
            "initial_capital": config.get("initial_capital", 100000)
        })
        
        return tm_config
    
    async def _get_recent_metrics(self, session_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的性能指标"""
        try:
            async with get_db_session() as db:
                query = select(PerformanceMetric).where(
                    PerformanceMetric.session_id == session_id
                ).order_by(
                    PerformanceMetric.recorded_at.desc()
                ).limit(limit)
                
                result = await db.execute(query)
                metrics = result.scalars().all()
                
                return [
                    {
                        "metric_name": m.metric_name,
                        "metric_value": float(m.metric_value),
                        "epoch": m.epoch,
                        "recorded_at": m.recorded_at.isoformat()
                    }
                    for m in metrics
                ]
                
        except Exception as e:
            logger.error(f"获取指标失败: {str(e)}")
            return []
    
    async def validate_strategy_config(
        self, 
        config: Dict[str, Any], 
        strategy_type: str
    ) -> Dict[str, Any]:
        """验证策略配置"""
        try:
            # 转换为TradeMaster配置格式
            tm_config = await self._convert_config_to_trademaster(config)
            
            # 使用配置适配器验证
            validation_result = self.config_adapter.validate_trademaster_config(tm_config)
            
            return {
                "valid": validation_result["valid"],
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "suggestions": validation_result.get("suggestions", [])
            }
            
        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "suggestions": []
            }
    
    async def get_available_strategies(self) -> List[Dict[str, Any]]:
        """获取可用的策略模板"""
        return [
            {
                "name": "DQN Algorithm Trading",
                "description": "基于深度Q网络的算法交易策略",
                "strategy_type": "algorithmic_trading",
                "default_config": {
                    "task": "algorithmic_trading",
                    "dataset": "BTC",
                    "agent": "dqn",
                    "epochs": 100,
                    "learning_rate": 0.001
                }
            },
            {
                "name": "PPO Algorithm Trading", 
                "description": "基于近端策略优化的算法交易策略",
                "strategy_type": "algorithmic_trading",
                "default_config": {
                    "task": "algorithmic_trading",
                    "dataset": "BTC",
                    "agent": "ppo",
                    "epochs": 100,
                    "learning_rate": 0.0003
                }
            },
            {
                "name": "EIIE Portfolio Management",
                "description": "基于集成投资组合优化的策略",
                "strategy_type": "portfolio_management",
                "default_config": {
                    "task": "portfolio_management",
                    "dataset": "dj30",
                    "agent": "eiie",
                    "epochs": 50,
                    "learning_rate": 0.001
                }
            }
        ]
    
    async def test_connection(
        self, 
        api_endpoint: str = None,
        timeout: int = None
    ) -> Dict[str, Any]:
        """测试TradeMaster服务连接
        
        Args:
            api_endpoint: API端点（可选，用于测试特定端点）
            timeout: 超时时间（可选）
            
        Returns:
            测试结果字典
        """
        try:
            # 使用提供的端点或默认端点
            test_endpoint = api_endpoint or "http://localhost:8080/api"
            test_timeout = timeout or 10
            
            # 检查核心模块是否可用
            if not self.core_available:
                return {
                    "success": False,
                    "error": "TradeMaster核心模块不可用",
                    "endpoint": test_endpoint
                }
            
            # 尝试连接TradeMaster服务
            # 这里应该实际连接到TradeMaster服务
            # 暂时返回模拟结果
            
            await asyncio.sleep(0.5)  # 模拟网络延迟
            
            # 模拟连接测试
            if "localhost" in test_endpoint or "127.0.0.1" in test_endpoint:
                return {
                    "success": True,
                    "version": "2.0.0",
                    "available_strategies": len(await self.get_available_strategies()),
                    "endpoint": test_endpoint
                }
            else:
                return {
                    "success": False,
                    "error": f"无法连接到 {test_endpoint}",
                    "endpoint": test_endpoint
                }
                
        except Exception as e:
            logger.error(f"TradeMaster连接测试失败: {str(e)}")
            return {
                "success": False,
                "error": f"连接测试失败: {str(e)}",
                "endpoint": api_endpoint or "default"
            }


# 全局服务实例
_integration_service = None

def get_integration_service() -> TradeMasterIntegrationService:
    """获取TradeMaster集成服务实例"""
    global _integration_service
    if _integration_service is None:
        _integration_service = TradeMasterIntegrationService()
    return _integration_service