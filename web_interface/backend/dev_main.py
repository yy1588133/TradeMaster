"""
开发环境专用后端主应用 - 跳过数据库连接用于API测试
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.api_v1.endpoints import mock_auth, strategies, data, training, analysis, tools, api_keys, sessions

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例 (开发模式，跳过数据库)
app = FastAPI(
    title=f"{settings.PROJECT_NAME} (Dev Mode)",
    version=settings.VERSION,
    description="开发环境专用 - 无数据库依赖的API测试版本",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS中间件 
cors_origins = ["http://localhost:3000", "http://localhost:3100", "http://127.0.0.1:3100"]
logger.info(f"✅ CORS配置: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "mode": "development_no_db"
    }

# 包含API路由（使用模拟的认证路由）
app.include_router(mock_auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["认证"])
app.include_router(strategies.router, prefix=f"{settings.API_V1_STR}/strategies", tags=["策略管理"])
app.include_router(data.router, prefix=f"{settings.API_V1_STR}/data", tags=["数据管理"]) 
app.include_router(training.router, prefix=f"{settings.API_V1_STR}/training", tags=["训练任务"])
app.include_router(analysis.router, prefix=f"{settings.API_V1_STR}/analysis", tags=["分析评估"])
app.include_router(tools.router, prefix=f"{settings.API_V1_STR}/tools", tags=["工具集成"])
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/api-keys", tags=["API密钥管理"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}/sessions", tags=["会话管理"])

# 根路径
@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.PROJECT_NAME} (开发模式)",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
        "health_url": "/health",
        "note": "开发环境版本 - 部分功能可能需要数据库支持"
    }

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "内部服务器错误 (开发模式)",
            "error": str(exc) if settings.DEBUG else "服务器内部错误"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 启动开发环境后端 (无数据库依赖)")
    
    # 开发服务器配置
    uvicorn.run(
        "dev_main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=settings.DEBUG,
    )