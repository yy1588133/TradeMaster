#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后的数据库连接测试
"""
import asyncio
import sys
from pathlib import Path

# 设置输出编码
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_postgresql_connection():
    """测试PostgreSQL连接"""
    try:
        import asyncpg
        print("测试PostgreSQL连接...")
        
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="trademaster", 
            password="TradeMaster2024!",  # 使用修复后的密码
            database="trademaster_web"
        )
        
        # 简单查询测试
        result = await conn.fetchval("SELECT 'PostgreSQL连接成功!' as message")
        print(f"成功: {result}")
        
        # 查看数据库信息
        db_info = await conn.fetchrow("SELECT current_database(), current_user, version()")
        print(f"数据库: {db_info['current_database']}")
        print(f"用户: {db_info['current_user']}")  
        print(f"版本: {db_info['version'][:50]}...")
        
        await conn.close()
        return True
        
    except ImportError:
        print("缺少asyncpg依赖，跳过PostgreSQL测试")
        return False
    except Exception as e:
        print(f"PostgreSQL连接失败: {e}")
        return False

def test_redis_connection():
    """测试Redis连接"""
    try:
        import redis
        print("测试Redis连接...")
        
        r = redis.Redis(
            host="localhost",
            port=6379,
            password="TradeMaster2024!",  # 使用修复后的密码
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
        
        # 测试读写
        test_key = "trademaster:test:fixed"
        r.set(test_key, "连接修复成功", ex=60)
        value = r.get(test_key)
        print(f"读写测试: {value}")
        
        r.delete(test_key)  # 清理
        return True
        
    except ImportError:
        print("缺少redis依赖，跳过Redis测试")
        return False
    except Exception as e:
        print(f"Redis连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 50)
    print("TradeMaster 数据库连接修复验证")
    print("=" * 50)
    
    # 测试PostgreSQL
    pg_ok = await test_postgresql_connection()
    
    print()  # 空行分隔
    
    # 测试Redis  
    redis_ok = test_redis_connection()
    
    print()
    print("=" * 50)
    print("测试结果总结")
    print("=" * 50)
    print(f"PostgreSQL: {'成功' if pg_ok else '失败'}")
    print(f"Redis: {'成功' if redis_ok else '失败'}")
    
    if pg_ok and redis_ok:
        print()
        print("数据库连接修复成功！")
        print("现在可以重新启动后端服务了")
    elif pg_ok or redis_ok:
        print()
        print("部分连接成功，请检查失败的服务")
    else:
        print()
        print("连接仍然失败，需要进一步排查")
    
    return pg_ok and redis_ok

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试执行出错: {e}")
        sys.exit(1)