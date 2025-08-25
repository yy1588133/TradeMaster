"""
数据库连接和操作诊断脚本
测试异步数据库操作是否正常工作
"""
import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import engine, get_db_session
from app.core.config import settings
from app.models.database import User
from app.crud.user import user_crud
from app.core.security import get_password_hash

async def test_basic_connection():
    """测试基础数据库连接"""
    print("1. 测试基础数据库连接...")
    try:
        start_time = time.time()
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            end_time = time.time()
            
            print(f"   ✅ 基础连接成功: {value}, 耗时: {end_time - start_time:.3f}秒")
            return True
    except Exception as e:
        print(f"   ❌ 基础连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_user_table_access():
    """测试用户表访问"""
    print("2. 测试用户表访问...")
    try:
        start_time = time.time()
        async with get_db_session() as session:
            result = await session.execute(select(User).limit(1))
            users = result.scalars().all()
            end_time = time.time()
            
            print(f"   ✅ 用户表访问成功, 找到 {len(users)} 个用户, 耗时: {end_time - start_time:.3f}秒")
            return True
    except Exception as e:
        print(f"   ❌ 用户表访问失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_user_authentication():
    """测试用户认证操作"""
    print("3. 测试用户认证操作...")
    try:
        start_time = time.time()
        async with get_db_session() as session:
            # 尝试认证管理员用户
            user = await user_crud.authenticate(session, username="admin", password="admin123")
            end_time = time.time()
            
            if user:
                print(f"   ✅ 用户认证成功: {user.username}, 耗时: {end_time - start_time:.3f}秒")
            else:
                print(f"   ⚠️ 用户认证返回None, 耗时: {end_time - start_time:.3f}秒")
            return True
    except Exception as e:
        print(f"   ❌ 用户认证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_concurrent_operations():
    """测试并发数据库操作"""
    print("4. 测试并发数据库操作...")
    try:
        start_time = time.time()
        
        # 创建多个并发的数据库查询
        async def single_query():
            async with get_db_session() as session:
                result = await session.execute(select(User).limit(1))
                return result.scalars().first()
        
        # 并发执行5个查询
        tasks = [single_query() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - success_count
        
        print(f"   并发操作结果: {success_count} 成功, {error_count} 失败, 耗时: {end_time - start_time:.3f}秒")
        
        if error_count > 0:
            print("   错误详情:")
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"     任务 {i+1}: {result}")
        
        return error_count == 0
    except Exception as e:
        print(f"   ❌ 并发测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_transaction_operations():
    """测试事务操作"""
    print("5. 测试事务操作...")
    try:
        start_time = time.time()
        async with get_db_session() as session:
            # 开始事务
            async with session.begin():
                # 模拟一个更新操作
                result = await session.execute(
                    text("UPDATE users SET login_count = login_count + 1 WHERE username = 'admin'")
                )
                print(f"     更新了 {result.rowcount} 行")
                
                # 模拟一个回滚（不实际提交）
                await session.rollback()
                
        end_time = time.time()
        print(f"   ✅ 事务操作测试完成, 耗时: {end_time - start_time:.3f}秒")
        return True
    except Exception as e:
        print(f"   ❌ 事务操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("TradeMaster Database Diagnostics")
    print("="*50)
    print(f"数据库URL: {settings.get_database_url()}")
    print(f"调试模式: {settings.DEBUG}")
    print()
    
    tests = [
        test_basic_connection,
        test_user_table_access,
        test_user_authentication,
        test_concurrent_operations,
        test_transaction_operations,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            success = await test_func()
            if success:
                passed += 1
            print()
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
            print()
    
    print("="*50)
    print(f"测试总结: {passed}/{total} 通过")
    
    if passed < total:
        print("\n🔧 建议修复措施:")
        print("1. 检查SQLite数据库文件权限")
        print("2. 考虑切换到PostgreSQL以获得更好的异步支持")
        print("3. 检查是否有其他进程锁定了数据库文件")
        print("4. 验证aiosqlite驱动版本兼容性")
    else:
        print("\n✅ 所有数据库操作测试通过！")
    
    # 清理连接
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())