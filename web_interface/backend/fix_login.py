#!/usr/bin/env python3
"""
修复登录问题的脚本

检查并创建默认用户，解决登录无法成功的问题。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import engine, Base, get_db_session
from app.core.config import settings
from app.core.security import get_password_hash, UserRole
from app.models.database import User
from app.crud.user import user_crud

async def check_database_tables():
    """检查数据库表是否存在"""
    print("🔍 检查数据库表结构...")
    
    async with engine.begin() as conn:
        # 检查用户表是否存在
        if settings.get_database_url(async_driver=True).startswith('sqlite'):
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
            ))
            table_exists = result.fetchone() is not None
        else:
            result = await conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');"
            ))
            table_exists = result.scalar()
        
        print(f"   用户表存在: {'✅' if table_exists else '❌'}")
        
        if not table_exists:
            print("   正在创建数据库表...")
            await conn.run_sync(Base.metadata.create_all)
            print("   ✅ 数据库表创建完成")
        
        return table_exists

async def check_users():
    """检查现有用户"""
    print("👥 检查现有用户...")
    
    async with get_db_session() as session:
        try:
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            print(f"   现有用户数量: {len(users)}")
            
            for user in users:
                print(f"   - {user.username} ({user.email}) - {user.role.value} - {'✅活跃' if user.is_active else '❌禁用'}")
            
            return users
        except Exception as e:
            print(f"   ❌ 查询用户失败: {e}")
            return []

async def create_default_users():
    """创建默认用户"""
    print("👤 创建默认用户...")
    
    async with get_db_session() as session:
        users_created = []
        
        # 创建管理员用户
        try:
            admin_user = await user_crud.get_by_username(session, username="admin")
            if not admin_user:
                admin_user = await user_crud.create(
                    session,
                    username="admin",
                    email="admin@trademaster.com",
                    password="admin123",
                    full_name="系统管理员",
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True
                )
                users_created.append(admin_user)
                print(f"   ✅ 创建管理员用户: {admin_user.username}")
            else:
                print(f"   ⚠️  管理员用户已存在: {admin_user.username}")
        except Exception as e:
            print(f"   ❌ 创建管理员用户失败: {e}")
        
        # 创建演示用户
        try:
            demo_user = await user_crud.get_by_username(session, username="demo")
            if not demo_user:
                demo_user = await user_crud.create(
                    session,
                    username="demo",
                    email="demo@trademaster.com",
                    password="demo123",
                    full_name="演示用户",
                    role=UserRole.USER,
                    is_active=True,
                    is_verified=True
                )
                users_created.append(demo_user)
                print(f"   ✅ 创建演示用户: {demo_user.username}")
            else:
                print(f"   ⚠️  演示用户已存在: {demo_user.username}")
        except Exception as e:
            print(f"   ❌ 创建演示用户失败: {e}")
        
        return users_created

async def test_authentication():
    """测试用户认证"""
    print("🔐 测试用户认证...")
    
    async with get_db_session() as session:
        # 测试管理员用户认证
        try:
            admin_user = await user_crud.authenticate(session, username="admin", password="admin123")
            if admin_user:
                print(f"   ✅ 管理员认证成功: {admin_user.username}")
            else:
                print("   ❌ 管理员认证失败")
        except Exception as e:
            print(f"   ❌ 管理员认证异常: {e}")
        
        # 测试演示用户认证
        try:
            demo_user = await user_crud.authenticate(session, username="demo", password="demo123")
            if demo_user:
                print(f"   ✅ 演示用户认证成功: {demo_user.username}")
            else:
                print("   ❌ 演示用户认证失败")
        except Exception as e:
            print(f"   ❌ 演示用户认证异常: {e}")

async def main():
    """主函数"""
    print("🚀 TradeMaster 登录问题修复脚本")
    print("="*50)
    
    try:
        # 1. 检查数据库表
        await check_database_tables()
        print()
        
        # 2. 检查现有用户
        users = await check_users()
        print()
        
        # 3. 创建默认用户（如果需要）
        if len(users) == 0:
            await create_default_users()
            print()
        
        # 4. 测试认证
        await test_authentication()
        print()
        
        print("🎉 修复完成！")
        print("="*50)
        print("📝 默认登录凭据:")
        print("   管理员 - 用户名: admin, 密码: admin123")
        print("   演示用户 - 用户名: demo, 密码: demo123")
        print("⚠️  请在生产环境中修改默认密码！")
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())