#!/usr/bin/env python3
"""简单数据库连接测试脚本"""

import asyncio
import asyncpg

async def test_connection():
    """测试数据库连接"""
    try:
        # 尝试连接到默认的postgres数据库
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='',
            database='postgres'
        )
        
        # 执行简单查询
        result = await conn.fetchval('SELECT 1')
        print(f"✅ 数据库连接成功! 查询结果: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())