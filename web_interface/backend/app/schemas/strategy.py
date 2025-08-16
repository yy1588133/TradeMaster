"""
策略相关的Pydantic模式定义

提供量化交易策略管理相关的数据验证和序列化模式，包括策略创建、
配置、版本管理、性能评估等功能的API数据模式。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.models.database import StrategyType, StrategyStatus


# ==================== 策略基础模式 ====================

class StrategyBase(BaseSchema):
    """策略基础信息模式"""
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="策略名称"
    )
    description: Optional[str] = Field(None, description="策略描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    category: Optional[str] = Field(None, max_length=50, description="策略分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证策略名称"""
        if not v or not v.strip():
            raise ValueError('策略名称不能为空')
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """验证标签列表"""
        if v:
            # 去重并限制数量
            unique_tags = list(set(tag.strip() for tag in v if tag.strip()))
            if len(unique_tags) > 10:
                raise ValueError('标签数量不能超过10个')
            return unique_tags
        return []


class StrategyCreate(StrategyBase):
    """策略创建模式"""
    config: Dict[str, Any] = Field(default_factory=dict, description="策略配置")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    parent_strategy_id: Optional[int] = Field(None, description="父策略ID")
    
    @field_validator('config')
    @classmethod
    def validate_config(cls, v):
        """验证策略配置"""
        if not isinstance(v, dict):
            raise ValueError('策略配置必须是字典格式')
        
        # 验证基本结构
        if 'task_name' not in v:
            raise ValueError('策略配置必须包含task_name字段')
        
        return v


class StrategyUpdate(BaseSchema):
    """策略更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    category: Optional[str] = Field(None, max_length=50, description="策略分类")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    config: Optional[Dict[str, Any]] = Field(None, description="策略配置")
    parameters: Optional[Dict[str, Any]] = Field(None, description="策略参数")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证策略名称"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('策略名称不能为空')
            return v.strip()
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """验证标签列表"""
        if v is not None:
            unique_tags = list(set(tag.strip() for tag in v if tag.strip()))
            if len(unique_tags) > 10:
                raise ValueError('标签数量不能超过10个')
            return unique_tags
        return v


# ==================== 策略响应模式 ====================

class StrategyInDB(StrategyBase, TimestampSchema, UUIDSchema):
    """数据库中的策略模式"""
    id: int = Field(..., description="策略ID")
    status: StrategyStatus = Field(..., description="策略状态")
    version: str = Field(..., description="版本号")
    config: Dict[str, Any] = Field(..., description="策略配置")
    parameters: Dict[str, Any] = Field(..., description="策略参数")
    
    # 性能指标
    total_return: Optional[float] = Field(None, description="总收益率(%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤(%)")
    win_rate: Optional[float] = Field(None, description="胜率(%)")
    
    # 关联信息
    owner_id: int = Field(..., description="所有者ID")
    parent_strategy_id: Optional[int] = Field(None, description="父策略ID")
    
    # 时间信息
    last_run_at: Optional[datetime] = Field(None, description="最后运行时间")


class StrategyResponse(BaseSchema):
    """策略响应模式"""
    id: int = Field(..., description="策略ID")
    uuid: str = Field(..., description="策略UUID")
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    status: StrategyStatus = Field(..., description="策略状态")
    version: str = Field(..., description="版本号")
    category: Optional[str] = Field(None, description="策略分类")
    tags: List[str] = Field(..., description="标签列表")
    
    # 性能指标
    performance: Optional["StrategyPerformance"] = Field(None, description="性能指标")
    
    # 关联信息
    owner_id: int = Field(..., description="所有者ID")
    parent_strategy_id: Optional[int] = Field(None, description="父策略ID")
    
    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_run_at: Optional[datetime] = Field(None, description="最后运行时间")


class StrategyDetail(StrategyResponse):
    """策略详情模式"""
    config: Dict[str, Any] = Field(..., description="策略配置")
    parameters: Dict[str, Any] = Field(..., description="策略参数")
    
    # 统计信息
    training_jobs_count: int = Field(0, description="训练任务数量")
    evaluations_count: int = Field(0, description="评估任务数量")
    versions_count: int = Field(0, description="版本数量")


class StrategySummary(BaseSchema):
    """策略摘要信息模式"""
    id: int = Field(..., description="策略ID")
    name: str = Field(..., description="策略名称")
    strategy_type: StrategyType = Field(..., description="策略类型")
    status: StrategyStatus = Field(..., description="策略状态")
    total_return: Optional[float] = Field(None, description="总收益率(%)")
    created_at: datetime = Field(..., description="创建时间")


# ==================== 策略性能模式 ====================

class StrategyPerformance(BaseSchema):
    """策略性能指标模式"""
    total_return: Optional[float] = Field(None, description="总收益率(%)")
    annual_return: Optional[float] = Field(None, description="年化收益率(%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤(%)")
    win_rate: Optional[float] = Field(None, description="胜率(%)")
    profit_factor: Optional[float] = Field(None, description="盈利因子")
    calmar_ratio: Optional[float] = Field(None, description="卡尔玛比率")
    sortino_ratio: Optional[float] = Field(None, description="索提诺比率")
    
    # 交易统计
    total_trades: Optional[int] = Field(None, description="总交易次数")
    winning_trades: Optional[int] = Field(None, description="盈利交易次数")
    losing_trades: Optional[int] = Field(None, description="亏损交易次数")
    avg_trade_return: Optional[float] = Field(None, description="平均交易收益(%)")
    
    # 风险指标
    volatility: Optional[float] = Field(None, description="波动率(%)")
    var_95: Optional[float] = Field(None, description="95% VaR")
    cvar_95: Optional[float] = Field(None, description="95% CVaR")
    beta: Optional[float] = Field(None, description="贝塔系数")
    
    @field_validator('total_return', 'annual_return', 'max_drawdown', 'win_rate', mode='before')
    @classmethod
    def validate_percentage_fields(cls, v):
        """验证百分比字段"""
        if v is not None:
            if isinstance(v, str):
                try:
                    v = float(v)
                except ValueError:
                    raise ValueError('无效的数值格式')
            if not isinstance(v, (int, float)):
                raise ValueError('必须是数值类型')
        return v


class StrategyPerformanceUpdate(BaseSchema):
    """策略性能更新模式"""
    total_return: Optional[float] = Field(None, description="总收益率(%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤(%)")
    win_rate: Optional[float] = Field(None, description="胜率(%)")
    
    @field_validator('total_return', 'max_drawdown', 'win_rate', mode='before')
    @classmethod
    def validate_percentage_fields(cls, v):
        """验证百分比字段"""
        if v is not None:
            if isinstance(v, str):
                try:
                    v = float(v)
                except ValueError:
                    raise ValueError('无效的数值格式')
        return v


# ==================== 策略版本模式 ====================

class StrategyVersionBase(BaseSchema):
    """策略版本基础模式"""
    version: str = Field(..., max_length=20, description="版本号")
    changelog: Optional[str] = Field(None, description="变更日志")


class StrategyVersionCreate(StrategyVersionBase):
    """策略版本创建模式"""
    config: Dict[str, Any] = Field(..., description="版本配置")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="版本参数")
    
    @field_validator('version')
    @classmethod
    def validate_version_format(cls, v):
        """验证版本号格式"""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('版本号格式必须是 x.y.z')
        return v


class StrategyVersionResponse(StrategyVersionBase, TimestampSchema):
    """策略版本响应模式"""
    id: int = Field(..., description="版本ID")
    strategy_id: int = Field(..., description="策略ID")
    config: Dict[str, Any] = Field(..., description="版本配置")
    parameters: Dict[str, Any] = Field(..., description="版本参数")
    is_active: bool = Field(..., description="是否为活跃版本")
    created_by: Optional[int] = Field(None, description="创建者ID")


# ==================== 策略操作模式 ====================

class StrategyStatusUpdate(BaseSchema):
    """策略状态更新模式"""
    status: StrategyStatus = Field(..., description="新状态")
    reason: Optional[str] = Field(None, description="状态变更原因")


class StrategyCloneRequest(BaseSchema):
    """策略克隆请求模式"""
    name: str = Field(..., min_length=1, max_length=100, description="新策略名称")
    description: Optional[str] = Field(None, description="新策略描述")
    copy_versions: bool = Field(False, description="是否复制版本历史")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证策略名称"""
        if not v or not v.strip():
            raise ValueError('策略名称不能为空')
        return v.strip()


class StrategyCompareRequest(BaseSchema):
    """策略对比请求模式"""
    strategy_ids: List[int] = Field(..., min_items=2, max_items=5, description="要对比的策略ID列表")
    metrics: List[str] = Field(
        default_factory=lambda: ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate'],
        description="对比指标列表"
    )
    
    @field_validator('strategy_ids')
    @classmethod
    def validate_strategy_ids(cls, v):
        """验证策略ID列表"""
        if len(set(v)) != len(v):
            raise ValueError('策略ID不能重复')
        return v


class StrategyCompareResponse(BaseSchema):
    """策略对比响应模式"""
    strategies: List[StrategySummary] = Field(..., description="策略列表")
    comparison: Dict[str, List[Any]] = Field(..., description="对比数据")
    chart_data: Optional[List[Dict[str, Any]]] = Field(None, description="图表数据")


# ==================== 策略查询模式 ====================

class StrategyListQuery(BaseSchema):
    """策略列表查询模式"""
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    strategy_type: Optional[StrategyType] = Field(None, description="策略类型筛选")
    status: Optional[StrategyStatus] = Field(None, description="状态筛选")
    category: Optional[str] = Field(None, description="分类筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    owner_id: Optional[int] = Field(None, description="所有者筛选")
    min_return: Optional[float] = Field(None, description="最小收益率筛选")
    max_drawdown: Optional[float] = Field(None, description="最大回撤筛选")
    sort: Optional[str] = Field("created_at:desc", description="排序字段")
    
    @field_validator('sort')
    @classmethod
    def validate_sort(cls, v):
        """验证排序参数"""
        if v is None:
            return "created_at:desc"
        
        allowed_fields = [
            'id', 'name', 'strategy_type', 'status', 'total_return',
            'sharpe_ratio', 'max_drawdown', 'win_rate', 'created_at',
            'updated_at', 'last_run_at'
        ]
        
        if ':' in v:
            field, order = v.split(':', 1)
            if field not in allowed_fields:
                raise ValueError(f'排序字段必须是: {", ".join(allowed_fields)}')
            if order.lower() not in ['asc', 'desc']:
                raise ValueError('排序方向必须是 asc 或 desc')
            return f"{field}:{order.lower()}"
        else:
            if v not in allowed_fields:
                raise ValueError(f'排序字段必须是: {", ".join(allowed_fields)}')
            return f"{v}:asc"


# ==================== 策略配置验证模式 ====================

class StrategyConfigValidation(BaseSchema):
    """策略配置验证模式"""
    config: Dict[str, Any] = Field(..., description="待验证的配置")
    strategy_type: StrategyType = Field(..., description="策略类型")
    
    @model_validator(mode='after')
    def validate_config_structure(self):
        """验证配置结构"""
        if not isinstance(self.config, dict):
            raise ValueError('配置必须是字典格式')
        
        if self.strategy_type:
            # 根据策略类型验证必需字段
            required_fields = {
                StrategyType.ALGORITHMIC_TRADING: ['task_name', 'dataset_name', 'agent_name'],
                StrategyType.PORTFOLIO_MANAGEMENT: ['task_name', 'dataset_name', 'agent_name'],
                StrategyType.ORDER_EXECUTION: ['task_name', 'dataset_name', 'agent_name'],
                StrategyType.HIGH_FREQUENCY_TRADING: ['task_name', 'dataset_name', 'agent_name']
            }
            
            required = required_fields.get(self.strategy_type, [])
            missing_fields = [field for field in required if field not in self.config]
            if missing_fields:
                raise ValueError(f'缺少必需字段: {", ".join(missing_fields)}')
        
        return self


class StrategyConfigValidationResponse(BaseSchema):
    """策略配置验证响应模式"""
    is_valid: bool = Field(..., description="配置是否有效")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    suggestions: List[str] = Field(default_factory=list, description="建议列表")


# ==================== 策略统计模式 ====================

class StrategyStats(BaseSchema):
    """策略统计信息模式"""
    total_strategies: int = Field(..., description="总策略数")
    active_strategies: int = Field(..., description="活跃策略数")
    draft_strategies: int = Field(..., description="草稿策略数")
    
    # 按类型分布
    type_distribution: Dict[str, int] = Field(..., description="类型分布")
    
    # 按状态分布
    status_distribution: Dict[str, int] = Field(..., description="状态分布")
    
    # 性能统计
    avg_return: Optional[float] = Field(None, description="平均收益率")
    avg_sharpe_ratio: Optional[float] = Field(None, description="平均夏普比率")
    best_performing: Optional[StrategySummary] = Field(None, description="最佳表现策略")
    
    # 时间趋势
    creation_trend: List[Dict[str, Any]] = Field(..., description="创建趋势")


# 前向引用解决
StrategyResponse.model_rebuild()

# 导出主要组件
__all__ = [
    # 基础模式
    "StrategyBase", "StrategyCreate", "StrategyUpdate",
    
    # 响应模式
    "StrategyInDB", "StrategyResponse", "StrategyDetail", "StrategySummary",
    
    # 性能模式
    "StrategyPerformance", "StrategyPerformanceUpdate",
    
    # 版本模式
    "StrategyVersionBase", "StrategyVersionCreate", "StrategyVersionResponse",
    
    # 操作模式
    "StrategyStatusUpdate", "StrategyCloneRequest", 
    "StrategyCompareRequest", "StrategyCompareResponse",
    
    # 查询模式
    "StrategyListQuery",
    
    # 配置验证模式
    "StrategyConfigValidation", "StrategyConfigValidationResponse",
    
    # 统计模式
    "StrategyStats"
]