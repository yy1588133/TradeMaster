"""
策略管理API端点

提供策略的增删改查、执行控制、状态监控等功能。
支持多种策略类型：算法交易、投资组合管理、订单执行、高频交易等。
"""

import time
from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_db,
    get_current_active_user,
    require_permission,
    get_pagination_params,
    get_sort_params,
    get_search_params,
    CurrentUser,
    DatabaseSession,
    PaginationDeps,
    SortDeps,
    SearchDeps
)
from app.core.security import Permission
from app.services.strategy_service import get_strategy_service, StrategyServiceError
from app.services.trademaster_integration import TradeMasterService
from app.crud.strategy import strategy_crud, strategy_version_crud
from app.schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyResponse, StrategyDetail,
    StrategyListQuery, StrategyConfigValidation, StrategyConfigValidationResponse,
    StrategyCloneRequest, StrategyCompareRequest, StrategyCompareResponse,
    StrategyStats, StrategyPerformance
)
from app.models.database import StrategyType, StrategyStatus


router = APIRouter()


# ==================== 请求模型 ====================

class StrategyExecuteRequest(BaseModel):
    """执行策略请求模型"""
    mode: str = Field(default="backtest", description="执行模式：backtest, paper_trading, live_trading")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    initial_capital: Optional[float] = Field(None, description="初始资金")
    risk_params: Dict[str, Any] = Field(default_factory=dict, description="风险参数")


class StrategyExecutionResponse(BaseModel):
    """策略执行响应模型"""
    execution_id: str = Field(..., description="执行ID")
    strategy_id: str = Field(..., description="策略ID")
    status: str = Field(..., description="执行状态")
    session_id: Optional[str] = Field(None, description="TradeMaster会话ID")
    message: str = Field(..., description="执行消息")
    started_at: str = Field(..., description="开始时间")


class StrategyListResponse(BaseModel):
    """策略列表响应模型"""
    strategies: List[StrategyResponse] = Field(..., description="策略列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页面大小")
    pages: int = Field(..., description="总页数")


class StrategyUpdateRequest(BaseModel):
    """策略更新请求模型"""
    name: Optional[str] = Field(None, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    config: Optional[Dict[str, Any]] = Field(None, description="策略配置")
    parameters: Optional[Dict[str, Any]] = Field(None, description="策略参数")
    tags: Optional[List[str]] = Field(None, description="标签列表")


class StrategyTemplateResponse(BaseModel):
    """策略模板响应模型"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    config_template: Dict[str, Any] = Field(..., description="配置模板")
    parameters_template: Dict[str, Any] = Field(..., description="参数模板")
    example_values: Dict[str, Any] = Field(..., description="示例值")


# ==================== API端点 ====================

@router.get("", response_model=StrategyListResponse, summary="获取策略列表")
async def list_strategies(
    pagination: PaginationDeps,
    sort: SortDeps,
    search: SearchDeps,
    current_user: CurrentUser,
    db: DatabaseSession,
    strategy_type: Optional[StrategyType] = Query(None, description="按策略类型过滤"),
    status: Optional[StrategyStatus] = Query(None, description="按状态过滤"),
    tags: Optional[str] = Query(None, description="按标签过滤（逗号分隔）"),
    category: Optional[str] = Query(None, description="按分类过滤")
) -> StrategyListResponse:
    """获取策略列表
    
    支持分页、排序、搜索和多种过滤条件。
    """
    try:
        # 解析标签
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # 查询策略列表
        strategies = await strategy_crud.get_multi(
            db,
            skip=pagination.skip,
            limit=pagination.limit,
            owner_id=current_user["id"],
            strategy_type=strategy_type,
            status=status,
            category=category,
            tags=tag_list,
            search=search.query,
            sort_by=sort.field,
            sort_order=sort.order,
            load_relations=False
        )
        
        # 统计总数
        total = await strategy_crud.count(
            db,
            owner_id=current_user["id"],
            strategy_type=strategy_type,
            status=status,
            category=category,
            tags=tag_list,
            search=search.query
        )
        
        # 转换为响应格式
        strategy_responses = []
        strategy_service = get_strategy_service()
        
        for strategy in strategies:
            strategy_response = await strategy_service._strategy_to_response(strategy)
            strategy_responses.append(strategy_response)
        
        return StrategyListResponse(
            strategies=strategy_responses,
            total=total,
            page=(pagination.skip // pagination.limit) + 1,
            size=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}"
        )


@router.post(
    "",
    response_model=StrategyResponse,
    summary="创建策略",
    dependencies=[Depends(require_permission(Permission.CREATE_STRATEGY))]
)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: CurrentUser,
    db: DatabaseSession
) -> StrategyResponse:
    """创建新策略
    
    用户可以创建各种类型的交易策略。
    """
    try:
        strategy_service = get_strategy_service()
        
        # 创建策略
        strategy_response = await strategy_service.create_strategy(
            db=db,
            strategy_data=strategy_data,
            user_id=current_user["id"]
        )
        
        return strategy_response
        
    except StrategyServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建策略失败: {str(e)}"
        )


@router.get("/{strategy_id}", response_model=StrategyResponse, summary="获取策略详情")
async def get_strategy(
    strategy_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
) -> StrategyResponse:
    """获取策略详情
    
    返回指定策略的完整信息。
    """
    # TODO: 从数据库获取策略信息
    # strategy = await get_strategy_by_id(db, strategy_id)
    # if not strategy or strategy.owner_id != current_user["id"]:
    #     raise HTTPException(404, "策略不存在")
    
    # 模拟策略数据
    if strategy_id not in ["1", "2"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    return StrategyResponse(
        id=strategy_id,
        name="示例策略",
        description="这是一个示例策略",
        strategy_type=StrategyType.ALGORITHMIC_TRADING,
        status=StrategyStatus.DRAFT,
        config={"param1": "value1"},
        parameters={"param2": "value2"},
        tags=["示例"],
        owner_id=current_user["id"],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        last_executed=None,
        performance=None
    )


@router.put(
    "/{strategy_id}", 
    response_model=StrategyResponse, 
    summary="更新策略",
    dependencies=[Depends(require_permission(Permission.UPDATE_STRATEGY))]
)
async def update_strategy(
    strategy_id: str,
    strategy_data: StrategyUpdateRequest,
    current_user: CurrentUser,
    db: DatabaseSession
) -> StrategyResponse:
    """更新策略信息
    
    允许用户修改自己创建的策略。
    """
    # TODO: 实现实际的策略更新逻辑
    # 1. 验证策略所有权
    # 2. 更新策略信息
    # 3. 验证配置有效性
    
    # 模拟策略更新
    if strategy_id not in ["1", "2"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    return StrategyResponse(
        id=strategy_id,
        name=strategy_data.name or "更新后的策略",
        description=strategy_data.description or "更新后的描述",
        strategy_type=StrategyType.ALGORITHMIC_TRADING,
        status=StrategyStatus.DRAFT,
        config=strategy_data.config or {},
        parameters=strategy_data.parameters or {},
        tags=strategy_data.tags or [],
        owner_id=current_user["id"],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T12:00:00Z",
        last_executed=None,
        performance=None
    )


@router.delete(
    "/{strategy_id}", 
    summary="删除策略",
    dependencies=[Depends(require_permission(Permission.DELETE_STRATEGY))]
)
async def delete_strategy(
    strategy_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
) -> Dict[str, Any]:
    """删除策略
    
    删除用户创建的策略及其相关数据。
    """
    # TODO: 实现实际的策略删除逻辑
    # 1. 验证策略所有权
    # 2. 检查策略是否在运行中
    # 3. 删除相关数据和文件
    
    if strategy_id not in ["1", "2"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    return {
        "message": "策略删除成功",
        "strategy_id": strategy_id,
        "timestamp": int(time.time())
    }


@router.post(
    "/{strategy_id}/execute",
    response_model=StrategyExecutionResponse,
    summary="执行策略",
    dependencies=[Depends(require_permission(Permission.EXECUTE_STRATEGY))]
)
async def execute_strategy(
    strategy_id: int,
    execute_data: StrategyExecuteRequest,
    current_user: CurrentUser,
    db: DatabaseSession
) -> StrategyExecutionResponse:
    """执行策略
    
    启动策略的回测或实盘运行。
    """
    try:
        from app.services.strategy_service import StrategyRunMode
        
        strategy_service = get_strategy_service()
        
        # 映射运行模式
        run_mode_mapping = {
            "backtest": StrategyRunMode.BACKTEST,
            "paper_trading": StrategyRunMode.PAPER_TRADING,
            "live_trading": StrategyRunMode.LIVE_TRADING
        }
        
        run_mode = run_mode_mapping.get(execute_data.mode, StrategyRunMode.BACKTEST)
        
        # 构建运行配置
        run_config = {
            "start_date": execute_data.start_date,
            "end_date": execute_data.end_date,
            "initial_capital": execute_data.initial_capital or 100000,
            "risk_params": execute_data.risk_params
        }
        
        # 启动策略
        result = await strategy_service.start_strategy(
            db=db,
            strategy_id=strategy_id,
            user_id=current_user["id"],
            run_mode=run_mode,
            run_config=run_config
        )
        
        execution_id = f"exec_{strategy_id}_{int(time.time())}"
        
        return StrategyExecutionResponse(
            execution_id=execution_id,
            strategy_id=str(strategy_id),
            status=result["status"],
            session_id=result.get("session_id"),
            message=result["message"],
            started_at=result["started_at"]
        )
        
    except StrategyServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"策略执行失败: {str(e)}"
        )


@router.post(
    "/{strategy_id}/stop",
    summary="停止策略",
    dependencies=[Depends(require_permission(Permission.EXECUTE_STRATEGY))]
)
async def stop_strategy(
    strategy_id: int,
    current_user: CurrentUser,
    db: DatabaseSession
) -> Dict[str, Any]:
    """停止策略执行
    
    停止正在运行的策略。
    """
    try:
        strategy_service = get_strategy_service()
        
        # 停止策略
        result = await strategy_service.stop_strategy(
            db=db,
            strategy_id=strategy_id,
            user_id=current_user["id"]
        )
        
        return result
        
    except StrategyServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止策略失败: {str(e)}"
        )


@router.get("/{strategy_id}/status", summary="获取策略状态")
async def get_strategy_status(
    strategy_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
) -> Dict[str, Any]:
    """获取策略运行状态
    
    返回策略的实时运行状态和性能指标。
    """
    # TODO: 实现实际的状态查询逻辑
    # 1. 查询数据库中的策略状态
    # 2. 调用TradeMaster状态API
    # 3. 汇总状态信息
    
    if strategy_id not in ["1", "2"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    return {
        "strategy_id": strategy_id,
        "status": StrategyStatus.ACTIVE,
        "running_time": 3600,  # 运行时间（秒）
        "current_position": {
            "symbol": "BTC-USDT",
            "quantity": 0.5,
            "side": "long"
        },
        "performance": {
            "total_return": 0.12,
            "daily_return": 0.002,
            "sharpe_ratio": 1.5,
            "max_drawdown": 0.05,
            "win_rate": 0.65
        },
        "trades_today": 15,
        "last_update": "2024-01-01T12:00:00Z"
    }


@router.get("/{strategy_id}/logs", summary="获取策略日志")
async def get_strategy_logs(
    strategy_id: str,
    current_user: CurrentUser,
    limit: int = Query(100, description="日志条数限制"),
    level: Optional[str] = Query(None, description="日志级别过滤"),
    db: DatabaseSession
) -> Dict[str, Any]:
    """获取策略执行日志
    
    返回策略的执行日志，支持级别过滤。
    """
    # TODO: 实现实际的日志查询逻辑
    # 1. 验证策略所有权
    # 2. 查询日志数据
    # 3. 应用过滤条件
    
    if strategy_id not in ["1", "2"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    # 模拟日志数据
    mock_logs = [
        {
            "timestamp": "2024-01-01T12:00:00Z",
            "level": "INFO",
            "message": "策略启动成功",
            "details": {}
        },
        {
            "timestamp": "2024-01-01T12:01:00Z",
            "level": "INFO",
            "message": "接收到新的市场数据",
            "details": {"symbol": "BTC-USDT", "price": 45000}
        },
        {
            "timestamp": "2024-01-01T12:02:00Z",
            "level": "WARNING",
            "message": "市场波动较大",
            "details": {"volatility": 0.05}
        }
    ]
    
    return {
        "strategy_id": strategy_id,
        "logs": mock_logs[:limit],
        "total_logs": len(mock_logs),
        "last_update": "2024-01-01T12:02:00Z"
    }


@router.post("/{strategy_id}/clone", response_model=StrategyResponse, summary="克隆策略")
async def clone_strategy(
    strategy_id: str,
    clone_name: str = Body(..., embed=True),
    current_user: CurrentUser,
    db: DatabaseSession
) -> StrategyResponse:
    """克隆策略
    
    基于现有策略创建一个副本。
    """
    # TODO: 实现实际的策略克隆逻辑
    # 1. 获取原策略信息
    # 2. 创建新的策略记录
    # 3. 复制配置和参数
    
    if strategy_id not in ["1", "2"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    cloned_strategy_id = f"strategy_clone_{int(time.time())}"
    
    return StrategyResponse(
        id=cloned_strategy_id,
        name=clone_name,
        description=f"克隆自策略 {strategy_id}",
        strategy_type=StrategyType.ALGORITHMIC_TRADING,
        status=StrategyStatus.DRAFT,
        config={"cloned_from": strategy_id},
        parameters={},
        tags=["克隆"],
        owner_id=current_user["id"],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        last_executed=None,
        performance=None
    )


# ==================== 新增API端点 ====================

@router.get("/templates", response_model=List[StrategyTemplateResponse], summary="获取策略模板列表")
async def get_strategy_templates(
    strategy_type: Optional[StrategyType] = Query(None, description="按策略类型过滤"),
    current_user: CurrentUser = Depends(get_current_active_user)
) -> List[StrategyTemplateResponse]:
    """获取策略模板列表
    
    返回可用的策略模板，用户可以基于模板创建新策略。
    """
    try:
        # 定义模板数据
        templates = []
        
        # 算法交易模板
        if not strategy_type or strategy_type == StrategyType.ALGORITHMIC_TRADING:
            templates.extend([
                StrategyTemplateResponse(
                    name="DQN算法交易策略",
                    description="基于深度Q网络的算法交易策略，适用于单资产交易",
                    strategy_type=StrategyType.ALGORITHMIC_TRADING,
                    config_template={
                        "task_name": "algorithmic_trading",
                        "dataset_name": "BTC",
                        "agent_name": "dqn",
                        "trainer_name": "algorithmic_trading",
                        "net_name": "dqn",
                        "optimizer_name": "adam"
                    },
                    parameters_template={
                        "learning_rate": 0.001,
                        "batch_size": 32,
                        "memory_size": 10000,
                        "epsilon_start": 1.0,
                        "epsilon_end": 0.01,
                        "epsilon_decay": 0.995
                    },
                    example_values={
                        "symbol": "BTC-USDT",
                        "timeframe": "1h",
                        "lookback_window": 30
                    }
                ),
                StrategyTemplateResponse(
                    name="PPO算法交易策略",
                    description="基于近端策略优化的算法交易策略，适用于连续动作空间",
                    strategy_type=StrategyType.ALGORITHMIC_TRADING,
                    config_template={
                        "task_name": "algorithmic_trading",
                        "dataset_name": "BTC",
                        "agent_name": "ppo",
                        "trainer_name": "algorithmic_trading",
                        "net_name": "ppo",
                        "optimizer_name": "adam"
                    },
                    parameters_template={
                        "learning_rate": 0.0003,
                        "batch_size": 64,
                        "n_steps": 2048,
                        "clip_range": 0.2,
                        "entropy_coef": 0.01
                    },
                    example_values={
                        "symbol": "ETH-USDT",
                        "timeframe": "15m",
                        "max_position": 1.0
                    }
                )
            ])
        
        # 投资组合管理模板
        if not strategy_type or strategy_type == StrategyType.PORTFOLIO_MANAGEMENT:
            templates.append(
                StrategyTemplateResponse(
                    name="EIIE投资组合策略",
                    description="基于集成投资组合优化的多资产配置策略",
                    strategy_type=StrategyType.PORTFOLIO_MANAGEMENT,
                    config_template={
                        "task_name": "portfolio_management",
                        "dataset_name": "dj30",
                        "agent_name": "eiie",
                        "trainer_name": "portfolio_management",
                        "net_name": "eiie",
                        "optimizer_name": "adam"
                    },
                    parameters_template={
                        "learning_rate": 0.001,
                        "batch_size": 128,
                        "window_size": 50,
                        "portfolio_size": 10,
                        "transaction_cost": 0.0025
                    },
                    example_values={
                        "assets": ["AAPL", "MSFT", "GOOGL", "AMZN"],
                        "rebalance_frequency": "daily",
                        "risk_tolerance": "medium"
                    }
                )
            )
        
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略模板失败: {str(e)}"
        )


@router.post("/{strategy_id}/validate", response_model=StrategyConfigValidationResponse, summary="验证策略配置")
async def validate_strategy_config(
    strategy_id: int,
    validation_request: StrategyConfigValidation,
    current_user: CurrentUser,
    db: DatabaseSession
) -> StrategyConfigValidationResponse:
    """验证策略配置
    
    检查策略配置的有效性，返回验证结果和建议。
    """
    try:
        # 验证策略所有权
        strategy = await strategy_crud.get(db, strategy_id=strategy_id)
        if not strategy or strategy.owner_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        strategy_service = get_strategy_service()
        
        # 验证配置
        validation_result = await strategy_service.validate_strategy_config(
            config=validation_request.config,
            strategy_type=validation_request.strategy_type
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置验证失败: {str(e)}"
        )


@router.get("/stats", response_model=StrategyStats, summary="获取策略统计")
async def get_strategy_stats(
    current_user: CurrentUser,
    db: DatabaseSession
) -> StrategyStats:
    """获取用户的策略统计信息
    
    返回策略数量、分布、性能等统计数据。
    """
    try:
        stats = await strategy_crud.get_strategy_stats(db, user_id=current_user["id"])
        
        # 查找最佳表现策略
        best_strategy = None
        best_strategies = await strategy_crud.get_multi(
            db,
            owner_id=current_user["id"],
            sort_by="total_return",
            sort_order="desc",
            limit=1
        )
        
        if best_strategies:
            strategy = best_strategies[0]
            from app.schemas.strategy import StrategySummary
            best_strategy = StrategySummary(
                id=strategy.id,
                name=strategy.name,
                strategy_type=strategy.strategy_type,
                status=strategy.status,
                total_return=float(strategy.total_return) if strategy.total_return else None,
                created_at=strategy.created_at
            )
        
        return StrategyStats(
            total_strategies=stats["total_strategies"],
            active_strategies=stats["active_strategies"],
            draft_strategies=stats["draft_strategies"],
            type_distribution=stats["type_distribution"],
            status_distribution=stats["status_distribution"],
            avg_return=stats["avg_return"],
            avg_sharpe_ratio=stats["avg_sharpe_ratio"],
            best_performing=best_strategy,
            creation_trend=[]  # TODO: 实现创建趋势数据
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略统计失败: {str(e)}"
        )