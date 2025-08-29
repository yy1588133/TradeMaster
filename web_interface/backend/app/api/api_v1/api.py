"""
API v1 路由聚合

将所有的API端点路由聚合到一个主路由器中，提供统一的API接口。
包含认证、策略管理、数据管理、训练任务、分析评估等模块的路由。
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    api_keys,
    sessions,
    strategies,
    data,
    training,
    analysis,
    tools,
    websocket,
    settings
)


# 创建API v1主路由器
api_router = APIRouter()

# 包含各个端点路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

api_router.include_router(
    api_keys.router,
    prefix="/api-keys",
    tags=["API密钥管理"]
)

api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["会话管理"]
)

api_router.include_router(
    strategies.router, 
    prefix="/strategies", 
    tags=["策略管理"]
)

api_router.include_router(
    data.router, 
    prefix="/data", 
    tags=["数据管理"]
)

api_router.include_router(
    training.router, 
    prefix="/training", 
    tags=["训练任务"]
)
api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["分析评估"]
)

api_router.include_router(
    tools.router,
    prefix="/tools",
    tags=["工具集成"]
)

api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket通信"]
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["设置管理"]
)


# API状态检查端点
@api_router.get("/status", tags=["系统"])
async def api_status():
    """API状态检查"""
    return {
        "status": "正常运行",
        "version": "v1",
        "message": "TradeMaster Web Interface API v1",
        "endpoints": {
            "auth": "认证相关接口",
            "api-keys": "API密钥管理接口",
            "sessions": "会话管理接口",
            "strategies": "策略管理接口",
            "data": "数据管理接口",
            "training": "训练任务接口",
            "analysis": "分析评估接口",
            "tools": "工具集成接口",
            "ws": "WebSocket实时通信接口",
            "settings": "设置管理接口"
        }
    }