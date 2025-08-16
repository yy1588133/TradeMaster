"""
训练管理API端点

提供策略训练、模型管理、超参数优化等功能的REST API接口。
支持多种训练模式，包括单策略训练、批量训练、分布式训练等。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_active_user,
    CurrentUser,
    DatabaseSession
)
from app.services.training_service import get_training_service, TrainingServiceError
from app.core.config import settings
from loguru import logger

router = APIRouter()

# ==================== 请求/响应模型 ====================

class TrainingJobRequest(BaseModel):
    """训练任务请求模型"""
    strategy_id: str = Field(..., description="策略ID")
    dataset_id: str = Field(..., description="数据集ID")
    job_name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    training_config: Dict[str, Any] = Field({}, description="训练配置")
    resource_config: Dict[str, Any] = Field({}, description="资源配置")
    notification_config: Dict[str, Any] = Field({}, description="通知配置")


class HyperparameterOptimizationRequest(BaseModel):
    """超参数优化请求模型"""
    strategy_id: str = Field(..., description="策略ID")
    dataset_id: str = Field(..., description="数据集ID")
    optimization_config: Dict[str, Any] = Field(..., description="优化配置")
    search_space: Dict[str, Any] = Field(..., description="搜索空间")
    optimization_method: str = Field("random", description="优化方法")
    max_trials: int = Field(50, description="最大试验次数")
    parallel_trials: int = Field(1, description="并行试验数")


class BatchTrainingRequest(BaseModel):
    """批量训练请求模型"""
    training_jobs: List[TrainingJobRequest] = Field(..., description="训练任务列表")
    execution_mode: str = Field("sequential", description="执行模式")
    max_parallel_jobs: int = Field(3, description="最大并行任务数")
    dependency_config: Dict[str, Any] = Field({}, description="依赖配置")


class TrainingJobUpdateRequest(BaseModel):
    """训练任务更新请求模型"""
    status: Optional[str] = Field(None, description="任务状态")
    priority: Optional[int] = Field(None, description="任务优先级")
    resource_config: Optional[Dict[str, Any]] = Field(None, description="资源配置")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="通知配置")


# ==================== 训练任务管理API ====================

@router.post("/jobs", response_model=Dict[str, Any])
async def create_training_job(
    request: TrainingJobRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    创建训练任务
    
    创建单个策略训练任务，支持自定义训练配置和资源分配
    """
    try:
        training_service = get_training_service()
        
        # 创建训练任务
        result = await training_service.create_training_job(
            strategy_id=request.strategy_id,
            dataset_id=request.dataset_id,
            job_config={
                "name": request.job_name,
                "description": request.description,
                "training_config": request.training_config,
                "resource_config": request.resource_config,
                "notification_config": request.notification_config
            },
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 创建训练任务: {request.job_name}")
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"创建训练任务失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建训练任务异常: {str(e)}")
        raise HTTPException(status_code=500, detail="创建训练任务失败")


@router.post("/jobs/batch", response_model=Dict[str, Any])
async def create_batch_training_jobs(
    request: BatchTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    创建批量训练任务
    
    支持顺序执行和并行执行模式
    """
    try:
        training_service = get_training_service()
        
        # 创建批量训练任务
        result = await training_service.create_batch_training_jobs(
            training_jobs=[job.dict() for job in request.training_jobs],
            batch_config={
                "execution_mode": request.execution_mode,
                "max_parallel_jobs": request.max_parallel_jobs,
                "dependency_config": request.dependency_config
            },
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 创建批量训练任务: {len(request.training_jobs)} 个任务")
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"创建批量训练任务失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建批量训练任务异常: {str(e)}")
        raise HTTPException(status_code=500, detail="创建批量训练任务失败")


@router.get("/jobs", response_model=Dict[str, Any])
async def list_training_jobs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="任务状态筛选"),
    strategy_id: Optional[str] = Query(None, description="策略ID筛选"),
    priority: Optional[int] = Query(None, description="优先级筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取训练任务列表
    
    支持分页、筛选和排序功能
    """
    try:
        training_service = get_training_service()
        
        # 构建查询参数
        query_params = {
            "page": page,
            "page_size": page_size,
            "user_id": current_user["id"],
            "status": status,
            "strategy_id": strategy_id,
            "priority": priority,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        result = await training_service.list_training_jobs(query_params)
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"获取训练任务列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取训练任务列表异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取训练任务列表失败")


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_training_job(
    job_id: str,
    include_logs: bool = Query(False, description="是否包含日志"),
    include_metrics: bool = Query(True, description="是否包含指标"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取训练任务详情
    
    包括任务配置、执行状态、训练指标等信息
    """
    try:
        training_service = get_training_service()
        
        result = await training_service.get_training_job_details(
            job_id=job_id,
            user_id=current_user["id"],
            include_logs=include_logs,
            include_metrics=include_metrics
        )
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"获取训练任务详情失败: {job_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取训练任务详情异常: {job_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取训练任务详情失败")


# ==================== 训练任务控制API ====================

@router.post("/jobs/{job_id}/start", response_model=Dict[str, Any])
async def start_training_job(
    job_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    启动训练任务
    """
    try:
        training_service = get_training_service()
        
        result = await training_service.start_training_job(
            job_id=job_id,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 启动训练任务: {job_id}")
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"启动训练任务失败: {job_id}, {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动训练任务异常: {job_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="启动训练任务失败")


@router.post("/jobs/{job_id}/stop", response_model=Dict[str, Any])
async def stop_training_job(
    job_id: str,
    force: bool = Query(False, description="是否强制停止"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    停止训练任务
    """
    try:
        training_service = get_training_service()
        
        result = await training_service.stop_training_job(
            job_id=job_id,
            user_id=current_user["id"],
            force=force
        )
        
        logger.info(f"用户 {current_user['username']} 停止训练任务: {job_id}")
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"停止训练任务失败: {job_id}, {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"停止训练任务异常: {job_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="停止训练任务失败")


# ==================== 超参数优化API ====================

@router.post("/hyperparameter-optimization", response_model=Dict[str, Any])
async def start_hyperparameter_optimization(
    request: HyperparameterOptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    启动超参数优化
    
    支持多种优化算法：随机搜索、网格搜索、贝叶斯优化等
    """
    try:
        training_service = get_training_service()
        
        result = await training_service.start_hyperparameter_optimization(
            strategy_id=request.strategy_id,
            dataset_id=request.dataset_id,
            optimization_config={
                "optimization_config": request.optimization_config,
                "search_space": request.search_space,
                "optimization_method": request.optimization_method,
                "max_trials": request.max_trials,
                "parallel_trials": request.parallel_trials
            },
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 启动超参数优化: {request.strategy_id}")
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"启动超参数优化失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动超参数优化异常: {str(e)}")
        raise HTTPException(status_code=500, detail="启动超参数优化失败")


# ==================== 训练监控API ====================

@router.get("/jobs/{job_id}/metrics", response_model=Dict[str, Any])
async def get_training_metrics(
    job_id: str,
    metric_type: Optional[str] = Query(None, description="指标类型"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取训练指标
    
    包括损失函数、准确率、训练速度等指标
    """
    try:
        training_service = get_training_service()
        
        result = await training_service.get_training_metrics(
            job_id=job_id,
            user_id=current_user["id"],
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time
        )
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"获取训练指标失败: {job_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取训练指标异常: {job_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取训练指标失败")


@router.get("/jobs/{job_id}/progress", response_model=Dict[str, Any])
async def get_training_progress(
    job_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取训练进度
    
    包括当前轮次、预计完成时间、资源使用情况等
    """
    try:
        training_service = get_training_service()
        
        result = await training_service.get_training_progress(
            job_id=job_id,
            user_id=current_user["id"]
        )
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"获取训练进度失败: {job_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取训练进度异常: {job_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取训练进度失败")


# ==================== 资源管理API ====================

@router.get("/resources/status", response_model=Dict[str, Any])
async def get_training_resources_status(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取训练资源状态
    
    包括CPU、内存、GPU使用情况和队列状态
    """
    try:
        training_service = get_training_service()
        
        result = await training_service.get_resources_status()
        
        return result
        
    except TrainingServiceError as e:
        logger.error(f"获取训练资源状态失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取训练资源状态异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取训练资源状态失败")


# 导出路由器
__all__ = ["router"]