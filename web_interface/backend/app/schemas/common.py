"""
通用响应和工具模式定义

提供评估分析、系统监控、WebSocket通信等通用功能的数据模式。
这些模式被多个模块共享使用，确保API响应的一致性。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.models.database import EvaluationType, EvaluationStatus, LogLevel


# ==================== 评估分析模式 ====================

class EvaluationBase(BaseSchema):
    """评估任务基础模式"""
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="评估任务名称"
    )
    evaluation_type: EvaluationType = Field(..., description="评估类型")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证评估任务名称"""
        if not v or not v.strip():
            raise ValueError('评估任务名称不能为空')
        return v.strip()


class BacktestConfig(BaseSchema):
    """回测配置模式"""
    start_date: str = Field(..., description="回测开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="回测结束日期 (YYYY-MM-DD)")
    initial_capital: float = Field(100000.0, gt=0, description="初始资金")
    benchmark: Optional[str] = Field(None, description="基准指数")
    transaction_cost: float = Field(0.001, ge=0, le=0.1, description="交易成本比例")
    slippage: float = Field(0.0001, ge=0, le=0.01, description="滑点比例")
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('日期格式必须是 YYYY-MM-DD')


class PerformanceAnalysisConfig(BaseSchema):
    """性能分析配置模式"""
    metrics: List[str] = Field(
        default_factory=lambda: [
            'total_return', 'annual_return', 'sharpe_ratio', 
            'max_drawdown', 'win_rate', 'profit_factor'
        ],
        description="要计算的指标列表"
    )
    benchmark: Optional[str] = Field(None, description="基准指数")
    risk_free_rate: float = Field(0.02, ge=0, le=1, description="无风险利率")
    confidence_level: float = Field(0.95, gt=0, lt=1, description="置信水平")


class RiskAnalysisConfig(BaseSchema):
    """风险分析配置模式"""
    var_confidence: float = Field(0.95, gt=0, lt=1, description="VaR置信水平")
    holding_period: int = Field(1, ge=1, description="持有期(天)")
    monte_carlo_simulations: int = Field(10000, ge=1000, description="蒙特卡洛模拟次数")
    stress_scenarios: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="压力测试场景"
    )


class EvaluationConfig(BaseSchema):
    """评估配置模式"""
    evaluation_type: EvaluationType = Field(..., description="评估类型")
    backtest_config: Optional[BacktestConfig] = Field(None, description="回测配置")
    performance_config: Optional[PerformanceAnalysisConfig] = Field(None, description="性能分析配置")  
    risk_config: Optional[RiskAnalysisConfig] = Field(None, description="风险分析配置")
    
    @field_validator('backtest_config', 'performance_config', 'risk_config')
    @classmethod
    def validate_config_match(cls, v, info):
        """验证配置与评估类型匹配"""
        if not info.data:
            return v
            
        evaluation_type = info.data.get('evaluation_type')
        field_name = info.field_name
        
        if evaluation_type == EvaluationType.BACKTEST and field_name == 'backtest_config':
            if v is None:
                raise ValueError('回测评估需要提供backtest_config')
        elif evaluation_type == EvaluationType.PERFORMANCE and field_name == 'performance_config':
            if v is None:
                raise ValueError('性能评估需要提供performance_config')
        elif evaluation_type == EvaluationType.RISK and field_name == 'risk_config':
            if v is None:
                raise ValueError('风险评估需要提供risk_config')
        
        return v


class EvaluationCreate(EvaluationBase):
    """评估任务创建模式"""
    strategy_id: int = Field(..., description="关联策略ID")
    dataset_id: Optional[int] = Field(None, description="数据集ID")
    config: EvaluationConfig = Field(..., description="评估配置")


class EvaluationResponse(BaseSchema):
    """评估任务响应模式"""
    id: int = Field(..., description="评估ID")
    uuid: str = Field(..., description="评估UUID")
    name: str = Field(..., description="评估名称")
    evaluation_type: EvaluationType = Field(..., description="评估类型")
    status: EvaluationStatus = Field(..., description="评估状态")
    
    # 关联信息
    strategy_id: int = Field(..., description="策略ID")
    dataset_id: Optional[int] = Field(None, description="数据集ID")
    user_id: int = Field(..., description="用户ID")
    
    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class EvaluationDetail(EvaluationResponse):
    """评估任务详情模式"""
    config: EvaluationConfig = Field(..., description="评估配置")
    results: Dict[str, Any] = Field(default_factory=dict, description="评估结果")
    report_path: Optional[str] = Field(None, description="报告文件路径")
    charts: List[Dict[str, Any]] = Field(default_factory=list, description="图表数据")


class EvaluationResults(BaseSchema):
    """评估结果模式"""
    # 基本性能指标
    total_return: Optional[float] = Field(None, description="总收益率(%)")
    annual_return: Optional[float] = Field(None, description="年化收益率(%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤(%)")
    win_rate: Optional[float] = Field(None, description="胜率(%)")
    profit_factor: Optional[float] = Field(None, description="盈利因子")
    
    # 风险指标
    volatility: Optional[float] = Field(None, description="波动率(%)")
    var_95: Optional[float] = Field(None, description="95% VaR")
    cvar_95: Optional[float] = Field(None, description="95% CVaR")
    beta: Optional[float] = Field(None, description="贝塔系数")
    
    # 交易统计
    total_trades: Optional[int] = Field(None, description="总交易次数")
    winning_trades: Optional[int] = Field(None, description="盈利交易次数")
    losing_trades: Optional[int] = Field(None, description="亏损交易次数")
    avg_trade_return: Optional[float] = Field(None, description="平均交易收益(%)")
    
    # 自定义指标
    custom_metrics: Dict[str, Any] = Field(default_factory=dict, description="自定义指标")


# ==================== 图表数据模式 ====================

class ChartType(str, Enum):
    """图表类型枚举"""
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    PIE = "pie"
    HEATMAP = "heatmap"
    CANDLESTICK = "candlestick"
    HISTOGRAM = "histogram"


class ChartSeries(BaseSchema):
    """图表数据系列模式"""
    name: str = Field(..., description="系列名称")
    data: List[Union[float, int, List[Union[float, int]]]] = Field(..., description="数据点")
    type: Optional[ChartType] = Field(None, description="图表类型")
    color: Optional[str] = Field(None, description="颜色")


class ChartConfig(BaseSchema):
    """图表配置模式"""
    title: str = Field(..., description="图表标题")
    chart_type: ChartType = Field(..., description="图表类型")
    x_axis_label: Optional[str] = Field(None, description="X轴标签")
    y_axis_label: Optional[str] = Field(None, description="Y轴标签")
    series: List[ChartSeries] = Field(..., description="数据系列")
    
    # 样式配置
    width: Optional[int] = Field(None, description="图表宽度")
    height: Optional[int] = Field(None, description="图表高度")
    show_legend: bool = Field(True, description="是否显示图例")
    show_grid: bool = Field(True, description="是否显示网格")
    
    # 交互配置
    enable_zoom: bool = Field(False, description="是否启用缩放")
    enable_pan: bool = Field(False, description="是否启用平移")
    enable_tooltip: bool = Field(True, description="是否启用工具提示")


# ==================== 系统监控模式 ====================

class SystemMetrics(BaseSchema):
    """系统指标模式"""
    # CPU和内存
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU使用率(%)")
    memory_usage: float = Field(..., ge=0, le=100, description="内存使用率(%)")
    disk_usage: float = Field(..., ge=0, le=100, description="磁盘使用率(%)")
    
    # 网络
    network_in: float = Field(..., ge=0, description="网络入流量(MB/s)")
    network_out: float = Field(..., ge=0, description="网络出流量(MB/s)")
    
    # 数据库
    db_connections: int = Field(..., ge=0, description="数据库连接数")
    db_query_time: float = Field(..., ge=0, description="数据库查询时间(ms)")
    
    # 缓存
    cache_hit_rate: float = Field(..., ge=0, le=100, description="缓存命中率(%)")
    cache_memory_usage: float = Field(..., ge=0, description="缓存内存使用(MB)")
    
    # 任务队列
    pending_tasks: int = Field(..., ge=0, description="待处理任务数")
    active_workers: int = Field(..., ge=0, description="活跃工作进程数")
    
    # 时间戳
    timestamp: datetime = Field(..., description="采集时间")


class AlertRule(BaseSchema):
    """告警规则模式"""
    name: str = Field(..., description="规则名称")
    metric: str = Field(..., description="监控指标")
    operator: str = Field(..., description="比较操作符 (>, <, >=, <=, ==)")
    threshold: float = Field(..., description="阈值")
    duration: int = Field(300, ge=60, description="持续时间(秒)")
    severity: str = Field(..., description="严重级别 (low, medium, high, critical)")
    enabled: bool = Field(True, description="是否启用")
    
    @field_validator('operator')
    @classmethod
    def validate_operator(cls, v):
        """验证比较操作符"""
        allowed_operators = ['>', '<', '>=', '<=', '==', '!=']
        if v not in allowed_operators:
            raise ValueError(f'操作符必须是: {", ".join(allowed_operators)}')
        return v
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        """验证严重级别"""
        allowed_severities = ['low', 'medium', 'high', 'critical']
        if v not in allowed_severities:
            raise ValueError(f'严重级别必须是: {", ".join(allowed_severities)}')
        return v


class Alert(BaseSchema):
    """告警信息模式"""
    id: int = Field(..., description="告警ID")
    rule_name: str = Field(..., description="规则名称")
    message: str = Field(..., description="告警消息")
    severity: str = Field(..., description="严重级别")
    status: str = Field(..., description="告警状态 (active, resolved)")
    
    # 时间信息
    triggered_at: datetime = Field(..., description="触发时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    
    # 额外信息
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


# ==================== 系统日志模式 ====================

class LogEntry(BaseSchema):
    """日志条目模式"""
    level: LogLevel = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    module: Optional[str] = Field(None, description="模块名称")
    function_name: Optional[str] = Field(None, description="函数名称")
    
    # 上下文信息
    user_id: Optional[int] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    # 额外数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    # 时间戳
    timestamp: datetime = Field(..., description="时间戳")


class LogQuery(BaseSchema):
    """日志查询模式"""
    level: Optional[LogLevel] = Field(None, description="日志级别筛选")
    module: Optional[str] = Field(None, description="模块筛选")
    user_id: Optional[int] = Field(None, description="用户筛选")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    search: Optional[str] = Field(None, description="搜索关键词")
    limit: int = Field(100, ge=1, le=1000, description="返回条数限制")


# ==================== WebSocket通信模式 ====================

class WebSocketEventType(str, Enum):
    """WebSocket事件类型枚举"""
    # 连接事件
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # 订阅事件
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    
    # 数据推送
    TRAINING_PROGRESS = "training_progress"
    EVALUATION_PROGRESS = "evaluation_progress"
    STRATEGY_STATUS = "strategy_status"
    SYSTEM_ALERT = "system_alert"
    
    # 通知事件
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"


class WebSocketEvent(BaseSchema):
    """WebSocket事件模式"""
    type: WebSocketEventType = Field(..., description="事件类型")
    data: Optional[Dict[str, Any]] = Field(None, description="事件数据")
    timestamp: datetime = Field(..., description="事件时间戳")
    event_id: Optional[str] = Field(None, description="事件ID")
    user_id: Optional[int] = Field(None, description="目标用户ID")
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def set_timestamp(cls, v):
        """自动设置时间戳"""
        if v is None:
            return datetime.utcnow()
        return v


class SubscribeRequest(BaseSchema):
    """订阅请求模式"""
    channel: str = Field(..., description="订阅频道")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    
    @field_validator('channel')
    @classmethod
    def validate_channel(cls, v):
        """验证频道名称"""
        allowed_channels = [
            'training_jobs', 'evaluations', 'strategies',
            'system_alerts', 'notifications', 'global'
        ]
        if v not in allowed_channels:
            raise ValueError(f'频道必须是: {", ".join(allowed_channels)}')
        return v


class UnsubscribeRequest(BaseSchema):
    """取消订阅请求模式"""
    channel: str = Field(..., description="取消订阅的频道")


class NotificationMessage(BaseSchema):
    """通知消息模式"""
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    level: str = Field("info", description="通知级别")
    category: Optional[str] = Field(None, description="通知分类")
    actions: Optional[List[Dict[str, str]]] = Field(None, description="操作按钮")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        """验证通知级别"""
        allowed_levels = ['info', 'success', 'warning', 'error']
        if v not in allowed_levels:
            raise ValueError(f'通知级别必须是: {", ".join(allowed_levels)}')
        return v


# ==================== 导出和导入模式 ====================

class ExportRequest(BaseSchema):
    """导出请求模式"""
    resource_type: str = Field(..., description="资源类型")
    resource_ids: List[int] = Field(..., description="资源ID列表")
    format: str = Field("json", description="导出格式")
    include_metadata: bool = Field(True, description="是否包含元数据")
    
    @field_validator('resource_type')
    @classmethod
    def validate_resource_type(cls, v):
        """验证资源类型"""
        allowed_types = ['strategies', 'datasets', 'training_jobs', 'evaluations']
        if v not in allowed_types:
            raise ValueError(f'资源类型必须是: {", ".join(allowed_types)}')
        return v
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """验证导出格式"""
        allowed_formats = ['json', 'csv', 'xlsx']
        if v not in allowed_formats:
            raise ValueError(f'导出格式必须是: {", ".join(allowed_formats)}')
        return v


class ExportResponse(BaseSchema):
    """导出响应模式"""
    task_id: str = Field(..., description="导出任务ID")
    resource_type: str = Field(..., description="资源类型")
    resource_count: int = Field(..., description="资源数量")
    format: str = Field(..., description="导出格式")
    estimated_size: Optional[int] = Field(None, description="预计文件大小")
    download_url: Optional[str] = Field(None, description="下载链接")


class ImportRequest(BaseSchema):
    """导入请求模式"""
    resource_type: str = Field(..., description="资源类型")
    file_path: str = Field(..., description="导入文件路径")
    conflict_resolution: str = Field("skip", description="冲突解决策略")
    validate_only: bool = Field(False, description="是否仅验证不导入")
    
    @field_validator('conflict_resolution')
    @classmethod
    def validate_conflict_resolution(cls, v):
        """验证冲突解决策略"""
        allowed_strategies = ['skip', 'overwrite', 'rename']
        if v not in allowed_strategies:
            raise ValueError(f'冲突解决策略必须是: {", ".join(allowed_strategies)}')
        return v


class ImportResponse(BaseSchema):
    """导入响应模式"""
    task_id: str = Field(..., description="导入任务ID")
    resource_type: str = Field(..., description="资源类型")
    total_records: int = Field(..., description="总记录数")
    imported_count: int = Field(0, description="已导入数量")
    skipped_count: int = Field(0, description="跳过数量")
    error_count: int = Field(0, description="错误数量")
    errors: List[str] = Field(default_factory=list, description="错误列表")


# 导出主要组件
__all__ = [
    # 评估模式
    "EvaluationBase", "BacktestConfig", "PerformanceAnalysisConfig", "RiskAnalysisConfig",
    "EvaluationConfig", "EvaluationCreate", "EvaluationResponse", "EvaluationDetail", "EvaluationResults",
    
    # 图表模式
    "ChartType", "ChartSeries", "ChartConfig",
    
    # 监控模式
    "SystemMetrics", "AlertRule", "Alert",
    
    # 日志模式
    "LogEntry", "LogQuery",
    
    # WebSocket模式
    "WebSocketEventType", "WebSocketEvent", "SubscribeRequest", "UnsubscribeRequest", "NotificationMessage",
    
    # 导入导出模式
    "ExportRequest", "ExportResponse", "ImportRequest", "ImportResponse"
]