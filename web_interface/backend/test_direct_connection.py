#!/usr/bin/env python3
"""
直接测试数据库连接
"""
import asyncio
import asyncpg
import redis
import traceback

async def test_postgresql():
    print("=== 测试PostgreSQL连接 ===")
    try:
        # 使用配置的连接参数
        conn = await asyncpg.connect(
            host="localhost",
            port=15432,
            user="trademaster", 
            password="TradeMaster2024!",
            database="trademaster_web"
        )
        
        # 简单查询测试
        result = await conn.fetchval("SELECT 'PostgreSQL连接成功!' as message")
        print(f"成功: {result}")
        
        # 查看数据库信息
        db_info = await conn.fetchrow("SELECT current_database(), current_user, version()")
        print(f"数据库: {db_info['current_database']}")
        print(f"用户: {db_info['current_user']}")  
        print(f"版本: {db_info['version']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"PostgreSQL连接失败: {e}")
        print("详细错误:")
        traceback.print_exc()
        return False

def test_redis():
    print("\n=== 测试Redis连接 ===")
    try:
        # 使用配置的连接参数
        r = redis.Redis(
            host="localhost",
            port=16379,
            password="TradeMaster2024!",
            db=0,
            decode_responses=True
        )
        
        # 简单ping测试
        response = r.ping()
        if response:
            print("Redis连接成功!")
            
        # 获取Redis信息
        info = r.info()
        print(f"Redis版本: {info.get('redis_version')}")
        print(f"已用内存: {info.get('used_memory_human')}")
        
        return True
        
    except Exception as e:
        print(f"Redis连接失败: {e}")
        print("详细错误:")
        traceback.print_exc()
        return False

async def main():
    print("开始数据库连接测试...")
    
    # 测试PostgreSQL
    pg_ok = await test_postgresql()
    
    # 测试Redis  
    redis_ok = test_redis()
    
    print("\n=== 测试结果总结 ===")
    print(f"PostgreSQL: {'成功' if pg_ok else '失败'}")
    print(f"Redis: {'成功' if redis_ok else '失败'}")
    
    if pg_ok and redis_ok:
        print("所有数据库连接正常!")
    else:
        print("数据库连接存在问题")

if __name__ == "__main__":
    asyncio.run(main())