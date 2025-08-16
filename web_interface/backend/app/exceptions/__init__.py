"""
异常模块初始化

导出所有自定义异常，提供统一的异常处理接口。
"""

from .strategy import (
    StrategyErrorCode,
    StrategyException,
    StrategyNotFoundError,
    StrategyAccessDeniedError,
    StrategyConfigValidationError,
    StrategyStatusError,
    StrategyExecutionError,
    StrategyDataError,
    StrategyVersionError,
    TradeMasterIntegrationError,
    StrategyQuotaExceededError,
    create_strategy_exception,
    handle_strategy_exceptions
)

__all__ = [
    # 策略异常
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