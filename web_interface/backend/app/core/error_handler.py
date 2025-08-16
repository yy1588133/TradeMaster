"""
统一错误处理和监控系统

提供全局异常处理、错误分类、监控告警和错误恢复机制。
集成日志记录、性能监控和错误统计功能。
"""

import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Type, Callable, Union
from enum import Enum
from collections import defaultdict, deque
import asyncio
import inspect

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings


class ErrorLevel(str, Enum):
    """错误级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """错误分类枚举"""
    AUTHENTICATION = "authentication"        # 认证错误
    AUTHORIZATION = "authorization"          # 授权错误
    VALIDATION = "validation"               # 验证错误
    BUSINESS_LOGIC = "business_logic"       # 业务逻辑错误
    EXTERNAL_SERVICE = "external_service"   # 外部服务错误
    DATABASE = "database"                   # 数据库错误
    NETWORK = "network"                     # 网络错误
    SYSTEM = "system"                       # 系统错误
    UNKNOWN = "unknown"                     # 未知错误


class ErrorCode(str, Enum):
    """错误代码枚举"""
    # 认证相关
    INVALID_CREDENTIALS = "E1001"
    TOKEN_EXPIRED = "E1002"
    TOKEN_INVALID = "E1003"
    
    # 授权相关
    PERMISSION_DENIED = "E2001"
    RESOURCE_FORBIDDEN = "E2002"
    
    # 验证相关
    INVALID_INPUT = "E3001"
    MISSING_REQUIRED_FIELD = "E3002"
    INVALID_FORMAT = "E3003"
    
    # 业务逻辑相关
    STRATEGY_NOT_FOUND = "E4001"
    STRATEGY_ALREADY_EXISTS = "E4002"
    INVALID_STRATEGY_STATE = "E4003"
    TRAINING_FAILED = "E4004"
    
    # 外部服务相关
    TRADEMASTER_API_ERROR = "E5001"
    REDIS_CONNECTION_ERROR = "E5002"
    DATABASE_CONNECTION_ERROR = "E5003"
    
    # 系统相关
    INTERNAL_SERVER_ERROR = "E9001"
    SERVICE_UNAVAILABLE = "E9002"
    TIMEOUT_ERROR = "E9003"


class ErrorInfo(BaseModel):
    """错误信息模型"""
    error_id: str = Field(..., description="错误ID")
    error_code: ErrorCode = Field(..., description="错误代码")
    error_level: ErrorLevel = Field(..., description="错误级别")
    error_category: ErrorCategory = Field(..., description="错误分类")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="错误详情")
    
    # 上下文信息
    user_id: Optional[str] = Field(None, description="用户ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    endpoint: Optional[str] = Field(None, description="API端点")
    method: Optional[str] = Field(None, description="HTTP方法")
    
    # 时间和位置信息
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="发生时间")
    module: Optional[str] = Field(None, description="模块名称")
    function: Optional[str] = Field(None, description="函数名称")
    line_number: Optional[int] = Field(None, description="行号")
    
    # 异常信息
    exception_type: Optional[str] = Field(None, description="异常类型")
    exception_message: Optional[str] = Field(None, description="异常消息")
    traceback: Optional[str] = Field(None, description="异常堆栈")
    
    # 元数据
    metadata: Dict[str, Any] = Field({}, description="元数据")


class ErrorStatistics(BaseModel):
    """错误统计模型"""
    total_errors: int = Field(0, description="总错误数")
    error_by_level: Dict[str, int] = Field({}, description="按级别统计")
    error_by_category: Dict[str, int] = Field({}, description="按分类统计")
    error_by_code: Dict[str, int] = Field({}, description="按代码统计")
    recent_errors: List[ErrorInfo] = Field([], description="最近错误")
    time_range: str = Field("1h", description="统计时间范围")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class CustomException(Exception):
    """自定义异常基类"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        error_level: ErrorLevel = ErrorLevel.ERROR,
        error_category: ErrorCategory = ErrorCategory.UNKNOWN,
        detail: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.error_level = error_level
        self.error_category = error_category
        self.detail = detail
        self.metadata = metadata or {}


class AuthenticationError(CustomException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败", **kwargs):
        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.INVALID_CREDENTIALS),
            error_level=ErrorLevel.WARNING,
            error_category=ErrorCategory.AUTHENTICATION,
            **{k: v for k, v in kwargs.items() if k != "error_code"}
        )


class AuthorizationError(CustomException):
    """授权错误"""
    
    def __init__(self, message: str = "权限不足", **kwargs):
        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.PERMISSION_DENIED),
            error_level=ErrorLevel.WARNING,
            error_category=ErrorCategory.AUTHORIZATION,
            **{k: v for k, v in kwargs.items() if k != "error_code"}
        )


class ValidationError(CustomException):
    """验证错误"""
    
    def __init__(self, message: str = "数据验证失败", **kwargs):
        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.INVALID_INPUT),
            error_level=ErrorLevel.WARNING,
            error_category=ErrorCategory.VALIDATION,
            **{k: v for k, v in kwargs.items() if k != "error_code"}
        )


class BusinessLogicError(CustomException):
    """业务逻辑错误"""
    
    def __init__(self, message: str = "业务逻辑错误", **kwargs):
        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.STRATEGY_NOT_FOUND),
            error_level=ErrorLevel.ERROR,
            error_category=ErrorCategory.BUSINESS_LOGIC,
            **{k: v for k, v in kwargs.items() if k != "error_code"}
        )


class ExternalServiceError(CustomException):
    """外部服务错误"""
    
    def __init__(self, message: str = "外部服务错误", **kwargs):
        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.TRADEMASTER_API_ERROR),
            error_level=ErrorLevel.ERROR,
            error_category=ErrorCategory.EXTERNAL_SERVICE,
            **{k: v for k, v in kwargs.items() if k != "error_code"}
        )


class ErrorHandler:
    """错误处理器
    
    提供统一的错误处理、记录、监控和恢复功能
    """
    
    def __init__(self):
        """初始化错误处理器"""
        self.error_storage = deque(maxlen=10000)  # 内存中存储最近的错误
        self.error_counts = defaultdict(int)      # 错误计数
        self.error_handlers: Dict[Type[Exception], Callable] = {}  # 异常处理器注册表
        self.recovery_strategies: Dict[ErrorCode, Callable] = {}   # 恢复策略注册表
        
        # 监控配置
        self.monitoring_enabled = True
        self.alert_thresholds = {
            ErrorLevel.CRITICAL: 1,    # 关键错误立即告警
            ErrorLevel.ERROR: 10,      # 错误达到10个时告警
            ErrorLevel.WARNING: 50     # 警告达到50个时告警
        }
        
        # 注册默认异常处理器
        self._register_default_handlers()
        
        logger.info("错误处理器初始化完成")
    
    # ==================== 错误记录 ====================
    
    async def record_error(
        self,
        error: Union[Exception, ErrorInfo],
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """记录错误信息
        
        Args:
            error: 异常对象或错误信息
            request: HTTP请求对象
            user_id: 用户ID
            extra_metadata: 额外元数据
            
        Returns:
            ErrorInfo: 错误信息对象
        """
        try:
            # 生成错误ID
            error_id = f"ERR_{int(datetime.utcnow().timestamp() * 1000)}"
            
            if isinstance(error, ErrorInfo):
                error_info = error
                error_info.error_id = error_id
            else:
                # 从异常对象创建错误信息
                error_info = await self._create_error_info_from_exception(
                    error, error_id, request, user_id, extra_metadata
                )
            
            # 存储错误信息
            self.error_storage.append(error_info)
            
            # 更新统计计数
            self._update_error_statistics(error_info)
            
            # 记录日志
            await self._log_error(error_info)
            
            # 检查是否需要告警
            await self._check_alert_conditions(error_info)
            
            return error_info
            
        except Exception as e:
            # 记录错误处理器自身的错误
            logger.critical(f"错误处理器内部错误: {str(e)}")
            logger.critical(traceback.format_exc())
            
            # 返回基本错误信息
            return ErrorInfo(
                error_id=f"ERR_HANDLER_{int(datetime.utcnow().timestamp())}",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                error_level=ErrorLevel.CRITICAL,
                error_category=ErrorCategory.SYSTEM,
                message="错误处理器内部错误"
            )
    
    async def _create_error_info_from_exception(
        self,
        exception: Exception,
        error_id: str,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """从异常对象创建错误信息"""
        
        # 获取调用栈信息
        tb = traceback.extract_tb(exception.__traceback__)
        last_frame = tb[-1] if tb else None
        
        # 确定错误属性
        if isinstance(exception, CustomException):
            error_code = exception.error_code
            error_level = exception.error_level
            error_category = exception.error_category
            message = exception.message
            detail = exception.detail
            metadata = exception.metadata.copy()
        else:
            error_code = self._map_exception_to_error_code(exception)
            error_level = self._map_exception_to_error_level(exception)
            error_category = self._map_exception_to_category(exception)
            message = str(exception) or "未知错误"
            detail = None
            metadata = {}
        
        # 添加额外元数据
        if extra_metadata:
            metadata.update(extra_metadata)
        
        # 获取请求信息
        endpoint = None
        method = None
        request_id = None
        
        if request:
            endpoint = str(request.url.path)
            method = request.method
            request_id = getattr(request.state, 'request_id', None)
            
            # 添加请求相关信息到元数据
            metadata.update({
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params)
            })
        
        return ErrorInfo(
            error_id=error_id,
            error_code=error_code,
            error_level=error_level,
            error_category=error_category,
            message=message,
            detail=detail,
            user_id=user_id,
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            module=last_frame.filename if last_frame else None,
            function=last_frame.name if last_frame else None,
            line_number=last_frame.lineno if last_frame else None,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            traceback=traceback.format_exc(),
            metadata=metadata
        )
    
    # ==================== 错误处理 ====================
    
    async def handle_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None
    ) -> JSONResponse:
        """处理错误并返回HTTP响应
        
        Args:
            error: 异常对象
            request: HTTP请求对象
            user_id: 用户ID
            
        Returns:
            JSONResponse: HTTP错误响应
        """
        try:
            # 记录错误
            error_info = await self.record_error(error, request, user_id)
            
            # 尝试错误恢复
            recovery_result = await self._attempt_error_recovery(error_info)
            
            # 获取注册的异常处理器
            handler = self._get_exception_handler(type(error))
            if handler:
                try:
                    return await handler(error, error_info, request)
                except Exception as handler_error:
                    logger.error(f"异常处理器执行失败: {str(handler_error)}")
            
            # 默认错误处理
            return await self._create_error_response(error_info)
            
        except Exception as e:
            logger.critical(f"错误处理失败: {str(e)}")
            
            # 返回通用错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "内部服务器错误",
                    "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                    "message": "系统发生未知错误",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def register_exception_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable
    ):
        """注册异常处理器
        
        Args:
            exception_type: 异常类型
            handler: 处理器函数
        """
        self.error_handlers[exception_type] = handler
        logger.info(f"注册异常处理器: {exception_type.__name__}")
    
    def register_recovery_strategy(
        self,
        error_code: ErrorCode,
        strategy: Callable
    ):
        """注册错误恢复策略
        
        Args:
            error_code: 错误代码
            strategy: 恢复策略函数
        """
        self.recovery_strategies[error_code] = strategy
        logger.info(f"注册恢复策略: {error_code.value}")
    
    # ==================== 错误监控 ====================
    
    async def get_error_statistics(
        self,
        time_range: str = "1h"
    ) -> ErrorStatistics:
        """获取错误统计信息
        
        Args:
            time_range: 统计时间范围 (1h, 6h, 1d, 1w)
            
        Returns:
            ErrorStatistics: 错误统计
        """
        try:
            # 解析时间范围
            time_delta = self._parse_time_range(time_range)
            cutoff_time = datetime.utcnow() - time_delta
            
            # 过滤指定时间范围内的错误
            recent_errors = [
                error for error in self.error_storage
                if error.timestamp >= cutoff_time
            ]
            
            # 统计各维度数据
            total_errors = len(recent_errors)
            
            error_by_level = defaultdict(int)
            error_by_category = defaultdict(int) 
            error_by_code = defaultdict(int)
            
            for error in recent_errors:
                error_by_level[error.error_level.value] += 1
                error_by_category[error.error_category.value] += 1
                error_by_code[error.error_code.value] += 1
            
            return ErrorStatistics(
                total_errors=total_errors,
                error_by_level=dict(error_by_level),
                error_by_category=dict(error_by_category),
                error_by_code=dict(error_by_code),
                recent_errors=recent_errors[-10:],  # 最近10个错误
                time_range=time_range
            )
            
        except Exception as e:
            logger.error(f"获取错误统计失败: {str(e)}")
            return ErrorStatistics(time_range=time_range)
    
    async def check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态
        
        Returns:
            Dict[str, Any]: 系统健康信息
        """
        try:
            # 获取最近1小时的错误统计
            stats = await self.get_error_statistics("1h")
            
            # 计算健康评分
            health_score = self._calculate_health_score(stats)
            
            # 确定健康状态
            if health_score >= 90:
                health_status = "healthy"
            elif health_score >= 70:
                health_status = "warning"
            else:
                health_status = "critical"
            
            # 获取主要问题
            issues = self._identify_major_issues(stats)
            
            return {
                "health_status": health_status,
                "health_score": health_score,
                "total_errors": stats.total_errors,
                "critical_errors": stats.error_by_level.get("critical", 0),
                "error_errors": stats.error_by_level.get("error", 0),
                "major_issues": issues,
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"系统健康检查失败: {str(e)}")
            return {
                "health_status": "unknown",
                "health_score": 0,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    # ==================== 私有方法 ====================
    
    def _register_default_handlers(self):
        """注册默认异常处理器"""
        
        async def handle_http_exception(error: HTTPException, error_info: ErrorInfo, request: Request):
            return JSONResponse(
                status_code=error.status_code,
                content={
                    "error": error.detail,
                    "error_code": error_info.error_code.value,
                    "error_id": error_info.error_id,
                    "timestamp": error_info.timestamp.isoformat()
                }
            )
        
        async def handle_validation_error(error: ValidationError, error_info: ErrorInfo, request: Request):
            return JSONResponse(
                status_code=422,
                content={
                    "error": error.message,
                    "error_code": error.error_code.value,
                    "error_id": error_info.error_id,
                    "detail": error.detail,
                    "timestamp": error_info.timestamp.isoformat()
                }
            )
        
        async def handle_authentication_error(error: AuthenticationError, error_info: ErrorInfo, request: Request):
            return JSONResponse(
                status_code=401,
                content={
                    "error": error.message,
                    "error_code": error.error_code.value,
                    "error_id": error_info.error_id,
                    "timestamp": error_info.timestamp.isoformat()
                }
            )
        
        async def handle_authorization_error(error: AuthorizationError, error_info: ErrorInfo, request: Request):
            return JSONResponse(
                status_code=403,
                content={
                    "error": error.message,
                    "error_code": error.error_code.value,
                    "error_id": error_info.error_id,
                    "timestamp": error_info.timestamp.isoformat()
                }
            )
        
        self.register_exception_handler(HTTPException, handle_http_exception)
        self.register_exception_handler(ValidationError, handle_validation_error)
        self.register_exception_handler(AuthenticationError, handle_authentication_error)
        self.register_exception_handler(AuthorizationError, handle_authorization_error)
    
    def _get_exception_handler(self, exception_type: Type[Exception]) -> Optional[Callable]:
        """获取异常处理器"""
        # 直接匹配
        if exception_type in self.error_handlers:
            return self.error_handlers[exception_type]
        
        # 查找父类匹配
        for exc_type, handler in self.error_handlers.items():
            if issubclass(exception_type, exc_type):
                return handler
        
        return None
    
    def _map_exception_to_error_code(self, exception: Exception) -> ErrorCode:
        """将异常映射到错误代码"""
        exception_mapping = {
            HTTPException: ErrorCode.INTERNAL_SERVER_ERROR,
            ValueError: ErrorCode.INVALID_INPUT,
            TypeError: ErrorCode.INVALID_INPUT,
            KeyError: ErrorCode.MISSING_REQUIRED_FIELD,
            AttributeError: ErrorCode.INVALID_INPUT,
            ConnectionError: ErrorCode.DATABASE_CONNECTION_ERROR,
            TimeoutError: ErrorCode.TIMEOUT_ERROR
        }
        
        for exc_type, error_code in exception_mapping.items():
            if isinstance(exception, exc_type):
                return error_code
        
        return ErrorCode.INTERNAL_SERVER_ERROR
    
    def _map_exception_to_error_level(self, exception: Exception) -> ErrorLevel:
        """将异常映射到错误级别"""
        if isinstance(exception, (ValueError, TypeError, KeyError)):
            return ErrorLevel.WARNING
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            return ErrorLevel.ERROR
        else:
            return ErrorLevel.ERROR
    
    def _map_exception_to_category(self, exception: Exception) -> ErrorCategory:
        """将异常映射到错误分类"""
        if isinstance(exception, (ValueError, TypeError, KeyError)):
            return ErrorCategory.VALIDATION
        elif isinstance(exception, ConnectionError):
            return ErrorCategory.NETWORK
        elif isinstance(exception, TimeoutError):
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.UNKNOWN
    
    async def _create_error_response(self, error_info: ErrorInfo) -> JSONResponse:
        """创建错误响应"""
        status_code = 500
        
        if error_info.error_category == ErrorCategory.AUTHENTICATION:
            status_code = 401
        elif error_info.error_category == ErrorCategory.AUTHORIZATION:
            status_code = 403
        elif error_info.error_category == ErrorCategory.VALIDATION:
            status_code = 422
        elif error_info.error_level == ErrorLevel.WARNING:
            status_code = 400
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": error_info.message,
                "error_code": error_info.error_code.value,
                "error_id": error_info.error_id,
                "detail": error_info.detail,
                "timestamp": error_info.timestamp.isoformat()
            }
        )
    
    def _update_error_statistics(self, error_info: ErrorInfo):
        """更新错误统计"""
        self.error_counts[f"level_{error_info.error_level.value}"] += 1
        self.error_counts[f"category_{error_info.error_category.value}"] += 1
        self.error_counts[f"code_{error_info.error_code.value}"] += 1
    
    async def _log_error(self, error_info: ErrorInfo):
        """记录错误日志"""
        log_message = f"[{error_info.error_id}] {error_info.message}"
        
        if error_info.error_level == ErrorLevel.DEBUG:
            logger.debug(log_message)
        elif error_info.error_level == ErrorLevel.INFO:
            logger.info(log_message)
        elif error_info.error_level == ErrorLevel.WARNING:
            logger.warning(log_message)
        elif error_info.error_level == ErrorLevel.ERROR:
            logger.error(log_message)
        elif error_info.error_level == ErrorLevel.CRITICAL:
            logger.critical(log_message)
        
        # 记录详细信息
        if error_info.traceback:
            logger.error(f"错误堆栈:\n{error_info.traceback}")
    
    async def _check_alert_conditions(self, error_info: ErrorInfo):
        """检查告警条件"""
        if not self.monitoring_enabled:
            return
        
        level_key = f"level_{error_info.error_level.value}"
        current_count = self.error_counts[level_key]
        threshold = self.alert_thresholds.get(error_info.error_level, float('inf'))
        
        if current_count >= threshold:
            await self._send_alert(error_info, current_count)
    
    async def _send_alert(self, error_info: ErrorInfo, count: int):
        """发送告警"""
        alert_message = f"错误告警: {error_info.error_level.value}级别错误已达到{count}次"
        logger.warning(f"[ALERT] {alert_message}")
        
        # 这里可以集成其他告警渠道，如邮件、短信、Slack等
        # await self._send_email_alert(error_info, count)
        # await self._send_slack_alert(error_info, count)
    
    async def _attempt_error_recovery(self, error_info: ErrorInfo) -> Optional[Dict[str, Any]]:
        """尝试错误恢复"""
        strategy = self.recovery_strategies.get(error_info.error_code)
        if strategy:
            try:
                return await strategy(error_info)
            except Exception as e:
                logger.warning(f"错误恢复策略执行失败: {str(e)}")
        
        return None
    
    def _parse_time_range(self, time_range: str) -> timedelta:
        """解析时间范围"""
        if time_range == "1h":
            return timedelta(hours=1)
        elif time_range == "6h":
            return timedelta(hours=6)
        elif time_range == "1d":
            return timedelta(days=1)
        elif time_range == "1w":
            return timedelta(weeks=1)
        else:
            return timedelta(hours=1)
    
    def _calculate_health_score(self, stats: ErrorStatistics) -> float:
        """计算健康评分"""
        if stats.total_errors == 0:
            return 100.0
        
        # 根据错误级别加权计算
        critical_weight = 10
        error_weight = 3
        warning_weight = 1
        
        critical_count = stats.error_by_level.get("critical", 0)
        error_count = stats.error_by_level.get("error", 0) 
        warning_count = stats.error_by_level.get("warning", 0)
        
        weighted_score = (
            critical_count * critical_weight +
            error_count * error_weight +
            warning_count * warning_weight
        )
        
        # 转换为0-100分
        max_score = stats.total_errors * critical_weight
        if max_score == 0:
            return 100.0
        
        health_score = max(0, 100 - (weighted_score / max_score) * 100)
        
        return round(health_score, 2)
    
    def _identify_major_issues(self, stats: ErrorStatistics) -> List[str]:
        """识别主要问题"""
        issues = []
        
        if stats.error_by_level.get("critical", 0) > 0:
            issues.append("检测到严重错误")
        
        if stats.error_by_level.get("error", 0) > 10:
            issues.append("错误数量过多")
        
        # 检查特定错误代码
        for code, count in stats.error_by_code.items():
            if count > 5:
                issues.append(f"频繁出现错误: {code}")
        
        return issues


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    def __init__(self, app, error_handler: ErrorHandler):
        super().__init__(app)
        self.error_handler = error_handler
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as error:
            return await self.error_handler.handle_error(error, request)


# 全局错误处理器实例
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """获取错误处理器实例
    
    Returns:
        ErrorHandler: 错误处理器实例
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# 导出主要类和函数
__all__ = [
    "ErrorHandler",
    "ErrorHandlerMiddleware",
    "ErrorInfo",
    "ErrorStatistics",
    "CustomException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "BusinessLogicError",
    "ExternalServiceError",
    "ErrorLevel",
    "ErrorCategory",
    "ErrorCode",
    "get_error_handler"
]