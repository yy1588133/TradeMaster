"""
策略管理服务

提供策略的完整生命周期管理，包括创建、配置、版本控制、运行监控等功能。
集成TradeMaster核心模块和数据库操作，支持多种策略类型和执行模式。
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.core.trademaster_config import (
    get_config_adapter,
    TaskType,
    AgentType,
    DatasetType
)
from app.services.trademaster_integration import (
    get_integration_service,
    TradeMasterAPIException
)
from app.models.database import (
    Strategy,
    StrategyVersion,
    StrategyStatus,
    StrategyType,
    TrainingJob,
    TrainingStatus,
    User
)
from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyDetail,
    StrategyConfigValidation,
    StrategyConfigValidationResponse
)


class StrategyServiceError(Exception):
    """策略服务异常"""
    pass


class StrategyRunMode(str, Enum):
    """策略运行模式"""
    BACKTEST = "backtest"
    PAPER_TRADING = "paper_trading"
    LIVE_TRADING = "live_trading"


class StrategyService:
    """策略管理服务
    
    提供策略的完整生命周期管理功能：
    - 策略CRUD操作
    - 配置验证和管理
    - 版本控制
    - 运行状态监控
    - 性能评估
    """
    
    def __init__(self):
        """初始化策略服务"""
        self.config_adapter = get_config_adapter()
        self.trademaster_service = get_integration_service()
        
        # 策略类型到TradeMaster任务类型的映射
        self.strategy_type_mapping = {
            StrategyType.ALGORITHMIC_TRADING: TaskType.ALGORITHMIC_TRADING,
            StrategyType.PORTFOLIO_MANAGEMENT: TaskType.PORTFOLIO_MANAGEMENT,
            StrategyType.ORDER_EXECUTION: TaskType.ORDER_EXECUTION,
            StrategyType.HIGH_FREQUENCY_TRADING: TaskType.HIGH_FREQUENCY_TRADING
        }
        
        logger.info("策略服务初始化完成")
    
    # ==================== 策略CRUD ====================
    
    async def create_strategy(
        self,
        db: AsyncSession,
        strategy_data: StrategyCreate,
        user_id: int
    ) -> StrategyResponse:
        """创建策略
        
        Args:
            db: 数据库会话
            strategy_data: 策略创建数据
            user_id: 用户ID
            
        Returns:
            StrategyResponse: 创建的策略信息
            
        Raises:
            StrategyServiceError: 策略创建失败时抛出
        """
        try:
            # 验证策略配置
            validation_result = await self.validate_strategy_config(
                strategy_data.config,
                strategy_data.strategy_type
            )
            
            if not validation_result.is_valid:
                raise StrategyServiceError(f"策略配置验证失败: {'; '.join(validation_result.errors)}")
            
            # 创建策略记录
            strategy = Strategy(
                uuid=str(uuid.uuid4()),
                name=strategy_data.name,
                description=strategy_data.description,
                strategy_type=strategy_data.strategy_type,
                category=strategy_data.category,
                tags=strategy_data.tags or [],
                config=strategy_data.config,
                parameters=strategy_data.parameters,
                owner_id=user_id,
                parent_strategy_id=strategy_data.parent_strategy_id,
                status=StrategyStatus.DRAFT,
                version="1.0.0"
            )
            
            db.add(strategy)
            await db.commit()
            await db.refresh(strategy)
            
            # 创建初始版本
            initial_version = StrategyVersion(
                strategy_id=strategy.id,
                version="1.0.0",
                config=strategy_data.config,
                parameters=strategy_data.parameters,
                changelog="初始版本",
                is_active=True,
                created_by=user_id
            )
            
            db.add(initial_version)
            await db.commit()
            
            logger.info(f"策略创建成功: {strategy.name} (ID: {strategy.id})")
            
            return await self._strategy_to_response(strategy)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"策略创建失败: {str(e)}")
            raise StrategyServiceError(f"策略创建失败: {str(e)}")
    
    async def get_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int,
        include_detail: bool = False
    ) -> Union[StrategyResponse, StrategyDetail]:
        """获取策略信息
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID
            include_detail: 是否包含详细信息
            
        Returns:
            Union[StrategyResponse, StrategyDetail]: 策略信息
            
        Raises:
            StrategyServiceError: 策略不存在或无权限时抛出
        """
        try:
            # 查询策略
            query = select(Strategy).where(
                Strategy.id == strategy_id,
                Strategy.owner_id == user_id
            )
            
            if include_detail:
                query = query.options(
                    selectinload(Strategy.versions),
                    selectinload(Strategy.training_jobs),
                    selectinload(Strategy.evaluations)
                )
            
            result = await db.execute(query)
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                raise StrategyServiceError("策略不存在或无权限访问")
            
            if include_detail:
                return await self._strategy_to_detail(strategy, db)
            else:
                return await self._strategy_to_response(strategy)
                
        except Exception as e:
            logger.error(f"获取策略失败: {str(e)}")
            raise StrategyServiceError(f"获取策略失败: {str(e)}")
    
    async def update_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        strategy_data: StrategyUpdate,
        user_id: int
    ) -> StrategyResponse:
        """更新策略
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            strategy_data: 策略更新数据
            user_id: 用户ID
            
        Returns:
            StrategyResponse: 更新后的策略信息
            
        Raises:
            StrategyServiceError: 更新失败时抛出
        """
        try:
            # 获取策略
            result = await db.execute(
                select(Strategy).where(
                    Strategy.id == strategy_id,
                    Strategy.owner_id == user_id
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                raise StrategyServiceError("策略不存在或无权限访问")
            
            # 检查策略状态
            if strategy.status == StrategyStatus.ACTIVE:
                raise StrategyServiceError("运行中的策略无法修改，请先停止策略")
            
            # 更新策略信息
            update_data = {}
            if strategy_data.name is not None:
                update_data["name"] = strategy_data.name
            if strategy_data.description is not None:
                update_data["description"] = strategy_data.description
            if strategy_data.category is not None:
                update_data["category"] = strategy_data.category
            if strategy_data.tags is not None:
                update_data["tags"] = strategy_data.tags
            
            # 如果更新了配置，需要验证并创建新版本
            if strategy_data.config is not None:
                validation_result = await self.validate_strategy_config(
                    strategy_data.config,
                    strategy.strategy_type
                )
                
                if not validation_result.is_valid:
                    raise StrategyServiceError(f"策略配置验证失败: {'; '.join(validation_result.errors)}")
                
                update_data["config"] = strategy_data.config
                
                # 创建新版本
                new_version = await self._create_new_version(
                    db, strategy, strategy_data.config, 
                    strategy_data.parameters or strategy.parameters,
                    user_id
                )
                update_data["version"] = new_version.version
            
            if strategy_data.parameters is not None:
                update_data["parameters"] = strategy_data.parameters
            
            # 执行更新
            if update_data:
                await db.execute(
                    update(Strategy)
                    .where(Strategy.id == strategy_id)
                    .values(**update_data)
                )
                await db.commit()
                
                # 重新获取更新后的策略
                await db.refresh(strategy)
            
            logger.info(f"策略更新成功: {strategy.name} (ID: {strategy.id})")
            
            return await self._strategy_to_response(strategy)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"策略更新失败: {str(e)}")
            raise StrategyServiceError(f"策略更新失败: {str(e)}")
    
    async def delete_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """删除策略
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 删除结果
            
        Raises:
            StrategyServiceError: 删除失败时抛出
        """
        try:
            # 获取策略
            result = await db.execute(
                select(Strategy).where(
                    Strategy.id == strategy_id,
                    Strategy.owner_id == user_id
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                raise StrategyServiceError("策略不存在或无权限访问")
            
            # 检查策略状态
            if strategy.status == StrategyStatus.ACTIVE:
                raise StrategyServiceError("运行中的策略无法删除，请先停止策略")
            
            # 检查是否有正在运行的训练任务
            running_jobs = await db.execute(
                select(TrainingJob).where(
                    TrainingJob.strategy_id == strategy_id,
                    TrainingJob.status.in_([TrainingStatus.PENDING, TrainingStatus.RUNNING])
                )
            )
            
            if running_jobs.scalars().first():
                raise StrategyServiceError("策略有正在运行的训练任务，无法删除")
            
            # 删除策略（级联删除相关记录）
            await db.execute(
                delete(Strategy).where(Strategy.id == strategy_id)
            )
            await db.commit()
            
            logger.info(f"策略删除成功: {strategy.name} (ID: {strategy.id})")
            
            return {
                "message": "策略删除成功",
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"策略删除失败: {str(e)}")
            raise StrategyServiceError(f"策略删除失败: {str(e)}")
    
    # ==================== 策略运行控制 ====================
    
    async def start_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int,
        run_mode: StrategyRunMode = StrategyRunMode.BACKTEST,
        run_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """启动策略
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID
            run_mode: 运行模式
            run_config: 运行配置
            
        Returns:
            Dict[str, Any]: 启动结果
            
        Raises:
            StrategyServiceError: 启动失败时抛出
        """
        try:
            # 获取策略
            result = await db.execute(
                select(Strategy).where(
                    Strategy.id == strategy_id,
                    Strategy.owner_id == user_id
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                raise StrategyServiceError("策略不存在或无权限访问")
            
            # 检查策略状态
            if strategy.status == StrategyStatus.ACTIVE:
                raise StrategyServiceError("策略已在运行中")
            
            if strategy.status == StrategyStatus.ERROR:
                raise StrategyServiceError("策略处于错误状态，请检查配置")
            
            # 构建TradeMaster配置
            tm_config = await self._build_trademaster_config(strategy, run_config)
            
            # 启动训练/运行
            if run_mode == StrategyRunMode.BACKTEST:
                result = await self.trademaster_service.train_strategy(tm_config)
            else:
                # 实盘或纸上交易模式的实现
                result = await self._start_live_trading(strategy, tm_config, run_mode)
            
            # 更新策略状态
            await db.execute(
                update(Strategy)
                .where(Strategy.id == strategy_id)
                .values(
                    status=StrategyStatus.ACTIVE,
                    last_run_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            logger.info(f"策略启动成功: {strategy.name} (模式: {run_mode})")
            
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "run_mode": run_mode,
                "session_id": result.get("session_id"),
                "status": "started",
                "message": f"策略已启动 ({run_mode})",
                "started_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"策略启动失败: {str(e)}")
            raise StrategyServiceError(f"策略启动失败: {str(e)}")
    
    async def stop_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """停止策略
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 停止结果
            
        Raises:
            StrategyServiceError: 停止失败时抛出
        """
        try:
            # 获取策略
            result = await db.execute(
                select(Strategy).where(
                    Strategy.id == strategy_id,
                    Strategy.owner_id == user_id
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                raise StrategyServiceError("策略不存在或无权限访问")
            
            if strategy.status != StrategyStatus.ACTIVE:
                raise StrategyServiceError("策略未在运行中")
            
            # 获取相关的训练任务
            training_jobs = await db.execute(
                select(TrainingJob).where(
                    TrainingJob.strategy_id == strategy_id,
                    TrainingJob.status.in_([TrainingStatus.PENDING, TrainingStatus.RUNNING])
                )
            )
            
            stop_results = []
            for job in training_jobs.scalars():
                if job.trademaster_session_id:
                    try:
                        result = await self.trademaster_service.stop_training(
                            job.trademaster_session_id
                        )
                        stop_results.append({
                            "job_id": job.id,
                            "session_id": job.trademaster_session_id,
                            "result": result
                        })
                    except Exception as e:
                        logger.warning(f"停止训练任务失败: {job.id}, {str(e)}")
            
            # 更新策略状态
            await db.execute(
                update(Strategy)
                .where(Strategy.id == strategy_id)
                .values(status=StrategyStatus.STOPPED)
            )
            await db.commit()
            
            logger.info(f"策略停止成功: {strategy.name}")
            
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "status": "stopped",
                "message": "策略已停止",
                "stop_results": stop_results,
                "stopped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"策略停止失败: {str(e)}")
            raise StrategyServiceError(f"策略停止失败: {str(e)}")
    
    # ==================== 策略配置和验证 ====================
    
    async def validate_strategy_config(
        self,
        config: Dict[str, Any],
        strategy_type: StrategyType
    ) -> StrategyConfigValidationResponse:
        """验证策略配置
        
        Args:
            config: 策略配置
            strategy_type: 策略类型
            
        Returns:
            StrategyConfigValidationResponse: 验证结果
        """
        try:
            # 转换为TradeMaster配置进行验证
            tm_task_type = self.strategy_type_mapping.get(strategy_type)
            if not tm_task_type:
                return StrategyConfigValidationResponse(
                    is_valid=False,
                    errors=[f"不支持的策略类型: {strategy_type}"]
                )
            
            # 构建验证配置
            validation_config = {
                "task": tm_task_type,
                **config
            }
            
            # 使用配置适配器验证
            errors = self.config_adapter.validate_config(validation_config)
            
            warnings = []
            suggestions = []
            
            # 检查推荐配置
            if not config.get("agent"):
                suggestions.append("建议指定智能体类型")
            
            if not config.get("dataset"):
                suggestions.append("建议指定数据集")
            
            # 检查参数范围
            if config.get("learning_rate") and config["learning_rate"] > 0.01:
                warnings.append("学习率较高，可能导致训练不稳定")
            
            return StrategyConfigValidationResponse(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return StrategyConfigValidationResponse(
                is_valid=False,
                errors=[f"配置验证失败: {str(e)}"]
            )
    
    async def get_config_template(
        self,
        strategy_type: StrategyType,
        agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取策略配置模板
        
        Args:
            strategy_type: 策略类型
            agent_type: 智能体类型
            
        Returns:
            Dict[str, Any]: 配置模板
        """
        try:
            tm_task_type = self.strategy_type_mapping.get(strategy_type)
            if not tm_task_type:
                raise StrategyServiceError(f"不支持的策略类型: {strategy_type}")
            
            # 获取默认智能体类型
            if not agent_type:
                default_agents = {
                    StrategyType.ALGORITHMIC_TRADING: AgentType.DQN,
                    StrategyType.PORTFOLIO_MANAGEMENT: AgentType.EIIE,
                    StrategyType.ORDER_EXECUTION: AgentType.ETEO,
                    StrategyType.HIGH_FREQUENCY_TRADING: AgentType.DDQN
                }
                agent_type = default_agents.get(strategy_type, AgentType.DQN)
            
            # 使用配置适配器获取模板
            template = self.config_adapter.get_config_template(tm_task_type, agent_type)
            
            return template
            
        except Exception as e:
            logger.error(f"获取配置模板失败: {str(e)}")
            raise StrategyServiceError(f"获取配置模板失败: {str(e)}")
    
    # ==================== 辅助方法 ====================
    
    async def _strategy_to_response(self, strategy: Strategy) -> StrategyResponse:
        """将Strategy模型转换为StrategyResponse"""
        performance = None
        if strategy.total_return is not None:
            performance = {
                "total_return": float(strategy.total_return) if strategy.total_return else None,
                "sharpe_ratio": float(strategy.sharpe_ratio) if strategy.sharpe_ratio else None,
                "max_drawdown": float(strategy.max_drawdown) if strategy.max_drawdown else None,
                "win_rate": float(strategy.win_rate) if strategy.win_rate else None
            }
        
        return StrategyResponse(
            id=strategy.id,
            uuid=strategy.uuid,
            name=strategy.name,
            description=strategy.description,
            strategy_type=strategy.strategy_type,
            status=strategy.status,
            version=strategy.version,
            category=strategy.category,
            tags=strategy.tags,
            performance=performance,
            owner_id=strategy.owner_id,
            parent_strategy_id=strategy.parent_strategy_id,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
            last_run_at=strategy.last_run_at
        )
    
    async def _strategy_to_detail(self, strategy: Strategy, db: AsyncSession) -> StrategyDetail:
        """将Strategy模型转换为StrategyDetail"""
        base_response = await self._strategy_to_response(strategy)
        
        # 统计信息
        training_jobs_count = len(strategy.training_jobs) if strategy.training_jobs else 0
        evaluations_count = len(strategy.evaluations) if strategy.evaluations else 0
        versions_count = len(strategy.versions) if strategy.versions else 0
        
        return StrategyDetail(
            **base_response.dict(),
            config=strategy.config,
            parameters=strategy.parameters,
            training_jobs_count=training_jobs_count,
            evaluations_count=evaluations_count,
            versions_count=versions_count
        )
    
    async def _build_trademaster_config(
        self,
        strategy: Strategy,
        run_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """构建TradeMaster配置"""
        tm_task_type = self.strategy_type_mapping.get(strategy.strategy_type)
        
        base_config = {
            "task": tm_task_type,
            **strategy.config,
            **strategy.parameters
        }
        
        if run_config:
            base_config.update(run_config)
        
        return base_config
    
    async def _create_new_version(
        self,
        db: AsyncSession,
        strategy: Strategy,
        config: Dict[str, Any],
        parameters: Dict[str, Any],
        user_id: int
    ) -> StrategyVersion:
        """创建新版本"""
        # 计算新版本号
        current_version = strategy.version
        major, minor, patch = map(int, current_version.split('.'))
        new_version = f"{major}.{minor}.{patch + 1}"
        
        # 停用当前版本
        await db.execute(
            update(StrategyVersion)
            .where(
                StrategyVersion.strategy_id == strategy.id,
                StrategyVersion.is_active == True
            )
            .values(is_active=False)
        )
        
        # 创建新版本
        new_version_obj = StrategyVersion(
            strategy_id=strategy.id,
            version=new_version,
            config=config,
            parameters=parameters,
            changelog=f"配置更新 - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            is_active=True,
            created_by=user_id
        )
        
        db.add(new_version_obj)
        await db.commit()
        
        return new_version_obj
    
    async def _start_live_trading(
        self,
        strategy: Strategy,
        tm_config: Dict[str, Any],
        run_mode: StrategyRunMode
    ) -> Dict[str, Any]:
        """启动实盘或纸上交易"""
        # 这里应该实现实盘交易的启动逻辑
        # 当前返回模拟结果
        return {
            "session_id": f"live_{strategy.id}_{int(datetime.utcnow().timestamp())}",
            "mode": run_mode,
            "status": "started",
            "message": f"实盘交易启动 ({run_mode})"
        }


# 全局服务实例
_strategy_service = None

def get_strategy_service() -> StrategyService:
    """获取策略服务实例
    
    Returns:
        StrategyService: 策略服务实例
    """
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategyService()
    return _strategy_service


# 导出主要类和函数
__all__ = [
    "StrategyService",
    "StrategyServiceError",
    "StrategyRunMode",
    "get_strategy_service"
]