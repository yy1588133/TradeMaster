"""
数据库模型定义

定义所有SQLAlchemy数据库模型，包括用户、策略、数据集、训练任务等核心实体。
基于TradeMaster业务需求设计，支持完整的量化交易平台功能。
"""

import enum
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Numeric, 
    BigInteger, ForeignKey, Index, CheckConstraint, UniqueConstraint,
    event, func, text, JSON
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, TSRANGE, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from app.core.database import Base
from app.core.config import settings


# 兼容的类型定义 - 支持PostgreSQL和SQLite
def get_json_type():
    """获取兼容的JSON类型"""
    database_url = getattr(settings, 'DATABASE_URL', '') or settings.get_database_url(async_driver=True)
    if database_url and database_url.startswith('sqlite'):
        return JSON
    else:
        from sqlalchemy.dialects.postgresql import JSONB
        return JSONB

def get_uuid_type():
    """获取兼容的UUID类型"""
    database_url = getattr(settings, 'DATABASE_URL', '') or settings.get_database_url(async_driver=True)
    if database_url and database_url.startswith('sqlite'):
        return String(36)  # SQLite中用固定长度字符串存储UUID
    else:
        return UUID(as_uuid=False)  # PostgreSQL中使用字符串形式的UUID

def get_inet_type():
    """获取兼容的INET类型 - 用于存储IP地址"""
    database_url = getattr(settings, 'DATABASE_URL', '') or settings.get_database_url(async_driver=True)
    if database_url and database_url.startswith('sqlite'):
        return String(45)  # SQLite中使用字符串存储IP地址 (支持IPv6)
    else:
        return INET  # PostgreSQL中使用INET类型

def get_array_type(item_type=String):
    """获取兼容的ARRAY类型 - 用于存储数组数据"""
    database_url = getattr(settings, 'DATABASE_URL', '') or settings.get_database_url(async_driver=True)
    if database_url and database_url.startswith('sqlite'):
        return Text  # SQLite中使用TEXT存储JSON格式的数组数据
    else:
        return ARRAY(item_type)  # PostgreSQL中使用ARRAY类型

def get_tsrange_type():
    """获取兼容的TSRANGE类型 - 用于存储时间范围"""
    database_url = getattr(settings, 'DATABASE_URL', '') or settings.get_database_url(async_driver=True)
    if database_url and database_url.startswith('sqlite'):
        return String(100)  # SQLite中使用字符串存储时间范围 (格式: "2023-01-01T00:00:00Z,2023-12-31T23:59:59Z")
    else:
        return TSRANGE  # PostgreSQL中使用TSRANGE类型

# 全局类型变量
CompatibleJSON = get_json_type()
CompatibleUUID = get_uuid_type()
CompatibleINET = get_inet_type()
CompatibleARRAY = get_array_type
CompatibleTSRANGE = get_tsrange_type()


# ==================== 枚举类型定义 ====================

class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    ANALYST = "analyst"
    VIEWER = "viewer"


class StrategyType(str, enum.Enum):
    """策略类型枚举"""
    ALGORITHMIC_TRADING = "algorithmic_trading"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    ORDER_EXECUTION = "order_execution"
    HIGH_FREQUENCY_TRADING = "high_frequency_trading"


class StrategyStatus(str, enum.Enum):
    """策略状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class DatasetStatus(str, enum.Enum):
    """数据集状态枚举"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class TrainingStatus(str, enum.Enum):
    """训练状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationType(str, enum.Enum):
    """评估类型枚举"""
    BACKTEST = "backtest"
    PERFORMANCE = "performance"
    RISK = "risk"
    COMPARISON = "comparison"


class EvaluationStatus(str, enum.Enum):
    """评估状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class LogLevel(str, enum.Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class SessionType(str, enum.Enum):
    """会话类型枚举"""
    TRAINING = "training"
    BACKTEST = "backtest"
    LIVE_TRADING = "live_trading"


class SessionStatus(str, enum.Enum):
    """会话状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== Mixin类 ====================

class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )


class UUIDMixin:
    """UUID混入类"""
    uuid: Mapped[str] = mapped_column(
        CompatibleUUID,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
        comment="全局唯一标识符"
    )


# ==================== 核心数据模型 ====================

class User(Base, TimestampMixin, UUIDMixin):
    """用户模型
    
    存储用户账户信息、权限设置和个人配置。
    支持用户认证、授权和个性化设置。
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_active", "is_active"),
        Index("idx_users_created_at", "created_at"),
        {"comment": "用户信息表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="用户ID")
    
    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="邮箱地址"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="加密密码"
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100), comment="真实姓名"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500), comment="头像URL"
    )
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否激活"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否超级用户"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否已验证邮箱"
    )
    role: Mapped[UserRole] = mapped_column(
        default=UserRole.USER, nullable=False, comment="用户角色"
    )
    
    # 登录信息
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="最后登录时间"
    )
    login_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="登录次数"
    )
    
    # 个人设置
    settings: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="用户设置"
    )
    
    # 关系映射
    strategies: Mapped[List["Strategy"]] = relationship(
        "Strategy", back_populates="owner", cascade="all, delete-orphan"
    )
    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset", back_populates="owner", cascade="all, delete-orphan"
    )
    training_jobs: Mapped[List["TrainingJob"]] = relationship(
        "TrainingJob", back_populates="user", cascade="all, delete-orphan"
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    strategy_sessions: Mapped[List["StrategySession"]] = relationship(
        "StrategySession", back_populates="user", cascade="all, delete-orphan"
    )
    websocket_connections: Mapped[List["WebSocketConnection"]] = relationship(
        "WebSocketConnection", back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @hybrid_property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == UserRole.ADMIN or self.is_superuser


class UserSession(Base, TimestampMixin):
    """用户会话模型
    
    管理用户登录会话、Token和设备信息。
    支持多设备登录和会话管理。
    """
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_token", "session_token"),
        Index("idx_sessions_expires", "expires_at"),
        {"comment": "用户会话表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="会话ID")
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, comment="用户ID"
    )
    
    # Token信息
    session_token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, comment="会话Token"
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, comment="刷新Token"
    )
    
    # 设备信息
    ip_address: Mapped[Optional[str]] = mapped_column(
        CompatibleINET, comment="IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, comment="用户代理"
    )
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否活跃"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="过期时间"
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="最后活动时间"
    )
    
    # 关系映射
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at='{self.expires_at}')>"


class Strategy(Base, TimestampMixin, UUIDMixin):
    """策略模型
    
    存储量化交易策略的基本信息、配置参数和性能指标。
    支持多种策略类型和版本管理。
    """
    __tablename__ = "strategies"
    __table_args__ = (
        Index("idx_strategies_owner", "owner_id"),
        Index("idx_strategies_type", "strategy_type"),
        Index("idx_strategies_status", "status"),
        Index("idx_strategies_created", "created_at"),
        Index("idx_strategies_tags", "tags", postgresql_using="gin"),
        Index("idx_strategies_config", "config", postgresql_using="gin"),
        CheckConstraint("total_return >= -100 AND total_return <= 1000", name="valid_return_range"),
        CheckConstraint("sharpe_ratio >= -10 AND sharpe_ratio <= 10", name="valid_sharpe_ratio"),
        {"comment": "策略信息表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="策略ID")
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="策略名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, comment="策略描述"
    )
    strategy_type: Mapped[StrategyType] = mapped_column(
        nullable=False, comment="策略类型"
    )
    status: Mapped[StrategyStatus] = mapped_column(
        default=StrategyStatus.DRAFT, nullable=False, comment="策略状态"
    )
    version: Mapped[str] = mapped_column(
        String(20), default="1.0.0", nullable=False, comment="版本号"
    )
    
    # 配置信息
    config: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="策略配置"
    )
    parameters: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="策略参数"
    )
    
    # 性能指标
    total_return: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 4), comment="总收益率(%)"
    )
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 4), comment="夏普比率"
    )
    max_drawdown: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 4), comment="最大回撤(%)"
    )
    win_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="胜率(%)"
    )
    
    # 关联信息
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, comment="所有者ID"
    )
    parent_strategy_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("strategies.id"), comment="父策略ID"
    )
    
    # 标签和分类
    tags: Mapped[List[str]] = mapped_column(
        CompatibleARRAY(String), default=list, nullable=False, comment="标签列表"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50), comment="策略分类"
    )
    
    # 时间信息
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="最后运行时间"
    )
    
    # 关系映射
    owner: Mapped["User"] = relationship("User", back_populates="strategies")
    parent_strategy: Mapped[Optional["Strategy"]] = relationship(
        "Strategy", remote_side="Strategy.id"
    )
    versions: Mapped[List["StrategyVersion"]] = relationship(
        "StrategyVersion", back_populates="strategy", cascade="all, delete-orphan"
    )
    training_jobs: Mapped[List["TrainingJob"]] = relationship(
        "TrainingJob", back_populates="strategy", cascade="all, delete-orphan"
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation", back_populates="strategy", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["StrategySession"]] = relationship(
        "StrategySession", back_populates="strategy", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, name='{self.name}', type='{self.strategy_type}')>"


class StrategyVersion(Base, TimestampMixin):
    """策略版本模型
    
    管理策略的版本历史和配置变更。
    支持策略回滚和版本对比。
    """
    __tablename__ = "strategy_versions"
    __table_args__ = (
        Index("idx_strategy_versions_strategy", "strategy_id"),
        Index("idx_strategy_versions_active", "strategy_id", "is_active"),
        UniqueConstraint("strategy_id", "version", name="uq_strategy_version"),
        {"comment": "策略版本表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="版本ID")
    
    # 关联策略
    strategy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("strategies.id", ondelete="CASCADE"), 
        nullable=False, comment="策略ID"
    )
    
    # 版本信息
    version: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="版本号"
    )
    config: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, nullable=False, comment="版本配置"
    )
    parameters: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="版本参数"
    )
    changelog: Mapped[Optional[str]] = mapped_column(
        Text, comment="变更日志"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否为活跃版本"
    )
    
    # 创建信息
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), comment="创建者ID"
    )
    
    # 关系映射
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="versions")
    creator: Mapped[Optional["User"]] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<StrategyVersion(id={self.id}, strategy_id={self.strategy_id}, version='{self.version}')>"


class Dataset(Base, TimestampMixin, UUIDMixin):
    """数据集模型
    
    管理上传的数据文件、元数据和处理状态。
    支持多种数据格式和自动化数据分析。
    """
    __tablename__ = "datasets"
    __table_args__ = (
        Index("idx_datasets_owner", "owner_id"),
        Index("idx_datasets_status", "status"),
        Index("idx_datasets_created", "created_at"),
        Index("idx_datasets_columns", "columns", postgresql_using="gin"),
        {"comment": "数据集信息表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="数据集ID")
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="数据集名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, comment="数据集描述"
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="文件路径"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger, comment="文件大小(字节)"
    )
    file_type: Mapped[Optional[str]] = mapped_column(
        String(20), comment="文件类型"
    )
    
    # 数据信息
    row_count: Mapped[Optional[int]] = mapped_column(
        Integer, comment="行数"
    )
    column_count: Mapped[Optional[int]] = mapped_column(
        Integer, comment="列数"
    )
    columns: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        CompatibleJSON, comment="列信息"
    )
    
    # 状态信息
    status: Mapped[DatasetStatus] = mapped_column(
        default=DatasetStatus.UPLOADING, nullable=False, comment="处理状态"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, comment="错误信息"
    )
    
    # 统计信息
    statistics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        CompatibleJSON, comment="数据统计信息"
    )
    sample_data: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        CompatibleJSON, comment="样本数据"
    )
    
    # 关联信息
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, comment="所有者ID"
    )
    
    # 时间信息
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="处理完成时间"
    )
    
    # 关系映射
    owner: Mapped["User"] = relationship("User", back_populates="datasets")
    training_jobs: Mapped[List["TrainingJob"]] = relationship(
        "TrainingJob", back_populates="dataset"
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation", back_populates="dataset"
    )
    
    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name='{self.name}', status='{self.status}')>"


class TrainingJob(Base, TimestampMixin, UUIDMixin):
    """训练任务模型
    
    管理机器学习模型的训练任务、进度和结果。
    集成TradeMaster训练流程和Celery异步任务。
    """
    __tablename__ = "training_jobs"
    __table_args__ = (
        Index("idx_training_jobs_user", "user_id"),
        Index("idx_training_jobs_strategy", "strategy_id"),
        Index("idx_training_jobs_dataset", "dataset_id"),
        Index("idx_training_jobs_status", "status"),
        Index("idx_training_jobs_created", "created_at"),
        Index("idx_training_jobs_session", "trademaster_session_id"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="valid_progress_range"),
        {"comment": "训练任务表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="任务ID")
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="任务名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, comment="任务描述"
    )
    
    # 状态信息
    status: Mapped[TrainingStatus] = mapped_column(
        default=TrainingStatus.PENDING, nullable=False, comment="任务状态"
    )
    progress: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0.0, nullable=False, comment="进度百分比"
    )
    current_epoch: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="当前轮次"
    )
    total_epochs: Mapped[Optional[int]] = mapped_column(
        Integer, comment="总轮次"
    )
    
    # 配置信息
    config: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, nullable=False, comment="训练配置"
    )
    hyperparameters: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="超参数"
    )
    
    # 结果信息
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="训练指标"
    )
    best_metrics: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="最佳指标"
    )
    model_path: Mapped[Optional[str]] = mapped_column(
        String(500), comment="模型文件路径"
    )
    logs: Mapped[Optional[str]] = mapped_column(
        Text, comment="训练日志"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, comment="错误信息"
    )
    
    # TradeMaster集成
    trademaster_session_id: Mapped[Optional[str]] = mapped_column(
        String(100), comment="TradeMaster会话ID"
    )
    
    # 关联信息
    strategy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("strategies.id", ondelete="CASCADE"), 
        nullable=False, comment="策略ID"
    )
    dataset_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("datasets.id"), comment="数据集ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, comment="用户ID"
    )
    parent_job_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("training_jobs.id"), comment="父任务ID"
    )
    
    # 资源使用
    estimated_duration: Mapped[Optional[int]] = mapped_column(
        Integer, comment="预估时长(秒)"
    )
    actual_duration: Mapped[Optional[int]] = mapped_column(
        Integer, comment="实际时长(秒)"
    )
    cpu_usage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="CPU使用率(%)"
    )
    memory_usage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="内存使用率(%)"
    )
    gpu_usage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="GPU使用率(%)"
    )
    
    # 时间信息
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="开始时间"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="完成时间"
    )
    
    # 关系映射
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="training_jobs")
    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset", back_populates="training_jobs")
    user: Mapped["User"] = relationship("User", back_populates="training_jobs")
    parent_job: Mapped[Optional["TrainingJob"]] = relationship(
        "TrainingJob", remote_side="TrainingJob.id"
    )
    metrics_history: Mapped[List["TrainingMetric"]] = relationship(
        "TrainingMetric", back_populates="training_job", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TrainingJob(id={self.id}, name='{self.name}', status='{self.status}')>"


class TrainingMetric(Base):
    """训练指标历史模型
    
    记录训练过程中每个轮次的详细指标数据。
    支持训练过程可视化和性能分析。
    """
    __tablename__ = "training_metrics"
    __table_args__ = (
        Index("idx_training_metrics_job", "training_job_id"),
        Index("idx_training_metrics_epoch", "training_job_id", "epoch"),
        {"comment": "训练指标历史表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="指标ID")
    
    # 关联任务
    training_job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_jobs.id", ondelete="CASCADE"), 
        nullable=False, comment="训练任务ID"
    )
    
    # 轮次信息
    epoch: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="训练轮次"
    )
    step: Mapped[Optional[int]] = mapped_column(
        Integer, comment="训练步数"
    )
    
    # 指标数据
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, nullable=False, comment="指标数据"
    )
    
    # 时间戳
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="记录时间"
    )
    
    # 关系映射
    training_job: Mapped["TrainingJob"] = relationship(
        "TrainingJob", back_populates="metrics_history"
    )
    
    def __repr__(self) -> str:
        return f"<TrainingMetric(id={self.id}, job_id={self.training_job_id}, epoch={self.epoch})>"


class Evaluation(Base, TimestampMixin, UUIDMixin):
    """评估任务模型
    
    管理策略评估、回测分析和性能报告。
    支持多种评估类型和结果可视化。
    """
    __tablename__ = "evaluations"
    __table_args__ = (
        Index("idx_evaluations_user", "user_id"),
        Index("idx_evaluations_strategy", "strategy_id"),
        Index("idx_evaluations_dataset", "dataset_id"),
        Index("idx_evaluations_type", "evaluation_type"),
        Index("idx_evaluations_status", "status"),
        {"comment": "评估任务表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="评估ID")
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="评估名称"
    )
    evaluation_type: Mapped[EvaluationType] = mapped_column(
        nullable=False, comment="评估类型"
    )
    status: Mapped[EvaluationStatus] = mapped_column(
        default=EvaluationStatus.PENDING, nullable=False, comment="评估状态"
    )
    
    # 配置信息
    config: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, nullable=False, comment="评估配置"
    )
    time_range: Mapped[Optional[str]] = mapped_column(
        CompatibleTSRANGE, comment="评估时间范围"
    )
    
    # 结果信息
    results: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="评估结果"
    )
    report_path: Mapped[Optional[str]] = mapped_column(
        String(500), comment="报告文件路径"
    )
    charts: Mapped[List[Dict[str, Any]]] = mapped_column(
        CompatibleJSON, default=list, nullable=False, comment="图表数据"
    )
    
    # 关联信息
    strategy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("strategies.id", ondelete="CASCADE"), 
        nullable=False, comment="策略ID"
    )
    dataset_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("datasets.id"), comment="数据集ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, comment="用户ID"
    )
    
    # 时间信息
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="完成时间"
    )
    
    # 关系映射
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="evaluations")
    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset", back_populates="evaluations")
    user: Mapped["User"] = relationship("User", back_populates="evaluations")
    
    def __repr__(self) -> str:
        return f"<Evaluation(id={self.id}, name='{self.name}', type='{self.evaluation_type}')>"


class SystemLog(Base):
    """系统日志模型
    
    记录系统运行日志、用户操作和错误信息。
    支持日志查询、分析和监控告警。
    """
    __tablename__ = "system_logs"
    __table_args__ = (
        Index("idx_system_logs_level", "level"),
        Index("idx_system_logs_user", "user_id"),
        Index("idx_system_logs_created", "created_at"),
        Index("idx_system_logs_module", "module"),
        {"comment": "系统日志表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="日志ID")
    
    # 日志信息
    level: Mapped[LogLevel] = mapped_column(
        nullable=False, comment="日志级别"
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="日志消息"
    )
    module: Mapped[Optional[str]] = mapped_column(
        String(100), comment="模块名称"
    )
    function_name: Mapped[Optional[str]] = mapped_column(
        String(100), comment="函数名称"
    )
    
    # 上下文信息
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), comment="用户ID"
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(255), comment="会话ID"
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100), comment="请求ID"
    )
    
    # 额外数据
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="元数据"
    )
    stack_trace: Mapped[Optional[str]] = mapped_column(
        Text, comment="堆栈跟踪"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        CompatibleINET, comment="IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, comment="用户代理"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    # 关系映射
    user: Mapped[Optional["User"]] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, level='{self.level}', message='{self.message[:50]}...')>"


class StrategySession(Base, TimestampMixin, UUIDMixin):
    """策略执行会话模型
    
    管理策略训练、回测、实盘交易的完整生命周期。
    与TradeMaster核心和Celery任务系统集成。
    """
    __tablename__ = "strategy_sessions"
    __table_args__ = (
        Index("idx_strategy_sessions_strategy", "strategy_id"),
        Index("idx_strategy_sessions_status", "status"),
        Index("idx_strategy_sessions_type_status", "session_type", "status"),
        Index("idx_strategy_sessions_user", "user_id"),
        Index("idx_strategy_sessions_celery_task", "celery_task_id"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="valid_session_progress"),
        {"comment": "策略执行会话表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="会话ID")
    
    # 基本信息
    session_type: Mapped[SessionType] = mapped_column(
        nullable=False, comment="会话类型"
    )
    status: Mapped[SessionStatus] = mapped_column(
        default=SessionStatus.PENDING, nullable=False, comment="会话状态"
    )
    
    # 关联信息
    strategy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("strategies.id", ondelete="CASCADE"), 
        nullable=False, comment="策略ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, comment="用户ID"
    )
    
    # TradeMaster集成
    trademaster_config: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, nullable=False, comment="TradeMaster配置"
    )
    trademaster_session_id: Mapped[Optional[str]] = mapped_column(
        String(100), comment="TradeMaster会话ID"
    )
    celery_task_id: Mapped[Optional[str]] = mapped_column(
        String(155), comment="Celery任务ID"
    )
    
    # 执行进度
    progress: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0.0, nullable=False, comment="进度百分比"
    )
    current_epoch: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="当前轮次"
    )
    total_epochs: Mapped[Optional[int]] = mapped_column(
        Integer, comment="总轮次"
    )
    
    # 结果数据
    final_metrics: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="最终指标"
    )
    model_path: Mapped[Optional[str]] = mapped_column(
        String(500), comment="模型文件路径"
    )
    log_file_path: Mapped[Optional[str]] = mapped_column(
        String(500), comment="日志文件路径"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, comment="错误信息"
    )
    
    # 时间戳
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="开始时间"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="完成时间"
    )
    
    # 关系映射
    strategy: Mapped["Strategy"] = relationship(
        "Strategy", back_populates="sessions"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="strategy_sessions"
    )
    metrics: Mapped[List["PerformanceMetric"]] = relationship(
        "PerformanceMetric", back_populates="session", cascade="all, delete-orphan"
    )
    resource_usage: Mapped[List["ResourceUsage"]] = relationship(
        "ResourceUsage", back_populates="session", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<StrategySession(id={self.id}, type='{self.session_type}', status='{self.status}')>"


class PerformanceMetric(Base):
    """实时性能指标模型
    
    记录策略执行过程中的性能指标数据。
    支持实时监控和历史分析。
    """
    __tablename__ = "performance_metrics"
    __table_args__ = (
        Index("idx_performance_metrics_session", "session_id"),
        Index("idx_performance_metrics_epoch", "session_id", "epoch"),
        Index("idx_performance_metrics_name_time", "metric_name", "recorded_at"),
        {"comment": "性能指标表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="指标ID")
    
    # 关联会话
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("strategy_sessions.id", ondelete="CASCADE"), 
        nullable=False, comment="会话ID"
    )
    
    # 指标信息
    metric_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="指标名称"
    )
    metric_value: Mapped[float] = mapped_column(
        Numeric(15, 8), nullable=False, comment="指标值"
    )
    epoch: Mapped[Optional[int]] = mapped_column(
        Integer, comment="轮次"
    )
    step: Mapped[Optional[int]] = mapped_column(
        Integer, comment="步数"
    )
    
    # 元数据
    metric_metadata: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON, default=dict, nullable=False, comment="元数据"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="记录时间"
    )
    
    # 关系映射
    session: Mapped["StrategySession"] = relationship(
        "StrategySession", back_populates="metrics"
    )
    
    def __repr__(self) -> str:
        return f"<PerformanceMetric(id={self.id}, name='{self.metric_name}', value={self.metric_value})>"


class ResourceUsage(Base):
    """系统资源使用记录模型
    
    记录会话执行过程中的系统资源使用情况。
    用于性能监控和资源优化。
    """
    __tablename__ = "resource_usage"
    __table_args__ = (
        Index("idx_resource_usage_session", "session_id"),
        Index("idx_resource_usage_time", "session_id", "recorded_at"),
        {"comment": "资源使用记录表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="记录ID")
    
    # 关联会话
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("strategy_sessions.id", ondelete="CASCADE"), 
        nullable=False, comment="会话ID"
    )
    
    # 资源指标
    cpu_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="CPU使用率(%)"
    )
    memory_mb: Mapped[Optional[int]] = mapped_column(
        Integer, comment="内存使用量(MB)"
    )
    gpu_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), comment="GPU使用率(%)"
    )
    gpu_memory_mb: Mapped[Optional[int]] = mapped_column(
        Integer, comment="GPU内存使用量(MB)"
    )
    disk_io_mb: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), comment="磁盘IO(MB)"
    )
    network_io_mb: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), comment="网络IO(MB)"
    )
    
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="记录时间"
    )
    
    # 关系映射
    session: Mapped["StrategySession"] = relationship(
        "StrategySession", back_populates="resource_usage"
    )
    
    def __repr__(self) -> str:
        return f"<ResourceUsage(id={self.id}, session_id={self.session_id}, cpu={self.cpu_percent}%)>"


class WebSocketConnection(Base, TimestampMixin):
    """WebSocket连接管理模型
    
    管理WebSocket连接状态和会话订阅。
    支持实时数据推送和连接监控。
    """
    __tablename__ = "websocket_connections"
    __table_args__ = (
        Index("idx_websocket_connections_user", "user_id"),
        Index("idx_websocket_connections_active", "is_active"),
        Index("idx_websocket_connections_id", "connection_id"),
        {"comment": "WebSocket连接表"}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="记录ID")
    
    # 用户关联
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, comment="用户ID"
    )
    connection_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="连接ID"
    )
    session_ids: Mapped[List[int]] = mapped_column(
        CompatibleARRAY(Integer), default=list, nullable=False, comment="订阅的会话ID列表"
    )
    
    # 连接信息
    ip_address: Mapped[Optional[str]] = mapped_column(
        CompatibleINET, comment="IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, comment="用户代理"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否活跃"
    )
    
    # 时间信息
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="连接时间"
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="最后活动时间"
    )
    
    # 关系映射
    user: Mapped["User"] = relationship(
        "User", back_populates="websocket_connections"
    )
    
    def __repr__(self) -> str:
        return f"<WebSocketConnection(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class CeleryTask(Base, TimestampMixin):
    """Celery任务记录模型
    
    跟踪异步任务的执行状态、结果和性能。
    与Celery任务系统集成，提供任务监控。
    """
    __tablename__ = "celery_tasks"
    __table_args__ = (
        Index("idx_celery_tasks_status", "status"),
        Index("idx_celery_tasks_user", "user_id"),
        Index("idx_celery_tasks_created", "created_at"),
        Index("idx_celery_tasks_related", "related_type", "related_id"),
        {"comment": "Celery任务记录表"}
    )
    
    # 主键 (使用Celery的task ID)
    id: Mapped[str] = mapped_column(
        String(155), primary_key=True, comment="Celery任务ID"
    )
    
    # 任务信息
    task_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="任务名称"
    )
    status: Mapped[TaskStatus] = mapped_column(
        default=TaskStatus.PENDING, nullable=False, comment="任务状态"
    )
    
    # 任务参数
    args: Mapped[Optional[List[Any]]] = mapped_column(
        CompatibleJSON, comment="位置参数"
    )
    kwargs: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        CompatibleJSON, comment="关键字参数"
    )
    result: Mapped[Optional[Any]] = mapped_column(
        CompatibleJSON, comment="任务结果"
    )
    
    # 执行信息
    worker_name: Mapped[Optional[str]] = mapped_column(
        String(100), comment="工作进程名称"
    )
    retries: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="重试次数"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False, comment="最大重试次数"
    )
    
    # 时间信息
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="开始时间"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), comment="完成时间"
    )
    
    # 关联信息
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), comment="用户ID"
    )
    related_id: Mapped[Optional[int]] = mapped_column(
        Integer, comment="关联业务对象ID"
    )
    related_type: Mapped[Optional[str]] = mapped_column(
        String(50), comment="关联业务对象类型"
    )
    
    # 关系映射
    user: Mapped[Optional["User"]] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<CeleryTask(id='{self.id}', task_name='{self.task_name}', status='{self.status}')>"


# ==================== 数据库事件监听器 ====================

# 自动更新updated_at字段
@event.listens_for(User, 'before_update')
@event.listens_for(Strategy, 'before_update')
@event.listens_for(Dataset, 'before_update')
@event.listens_for(TrainingJob, 'before_update')
@event.listens_for(Evaluation, 'before_update')
@event.listens_for(CeleryTask, 'before_update')
def receive_before_update(mapper, connection, target):
    """更新前自动设置updated_at字段"""
    if hasattr(target, 'updated_at'):
        target.updated_at = datetime.utcnow()


# 用户登录计数更新
@event.listens_for(User.last_login_at, 'set')
def receive_login_update(target, value, oldvalue, initiator):
    """用户登录时自动增加登录计数"""
    if value is not None and oldvalue != value:
        target.login_count = (target.login_count or 0) + 1


# 导出所有模型
__all__ = [
    # 枚举
    "UserRole", "StrategyType", "StrategyStatus", "DatasetStatus",
    "TrainingStatus", "EvaluationType", "EvaluationStatus", 
    "LogLevel", "TaskStatus", "SessionType", "SessionStatus",
    
    # Mixin类
    "TimestampMixin", "UUIDMixin",
    
    # 模型类
    "User", "UserSession", "Strategy", "StrategyVersion",
    "Dataset", "TrainingJob", "TrainingMetric", "Evaluation",
    "SystemLog", "CeleryTask", "StrategySession", "PerformanceMetric", 
    "ResourceUsage", "WebSocketConnection"
]