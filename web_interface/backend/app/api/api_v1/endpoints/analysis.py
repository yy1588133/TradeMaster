"""
分析评估API端点

提供策略分析、回测评估、风险分析、性能对比等功能的REST API接口。
支持多种分析方法和可视化图表生成。
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
from app.services.evaluation_service import get_evaluation_service, EvaluationServiceError
from app.core.config import settings
from loguru import logger

router = APIRouter()

# ==================== 请求/响应模型 ====================

class BacktestRequest(BaseModel):
    """回测请求模型"""
    strategy_id: str = Field(..., description="策略ID")
    dataset_id: str = Field(..., description="数据集ID")
    backtest_config: Dict[str, Any] = Field({}, description="回测配置")
    start_date: Optional[str] = Field(None, description="回测开始日期")
    end_date: Optional[str] = Field(None, description="回测结束日期")
    initial_capital: float = Field(1000000, description="初始资金")
    benchmark: Optional[str] = Field(None, description="基准指标")


class PerformanceAnalysisRequest(BaseModel):
    """性能分析请求模型"""
    strategy_id: str = Field(..., description="策略ID")
    analysis_type: str = Field("comprehensive", description="分析类型")
    time_range: str = Field("1y", description="分析时间范围")
    metrics: List[str] = Field([], description="指定分析指标")
    benchmark_comparison: bool = Field(True, description="是否包含基准对比")


class RiskAnalysisRequest(BaseModel):
    """风险分析请求模型"""
    strategy_id: str = Field(..., description="策略ID")
    risk_metrics: List[str] = Field([], description="风险指标")
    confidence_levels: List[float] = Field([0.95, 0.99], description="置信水平")
    analysis_period: str = Field("1y", description="分析周期")
    stress_test: bool = Field(False, description="是否进行压力测试")


class ComparisonAnalysisRequest(BaseModel):
    """对比分析请求模型"""
    strategy_ids: List[str] = Field(..., description="策略ID列表")
    comparison_metrics: List[str] = Field([], description="对比指标")
    time_range: str = Field("1y", description="对比时间范围")
    benchmark: Optional[str] = Field(None, description="基准指标")
    analysis_method: str = Field("comprehensive", description="分析方法")


# ==================== 回测分析API ====================

@router.post("/backtest", response_model=Dict[str, Any])
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    运行策略回测
    
    对指定策略在历史数据上进行回测分析
    """
    try:
        evaluation_service = get_evaluation_service()
        
        # 构建回测配置
        backtest_config = {
            "strategy_id": request.strategy_id,
            "dataset_id": request.dataset_id,
            "config": request.backtest_config,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "initial_capital": request.initial_capital,
            "benchmark": request.benchmark
        }
        
        result = await evaluation_service.run_backtest_evaluation(
            backtest_config=backtest_config,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 启动回测: {request.strategy_id}")
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"回测失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"回测异常: {str(e)}")
        raise HTTPException(status_code=500, detail="回测失败")


@router.get("/backtest/{backtest_id}", response_model=Dict[str, Any])
async def get_backtest_results(
    backtest_id: str,
    include_trades: bool = Query(True, description="是否包含交易记录"),
    include_charts: bool = Query(True, description="是否包含图表"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取回测结果
    
    包括回测报告、交易记录、性能指标等
    """
    try:
        evaluation_service = get_evaluation_service()
        
        result = await evaluation_service.get_backtest_results(
            backtest_id=backtest_id,
            user_id=current_user["id"],
            include_trades=include_trades,
            include_charts=include_charts
        )
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"获取回测结果失败: {backtest_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取回测结果异常: {backtest_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取回测结果失败")


@router.get("/backtests", response_model=Dict[str, Any])
async def list_backtests(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    strategy_id: Optional[str] = Query(None, description="策略ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取回测列表
    
    支持分页、筛选和排序功能
    """
    try:
        evaluation_service = get_evaluation_service()
        
        query_params = {
            "page": page,
            "page_size": page_size,
            "user_id": current_user["id"],
            "strategy_id": strategy_id,
            "status": status,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        result = await evaluation_service.list_backtests(query_params)
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"获取回测列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取回测列表异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取回测列表失败")


# ==================== 性能分析API ====================

@router.post("/performance", response_model=Dict[str, Any])
async def run_performance_analysis(
    request: PerformanceAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    运行策略性能分析
    
    全面分析策略的收益、风险、稳定性等性能指标
    """
    try:
        evaluation_service = get_evaluation_service()
        
        analysis_config = {
            "strategy_id": request.strategy_id,
            "analysis_type": request.analysis_type,
            "time_range": request.time_range,
            "metrics": request.metrics,
            "benchmark_comparison": request.benchmark_comparison
        }
        
        result = await evaluation_service.run_performance_evaluation(
            analysis_config=analysis_config,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 启动性能分析: {request.strategy_id}")
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"性能分析失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"性能分析异常: {str(e)}")
        raise HTTPException(status_code=500, detail="性能分析失败")


@router.get("/performance/{analysis_id}", response_model=Dict[str, Any])
async def get_performance_analysis_results(
    analysis_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取性能分析结果
    
    包括各项性能指标、趋势分析和建议
    """
    try:
        evaluation_service = get_evaluation_service()
        
        result = await evaluation_service.get_performance_analysis_results(
            analysis_id=analysis_id,
            user_id=current_user["id"]
        )
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"获取性能分析结果失败: {analysis_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取性能分析结果异常: {analysis_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取性能分析结果失败")


# ==================== 风险分析API ====================

@router.post("/risk", response_model=Dict[str, Any])
async def run_risk_analysis(
    request: RiskAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    运行策略风险分析
    
    评估策略的各种风险指标和风险水平
    """
    try:
        evaluation_service = get_evaluation_service()
        
        risk_config = {
            "strategy_id": request.strategy_id,
            "risk_metrics": request.risk_metrics,
            "confidence_levels": request.confidence_levels,
            "analysis_period": request.analysis_period,
            "stress_test": request.stress_test
        }
        
        result = await evaluation_service.run_risk_evaluation(
            risk_config=risk_config,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 启动风险分析: {request.strategy_id}")
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"风险分析失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"风险分析异常: {str(e)}")
        raise HTTPException(status_code=500, detail="风险分析失败")


@router.get("/risk/{analysis_id}", response_model=Dict[str, Any])
async def get_risk_analysis_results(
    analysis_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取风险分析结果
    
    包括风险评级、风险指标和风险控制建议
    """
    try:
        evaluation_service = get_evaluation_service()
        
        result = await evaluation_service.get_risk_analysis_results(
            analysis_id=analysis_id,
            user_id=current_user["id"]
        )
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"获取风险分析结果失败: {analysis_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取风险分析结果异常: {analysis_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取风险分析结果失败")


# ==================== 对比分析API ====================

@router.post("/comparison", response_model=Dict[str, Any])
async def run_comparison_analysis(
    request: ComparisonAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    运行策略对比分析
    
    对多个策略进行全面的性能对比分析
    """
    try:
        evaluation_service = get_evaluation_service()
        
        comparison_config = {
            "strategy_ids": request.strategy_ids,
            "comparison_metrics": request.comparison_metrics,
            "time_range": request.time_range,
            "benchmark": request.benchmark,
            "analysis_method": request.analysis_method
        }
        
        result = await evaluation_service.run_comparison_evaluation(
            comparison_config=comparison_config,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 启动对比分析: {len(request.strategy_ids)} 个策略")
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"对比分析失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"对比分析异常: {str(e)}")
        raise HTTPException(status_code=500, detail="对比分析失败")


@router.get("/comparison/{analysis_id}", response_model=Dict[str, Any])
async def get_comparison_analysis_results(
    analysis_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取对比分析结果
    
    包括详细的对比报告、排名和选择建议
    """
    try:
        evaluation_service = get_evaluation_service()
        
        result = await evaluation_service.get_comparison_analysis_results(
            analysis_id=analysis_id,
            user_id=current_user["id"]
        )
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"获取对比分析结果失败: {analysis_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取对比分析结果异常: {analysis_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取对比分析结果失败")


# ==================== 指标计算API ====================

@router.get("/metrics/available", response_model=Dict[str, Any])
async def get_available_metrics(
    category: Optional[str] = Query(None, description="指标分类"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取可用的分析指标列表
    
    包括收益指标、风险指标、比率指标等
    """
    try:
        evaluation_service = get_evaluation_service()
        
        result = await evaluation_service.get_available_metrics(category=category)
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"获取可用指标失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取可用指标异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取可用指标失败")


@router.post("/metrics/calculate", response_model=Dict[str, Any])
async def calculate_metrics(
    strategy_id: str = Body(..., description="策略ID"),
    metrics: List[str] = Body(..., description="指标列表"),
    time_range: str = Body("1y", description="计算时间范围"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    计算指定指标
    
    为策略计算指定的性能和风险指标
    """
    try:
        evaluation_service = get_evaluation_service()
        
        result = await evaluation_service.calculate_strategy_metrics(
            strategy_id=strategy_id,
            metrics=metrics,
            time_range=time_range,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 计算策略指标: {strategy_id}")
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"计算指标失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"计算指标异常: {str(e)}")
        raise HTTPException(status_code=500, detail="计算指标失败")


# ==================== 报告生成API ====================

@router.post("/reports/generate", response_model=Dict[str, Any])
async def generate_analysis_report(
    analysis_ids: List[str] = Body(..., description="分析ID列表"),
    report_config: Dict[str, Any] = Body({}, description="报告配置"),
    format: str = Body("pdf", description="报告格式"),
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    生成分析报告
    
    将多个分析结果合并生成综合报告
    """
    try:
        evaluation_service = get_evaluation_service()
        
        result = await evaluation_service.generate_comprehensive_report(
            analysis_ids=analysis_ids,
            report_config=report_config,
            format=format,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 生成分析报告: {len(analysis_ids)} 个分析")
        
        return result
        
    except EvaluationServiceError as e:
        logger.error(f"生成分析报告失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"生成分析报告异常: {str(e)}")
        raise HTTPException(status_code=500, detail="生成分析报告失败")


# 导出路由器
__all__ = ["router"]