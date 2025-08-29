#!/usr/bin/env python3
"""
测试SQLAlchemy引擎连接
"""
import asyncio
import traceback
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_sqlalchemy_engine():
    print("=== 测试SQLAlchemy异步引擎连接 ===")
    
    try:
        # 使用与配置相同的连接参数
        database_url = "postgresql+asyncpg://trademaster:TradeMaster2024!@localhost:15432/trademaster_web"
        print(f"连接URL: {database_url}")
        
        # 创建异步引擎
        engine = create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=False,
            future=True
        )
        
        print("引擎创建成功")
        
        # 测试连接
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 'SQLAlchemy引擎连接成功!' as message, current_user, current_database()"))
            row = result.fetchone()
            print(f"测试查询结果: {row[0]}")
            print(f"当前用户: {row[1]}")
            print(f"当前数据库: {row[2]}")
        
        # 测试连接池状态
        pool = engine.pool
        print(f"连接池状态: size={pool.size()}, checked_in={pool.checkedin()}, checked_out={pool.checkedout()}")
        
        await engine.dispose()
        print("引擎连接测试成功!")
        return True
        
    except Exception as e:
        print(f"SQLAlchemy引擎连接失败: {e}")
        print("详细错误:")
        traceback.print_exc()
        return False

async def main():
    print("开始SQLAlchemy引擎连接测试...")
    success = await test_sqlalchemy_engine()
    
    if success:
        print("SQLAlchemy引擎连接正常!")
    else:
        print("SQLAlchemy引擎连接存在问题")

if __name__ == "__main__":
    asyncio.run(main())