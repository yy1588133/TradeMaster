"""
Pydantic模式模块

包含所有的数据验证和序列化模式定义。
"""

# 导入基础模式
from .base import (
    # 基础模式
    BaseSchema, TimestampSchema, UUIDSchema,
    
    # 响应模式
    BaseResponse, SuccessResponse, ErrorResponse,
    ErrorDetail, ErrorInfo,
    
    # 分页模式
    PaginationParams, PaginationInfo, PaginatedData, PaginatedResponse,
    
    # 查询模式
    SortOrder, SortField, QueryParams,
    
    # 操作结果模式
    OperationResult, BulkOperationResult,
    
    # 状态模式
    StatusUpdate, ProgressUpdate,
    
    # 文件模式
    FileInfo, UploadResponse,
    
    # 健康检查模式
    HealthStatus, DatabaseHealth, SystemInfo,
    
    # WebSocket模式
    WebSocketMessage, SubscriptionMessage, UnsubscriptionMessage, NotificationMessage,
    
    # 工具函数
    create_response, create_error_response, create_paginated_response
)

# 导入用户相关模式
from .user import (
    # 基础模式
    UserBase, UserCreate, UserUpdate, UserPasswordUpdate,
    
    # 响应模式
    UserInDB, UserResponse, UserProfile, UserSummary,
    
    # 认证模式
    LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse, LogoutRequest,
    
    # 邮箱验证模式
    EmailVerificationRequest, EmailVerificationConfirm,
    PasswordResetRequest, PasswordResetConfirm,
    
    # 管理模式
    UserAdminUpdate, UserListQuery, UserStats,
    
    # 活动模式
    UserActivity, UserActivityQuery,
    
    # 设置模式
    UserSettings
)

# 导入策略相关模式
from .strategy import (
    # 基础模式
    StrategyBase, StrategyCreate, StrategyUpdate,
    
    # 响应模式
    StrategyInDB, StrategyResponse, StrategyDetail, StrategySummary,
    
    # 性能模式
    StrategyPerformance, StrategyPerformanceUpdate,
    
    # 版本模式
    StrategyVersionBase, StrategyVersionCreate, StrategyVersionResponse,
    
    # 操作模式
    StrategyStatusUpdate, StrategyCloneRequest,
    StrategyCompareRequest, StrategyCompareResponse,
    
    # 查询模式
    StrategyListQuery,
    
    # 配置验证模式
    StrategyConfigValidation, StrategyConfigValidationResponse,
    
    # 统计模式
    StrategyStats
)

# 导入数据集相关模式
from .dataset import (
    # 枚举
    DatasetFileType, DataProcessingOperation, FillMethod, NormalizationMethod,
    
    # 基础模式
    DatasetBase, DatasetCreate, DatasetUpdate,
    
    # 响应模式
    DatasetInDB, DatasetResponse, DatasetDetail, DatasetSummary,
    ColumnInfo, DatasetStatistics,
    
    # 上传模式
    FileUploadRequest, FileUploadResponse, UploadProgress,
    
    # 预处理模式
    PreprocessingOperation, PreprocessingRequest, PreprocessingResponse, PreprocessingProgress,
    
    # 查询和分析模式
    DatasetListQuery, DataSampleRequest, DataSampleResponse,
    ColumnAnalysisRequest, ColumnAnalysisResponse,
    
    # 导出模式
    DataExportRequest, DataExportResponse,
    
    # 统计模式
    DatasetStats
)

# 导入训练任务相关模式
from .training import (
    # 枚举
    TrainingTaskType, AgentType, OptimizerType, LossType, MetricType,
    
    # 基础模式
    TrainingJobBase, TrainingConfig, HyperParameters,
    TrainingJobCreate, TrainingJobUpdate,
    
    # 响应模式
    TrainingJobInDB, TrainingJobResponse, TrainingJobDetail, TrainingJobSummary,
    
    # 指标模式
    TrainingMetrics, TrainingMetricHistory, MetricsQuery,
    
    # 资源模式
    ResourceUsage, ResourceMonitoring,
    
    # 操作模式
    TrainingJobStart, TrainingJobStop, TrainingJobPause, TrainingJobResume, TrainingJobClone,
    
    # 查询模式
    TrainingJobListQuery,
    
    # 统计模式
    TrainingJobStats,
    
    # TradeMaster集成模式
    TradeMasterSession, TradeMasterLog
)

# 导入通用模式
from .common import (
    # 评估模式
    EvaluationBase, BacktestConfig, PerformanceAnalysisConfig, RiskAnalysisConfig,
    EvaluationConfig, EvaluationCreate, EvaluationResponse, EvaluationDetail, EvaluationResults,
    
    # 图表模式
    ChartType, ChartSeries, ChartConfig,
    
    # 监控模式
    SystemMetrics, AlertRule, Alert,
    
    # 日志模式
    LogEntry, LogQuery,
    
    # WebSocket模式
    WebSocketEventType, WebSocketEvent, SubscribeRequest, UnsubscribeRequest,
    
    # 导入导出模式
    ExportRequest, ExportResponse, ImportRequest, ImportResponse
)

# 导出所有模式
__all__ = [
    # 基础模式
    "BaseSchema", "TimestampSchema", "UUIDSchema",
    "BaseResponse", "SuccessResponse", "ErrorResponse", "ErrorDetail", "ErrorInfo",
    "PaginationParams", "PaginationInfo", "PaginatedData", "PaginatedResponse",
    "SortOrder", "SortField", "QueryParams",
    "OperationResult", "BulkOperationResult",
    "StatusUpdate", "ProgressUpdate",
    "FileInfo", "UploadResponse",
    "HealthStatus", "DatabaseHealth", "SystemInfo",
    "WebSocketMessage", "SubscriptionMessage", "UnsubscriptionMessage", "NotificationMessage",
    "create_response", "create_error_response", "create_paginated_response",
    
    # 用户模式
    "UserBase", "UserCreate", "UserUpdate", "UserPasswordUpdate",
    "UserInDB", "UserResponse", "UserProfile", "UserSummary",
    "LoginRequest", "LoginResponse", "RefreshTokenRequest", "RefreshTokenResponse", "LogoutRequest",
    "EmailVerificationRequest", "EmailVerificationConfirm", "PasswordResetRequest", "PasswordResetConfirm",
    "UserAdminUpdate", "UserListQuery", "UserStats",
    "UserActivity", "UserActivityQuery", "UserSettings",
    
    # 策略模式
    "StrategyBase", "StrategyCreate", "StrategyUpdate",
    "StrategyInDB", "StrategyResponse", "StrategyDetail", "StrategySummary",
    "StrategyPerformance", "StrategyPerformanceUpdate",
    "StrategyVersionBase", "StrategyVersionCreate", "StrategyVersionResponse",
    "StrategyStatusUpdate", "StrategyCloneRequest", "StrategyCompareRequest", "StrategyCompareResponse",
    "StrategyListQuery", "StrategyConfigValidation", "StrategyConfigValidationResponse", "StrategyStats",
    
    # 数据集模式
    "DatasetFileType", "DataProcessingOperation", "FillMethod", "NormalizationMethod",
    "DatasetBase", "DatasetCreate", "DatasetUpdate",
    "DatasetInDB", "DatasetResponse", "DatasetDetail", "DatasetSummary", "ColumnInfo", "DatasetStatistics",
    "FileUploadRequest", "FileUploadResponse", "UploadProgress",
    "PreprocessingOperation", "PreprocessingRequest", "PreprocessingResponse", "PreprocessingProgress",
    "DatasetListQuery", "DataSampleRequest", "DataSampleResponse",
    "ColumnAnalysisRequest", "ColumnAnalysisResponse",
    "DataExportRequest", "DataExportResponse", "DatasetStats",
    
    # 训练任务模式
    "TrainingTaskType", "AgentType", "OptimizerType", "LossType", "MetricType",
    "TrainingJobBase", "TrainingConfig", "HyperParameters",
    "TrainingJobCreate", "TrainingJobUpdate",
    "TrainingJobInDB", "TrainingJobResponse", "TrainingJobDetail", "TrainingJobSummary",
    "TrainingMetrics", "TrainingMetricHistory", "MetricsQuery",
    "ResourceUsage", "ResourceMonitoring",
    "TrainingJobStart", "TrainingJobStop", "TrainingJobPause", "TrainingJobResume", "TrainingJobClone",
    "TrainingJobListQuery", "TrainingJobStats",
    "TradeMasterSession", "TradeMasterLog",
    
    # 通用模式
    "EvaluationBase", "BacktestConfig", "PerformanceAnalysisConfig", "RiskAnalysisConfig",
    "EvaluationConfig", "EvaluationCreate", "EvaluationResponse", "EvaluationDetail", "EvaluationResults",
    "ChartType", "ChartSeries", "ChartConfig",
    "SystemMetrics", "AlertRule", "Alert",
    "LogEntry", "LogQuery",
    "WebSocketEventType", "WebSocketEvent", "SubscribeRequest", "UnsubscribeRequest",
    "ExportRequest", "ExportResponse", "ImportRequest", "ImportResponse"
]