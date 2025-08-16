"""
Alembic环境配置

配置数据库迁移环境，支持异步SQLAlchemy和自动生成迁移脚本。
集成项目配置，提供离线和在线迁移模式。
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# 添加项目路径到sys.path
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)
sys.path.insert(0, parent_path)

# 导入项目配置和模型
from app.core.config import settings
from app.core.database import Base

# Alembic配置对象
config = context.config

# 设置数据库URL
database_url = settings.get_database_url(async_driver=False)  # 使用同步驱动用于迁移
config.set_main_option("sqlalchemy.url", database_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的MetaData对象用于自动生成迁移
target_metadata = Base.metadata

# 其他值由env.py中的Alembic Config对象填充
# 从config.get_main_option获取值()


def run_migrations_offline() -> None:
    """在'离线'模式下运行迁移。

    这将配置上下文，只需要一个URL
    而不是Engine，尽管Engine也可以接受
    在这里。通过跳过Engine创建
    我们甚至不需要DBAPI可用。

    使用--sql标志调用alembic以转储SQL脚本而不是连接到数据库。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """运行实际的迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        # 包含特定的对象
        include_object=include_object,
        # 渲染项目配置
        render_as_batch=True,  # 支持SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """确定是否包含对象在迁移中
    
    Args:
        object: 数据库对象
        name: 对象名称
        type_: 对象类型
        reflected: 是否从数据库反射
        compare_to: 比较的目标对象
        
    Returns:
        bool: 是否包含此对象
    """
    # 跳过某些表或索引
    if type_ == "table":
        # 跳过Alembic版本表
        if name == "alembic_version":
            return False
        # 跳过临时表
        if name.startswith("temp_"):
            return False
    
    # 包含其他所有对象
    return True


async def run_async_migrations():
    """异步运行迁移"""
    # 创建异步引擎
    connectable = create_async_engine(
        settings.get_database_url(async_driver=True),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在'在线'模式下运行迁移。

    在这种情况下，我们需要创建一个Engine
    并将连接与上下文关联。
    """
    # 检查是否使用异步引擎
    if settings.get_database_url().startswith("postgresql+asyncpg"):
        # 使用异步迁移
        asyncio.run(run_async_migrations())
    else:
        # 使用同步迁移
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)


# 根据模式运行相应的迁移函数
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()