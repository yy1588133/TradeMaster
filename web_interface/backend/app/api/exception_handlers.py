"""
全局异常处理器

提供统一的错误处理和响应格式，确保API的一致性和用户友好性。
支持不同类型的异常处理，包括验证错误、业务逻辑错误、系统错误等。
"""

import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.trademaster_config import TradeMasterConfigError


class APIException(Exception):
    """自定义API异常基类"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "API_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(APIException):
    """验证异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class BusinessLogicException(APIException):
    """业务逻辑异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details
        )


class ResourceNotFoundException(APIException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, identifier: Union[str, int]):
        super().__init__(
            message=f"{resource}未找到: {identifier}",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)}
        )


class DatabaseException(APIException):
    """数据库操作异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )


class ExternalServiceException(APIException):
    """外部服务异常"""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{service}服务异常: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, **(details or {})}
        )


def create_error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: str = "INTERNAL_ERROR",
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> JSONResponse:
    """创建标准错误响应
    
    Args:
        message: 错误消息
        status_code: HTTP状态码
        error_code: 错误代码
        details: 错误详细信息
        request: FastAPI请求对象
        
    Returns:
        JSONResponse: 标准错误响应
    """
    error_data = {
        "success": False,
        "error": {
            "message": message,
            "code": error_code,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
    }
    
    # 添加请求信息（如果可用）
    if request:
        error_data["error"]["request"] = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None
        }
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


# ==================== 全局异常处理器 ====================

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """API自定义异常处理器"""
    logger.warning(f"API异常: {exc.error_code} - {exc.message}")
    
    return create_error_response(
        message=exc.message,
        status_code=exc.status_code,
        error_code=exc.error_code,
        details=exc.details,
        request=request
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return create_error_response(
        message=str(exc.detail),
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
        request=request
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求验证异常处理器"""
    logger.warning(f"请求验证失败: {exc.errors()}")
    
    # 格式化验证错误
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": " -> ".join([str(x) for x in error["loc"]]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return create_error_response(
        message="请求参数验证失败",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": validation_errors},
        request=request
    )


async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Pydantic验证异常处理器"""
    logger.warning(f"数据验证失败: {exc.errors()}")
    
    # 格式化验证错误
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": " -> ".join([str(x) for x in error["loc"]]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        message="数据验证失败",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="DATA_VALIDATION_ERROR",
        details={"validation_errors": validation_errors},
        request=request
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """数据库异常处理器"""
    logger.error(f"数据库异常: {str(exc)}")
    
    # 不同类型的数据库异常
    if isinstance(exc, IntegrityError):
        return create_error_response(
            message="数据完整性约束违反",
            status_code=status.HTTP_409_CONFLICT,
            error_code="INTEGRITY_ERROR",
            details={"constraint": "数据约束违反"},
            request=request
        )
    elif isinstance(exc, OperationalError):
        return create_error_response(
            message="数据库操作失败",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_UNAVAILABLE",
            details={"error": "数据库连接或操作失败"},
            request=request
        )
    else:
        return create_error_response(
            message="数据库异常",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            request=request
        )


async def trademaster_config_exception_handler(request: Request, exc: TradeMasterConfigError) -> JSONResponse:
    """TradeMaster配置异常处理器"""
    logger.warning(f"TradeMaster配置异常: {str(exc)}")
    
    return create_error_response(
        message=str(exc),
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="TRADEMASTER_CONFIG_ERROR",
        request=request
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器（最后的fallback）"""
    logger.error(f"未处理异常: {type(exc).__name__}: {str(exc)}")
    logger.error(f"异常堆栈: {traceback.format_exc()}")
    
    # 生产环境不暴露详细错误信息
    from app.core.config import get_settings
    settings = get_settings()
    
    if settings.is_production:
        message = "服务器内部错误"
        details = {}
    else:
        message = f"{type(exc).__name__}: {str(exc)}"
        details = {
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc() if settings.DEBUG else None
        }
    
    return create_error_response(
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
        details=details,
        request=request
    )


# ==================== 工具函数 ====================

def log_and_raise_api_exception(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: str = "API_ERROR",
    details: Optional[Dict[str, Any]] = None,
    log_level: str = "warning"
) -> None:
    """记录日志并抛出API异常
    
    Args:
        message: 错误消息
        status_code: HTTP状态码
        error_code: 错误代码
        details: 错误详细信息
        log_level: 日志级别
    """
    # 记录日志
    log_func = getattr(logger, log_level.lower(), logger.warning)
    log_func(f"{error_code}: {message}")
    
    # 抛出异常
    raise APIException(
        message=message,
        status_code=status_code,
        error_code=error_code,
        details=details
    )


def handle_external_service_error(
    service_name: str,
    error: Exception,
    context: str = ""
) -> None:
    """处理外部服务错误
    
    Args:
        service_name: 服务名称
        error: 原始异常
        context: 上下文信息
    """
    logger.error(f"{service_name}服务错误: {str(error)} {context}")
    
    raise ExternalServiceException(
        service=service_name,
        message=str(error),
        details={"context": context}
    )


def validate_and_raise(condition: bool, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """验证条件，失败时抛出验证异常
    
    Args:
        condition: 验证条件
        message: 错误消息
        details: 错误详细信息
    """
    if not condition:
        raise ValidationException(message=message, details=details)


def ensure_resource_exists(resource: Any, resource_name: str, identifier: Union[str, int]) -> Any:
    """确保资源存在，不存在时抛出异常
    
    Args:
        resource: 资源对象
        resource_name: 资源名称
        identifier: 资源标识符
        
    Returns:
        资源对象（如果存在）
        
    Raises:
        ResourceNotFoundException: 资源不存在时抛出
    """
    if resource is None:
        raise ResourceNotFoundException(resource_name, identifier)
    return resource


# 导出主要类和函数
__all__ = [
    # 异常类
    "APIException",
    "ValidationException",
    "BusinessLogicException",
    "ResourceNotFoundException",
    "DatabaseException",
    "ExternalServiceException",
    # 异常处理器
    "api_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "pydantic_validation_exception_handler",
    "database_exception_handler",
    "trademaster_config_exception_handler",
    "general_exception_handler",
    # 工具函数
    "create_error_response",
    "log_and_raise_api_exception",
    "handle_external_service_error",
    "validate_and_raise",
    "ensure_resource_exists"
]