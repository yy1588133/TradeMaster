"""
数据模型模块

包含所有的SQLAlchemy数据库模型定义。
"""

# 导入数据库核心组件
from app.core.database import (
    Base, engine, AsyncSessionLocal, get_db_session, get_db,
    init_database, drop_database, check_database_connection,
    get_database_info, DatabaseManager
)

# 导入所有数据库模型
from .database import (
    # 枚举类型
    UserRole, StrategyType, StrategyStatus, DatasetStatus,
    TrainingStatus, EvaluationType, EvaluationStatus,
    LogLevel, TaskStatus,
    
    # Mixin类
    TimestampMixin, UUIDMixin,
    
    # 核心模型
    User, UserSession, Strategy, StrategyVersion,
    Dataset, TrainingJob, TrainingMetric, Evaluation,
    SystemLog, CeleryTask
)

# 导出所有组件
__all__ = [
    # 数据库核心
    "Base", "engine", "AsyncSessionLocal", "get_db_session", "get_db",
    "init_database", "drop_database", "check_database_connection",
    "get_database_info", "DatabaseManager",
    
    # 枚举类型
    "UserRole", "StrategyType", "StrategyStatus", "DatasetStatus",
    "TrainingStatus", "EvaluationType", "EvaluationStatus",
    "LogLevel", "TaskStatus",
    
    # Mixin类
    "TimestampMixin", "UUIDMixin",
    
    # 数据库模型
    "User", "UserSession", "Strategy", "StrategyVersion",
    "Dataset", "TrainingJob", "TrainingMetric", "Evaluation",
    "SystemLog", "CeleryTask"
]