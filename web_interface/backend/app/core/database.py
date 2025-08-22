"""
数据库核心配置和连接管理

提供异步SQLAlchemy引擎、会话管理、连接池配置等数据库核心功能。
支持PostgreSQL异步连接，包含健康检查和连接池优化。
"""

import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
import logging

from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """SQLAlchemy声明式基类
    
    所有数据库模型都应该继承这个基类。
    包含通用的表配置和约定。
    """
    pass


# 创建异步数据库引擎
def create_database_engine() -> AsyncEngine:
    """创建异步数据库引擎
    
    配置连接池、超时、重试等参数，优化数据库连接性能。
    
    Returns:
        AsyncEngine: 配置好的异步数据库引擎
    """
    # 构建数据库连接URL
    database_url = settings.get_database_url(async_driver=True)
    
    # 连接池配置
    if settings.is_production:
        # 生产环境使用连接池
        poolclass = QueuePool
        pool_size = settings.DB_POOL_SIZE
        max_overflow = settings.DB_MAX_OVERFLOW
        pool_timeout = settings.DB_POOL_TIMEOUT
        pool_recycle = 3600  # 1小时回收连接
        pool_pre_ping = True  # 连接前ping测试
    else:
        # 开发环境使用简单连接池
        poolclass = QueuePool
        pool_size = 5
        max_overflow = 10
        pool_timeout = 30
        pool_recycle = 1800  # 30分钟回收连接
        pool_pre_ping = True
    
    # 创建引擎
    engine = create_async_engine(
        database_url,
        # 连接池配置
        poolclass=poolclass,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
        
        # 性能配置
        echo=settings.DEBUG,  # 开发环境输出SQL日志
        echo_pool=False,  # 不输出连接池日志
        future=True,  # 使用SQLAlchemy 2.0风格
        
        # 连接参数
        connect_args={
            "server_settings": {
                "application_name": "TradeMaster_Web_Interface",
            },
            "command_timeout": 60,
        }
    )
    
    return engine


# 全局数据库引擎实例
engine: AsyncEngine = create_database_engine()

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 不在提交后过期对象
    autoflush=True,  # 自动flush
    autocommit=False,  # 不自动提交
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话上下文管理器
    
    使用async with语句自动管理会话的创建和关闭。
    在异常情况下自动回滚事务。
    
    Yields:
        AsyncSession: 数据库会话实例
        
    Example:
        async with get_db_session() as session:
            result = await session.execute(select(User))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入的数据库会话获取器
    
    用于FastAPI路由函数的依赖注入。
    
    Yields:
        AsyncSession: 数据库会话实例
        
    Example:
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with get_db_session() as session:
        yield session


# 为兼容性提供别名
get_async_db = get_db


async def init_database() -> None:
    """初始化数据库
    
    创建所有数据表。通常在应用启动时调用。
    注意：生产环境建议使用Alembic进行数据库迁移。
    """
    logger.info("正在初始化数据库...")
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("数据库初始化完成")


async def drop_database() -> None:
    """删除所有数据表
    
    警告：这将删除所有数据！仅用于开发和测试环境。
    """
    logger.warning("正在删除所有数据表...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("所有数据表已删除")


async def check_database_connection() -> bool:
    """检查数据库连接健康状态
    
    Returns:
        bool: 连接是否正常
    """
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False


async def get_database_info() -> dict:
    """获取数据库信息
    
    Returns:
        dict: 包含数据库版本、连接数等信息的字典
    """
    try:
        async with get_db_session() as session:
            # 获取PostgreSQL版本
            version_result = await session.execute(text("SELECT version()"))
            version = version_result.scalar()
            
            # 获取当前连接数
            conn_result = await session.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            ))
            active_connections = conn_result.scalar()
            
            # 获取数据库大小
            size_result = await session.execute(text(
                f"SELECT pg_size_pretty(pg_database_size('{settings.POSTGRES_DB}'))"
            ))
            database_size = size_result.scalar()
            
            return {
                "version": version,
                "active_connections": active_connections,
                "database_size": database_size,
                "pool_size": engine.pool.size(),
                "checked_out_connections": engine.pool.checkedout(),
            }
    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        return {"error": str(e)}


# 事件监听器：连接创建时的初始化
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """数据库连接初始化事件监听器
    
    在每个新连接创建时执行初始化配置。
    """
    # 这里主要针对PostgreSQL，可以设置一些连接级别的参数
    pass


@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """SQL执行前的事件监听器
    
    可用于记录SQL执行日志、性能监控等。
    """
    if settings.DEBUG:
        logger.debug(f"执行SQL: {statement}")


# 数据库工具类
class DatabaseManager:
    """数据库管理工具类
    
    提供数据库操作的高级接口，包括事务管理、批量操作等。
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute_in_transaction(self, func, *args, **kwargs):
        """在事务中执行函数
        
        Args:
            func: 要执行的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        try:
            result = await func(self.session, *args, **kwargs)
            await self.session.commit()
            return result
        except Exception:
            await self.session.rollback()
            raise
    
    async def bulk_insert(self, model_class, data_list: list) -> None:
        """批量插入数据
        
        Args:
            model_class: SQLAlchemy模型类
            data_list: 要插入的数据列表
        """
        objects = [model_class(**data) for data in data_list]
        self.session.add_all(objects)
        await self.session.flush()
    
    async def bulk_update(self, model_class, data_list: list, update_fields: list) -> None:
        """批量更新数据
        
        Args:
            model_class: SQLAlchemy模型类
            data_list: 包含id和更新字段的数据列表
            update_fields: 要更新的字段列表
        """
        for data in data_list:
            await self.session.execute(
                model_class.__table__.update()
                .where(model_class.id == data['id'])
                .values(**{field: data[field] for field in update_fields if field in data})
            )


# 导出主要组件
__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db_session",
    "get_db",
    "get_async_db",
    "init_database",
    "drop_database",
    "check_database_connection",
    "get_database_info",
    "DatabaseManager"
]