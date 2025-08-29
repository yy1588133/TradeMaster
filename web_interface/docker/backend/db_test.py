#!/usr/bin/env python3
"""
数据库连接测试脚本
用于在Docker容器启动时测试PostgreSQL和Redis连接
"""

import os
import sys
import asyncio
import logging
from urllib.parse import urlparse
from typing import Optional

try:
    import asyncpg
    import redis
    from sqlalchemy.ext.asyncio import create_async_engine
except ImportError as e:
    print(f"缺少必要依赖: {e}")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseTester:
    """数据库连接测试器"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL')
        
        if not self.db_url:
            raise ValueError("DATABASE_URL环境变量未设置")
        if not self.redis_url:
            raise ValueError("REDIS_URL环境变量未设置")
    
    async def test_postgresql_connection(self) -> bool:
        """测试PostgreSQL连接"""
        try:
            logger.info(f"测试PostgreSQL连接: {self.db_url}")
            
            # 方法1: 使用asyncpg直接连接
            parsed = urlparse(self.db_url)
            
            # 提取连接参数
            host = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/') if parsed.path else 'postgres'
            user = parsed.username
            password = parsed.password
            
            logger.info(f"连接参数: host={host}, port={port}, database={database}, user={user}")
            
            # 使用asyncpg连接
            conn = await asyncpg.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            
            # 执行简单查询
            result = await conn.fetchval('SELECT version()')
            logger.info(f"PostgreSQL版本: {result}")
            
            # 检查连接数
            active_connections = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )
            logger.info(f"活跃连接数: {active_connections}")
            
            await conn.close()
            logger.info("✅ PostgreSQL连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接测试失败: {str(e)}")
            
            # 尝试方法2: 使用SQLAlchemy连接
            try:
                logger.info("尝试使用SQLAlchemy连接...")
                engine = create_async_engine(
                    self.db_url,
                    echo=False,
                    pool_size=1,
                    max_overflow=0
                )
                
                async with engine.begin() as conn:
                    result = await conn.execute("SELECT 1")
                    await result.fetchone()
                
                await engine.dispose()
                logger.info("✅ PostgreSQL连接测试成功 (SQLAlchemy)")
                return True
                
            except Exception as e2:
                logger.error(f"❌ SQLAlchemy连接也失败: {str(e2)}")
                return False
    
    def test_redis_connection(self) -> bool:
        """测试Redis连接"""
        try:
            logger.info(f"测试Redis连接: {self.redis_url}")
            
            # 解析Redis URL
            parsed = urlparse(self.redis_url)
            
            # 构建Redis连接参数
            redis_params = {
                'host': parsed.hostname or 'localhost',
                'port': parsed.port or 6379,
                'db': int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0,
                'decode_responses': True,
                'socket_timeout': 10.0,
                'socket_connect_timeout': 10.0
            }
            
            # 如果URL中包含密码，添加到连接参数
            if parsed.password:
                redis_params['password'] = parsed.password
                
            logger.info(f"Redis连接参数: host={redis_params['host']}, port={redis_params['port']}, db={redis_params['db']}")
            
            # 创建Redis连接
            r = redis.Redis(**redis_params)
            
            # 测试连接
            pong = r.ping()
            if pong:
                logger.info("✅ Redis PING测试成功")
                
                # 测试基本操作
                r.set('__test_key__', 'test_value', ex=60)
                value = r.get('__test_key__')
                r.delete('__test_key__')
                
                if value == 'test_value':
                    logger.info("✅ Redis读写测试成功")
                    
                    # 获取Redis信息
                    info = r.info('server')
                    logger.info(f"Redis版本: {info.get('redis_version', 'unknown')}")
                    
                    return True
                else:
                    logger.error("❌ Redis读写测试失败")
                    return False
            else:
                logger.error("❌ Redis PING测试失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ Redis连接测试失败: {str(e)}")
            return False
    
    async def run_all_tests(self) -> bool:
        """运行所有数据库连接测试"""
        logger.info("🚀 开始数据库连接测试...")
        
        # 测试PostgreSQL
        pg_result = await self.test_postgresql_connection()
        
        # 测试Redis  
        redis_result = self.test_redis_connection()
        
        # 汇总结果
        if pg_result and redis_result:
            logger.info("🎉 所有数据库连接测试通过")
            return True
        else:
            logger.error("💥 数据库连接测试失败")
            if not pg_result:
                logger.error("  - PostgreSQL连接失败")
            if not redis_result:
                logger.error("  - Redis连接失败")
            return False

async def main():
    """主函数"""
    try:
        tester = DatabaseTester()
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())