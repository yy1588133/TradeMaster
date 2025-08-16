#!/usr/bin/env python3
"""
认证系统测试脚本

测试用户注册、登录、令牌刷新等认证相关功能。
用于验证认证系统的正确性和安全性。
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine
from app.core.security import verify_password, verify_token, TokenType
from app.services.user_service import user_service
from app.crud.user import user_crud
from app.models.database import UserRole


class AuthTester:
    """认证系统测试类"""
    
    def __init__(self):
        self.test_results = []
        self.test_data = {}
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: dict = None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
    
    async def test_user_registration(self):
        """测试用户注册"""
        print("\n🔐 测试用户注册...")
        
        async with AsyncSession(engine) as session:
            try:
                # 测试正常注册
                user = await user_service.register_user(
                    session,
                    username="testuser",
                    email="test@example.com",
                    password="TestPass123!",
                    full_name="测试用户"
                )
                
                self.test_data["test_user"] = user
                self.log_test(
                    "用户注册", 
                    True, 
                    f"用户 {user.username} 注册成功",
                    {"user_id": user.id, "username": user.username}
                )
                
                # 测试重复用户名注册
                try:
                    await user_service.register_user(
                        session,
                        username="testuser",
                        email="test2@example.com", 
                        password="TestPass123!"
                    )
                    self.log_test("重复用户名检测", False, "应该阻止重复用户名注册")
                except Exception:
                    self.log_test("重复用户名检测", True, "正确阻止了重复用户名注册")
                
                # 测试重复邮箱注册
                try:
                    await user_service.register_user(
                        session,
                        username="testuser2",
                        email="test@example.com",
                        password="TestPass123!"
                    )
                    self.log_test("重复邮箱检测", False, "应该阻止重复邮箱注册")
                except Exception:
                    self.log_test("重复邮箱检测", True, "正确阻止了重复邮箱注册")
                
                # 测试弱密码
                try:
                    await user_service.register_user(
                        session,
                        username="testuser3",
                        email="test3@example.com",
                        password="123"
                    )
                    self.log_test("弱密码检测", False, "应该阻止弱密码")
                except Exception:
                    self.log_test("弱密码检测", True, "正确阻止了弱密码")
                    
            except Exception as e:
                self.log_test("用户注册", False, f"注册失败: {str(e)}")
    
    async def test_user_authentication(self):
        """测试用户认证"""
        print("\n🔑 测试用户认证...")
        
        async with AsyncSession(engine) as session:
            try:
                # 测试正确凭据登录
                user, token_data = await user_service.authenticate_user(
                    session,
                    username="testuser",
                    password="TestPass123!",
                    ip_address="127.0.0.1",
                    user_agent="Test Client"
                )
                
                self.test_data["access_token"] = token_data["access_token"]
                self.test_data["refresh_token"] = token_data["refresh_token"]
                
                self.log_test(
                    "用户登录",
                    True,
                    f"用户 {user.username} 登录成功",
                    {
                        "user_id": user.id,
                        "has_access_token": bool(token_data["access_token"]),
                        "has_refresh_token": bool(token_data["refresh_token"])
                    }
                )
                
                # 测试错误密码
                try:
                    await user_service.authenticate_user(
                        session,
                        username="testuser",
                        password="wrongpassword"
                    )
                    self.log_test("错误密码检测", False, "应该阻止错误密码登录")
                except Exception:
                    self.log_test("错误密码检测", True, "正确阻止了错误密码登录")
                
                # 测试不存在的用户
                try:
                    await user_service.authenticate_user(
                        session,
                        username="nonexistentuser",
                        password="TestPass123!"
                    )
                    self.log_test("不存在用户检测", False, "应该阻止不存在的用户登录")
                except Exception:
                    self.log_test("不存在用户检测", True, "正确阻止了不存在的用户登录")
                    
            except Exception as e:
                self.log_test("用户认证", False, f"认证失败: {str(e)}")
    
    async def test_token_operations(self):
        """测试令牌操作"""
        print("\n🎫 测试令牌操作...")
        
        if "access_token" not in self.test_data:
            self.log_test("令牌测试", False, "没有可用的访问令牌")
            return
        
        try:
            # 测试访问令牌验证
            access_token = self.test_data["access_token"]
            payload = verify_token(access_token, TokenType.ACCESS)
            
            self.log_test(
                "访问令牌验证",
                True,
                "访问令牌验证成功",
                {
                    "user_id": payload.get("sub"),
                    "username": payload.get("username"),
                    "expires_at": payload.get("exp")
                }
            )
            
            # 测试刷新令牌
            async with AsyncSession(engine) as session:
                refresh_token = self.test_data["refresh_token"]
                user, new_token_data = await user_service.refresh_user_token(
                    session,
                    refresh_token=refresh_token
                )
                
                self.test_data["new_access_token"] = new_token_data["access_token"]
                
                self.log_test(
                    "令牌刷新",
                    True,
                    "令牌刷新成功",
                    {
                        "user_id": user.id,
                        "new_token_available": bool(new_token_data["access_token"])
                    }
                )
            
        except Exception as e:
            self.log_test("令牌操作", False, f"令牌操作失败: {str(e)}")
    
    async def test_password_operations(self):
        """测试密码操作"""
        print("\n🔒 测试密码操作...")
        
        async with AsyncSession(engine) as session:
            try:
                # 获取测试用户
                user = self.test_data.get("test_user")
                if not user:
                    user = await user_crud.get_by_username(session, username="testuser")
                
                if not user:
                    self.log_test("密码测试", False, "找不到测试用户")
                    return
                
                # 测试密码修改
                await user_service.change_user_password(
                    session,
                    user_id=user.id,
                    current_password="TestPass123!",
                    new_password="NewTestPass123!"
                )
                
                self.log_test("密码修改", True, "密码修改成功")
                
                # 验证新密码
                updated_user = await user_crud.get(session, user_id=user.id)
                password_valid = verify_password("NewTestPass123!", updated_user.hashed_password)
                
                self.log_test(
                    "新密码验证",
                    password_valid,
                    "新密码验证成功" if password_valid else "新密码验证失败"
                )
                
                # 测试错误的当前密码
                try:
                    await user_service.change_user_password(
                        session,
                        user_id=user.id,
                        current_password="wrongcurrentpassword",
                        new_password="AnotherNewPass123!"
                    )
                    self.log_test("错误当前密码检测", False, "应该阻止错误的当前密码")
                except Exception:
                    self.log_test("错误当前密码检测", True, "正确阻止了错误的当前密码")
                    
            except Exception as e:
                self.log_test("密码操作", False, f"密码操作失败: {str(e)}")
    
    async def test_user_profile_operations(self):
        """测试用户资料操作"""
        print("\n👤 测试用户资料操作...")
        
        async with AsyncSession(engine) as session:
            try:
                # 获取测试用户
                user = self.test_data.get("test_user")
                if not user:
                    user = await user_crud.get_by_username(session, username="testuser")
                
                if not user:
                    self.log_test("资料测试", False, "找不到测试用户")
                    return
                
                # 测试获取用户资料
                profile = await user_service.get_user_profile(session, user_id=user.id)
                
                self.log_test(
                    "获取用户资料",
                    True,
                    f"成功获取用户 {profile.username} 的资料",
                    {
                        "username": profile.username,
                        "email": profile.email,
                        "full_name": profile.full_name
                    }
                )
                
                # 测试更新用户资料
                updated_profile = await user_service.update_user_profile(
                    session,
                    user_id=user.id,
                    update_data={
                        "full_name": "更新后的测试用户",
                        "avatar_url": "https://example.com/avatar.jpg"
                    }
                )
                
                self.log_test(
                    "更新用户资料",
                    True,
                    "用户资料更新成功",
                    {
                        "new_full_name": updated_profile.full_name,
                        "avatar_url": updated_profile.avatar_url
                    }
                )
                
            except Exception as e:
                self.log_test("用户资料操作", False, f"用户资料操作失败: {str(e)}")
    
    async def test_user_logout(self):
        """测试用户登出"""
        print("\n🚪 测试用户登出...")
        
        async with AsyncSession(engine) as session:
            try:
                # 获取测试用户
                user = self.test_data.get("test_user")
                if not user:
                    user = await user_crud.get_by_username(session, username="testuser")
                
                if not user:
                    self.log_test("登出测试", False, "找不到测试用户")
                    return
                
                # 测试登出
                access_token = self.test_data.get("new_access_token") or self.test_data.get("access_token")
                success = await user_service.logout_user(
                    session,
                    session_token=access_token,
                    user_id=user.id
                )
                
                self.log_test(
                    "用户登出",
                    success,
                    "用户登出成功" if success else "用户登出失败"
                )
                
            except Exception as e:
                self.log_test("用户登出", False, f"登出失败: {str(e)}")
    
    async def cleanup_test_data(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        async with AsyncSession(engine) as session:
            try:
                # 删除测试用户
                test_user = await user_crud.get_by_username(session, username="testuser")
                if test_user:
                    await user_crud.delete(session, user_id=test_user.id)
                    self.log_test("清理测试数据", True, "测试用户已删除")
                else:
                    self.log_test("清理测试数据", True, "没有需要清理的测试用户")
                    
            except Exception as e:
                self.log_test("清理测试数据", False, f"清理失败: {str(e)}")
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("📊 测试结果摘要")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests / total_tests * 100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("="*60)
    
    async def run_all_tests(self, cleanup: bool = True):
        """运行所有测试"""
        print("🧪 开始认证系统测试...\n")
        
        # 运行测试
        await self.test_user_registration()
        await self.test_user_authentication()
        await self.test_token_operations()
        await self.test_password_operations()
        await self.test_user_profile_operations()
        await self.test_user_logout()
        
        # 清理测试数据
        if cleanup:
            await self.cleanup_test_data()
        
        # 打印摘要
        self.print_summary()
        
        return sum(1 for result in self.test_results if result["success"]) == len(self.test_results)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TradeMaster 认证系统测试工具")
    parser.add_argument("--no-cleanup", action="store_true", help="不清理测试数据")
    parser.add_argument("--output", help="输出测试结果到JSON文件")
    
    args = parser.parse_args()
    
    try:
        tester = AuthTester()
        success = await tester.run_all_tests(cleanup=not args.no_cleanup)
        
        # 输出到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(tester.test_results, f, ensure_ascii=False, indent=2)
            print(f"测试结果已保存到: {args.output}")
        
        # 设置退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n测试已取消")
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await engine.dispose()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())