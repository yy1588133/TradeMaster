"""
工具集成API端点

提供TradeMaster生态系统中各种专业工具的REST API接口。
包括FinAgent、EarnMore、数据预处理、市场动态建模等工具的集成。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Body, Form, UploadFile, File
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_active_user,
    CurrentUser,
    DatabaseSession
)
from app.services.tools_service import get_tools_service, ToolServiceError, ToolType, ToolExecutionMode
from app.core.config import settings
from loguru import logger

router = APIRouter()

# ==================== 请求/响应模型 ====================

class FinAgentRequest(BaseModel):
    """FinAgent请求模型"""
    symbol: str = Field("AAPL", description="交易标的")
    start_date: str = Field("2020-01-01", description="开始日期")
    end_date: str = Field("2023-12-31", description="结束日期")
    execution_mode: ToolExecutionMode = Field(ToolExecutionMode.ASYNC, description="执行模式")
    if_train: bool = Field(True, description="是否训练")
    if_valid: bool = Field(True, description="是否验证")
    custom_config: Dict[str, Any] = Field({}, description="自定义配置")


class EarnMoreRequest(BaseModel):
    """EarnMore请求模型"""
    dataset: str = Field("dj30", description="数据集名称")
    agent: str = Field("sac", description="智能体类型")
    execution_mode: ToolExecutionMode = Field(ToolExecutionMode.ASYNC, description="执行模式")
    num_episodes: int = Field(1000, description="训练轮次")
    learning_rate: float = Field(0.001, description="学习率")
    custom_config: Dict[str, Any] = Field({}, description="自定义配置")


class DataPreprocessorRequest(BaseModel):
    """数据预处理请求模型"""
    data_source: str = Field("yahoofinance", description="数据源")
    symbols: List[str] = Field(..., description="证券代码列表")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    preprocessor_type: str = Field("yahoofinance", description="预处理器类型")
    features: List[str] = Field(["open", "high", "low", "close", "volume"], description="特征列表")


class MarketDynamicsRequest(BaseModel):
    """市场动态建模请求模型"""
    # 解决Pydantic字段命名冲突警告
    model_config = ConfigDict(protected_namespaces=())
    
    dataset: str = Field("BTC", description="数据集")
    start_date: str = Field("2020-01-01", description="开始日期")
    end_date: str = Field("2021-12-31", description="结束日期")
    model_type: str = Field("lstm", description="模型类型")
    custom_config: Dict[str, Any] = Field({}, description="自定义配置")


# ==================== 工具状态管理API ====================

@router.get("/status", response_model=Dict[str, Any])
async def get_all_tools_status(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取所有工具状态
    
    返回所有可用工具的状态信息
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.get_all_tools_status()
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"获取工具状态失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取工具状态异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取工具状态失败")


@router.get("/status/{tool_type}", response_model=Dict[str, Any])
async def get_tool_status(
    tool_type: ToolType,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取指定工具状态
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.get_tool_status(tool_type)
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"获取工具状态失败: {tool_type}, {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取工具状态异常: {tool_type}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取工具状态失败")


@router.get("/health", response_model=Dict[str, Any])
async def health_check_tools(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    工具健康检查
    
    检查所有工具的健康状态和可用性
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.health_check_all_tools()
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"工具健康检查失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"工具健康检查异常: {str(e)}")
        raise HTTPException(status_code=500, detail="工具健康检查失败")


# ==================== FinAgent API ====================

@router.post("/finagent/run", response_model=Dict[str, Any])
async def run_finagent(
    request: FinAgentRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    运行FinAgent多模态金融智能体
    
    执行FinAgent工具进行金融交易分析和预测
    """
    try:
        tools_service = get_tools_service()
        
        # 构建FinAgent配置
        finagent_config = {
            "symbol": request.symbol,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "if_train": request.if_train,
            "if_valid": request.if_valid,
            **request.custom_config
        }
        
        result = await tools_service.run_finagent(
            config=finagent_config,
            execution_mode=request.execution_mode
        )
        
        logger.info(f"用户 {current_user['username']} 启动FinAgent: {request.symbol}")
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"FinAgent执行失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"FinAgent执行异常: {str(e)}")
        raise HTTPException(status_code=500, detail="FinAgent执行失败")


@router.get("/finagent/config/template", response_model=Dict[str, Any])
async def get_finagent_config_template(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取FinAgent配置模板
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.get_tool_config_template(ToolType.FINAGENT)
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"获取FinAgent配置模板失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取FinAgent配置模板异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取FinAgent配置模板失败")


# ==================== EarnMore API ====================

@router.post("/earnmore/run", response_model=Dict[str, Any])
async def run_earnmore(
    request: EarnMoreRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    运行EarnMore强化学习投资组合管理
    
    执行EarnMore工具进行投资组合优化
    """
    try:
        tools_service = get_tools_service()
        
        # 构建EarnMore配置
        earnmore_config = {
            "dataset": request.dataset,
            "agent": request.agent,
            "num_episodes": request.num_episodes,
            "learning_rate": request.learning_rate,
            **request.custom_config
        }
        
        result = await tools_service.run_earnmore(
            config=earnmore_config,
            execution_mode=request.execution_mode
        )
        
        logger.info(f"用户 {current_user['username']} 启动EarnMore: {request.dataset}")
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"EarnMore执行失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"EarnMore执行异常: {str(e)}")
        raise HTTPException(status_code=500, detail="EarnMore执行失败")


@router.get("/earnmore/config/template", response_model=Dict[str, Any])
async def get_earnmore_config_template(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取EarnMore配置模板
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.get_tool_config_template(ToolType.EARNMORE)
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"获取EarnMore配置模板失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取EarnMore配置模板异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取EarnMore配置模板失败")


# ==================== 数据预处理API ====================

@router.post("/preprocessor/run", response_model=Dict[str, Any])
async def run_data_preprocessor(
    request: DataPreprocessorRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    运行数据预处理工具
    
    从指定数据源获取和预处理金融数据
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.run_data_preprocessor(
            data_source=request.data_source,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            preprocessor_type=request.preprocessor_type
        )
        
        logger.info(f"用户 {current_user['username']} 启动数据预处理: {request.symbols}")
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"数据预处理失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"数据预处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail="数据预处理失败")


@router.get("/preprocessor/config/template", response_model=Dict[str, Any])
async def get_preprocessor_config_template(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取数据预处理配置模板
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.get_tool_config_template(ToolType.DATA_PROCESSOR)
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"获取数据预处理配置模板失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取数据预处理配置模板异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取数据预处理配置模板失败")


# ==================== 市场动态建模API ====================

@router.post("/market-dynamics/run", response_model=Dict[str, Any])
async def run_market_dynamics_modeling(
    request: MarketDynamicsRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    运行市场动态建模工具
    
    建立市场动态模型进行趋势预测和分析
    """
    try:
        tools_service = get_tools_service()
        
        # 构建建模配置
        modeling_config = {
            "dataset": request.dataset,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "model_type": request.model_type,
            **request.custom_config
        }
        
        result = await tools_service.run_market_dynamics_modeling(
            config=modeling_config
        )
        
        logger.info(f"用户 {current_user['username']} 启动市场动态建模: {request.dataset}")
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"市场动态建模失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"市场动态建模异常: {str(e)}")
        raise HTTPException(status_code=500, detail="市场动态建模失败")


# ==================== 任务管理API ====================

@router.get("/tasks", response_model=Dict[str, Any])
async def list_active_tasks(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取活跃任务列表
    
    列出所有正在运行的工具任务
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.list_active_tasks()
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"获取活跃任务列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取活跃任务列表异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取活跃任务列表失败")


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取任务状态
    
    查询指定任务的执行状态和结果
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.get_task_status(task_id)
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"获取任务状态失败: {task_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务状态异常: {task_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")


@router.delete("/tasks/{task_id}", response_model=Dict[str, Any])
async def cancel_task(
    task_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    取消任务
    
    取消正在运行的工具任务
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.cancel_task(task_id)
        
        logger.info(f"用户 {current_user['username']} 取消任务: {task_id}")
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"取消任务失败: {task_id}, {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取消任务异常: {task_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="取消任务失败")


# ==================== 工具配置API ====================

@router.get("/config/templates", response_model=Dict[str, Any])
async def get_all_config_templates(
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取所有工具配置模板
    
    返回所有可用工具的配置模板和参数说明
    """
    try:
        tools_service = get_tools_service()
        
        templates = {}
        for tool_type in ToolType:
            try:
                template = await tools_service.get_tool_config_template(tool_type)
                templates[tool_type.value] = template
            except Exception as e:
                logger.warning(f"获取工具配置模板失败: {tool_type}, {str(e)}")
                continue
        
        return {
            "templates": templates,
            "total_tools": len(templates),
            "supported_tools": list(templates.keys())
        }
        
    except Exception as e:
        logger.error(f"获取所有配置模板异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置模板失败")


@router.get("/config/templates/{tool_type}", response_model=Dict[str, Any])
async def get_tool_config_template(
    tool_type: ToolType,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取指定工具配置模板
    """
    try:
        tools_service = get_tools_service()
        
        result = await tools_service.get_tool_config_template(tool_type)
        
        return result
        
    except ToolServiceError as e:
        logger.error(f"获取工具配置模板失败: {tool_type}, {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取工具配置模板异常: {tool_type}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取工具配置模板失败")


# ==================== 工具文档API ====================

@router.get("/documentation", response_model=Dict[str, Any])
async def get_tools_documentation(
    current_user: CurrentUser,
    db: DatabaseSession,
    tool_type: Optional[ToolType] = Query(None, description="工具类型")
):
    """
    获取工具文档
    
    提供各工具的使用说明、API文档和示例
    """
    try:
        documentation = {
            "finagent": {
                "name": "FinAgent多模态金融智能体",
                "description": "基于多模态数据的智能金融交易分析工具",
                "parameters": {
                    "symbol": "交易标的代码，如AAPL、MSFT等",
                    "start_date": "分析开始日期，格式YYYY-MM-DD",
                    "end_date": "分析结束日期，格式YYYY-MM-DD",
                    "if_train": "是否进行模型训练",
                    "if_valid": "是否进行模型验证"
                },
                "examples": [
                    {
                        "description": "分析苹果股票",
                        "config": {
                            "symbol": "AAPL",
                            "start_date": "2023-01-01",
                            "end_date": "2023-12-31",
                            "if_train": True,
                            "if_valid": True
                        }
                    }
                ]
            },
            "earnmore": {
                "name": "EarnMore强化学习投资组合管理",
                "description": "基于强化学习的投资组合优化工具",
                "parameters": {
                    "dataset": "数据集名称，如dj30、sp500等",
                    "agent": "强化学习智能体类型，如sac、ppo、ddpg",
                    "num_episodes": "训练轮次",
                    "learning_rate": "学习率"
                },
                "examples": [
                    {
                        "description": "优化道琼斯30投资组合",
                        "config": {
                            "dataset": "dj30",
                            "agent": "sac",
                            "num_episodes": 1000,
                            "learning_rate": 0.001
                        }
                    }
                ]
            },
            "data_processor": {
                "name": "数据预处理工具",
                "description": "金融数据获取和预处理工具",
                "parameters": {
                    "data_source": "数据源，如yahoofinance、alpha_vantage等",
                    "symbols": "证券代码列表",
                    "start_date": "数据开始日期",
                    "end_date": "数据结束日期",
                    "preprocessor_type": "预处理器类型"
                },
                "examples": [
                    {
                        "description": "获取多只股票数据",
                        "config": {
                            "data_source": "yahoofinance",
                            "symbols": ["AAPL", "MSFT", "GOOGL"],
                            "start_date": "2023-01-01",
                            "end_date": "2023-12-31",
                            "preprocessor_type": "yahoofinance"
                        }
                    }
                ]
            }
        }
        
        if tool_type:
            doc = documentation.get(tool_type.value)
            if not doc:
                raise HTTPException(status_code=404, detail="工具文档不存在")
            return {
                "tool_type": tool_type.value,
                "documentation": doc
            }
        
        return {
            "documentation": documentation,
            "available_tools": list(documentation.keys()),
            "total_tools": len(documentation)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具文档异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取工具文档失败")


# 导出路由器
__all__ = ["router"]