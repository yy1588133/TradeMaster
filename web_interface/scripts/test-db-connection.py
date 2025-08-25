#!/usr/bin/env python3
"""
TradeMaster 数据库连接测试工具

用法：
python test-db-connection.py [--scheme docker|native]
"""

import asyncio
import sys
import os
from pathlib import Path
import argparse

# 添加backend路径到Python路径
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from sqlalchemy.ext.asyncio import create_async_engine
    import redis.asyncio as redis
    from sqlalchemy import text
except ImportError as e:
    print(f"❌ 缺少必要的依赖: {e}")
    print("请安装依赖: pip install sqlalchemy asyncpg redis")
    sys.exit(1)


class DatabaseTester:
    """数据库连接测试器"""
    
    def __init__(self, scheme: str = "auto"):
        self.scheme = scheme
        self.config = self._load_config()
    
    def _load_config(self):
        """加载数据库配置"""
        # 读取数据库方案
        scheme_file = Path("../.db-scheme")
        if self.scheme == "auto" and scheme_file.exists():
            with open(scheme_file, 'r') as f:
                self.scheme = f.read().strip()
        
        if self.scheme not in ["docker", "native"]:
            self.scheme = "docker"  # 默认Docker方案
        
        # 根据方案设置配置
        if self.scheme == "docker":
            return {
                "postgresql": {
                    "host": "localhost",
                    "port": 15432,
                    "user": "trademaster",
                    "password": "TradeMaster2024!",
                    "database": "trademaster_web"
                },
                "redis": {
                    "host": "localhost", 
                    "port": 16379,
                    "password": "TradeMaster2024!",
                    "db": 0
                }
            }
        else:  # native
            return {
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "trademaster",
                    "password": "TradeMaster2024!",
                    "database": "trademaster_web"
                },
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "password": "TradeMaster2024!",
                    "db": 0
                }
            }
    
    async def test_postgresql(self):
        """测试PostgreSQL连接"""
        print(f"🔍 测试PostgreSQL连接 ({self.scheme}方案)...")
        
        pg_config = self.config["postgresql"]
        database_url = (
            f"postgresql+asyncpg://{pg_config['user']}:{pg_config['password']}"
            f"@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
        )
        
        try:
            engine = create_async_engine(database_url, echo=False)
            
            async with engine.begin() as conn:
                # 基础连接测试
                result = await conn.execute(text("SELECT version();"))
                version = result.scalar()
                print(f"✅ PostgreSQL连接成功")
                print(f"   版本: {version}")
                
                # 测试数据库和用户权限
                result = await conn.execute(text("SELECT current_database();"))
                db_name = result.scalar()
                print(f"   当前数据库: {db_name}")
                
                result = await conn.execute(text("SELECT current_user;"))
                user_name = result.scalar()
                print(f"   当前用户: {user_name}")
                
                # 测试表创建权限
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS test_connection (
                        id SERIAL PRIMARY KEY,
                        test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                await conn.execute(text("""
                    INSERT INTO test_connection DEFAULT VALUES;
                """))
                
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM test_connection;
                """))
                count = result.scalar()
                print(f"   测试记录数: {count}")
                
                # 清理测试表
                await conn.execute(text("DROP TABLE test_connection;"))
                
            await engine.dispose()
            return True
            
        except Exception as e:
            print(f"❌ PostgreSQL连接失败: {e}")
            return False
    
    async def test_redis(self):
        """测试Redis连接"""
        print(f"🔍 测试Redis连接 ({self.scheme}方案)...")
        
        redis_config = self.config["redis"]
        
        try:
            r = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                password=redis_config["password"],
                db=redis_config["db"],
                decode_responses=True
            )
            
            # 基础连接测试
            pong = await r.ping()
            if pong:
                print("✅ Redis连接成功")
                
                # 获取Redis信息
                info = await r.info("server")
                print(f"   Redis版本: {info.get('redis_version', 'unknown')}")
                print(f"   运行模式: {info.get('redis_mode', 'unknown')}")
                
                # 测试读写操作
                test_key = "trademaster:test:connection"
                await r.set(test_key, "test_value", ex=60)
                value = await r.get(test_key)
                
                if value == "test_value":
                    print("   读写测试: 成功")
                else:
                    print("   读写测试: 失败")
                
                # 清理测试键
                await r.delete(test_key)
                
                # 测试不同数据库
                await r.select(1)
                await r.set("test_db", "db1")
                await r.select(0)
                
                print("   多数据库测试: 成功")
                
                await r.close()
                return True
            else:
                print("❌ Redis ping失败")
                return False
                
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("==========================================")
        print("     TradeMaster 数据库连接测试")
        print("==========================================")
        print(f"数据库方案: {self.scheme}")
        print("==========================================")
        
        # 测试PostgreSQL
        pg_success = await self.test_postgresql()
        print()
        
        # 测试Redis  
        redis_success = await self.test_redis()
        print()
        
        # 总结
        print("==========================================")
        print("           测试结果总结")
        print("==========================================")
        
        if pg_success and redis_success:
            print("🎉 所有数据库连接测试通过！")
            print("✅ PostgreSQL: 连接正常")
            print("✅ Redis: 连接正常")
            print("")
            print("您现在可以启动TradeMaster后端应用了。")
            return True
        else:
            print("⚠️ 部分数据库连接测试失败:")
            print(f"{'✅' if pg_success else '❌'} PostgreSQL: {'正常' if pg_success else '失败'}")
            print(f"{'✅' if redis_success else '❌'} Redis: {'正常' if redis_success else '失败'}")
            print("")
            print("请检查数据库服务状态和配置。")
            return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradeMaster数据库连接测试")
    parser.add_argument(
        "--scheme", 
        choices=["docker", "native", "auto"],
        default="auto",
        help="数据库方案 (docker/native/auto)"
    )
    
    args = parser.parse_args()
    
    # 创建测试器并运行测试
    tester = DatabaseTester(args.scheme)
    success = await tester.run_all_tests()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
        sys.exit(1)