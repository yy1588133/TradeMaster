"""
训练任务相关的Pydantic模式定义

提供机器学习模型训练任务管理相关的数据验证和序列化模式，包括任务创建、
进度监控、结果分析、TradeMaster集成等功能的API数据模式。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import Field, field_validator, model_validator, ConfigDict

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.models.database import TrainingStatus


# ==================== 训练相关枚举 ====================

class TrainingTaskType(str, Enum):
    """训练任务类型枚举"""
    ALGORITHMIC_TRADING = "algorithmic_trading"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    ORDER_EXECUTION = "order_execution"
    HIGH_FREQUENCY_TRADING = "high_frequency_trading"


class AgentType(str, Enum):
    """智能体类型枚举"""
    DQN = "dqn"
    DDPG = "ddpg"
    PPO = "ppo"
    SAC = "sac"
    TD3 = "td3"
    A2C = "a2c"


class OptimizerType(str, Enum):
    """优化器类型枚举"""
    ADAM = "adam"
    SGD = "sgd"
    RMSPROP = "rmsprop"
    ADAGRAD = "adagrad"


class LossType(str, Enum):
    """损失函数类型枚举"""
    MSE = "mse"
    MAE = "mae"
    HUBER = "huber"
    CROSS_ENTROPY = "cross_entropy"


class MetricType(str, Enum):
    """评估指标类型枚举"""
    LOSS = "loss"
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    SHARPE_RATIO = "sharpe_ratio"
    TOTAL_RETURN = "total_return"
    MAX_DRAWDOWN = "max_drawdown"


# ==================== 训练任务基础模式 ====================

class TrainingJobBase(BaseSchema):
    """训练任务基础信息模式"""
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="任务名称"
    )
    description: Optional[str] = Field(None, description="任务描述")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证任务名称"""
        if not v or not v.strip():
            raise ValueError('任务名称不能为空')
        return v.strip()


class TrainingConfig(BaseSchema):
    """训练配置模式"""
    # TradeMaster配置
    task_name: str = Field(..., description="TradeMaster任务名称")
    dataset_name: str = Field(..., description="数据集名称")
    agent_name: str = Field(..., description="智能体名称")
    optimizer_name: str = Field(..., description="优化器名称")
    loss_name: str = Field(..., description="损失函数名称")
    
    # 训练参数
    epochs: int = Field(100, ge=1, le=10000, description="训练轮数")
    batch_size: int = Field(32, ge=1, le=1024, description="批次大小")
    learning_rate: float = Field(0.001, gt=0, le=1, description="学习率")
    
    # 环境配置
    device: str = Field("auto", description="训练设备 (auto/cpu/cuda)")
    seed: Optional[int] = Field(None, description="随机种子")
    
    # 高级配置
    early_stopping: bool = Field(True, description="是否启用早停")
    patience: int = Field(10, ge=1, description="早停耐心值")
    save_checkpoints: bool = Field(True, description="是否保存检查点")
    checkpoint_interval: int = Field(100, ge=1, description="检查点保存间隔")
    @field_validator('task_name')
    @classmethod
    def validate_task_name(cls, v):
        """验证任务名称"""
        allowed_tasks = [
            'algorithmic_trading', 'portfolio_management',
            'order_execution', 'high_frequency_trading'
        ]
        if v not in allowed_tasks:
            raise ValueError(f'task_name必须是: {", ".join(allowed_tasks)}')
        return v
    
    @field_validator('agent_name')
    @classmethod
    def validate_agent_name(cls, v):
        """验证智能体名称格式"""
        # 格式应该是 task_type:agent_type
        if ':' not in v:
            raise ValueError('agent_name格式应该是 task_type:agent_type')
        
        task_type, agent_type = v.split(':', 1)
        allowed_agents = ['dqn', 'ddpg', 'ppo', 'sac', 'td3', 'a2c']
        if agent_type not in allowed_agents:
            raise ValueError(f'智能体类型必须是: {", ".join(allowed_agents)}')
        
        return v
    
    @field_validator('device')
    @classmethod
    def validate_device(cls, v):
        """验证设备配置"""
        allowed_devices = ['auto', 'cpu', 'cuda', 'cuda:0', 'cuda:1']
        if v not in allowed_devices and not v.startswith('cuda:'):
            raise ValueError('device必须是auto、cpu或cuda相关设备')
        return v
        return v


class HyperParameters(BaseSchema):
    """超参数模式"""
    # 网络结构参数
    hidden_layers: List[int] = Field(
        default_factory=lambda: [128, 64], 
        description="隐藏层大小列表"
    )
    activation: str = Field("relu", description="激活函数")
    dropout_rate: float = Field(0.1, ge=0, le=1, description="Dropout比率")
    
    # 训练参数
    gamma: float = Field(0.99, gt=0, le=1, description="折扣因子")
    tau: float = Field(0.005, gt=0, le=1, description="软更新系数")
    buffer_size: int = Field(100000, ge=1000, description="经验回放缓冲区大小")
    
    # 探索参数
    epsilon: float = Field(0.1, ge=0, le=1, description="探索率")
    epsilon_decay: float = Field(0.995, gt=0, le=1, description="探索率衰减")
    epsilon_min: float = Field(0.01, ge=0, le=1, description="最小探索率")
    
    # 优化器参数
    weight_decay: float = Field(0.0001, ge=0, description="权重衰减")
    gradient_clip: Optional[float] = Field(None, gt=0, description="梯度裁剪")
    
    @field_validator('hidden_layers')
    @classmethod
    def validate_hidden_layers(cls, v):
        """验证隐藏层配置"""
        if not v:
            raise ValueError('至少需要一个隐藏层')
        if any(layer <= 0 for layer in v):
            raise ValueError('隐藏层大小必须大于0')
        return v
    
    @field_validator('activation')
    @classmethod
    def validate_activation(cls, v):
        """验证激活函数"""
        allowed_activations = ['relu', 'tanh', 'sigmoid', 'leaky_relu', 'elu']
        if v not in allowed_activations:
            raise ValueError(f'激活函数必须是: {", ".join(allowed_activations)}')
        return v


class TrainingJobCreate(TrainingJobBase):
    """训练任务创建模式"""
    strategy_id: int = Field(..., description="关联策略ID")
    dataset_id: Optional[int] = Field(None, description="数据集ID")
    config: TrainingConfig = Field(..., description="训练配置")
    hyperparameters: HyperParameters = Field(
        default_factory=HyperParameters, 
        description="超参数"
    )
    
    # 资源配置
    estimated_duration: Optional[int] = Field(None, ge=1, description="预估时长(秒)")
    priority: int = Field(1, ge=1, le=5, description="任务优先级(1-5)")


class TrainingJobUpdate(BaseSchema):
    """训练任务更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证任务名称"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('任务名称不能为空')
            return v.strip()
        return v


# ==================== 训练任务响应模式 ====================

class TrainingJobInDB(TrainingJobBase, TimestampSchema, UUIDSchema):
    """数据库中的训练任务模式"""
    # 解决Pydantic字段命名冲突警告
    model_config = ConfigDict(protected_namespaces=())
    
    id: int = Field(..., description="任务ID")
    status: TrainingStatus = Field(..., description="任务状态")
    progress: float = Field(..., description="进度百分比")
    current_epoch: int = Field(..., description="当前轮次")
    total_epochs: Optional[int] = Field(None, description="总轮次")
    
    # 配置信息
    config: Dict[str, Any] = Field(..., description="训练配置")
    hyperparameters: Dict[str, Any] = Field(..., description="超参数")
    
    # 结果信息
    metrics: Dict[str, Any] = Field(..., description="训练指标")
    best_metrics: Dict[str, Any] = Field(..., description="最佳指标")
    model_path: Optional[str] = Field(None, description="模型文件路径")
    logs: Optional[str] = Field(None, description="训练日志")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # TradeMaster集成
    trademaster_session_id: Optional[str] = Field(None, description="TradeMaster会话ID")
    
    # 关联信息
    strategy_id: int = Field(..., description="策略ID")
    dataset_id: Optional[int] = Field(None, description="数据集ID")
    user_id: int = Field(..., description="用户ID")
    parent_job_id: Optional[int] = Field(None, description="父任务ID")
    
    # 资源使用
    estimated_duration: Optional[int] = Field(None, description="预估时长(秒)")
    actual_duration: Optional[int] = Field(None, description="实际时长(秒)")
    cpu_usage: Optional[float] = Field(None, description="CPU使用率(%)")
    memory_usage: Optional[float] = Field(None, description="内存使用率(%)")
    gpu_usage: Optional[float] = Field(None, description="GPU使用率(%)")
    
    # 时间信息
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class TrainingJobResponse(BaseSchema):
    """训练任务响应模式"""
    id: int = Field(..., description="任务ID")
    uuid: str = Field(..., description="任务UUID")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    status: TrainingStatus = Field(..., description="任务状态")
    progress: float = Field(..., description="进度百分比")
    current_epoch: int = Field(..., description="当前轮次")
    total_epochs: Optional[int] = Field(None, description="总轮次")
    
    # 关联信息
    strategy_id: int = Field(..., description="策略ID")
    dataset_id: Optional[int] = Field(None, description="数据集ID")
    user_id: int = Field(..., description="用户ID")
    
    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 预估时间
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")


class TrainingJobDetail(TrainingJobResponse):
    """训练任务详情模式"""
    # 解决Pydantic字段命名冲突警告
    model_config = ConfigDict(protected_namespaces=())
    
    config: TrainingConfig = Field(..., description="训练配置")
    hyperparameters: HyperParameters = Field(..., description="超参数")
    
    # 结果信息
    metrics: Dict[str, Any] = Field(default_factory=dict, description="当前指标")
    best_metrics: Dict[str, Any] = Field(default_factory=dict, description="最佳指标")
    model_path: Optional[str] = Field(None, description="模型文件路径")
    logs: Optional[str] = Field(None, description="训练日志")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # TradeMaster集成
    trademaster_session_id: Optional[str] = Field(None, description="TradeMaster会话ID")
    
    # 资源使用
    estimated_duration: Optional[int] = Field(None, description="预估时长(秒)")
    actual_duration: Optional[int] = Field(None, description="实际时长(秒)")
    resource_usage: Optional["ResourceUsage"] = Field(None, description="资源使用情况")


class TrainingJobSummary(BaseSchema):
    """训练任务摘要信息模式"""
    id: int = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    status: TrainingStatus = Field(..., description="任务状态")
    progress: float = Field(..., description="进度百分比")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    created_at: datetime = Field(..., description="创建时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")


# ==================== 训练指标模式 ====================

class TrainingMetrics(BaseSchema):
    """训练指标模式"""
    # 损失指标
    loss: Optional[float] = Field(None, description="训练损失")
    val_loss: Optional[float] = Field(None, description="验证损失")
    
    # 准确率指标
    accuracy: Optional[float] = Field(None, description="训练准确率")
    val_accuracy: Optional[float] = Field(None, description="验证准确率")
    
    # 金融指标
    total_return: Optional[float] = Field(None, description="总收益率")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤")
    win_rate: Optional[float] = Field(None, description="胜率")
    
    # 自定义指标
    custom_metrics: Dict[str, float] = Field(default_factory=dict, description="自定义指标")


class TrainingMetricHistory(BaseSchema):
    """训练指标历史模式"""
    epoch: int = Field(..., description="训练轮次")
    step: Optional[int] = Field(None, description="训练步数")
    metrics: TrainingMetrics = Field(..., description="指标数据")
    recorded_at: datetime = Field(..., description="记录时间")


class MetricsQuery(BaseSchema):
    """指标查询模式"""
    start_epoch: Optional[int] = Field(None, ge=0, description="起始轮次")
    end_epoch: Optional[int] = Field(None, ge=0, description="结束轮次")
    metrics: Optional[List[str]] = Field(None, description="指定指标列表")
    interval: int = Field(1, ge=1, description="采样间隔")
    
    @model_validator(mode='before')
    @classmethod
    def validate_epoch_range(cls, values):
        """验证轮次范围"""
        start_epoch = values.get('start_epoch')
        end_epoch = values.get('end_epoch')
        
        if start_epoch is not None and end_epoch is not None:
            if start_epoch >= end_epoch:
                raise ValueError('起始轮次必须小于结束轮次')
        
        return values


# ==================== 资源使用模式 ====================

class ResourceUsage(BaseSchema):
    """资源使用情况模式"""
    cpu_usage: Optional[float] = Field(None, ge=0, le=100, description="CPU使用率(%)")
    memory_usage: Optional[float] = Field(None, ge=0, le=100, description="内存使用率(%)")
    gpu_usage: Optional[float] = Field(None, ge=0, le=100, description="GPU使用率(%)")
    gpu_memory_usage: Optional[float] = Field(None, ge=0, le=100, description="GPU内存使用率(%)")
    disk_usage: Optional[float] = Field(None, ge=0, description="磁盘使用量(MB)")
    network_io: Optional[float] = Field(None, ge=0, description="网络IO(MB/s)")


class ResourceMonitoring(BaseSchema):
    """资源监控模式"""
    timestamp: datetime = Field(..., description="监控时间")
    job_id: int = Field(..., description="任务ID")
    usage: ResourceUsage = Field(..., description="资源使用情况")


# ==================== 训练任务操作模式 ====================

class TrainingJobStart(BaseSchema):
    """训练任务启动模式"""
    priority: int = Field(1, ge=1, le=5, description="任务优先级")
    force_restart: bool = Field(False, description="是否强制重启")


class TrainingJobStop(BaseSchema):
    """训练任务停止模式"""
    reason: Optional[str] = Field(None, description="停止原因")
    save_checkpoint: bool = Field(True, description="是否保存检查点")


class TrainingJobPause(BaseSchema):
    """训练任务暂停模式"""
    reason: Optional[str] = Field(None, description="暂停原因")
    save_checkpoint: bool = Field(True, description="是否保存检查点")


class TrainingJobResume(BaseSchema):
    """训练任务恢复模式"""
    from_checkpoint: bool = Field(True, description="是否从检查点恢复")
    checkpoint_path: Optional[str] = Field(None, description="检查点路径")


class TrainingJobClone(BaseSchema):
    """训练任务克隆模式"""
    name: str = Field(..., min_length=1, max_length=100, description="新任务名称")
    description: Optional[str] = Field(None, description="新任务描述")
    strategy_id: Optional[int] = Field(None, description="关联策略ID，None表示使用原策略")
    modify_config: bool = Field(False, description="是否修改配置")
    config_updates: Optional[Dict[str, Any]] = Field(None, description="配置更新")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证任务名称"""
        if not v or not v.strip():
            raise ValueError('任务名称不能为空')
        return v.strip()


# ==================== 训练任务查询模式 ====================

class TrainingJobListQuery(BaseSchema):
    """训练任务列表查询模式"""
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    status: Optional[TrainingStatus] = Field(None, description="状态筛选")
    strategy_id: Optional[int] = Field(None, description="策略筛选")
    dataset_id: Optional[int] = Field(None, description="数据集筛选")
    user_id: Optional[int] = Field(None, description="用户筛选")
    start_date: Optional[datetime] = Field(None, description="开始时间筛选")
    end_date: Optional[datetime] = Field(None, description="结束时间筛选")
    sort: Optional[str] = Field("created_at:desc", description="排序字段")
    
    @field_validator('sort')
    @classmethod
    def validate_sort(cls, v):
        """验证排序参数"""
        if v is None:
            return "created_at:desc"
        
        allowed_fields = [
            'id', 'name', 'status', 'progress', 'current_epoch',
            'created_at', 'updated_at', 'started_at', 'completed_at'
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
    
    @model_validator(mode='before')
    @classmethod
    def validate_date_range(cls, values):
        """验证日期范围"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if start_date is not None and end_date is not None:
            if start_date >= end_date:
                raise ValueError('开始时间必须早于结束时间')
        
        return values


# ==================== 训练任务统计模式 ====================

class TrainingJobStats(BaseSchema):
    """训练任务统计信息模式"""
    total_jobs: int = Field(..., description="总任务数")
    running_jobs: int = Field(..., description="运行中任务数")
    completed_jobs: int = Field(..., description="已完成任务数")
    failed_jobs: int = Field(..., description="失败任务数")
    
    # 状态分布
    status_distribution: Dict[str, int] = Field(..., description="状态分布")
    
    # 类型分布
    task_type_distribution: Dict[str, int] = Field(..., description="任务类型分布")
    agent_type_distribution: Dict[str, int] = Field(..., description="智能体类型分布")
    
    # 性能统计
    avg_duration: Optional[float] = Field(None, description="平均持续时间(秒)")
    success_rate: float = Field(..., description="成功率(%)")
    
    # 资源使用统计
    avg_cpu_usage: Optional[float] = Field(None, description="平均CPU使用率(%)")
    avg_memory_usage: Optional[float] = Field(None, description="平均内存使用率(%)")
    avg_gpu_usage: Optional[float] = Field(None, description="平均GPU使用率(%)")
    
    # 最近活动
    recent_jobs: List[TrainingJobSummary] = Field(..., description="最近任务")
    best_performing_jobs: List[TrainingJobSummary] = Field(..., description="最佳表现任务")


# ==================== TradeMaster集成模式 ====================

class TradeMasterSession(BaseSchema):
    """TradeMaster会话信息模式"""
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="会话状态")
    task_info: Dict[str, Any] = Field(..., description="任务信息")
    created_at: datetime = Field(..., description="创建时间")
    last_heartbeat: Optional[datetime] = Field(None, description="最后心跳时间")


class TradeMasterLog(BaseSchema):
    """TradeMaster日志模式"""
    timestamp: datetime = Field(..., description="时间戳")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    module: Optional[str] = Field(None, description="模块名称")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外信息")


# 前向引用解决
TrainingJobDetail.model_rebuild()

# 导出主要组件
__all__ = [
    # 枚举
    "TrainingTaskType", "AgentType", "OptimizerType", "LossType", "MetricType",
    
    # 基础模式
    "TrainingJobBase", "TrainingConfig", "HyperParameters",
    "TrainingJobCreate", "TrainingJobUpdate",
    
    # 响应模式
    "TrainingJobInDB", "TrainingJobResponse", "TrainingJobDetail", "TrainingJobSummary",
    
    # 指标模式
    "TrainingMetrics", "TrainingMetricHistory", "MetricsQuery",
    
    # 资源模式
    "ResourceUsage", "ResourceMonitoring",
    
    # 操作模式
    "TrainingJobStart", "TrainingJobStop", "TrainingJobPause", "TrainingJobResume", "TrainingJobClone",
    
    # 查询模式
    "TrainingJobListQuery",
    
    # 统计模式
    "TrainingJobStats",
    
    # TradeMaster集成模式
    "TradeMasterSession", "TradeMasterLog"
]