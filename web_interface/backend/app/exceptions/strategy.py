"""
策略管理相关异常类

定义策略管理过程中可能出现的各种异常，提供详细的错误信息和处理建议。
支持异常分类、错误码和国际化消息。
"""

from typing import Dict, Any, Optional, List
from enum import Enum


class StrategyErrorCode(str, Enum):
    """策略错误码枚举"""
    # 通用错误 1000-1099
    STRATEGY_NOT_FOUND = "STRATEGY_E1001"
    STRATEGY_ACCESS_DENIED = "STRATEGY_E1002"
    STRATEGY_ALREADY_EXISTS = "STRATEGY_E1003"
    
    # 配置相关错误 1100-1199
    INVALID_CONFIG = "STRATEGY_E1101"
    MISSING_REQUIRED_CONFIG = "STRATEGY_E1102"
    CONFIG_VALIDATION_FAILED = "STRATEGY_E1103"
    INCOMPATIBLE_CONFIG = "STRATEGY_E1104"
    
    # 状态相关错误 1200-1299
    INVALID_STATUS_TRANSITION = "STRATEGY_E1201"
    STRATEGY_ALREADY_RUNNING = "STRATEGY_E1202"
    STRATEGY_NOT_RUNNING = "STRATEGY_E1203"
    STRATEGY_IN_ERROR_STATE = "STRATEGY_E1204"
    
    # 执行相关错误 1300-1399
    EXECUTION_FAILED = "STRATEGY_E1301"
    INSUFFICIENT_RESOURCES = "STRATEGY_E1302"
    EXECUTION_TIMEOUT = "STRATEGY_E1303"
    EXECUTION_CANCELLED = "STRATEGY_E1304"
    
    # 数据相关错误 1400-1499
    INVALID_DATA_FORMAT = "STRATEGY_E1401"
    DATA_NOT_AVAILABLE = "STRATEGY_E1402"
    DATA_CORRUPTED = "STRATEGY_E1403"
    
    # 版本相关错误 1500-1599
    VERSION_NOT_FOUND = "STRATEGY_E1501"
    VERSION_CONFLICT = "STRATEGY_E1502"
    INVALID_VERSION_FORMAT = "STRATEGY_E1503"
    
    # TradeMaster集成错误 1600-1699
    TRADEMASTER_CONNECTION_FAILED = "STRATEGY_E1601"
    TRADEMASTER_API_ERROR = "STRATEGY_E1602"
    TRADEMASTER_CONFIG_ERROR = "STRATEGY_E1603"
    
    # 权限相关错误 1700-1799
    INSUFFICIENT_PERMISSIONS = "STRATEGY_E1701"
    QUOTA_EXCEEDED = "STRATEGY_E1702"
    RESOURCE_LOCKED = "STRATEGY_E1703"


class StrategyException(Exception):
    """策略管理基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: StrategyErrorCode,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        recovery_actions: Optional[List[str]] = None
    ):
        """初始化策略异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 错误详情
            suggestions: 解决建议
            recovery_actions: 恢复操作
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.suggestions = suggestions or []
        self.recovery_actions = recovery_actions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
            "recovery_actions": self.recovery_actions
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"


class StrategyNotFoundError(StrategyException):
    """策略不存在异常"""
    
    def __init__(
        self,
        strategy_id: Optional[int] = None,
        strategy_name: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        identifier = strategy_id or strategy_name or "未知"
        message = f"策略不存在: {identifier}"
        
        details = {}
        if strategy_id:
            details["strategy_id"] = strategy_id
        if strategy_name:
            details["strategy_name"] = strategy_name
        if user_id:
            details["user_id"] = user_id
        
        suggestions = [
            "检查策略ID是否正确",
            "确认策略是否已被删除",
            "验证用户是否有访问权限"
        ]
        
        recovery_actions = [
            "重新查询策略列表",
            "联系策略创建者确认状态"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.STRATEGY_NOT_FOUND,
            details=details,
            suggestions=suggestions,
            recovery_actions=recovery_actions
        )


class StrategyAccessDeniedError(StrategyException):
    """策略访问被拒绝异常"""
    
    def __init__(
        self,
        strategy_id: int,
        user_id: int,
        required_permission: Optional[str] = None
    ):
        message = f"无权限访问策略: {strategy_id}"
        if required_permission:
            message += f"，需要权限: {required_permission}"
        
        details = {
            "strategy_id": strategy_id,
            "user_id": user_id,
            "required_permission": required_permission
        }
        
        suggestions = [
            "联系策略所有者获取权限",
            "检查用户角色配置",
            "确认策略是否为公开策略"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.STRATEGY_ACCESS_DENIED,
            details=details,
            suggestions=suggestions
        )


class StrategyConfigValidationError(StrategyException):
    """策略配置验证异常"""
    
    def __init__(
        self,
        validation_errors: List[str],
        config: Optional[Dict[str, Any]] = None
    ):
        message = f"策略配置验证失败: {'; '.join(validation_errors)}"
        
        details = {
            "validation_errors": validation_errors,
            "config": config
        }
        
        suggestions = [
            "检查必需配置项是否完整",
            "验证配置值的类型和范围",
            "参考策略模板修正配置",
            "使用配置验证API检查配置"
        ]
        
        recovery_actions = [
            "修正配置中的错误项",
            "使用推荐的默认值",
            "查看配置文档和示例"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.CONFIG_VALIDATION_FAILED,
            details=details,
            suggestions=suggestions,
            recovery_actions=recovery_actions
        )


class StrategyStatusError(StrategyException):
    """策略状态异常"""
    
    def __init__(
        self,
        current_status: str,
        attempted_action: str,
        allowed_statuses: Optional[List[str]] = None
    ):
        message = f"策略状态错误: 当前状态 '{current_status}' 不允许执行操作 '{attempted_action}'"
        if allowed_statuses:
            message += f"，允许的状态: {', '.join(allowed_statuses)}"
        
        details = {
            "current_status": current_status,
            "attempted_action": attempted_action,
            "allowed_statuses": allowed_statuses
        }
        
        suggestions = [
            "等待策略状态改变",
            "停止正在运行的策略",
            "检查策略执行日志"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.INVALID_STATUS_TRANSITION,
            details=details,
            suggestions=suggestions
        )


class StrategyExecutionError(StrategyException):
    """策略执行异常"""
    
    def __init__(
        self,
        strategy_id: int,
        execution_id: Optional[str] = None,
        error_details: Optional[str] = None,
        trademaster_error: Optional[str] = None
    ):
        message = f"策略执行失败: {strategy_id}"
        if error_details:
            message += f" - {error_details}"
        
        details = {
            "strategy_id": strategy_id,
            "execution_id": execution_id,
            "error_details": error_details,
            "trademaster_error": trademaster_error
        }
        
        suggestions = [
            "检查策略配置是否正确",
            "验证数据源是否可用",
            "查看执行日志了解详细错误",
            "检查系统资源使用情况"
        ]
        
        recovery_actions = [
            "修正配置后重新执行",
            "重启TradeMaster服务",
            "联系系统管理员"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.EXECUTION_FAILED,
            details=details,
            suggestions=suggestions,
            recovery_actions=recovery_actions
        )


class StrategyDataError(StrategyException):
    """策略数据异常"""
    
    def __init__(
        self,
        data_type: str,
        error_message: str,
        data_source: Optional[str] = None
    ):
        message = f"策略数据错误 ({data_type}): {error_message}"
        if data_source:
            message += f" - 数据源: {data_source}"
        
        details = {
            "data_type": data_type,
            "error_message": error_message,
            "data_source": data_source
        }
        
        suggestions = [
            "检查数据源连接",
            "验证数据格式",
            "确认数据时间范围",
            "使用备用数据源"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.INVALID_DATA_FORMAT,
            details=details,
            suggestions=suggestions
        )


class StrategyVersionError(StrategyException):
    """策略版本异常"""
    
    def __init__(
        self,
        strategy_id: int,
        version: str,
        operation: str,
        error_reason: str
    ):
        message = f"策略版本操作失败: 策略 {strategy_id}, 版本 {version}, 操作 {operation} - {error_reason}"
        
        details = {
            "strategy_id": strategy_id,
            "version": version,
            "operation": operation,
            "error_reason": error_reason
        }
        
        suggestions = [
            "检查版本号格式",
            "确认版本是否已存在",
            "验证版本配置完整性"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.VERSION_CONFLICT,
            details=details,
            suggestions=suggestions
        )


class TradeMasterIntegrationError(StrategyException):
    """TradeMaster集成异常"""
    
    def __init__(
        self,
        operation: str,
        tm_error: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        message = f"TradeMaster集成错误: {operation}"
        if tm_error:
            message += f" - {tm_error}"
        if status_code:
            message += f" (状态码: {status_code})"
        
        details = {
            "operation": operation,
            "trademaster_error": tm_error,
            "status_code": status_code
        }
        
        suggestions = [
            "检查TradeMaster服务状态",
            "验证API接口配置",
            "确认网络连接",
            "查看TradeMaster日志"
        ]
        
        recovery_actions = [
            "重启TradeMaster服务",
            "检查服务配置文件",
            "更新API凭证"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.TRADEMASTER_API_ERROR,
            details=details,
            suggestions=suggestions,
            recovery_actions=recovery_actions
        )


class StrategyQuotaExceededError(StrategyException):
    """策略配额超限异常"""
    
    def __init__(
        self,
        resource_type: str,
        current_usage: int,
        quota_limit: int,
        user_id: int
    ):
        message = f"策略配额超限: {resource_type} 使用量 {current_usage} 超过限制 {quota_limit}"
        
        details = {
            "resource_type": resource_type,
            "current_usage": current_usage,
            "quota_limit": quota_limit,
            "user_id": user_id
        }
        
        suggestions = [
            "删除不需要的策略",
            "升级账户获得更多配额",
            "优化策略资源使用",
            "联系管理员增加配额"
        ]
        
        super().__init__(
            message=message,
            error_code=StrategyErrorCode.QUOTA_EXCEEDED,
            details=details,
            suggestions=suggestions
        )


# 异常工厂函数
def create_strategy_exception(
    error_type: str,
    **kwargs
) -> StrategyException:
    """创建策略异常的工厂函数
    
    Args:
        error_type: 异常类型
        **kwargs: 异常参数
        
    Returns:
        StrategyException: 对应的异常实例
    """
    exception_mapping = {
        "not_found": StrategyNotFoundError,
        "access_denied": StrategyAccessDeniedError,
        "config_validation": StrategyConfigValidationError,
        "status_error": StrategyStatusError,
        "execution_error": StrategyExecutionError,
        "data_error": StrategyDataError,
        "version_error": StrategyVersionError,
        "trademaster_error": TradeMasterIntegrationError,
        "quota_exceeded": StrategyQuotaExceededError
    }
    
    exception_class = exception_mapping.get(error_type, StrategyException)
    return exception_class(**kwargs)


# 异常处理装饰器
def handle_strategy_exceptions(func):
    """策略异常处理装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except StrategyException:
            # 策略异常直接抛出
            raise
        except Exception as e:
            # 其他异常转换为策略异常
            raise StrategyException(
                message=f"未知策略错误: {str(e)}",
                error_code=StrategyErrorCode.EXECUTION_FAILED,
                details={"original_error": str(e)}
            )
    return wrapper


# 导出所有异常类
__all__ = [
    "StrategyErrorCode",
    "StrategyException",
    "StrategyNotFoundError",
    "StrategyAccessDeniedError", 
    "StrategyConfigValidationError",
    "StrategyStatusError",
    "StrategyExecutionError",
    "StrategyDataError",
    "StrategyVersionError",
    "TradeMasterIntegrationError",
    "StrategyQuotaExceededError",
    "create_strategy_exception",
    "handle_strategy_exceptions"
]