"""
TradeMaster Web Interface 主应用

FastAPI应用主入口，配置路由、中间件、认证系统等核心功能。
集成完整的认证体系和业务逻辑。
"""

import time
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings, validate_settings
from app.core.database import init_database, check_database_connection, get_database_info
from app.core.security_middleware import SecurityMiddleware
from app.api.api_v1.api import api_router


# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 TradeMaster Web Interface 启动中...")
    
    try:
        # 验证配置
        validate_settings()
        logger.info("✅ 配置验证通过")
        
        # 检查数据库连接
        db_connected = await check_database_connection()
        if not db_connected:
            logger.error("❌ 数据库连接失败")
            raise Exception("数据库连接失败")
        
        logger.info("✅ 数据库连接正常")
        
        # 获取数据库信息
        db_info = await get_database_info()
        if "error" not in db_info:
            logger.info(f"📊 数据库信息: {db_info.get('active_connections')} 个活跃连接")
        
        # 在开发环境下初始化数据库
        if settings.DEBUG:
            try:
                await init_database()
                logger.info("✅ 数据库表结构检查完成")
            except Exception as e:
                logger.warning(f"⚠️ 数据库初始化警告: {e}")
        
        logger.info("🎉 应用启动完成")
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("👋 TradeMaster Web Interface 关闭中...")
    
    # 清理资源
    from app.core.database import engine
    await engine.dispose()
    logger.info("✅ 数据库连接已关闭")
    
    logger.info("✅ 应用已安全关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="专业的量化交易平台 Web 接口",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)


# ==================== 中间件配置 ====================

# CORS中间件 - 处理环境变量中的CORS配置
cors_origins = settings.BACKEND_CORS_ORIGINS
if isinstance(cors_origins, str):
    # 如果是字符串，按逗号分割
    cors_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
elif not isinstance(cors_origins, list):
    # 如果既不是字符串也不是列表，使用默认值
    cors_origins = ["http://localhost:3000", "http://localhost:3100", "http://127.0.0.1:3100"]

# 从环境变量覆盖CORS配置
import os
env_cors = os.getenv("BACKEND_CORS_ORIGINS")
if env_cors:
    cors_origins = [origin.strip() for origin in env_cors.split(",") if origin.strip()]

if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"✅ CORS配置: {cors_origins}")

# 受信任主机中间件
if settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# 安全中间件
app.add_middleware(SecurityMiddleware)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录HTTP请求日志"""
    start_time = time.time()
    
    # 记录请求开始
    if settings.DEBUG:
        logger.info(f"📨 {request.method} {request.url}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录响应
    if settings.DEBUG:
        logger.info(
            f"📤 {request.method} {request.url} - "
            f"{response.status_code} - {process_time:.3f}s"
        )
    
    # 添加处理时间头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 安全头中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """添加安全响应头"""
    response = await call_next(request)
    
    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # 在生产环境添加HSTS
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# ==================== 异常处理器 ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """验证异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "请求数据验证失败",
            "errors": exc.errors(),
            "status_code": 422,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "服务器内部错误" if settings.is_production else str(exc),
            "status_code": 500,
            "timestamp": time.time()
        }
    )


# ==================== 路由配置 ====================

# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    db_connected = await check_database_connection()
    
    return {
        "status": "healthy" if db_connected else "unhealthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "database": "connected" if db_connected else "disconnected",
        "environment": "development" if settings.DEBUG else "production"
    }


# 系统信息端点
@app.get("/info", tags=["系统"])
async def system_info():
    """系统信息端点"""
    db_info = await get_database_info()
    
    return {
        "application": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": "development" if settings.DEBUG else "production"
        },
        "database": db_info,
        "timestamp": time.time()
    }


# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


# 根路径重定向到文档
@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
        "health_url": "/health",
        "timestamp": time.time()
    }


# ==================== 启动配置 ====================

if __name__ == "__main__":
    import uvicorn
    
    # 开发服务器配置
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
        access_log=settings.DEBUG,
    )