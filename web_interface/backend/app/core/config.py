"""
应用核心配置管理

使用Pydantic Settings进行配置管理，支持环境变量和.env文件。
提供类型安全的配置项，包括数据库连接、Redis缓存、安全设置等。
"""

import os
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache

from pydantic import PostgresDsn, HttpUrl, Field, field_validator, ConfigDict
from pydantic.networks import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类
    
    使用Pydantic BaseSettings自动处理环境变量和类型验证。
    支持从.env文件加载配置，提供合理的默认值。
    """
    
    # 设置模型配置，允许额外字段以兼容现有.env文件
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 忽略额外的环境变量，避免验证错误
    )
    
    # ==================== 基础配置 ====================
    PROJECT_NAME: str = Field(default="TradeMaster Web Interface", alias="APP_NAME")
    VERSION: str = Field(default="1.0.0", alias="APP_VERSION")
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = Field(default=False, description="调试模式开关")
    
    # ==================== 服务器配置 ====================
    SERVER_HOST: str = Field(default="0.0.0.0", description="服务器绑定地址")
    SERVER_PORT: int = Field(default=8000, description="服务器端口")
    
    # CORS配置 - 使用property避免Pydantic解析问题
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """获取CORS源地址列表"""
        return self._parse_cors_origins_safely()
    
    @staticmethod
    def _parse_cors_origins_safely() -> List[str]:
        """安全地解析CORS源地址列表
        
        直接从环境变量读取，避免Pydantic的自动解析问题
        """
        import json
        
        # 直接从环境变量获取
        cors_env = os.environ.get('BACKEND_CORS_ORIGINS', '')
        
        if not cors_env or cors_env.strip() == '':
            # 返回默认值
            return [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://localhost:3100",
                "http://127.0.0.1:3100"
            ]
        
        # 尝试JSON解析
        try:
            parsed = json.loads(cors_env)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 尝试逗号分隔解析
        if ',' in cors_env:
            return [origin.strip() for origin in cors_env.split(',') if origin.strip()]
        
        # 单个URL
        if cors_env.strip():
            return [cors_env.strip()]
        
        # 如果所有解析都失败，返回默认值
        return [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:3100",
            "http://127.0.0.1:3100"
        ]
    # 信任主机配置
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"],
        description="允许的主机列表"
    )
    
    # ==================== 安全配置 ====================
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT签名密钥，生产环境必须更改"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        description="访问令牌过期时间（分钟）"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="刷新令牌过期时间（天）"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    
    # 密码策略
    MIN_PASSWORD_LENGTH: int = Field(default=8, description="最小密码长度")
    REQUIRE_SPECIAL_CHARS: bool = Field(default=True, description="密码是否需要特殊字符")
    
    # ==================== 数据库配置 ====================
    POSTGRES_SERVER: str = Field(default="localhost", description="PostgreSQL服务器地址", alias="DB_HOST")
    POSTGRES_USER: str = Field(default="postgres", description="数据库用户名", alias="DB_USER")
    POSTGRES_PASSWORD: str = Field(default="password", description="数据库密码", alias="DB_PASSWORD")
    POSTGRES_DB: str = Field(default="trademaster_web", description="数据库名称", alias="DB_NAME")
    POSTGRES_PORT: str = Field(default="5432", description="数据库端口", alias="DB_PORT")
    
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        """构建数据库连接URL"""
        if isinstance(v, str):
            return v
        
        # 如果没有设置DATABASE_URL，从其他字段构建
        values = info.data if hasattr(info, 'data') else {}
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER', 'postgres')}"
            f":{values.get('POSTGRES_PASSWORD', 'password')}"
            f"@{values.get('POSTGRES_SERVER', 'localhost')}"
            f":{values.get('POSTGRES_PORT', '5432')}"
            f"/{values.get('POSTGRES_DB', 'trademaster_web')}"
        )
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = Field(default=10, description="数据库连接池大小")
    DB_MAX_OVERFLOW: int = Field(default=20, description="数据库连接池最大溢出")
    DB_POOL_TIMEOUT: int = Field(default=30, description="连接池超时时间（秒）")
    
    # ==================== Redis配置 ====================
    REDIS_HOST: str = Field(default="localhost", description="Redis服务器地址")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_DB: int = Field(default=0, description="Redis数据库编号")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    REDIS_SSL: bool = Field(default=False, description="是否使用SSL连接Redis")
    
    @property
    def REDIS_URL(self) -> str:
        """构建Redis连接URL"""
        scheme = "rediss" if self.REDIS_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{scheme}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Redis缓存配置
    CACHE_EXPIRE_SECONDS: int = Field(default=3600, description="缓存过期时间（秒）")
    CACHE_KEY_PREFIX: str = Field(default="trademaster:", description="缓存键前缀")
    
    # ==================== Celery异步任务配置 ====================
    @property
    def CELERY_BROKER_URL(self) -> str:
        """Celery消息代理URL"""
        return self.REDIS_URL
    
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Celery结果后端URL"""
        return self.REDIS_URL
    
    CELERY_TASK_TIMEOUT: int = Field(default=1800, description="Celery任务超时时间（秒）")
    CELERY_MAX_RETRIES: int = Field(default=3, description="Celery任务最大重试次数")
    
    # ==================== TradeMaster集成配置 ====================
    TRADEMASTER_API_URL: str = Field(
        default="http://localhost:8080",
        description="TradeMaster Flask API地址"
    )
    TRADEMASTER_API_TIMEOUT: int = Field(
        default=300,
        description="TradeMaster API请求超时时间（秒）"
    )
    TRADEMASTER_API_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="TradeMaster API重试次数"
    )
    TRADEMASTER_API_RETRY_DELAY: int = Field(
        default=5,
        description="TradeMaster API重试延迟（秒）"
    )
    
    # ==================== 文件存储配置 ====================
    UPLOAD_DIR: str = Field(default="uploads", description="文件上传目录")
    MAX_UPLOAD_SIZE: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="最大上传文件大小（字节）"
    )
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[".csv", ".json", ".xlsx", ".xls", ".parquet"],
        description="允许上传的文件扩展名"
    )
    
    # 文件存储路径配置
    DATA_DIR: str = Field(default="data", description="数据文件目录")
    MODEL_DIR: str = Field(default="models", description="模型文件目录")
    LOG_DIR: str = Field(default="logs", description="日志文件目录")
    
    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    SQLALCHEMY_LOG_LEVEL: str = Field(default="WARNING", description="SQLAlchemy日志级别")
    LOG_FORMAT: str = Field(default="json", description="日志格式")
    LOG_FILE_MAX_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="单个日志文件最大大小（字节）"
    )
    LOG_FILE_BACKUP_COUNT: int = Field(default=5, description="日志文件备份数量")
    
    # ==================== 监控配置 ====================
    SENTRY_DSN: Optional[HttpUrl] = Field(default=None, description="Sentry DSN")
    ENABLE_METRICS: bool = Field(default=True, description="是否启用指标收集")
    METRICS_PORT: int = Field(default=9090, description="Prometheus指标端口")
    
    # ==================== 邮件配置 ====================
    SMTP_TLS: bool = Field(default=True, description="SMTP是否使用TLS")
    SMTP_SSL: bool = Field(default=False, description="SMTP是否使用SSL")
    SMTP_PORT: Optional[int] = Field(default=587, description="SMTP端口")
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP服务器地址")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP用户名")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP密码")
    EMAILS_FROM_EMAIL: Optional[str] = Field(default=None, description="发件人邮箱")
    EMAILS_FROM_NAME: Optional[str] = Field(default=None, description="发件人姓名")
    
    # ==================== API限流配置 ====================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用API限流")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="每分钟API调用限制")
    RATE_LIMIT_BURST: int = Field(default=20, description="突发请求限制")
    
    # ==================== WebSocket配置 ====================
    WEBSOCKET_ENABLED: bool = Field(default=True, description="是否启用WebSocket")
    WEBSOCKET_MAX_CONNECTIONS: int = Field(
        default=100,
        description="WebSocket最大连接数"
    )
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(
        default=30,
        description="WebSocket心跳间隔（秒）"
    )
    
    # ==================== 数据处理配置 ====================
    DATA_PROCESSING_CHUNK_SIZE: int = Field(
        default=10000,
        description="数据处理块大小"
    )
    DATA_PROCESSING_MAX_WORKERS: int = Field(
        default=4,
        description="数据处理最大工作进程数"
    )
    
    # ==================== 模型训练配置 ====================
    TRAINING_MAX_CONCURRENT_JOBS: int = Field(
        default=2,
        description="最大并发训练任务数"
    )
    TRAINING_CHECKPOINT_INTERVAL: int = Field(
        default=100,
        description="训练检查点保存间隔"
    )
    TRAINING_EARLY_STOPPING_PATIENCE: int = Field(
        default=10,
        description="早停机制的耐心值"
    )
    
    # ==================== 环境特定配置 ====================
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.DEBUG
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return not self.DEBUG
    
    def get_database_url(self, async_driver: bool = True) -> str:
        """获取数据库连接URL
        
        Args:
            async_driver: 是否使用异步驱动
            
        Returns:
            数据库连接URL字符串
        """
        if self.DATABASE_URL:
            return str(self.DATABASE_URL)
        
        # 如果是开发环境或没有配置PostgreSQL，使用SQLite
        if (self.is_development or 
            not self.POSTGRES_PASSWORD or
            self.POSTGRES_PASSWORD == "password"):
            
            sqlite_path = "sqlite+aiosqlite:///./trademaster_web.db"
            return sqlite_path if async_driver else sqlite_path.replace("+aiosqlite", "")
        
        # 生产环境使用PostgreSQL
        driver = "postgresql+asyncpg" if async_driver else "postgresql"
        return (
            f"{driver}://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    def get_upload_path(self, filename: str) -> str:
        """获取上传文件的完整路径
        
        Args:
            filename: 文件名
            
        Returns:
            完整的文件路径
        """
        upload_dir = os.path.abspath(self.UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        return os.path.join(upload_dir, filename)
        

@lru_cache()
def get_settings() -> Settings:
    """获取应用配置实例
    
    使用LRU缓存确保配置单例，提高性能。
    
    Returns:
        Settings实例
    """
    return Settings()


# 全局配置实例
settings = get_settings()


# 配置验证函数
def validate_settings() -> None:
    """验证配置的有效性
    
    在应用启动时调用，确保关键配置项正确设置。
    
    Raises:
        ValueError: 当配置无效时抛出异常
    """
    if settings.is_production:
        # 生产环境必须设置的配置项
        required_prod_settings = [
            ("SECRET_KEY", "生产环境必须设置SECRET_KEY"),
            ("POSTGRES_PASSWORD", "生产环境必须设置数据库密码"),
        ]
        
        for setting_name, error_msg in required_prod_settings:
            value = getattr(settings, setting_name)
            if not value or (setting_name == "SECRET_KEY" and value == "your-secret-key-change-in-production"):
                raise ValueError(error_msg)
    
    # 验证端口范围
    if not (1 <= settings.SERVER_PORT <= 65535):
        raise ValueError(f"无效的服务器端口: {settings.SERVER_PORT}")
    
    # 验证文件大小限制
    if settings.MAX_UPLOAD_SIZE <= 0:
        raise ValueError("最大上传文件大小必须大于0")
    
    # 验证Redis配置
    if not (0 <= settings.REDIS_DB <= 15):
        raise ValueError(f"无效的Redis数据库编号: {settings.REDIS_DB}")


# 导出主要配置
__all__ = ["settings", "get_settings", "validate_settings", "Settings"]