#!/usr/bin/env python3
"""
数据库初始化脚本

创建数据库表结构，插入初始数据（管理员用户、基础配置等）。
可以通过命令行运行，也可以在应用启动时调用。
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import engine, Base
from app.core.config import settings
from app.core.security import get_password_hash, UserRole
from app.models.database import User
from app.crud.user import user_crud


async def create_tables():
    """创建数据库表"""
    print("🔧 正在创建数据库表...")
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 数据库表创建完成")


async def create_admin_user():
    """创建管理员用户"""
    print("👤 正在创建管理员用户...")
    
    async with AsyncSession(engine) as session:
        # 检查是否已存在管理员用户
        existing_admin = await user_crud.get_by_username(session, username="admin")
        
        if existing_admin:
            print("⚠️  管理员用户已存在，跳过创建")
            return existing_admin
        
        # 创建管理员用户
        admin_user = await user_crud.create(
            session,
            username="admin",
            email="admin@trademaster.com",
            password="admin123",  # 默认密码，生产环境应该修改
            full_name="系统管理员",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        print(f"✅ 管理员用户创建成功")
        print(f"   用户名: {admin_user.username}")
        print(f"   邮箱: {admin_user.email}")
        print(f"   默认密码: admin123")
        print("   ⚠️  请及时修改默认密码！")
        
        return admin_user


async def create_demo_user():
    """创建演示用户"""
    print("👤 正在创建演示用户...")
    
    async with AsyncSession(engine) as session:
        # 检查是否已存在演示用户
        existing_user = await user_crud.get_by_username(session, username="demo")
        
        if existing_user:
            print("⚠️  演示用户已存在，跳过创建")
            return existing_user
        
        # 创建演示用户
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
        
        print(f"✅ 演示用户创建成功")
        print(f"   用户名: {demo_user.username}")
        print(f"   邮箱: {demo_user.email}")
        print(f"   密码: demo123")
        
        return demo_user


async def verify_installation():
    """验证安装"""
    print("🔍 正在验证安装...")
    
    async with AsyncSession(engine) as session:
        # 检查用户表
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"✅ 数据库连接正常")
        print(f"   当前用户数量: {len(users)}")
        
        # 显示用户信息
        for user in users:
            print(f"   - {user.username} ({user.email}) - {user.role.value}")


async def init_database():
    """完整的数据库初始化流程"""
    print("🚀 开始数据库初始化...")
    print(f"📊 数据库: {settings.POSTGRES_DB}")
    print(f"🏠 主机: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
    print()
    
    try:
        # 1. 创建表结构
        await create_tables()
        print()
        
        # 2. 创建管理员用户
        await create_admin_user()
        print()
        
        # 3. 创建演示用户（开发环境）
        if settings.DEBUG:
            await create_demo_user()
            print()
        
        # 4. 验证安装
        await verify_installation()
        print()
        
        print("🎉 数据库初始化完成！")
        
        # 显示重要提示
        print("\n" + "="*50)
        print("🔐 重要安全提示:")
        print("1. 请立即修改管理员默认密码！")
        print("2. 生产环境请删除或禁用演示用户")
        print("3. 请确保数据库连接安全")
        print("="*50)
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


async def reset_database():
    """重置数据库（删除所有数据）"""
    print("⚠️  正在重置数据库...")
    print("这会删除所有数据，请确认操作！")
    
    response = input("输入 'yes' 确认重置数据库: ")
    if response.lower() != 'yes':
        print("操作已取消")
        return
    
    async with engine.begin() as conn:
        # 删除所有表
        await conn.run_sync(Base.metadata.drop_all)
        print("🗑️  所有表已删除")
        
        # 重新创建表
        await conn.run_sync(Base.metadata.create_all)  
        print("🔧 表结构已重新创建")
    
    print("✅ 数据库重置完成")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TradeMaster 数据库初始化工具")
    parser.add_argument("--reset", action="store_true", help="重置数据库（删除所有数据）")
    parser.add_argument("--force", action="store_true", help="强制执行，不询问确认")
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            await reset_database()
        else:
            await init_database()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await engine.dispose()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())