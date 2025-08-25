#!/usr/bin/env python3
"""
CORS修复验证脚本
测试修复后的CORS配置是否正常工作
"""

import asyncio
import aiohttp
import sys
from pathlib import Path


async def test_cors_fix():
    """测试CORS修复"""
    print("🔍 测试TradeMaster CORS修复效果...")
    print("=" * 50)
    
    # 测试配置
    backend_url = "http://localhost:8000"
    test_origin = "http://localhost:3000"
    
    print(f"📍 后端地址: {backend_url}")
    print(f"🌐 测试源地址: {test_origin}")
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print("\n🏥 测试1: 健康检查端点")
            try:
                async with session.get(f"{backend_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ 健康检查成功: {data.get('status', 'unknown')}")
                    else:
                        print(f"⚠️ 健康检查返回状态码: {response.status}")
                        
            except asyncio.TimeoutError:
                print("❌ 健康检查超时 - 后端服务可能未完全启动")
                return False
            except Exception as e:
                print(f"❌ 健康检查失败: {e}")
                return False
            
            print("\n🚀 测试2: CORS预检请求")
            headers = {
                'Origin': test_origin,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            try:
                async with session.options(
                    f"{backend_url}/api/v1/auth/register",
                    headers=headers
                ) as response:
                    print(f"   预检请求状态码: {response.status}")
                    
                    if response.status == 200:
                        print("✅ CORS预检请求成功!")
                        
                        # 检查响应头
                        cors_headers = {
                            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
                        }
                        
                        print("\n📋 CORS响应头:")
                        for header, value in cors_headers.items():
                            if value:
                                print(f"   {header}: {value}")
                            else:
                                print(f"   ❌ {header}: 未设置")
                        
                        # 验证关键头部
                        required_checks = [
                            ('Allow-Origin', cors_headers['Access-Control-Allow-Origin'], [test_origin, '*']),
                            ('Allow-Methods', cors_headers['Access-Control-Allow-Methods'], ['POST', '*']),
                            ('Allow-Headers', cors_headers['Access-Control-Allow-Headers'], ['Content-Type', '*']),
                        ]
                        
                        print("\n✅ CORS配置验证:")
                        all_good = True
                        for check_name, header_value, expected in required_checks:
                            if header_value and any(exp in header_value for exp in expected):
                                print(f"   ✅ {check_name}: 正确")
                            else:
                                print(f"   ❌ {check_name}: 可能有问题")
                                all_good = False
                        
                        return all_good
                    else:
                        print(f"❌ CORS预检请求失败: HTTP {response.status}")
                        text = await response.text()
                        print(f"   响应内容: {text}")
                        return False
                        
            except asyncio.TimeoutError:
                print("❌ CORS预检请求超时")
                return False
            except Exception as e:
                print(f"❌ CORS预检请求异常: {e}")
                return False
            
    except Exception as e:
        print(f"❌ 连接后端服务失败: {e}")
        return False


async def main():
    """主函数"""
    print("🎯 TradeMaster CORS修复验证工具")
    print("=" * 50)
    
    success = await test_cors_fix()
    
    if success:
        print("\n🎉 恭喜！CORS修复验证通过")
        print("📱 前端现在应该可以正常登录了")
        print("\n💡 建议测试:")
        print("   1. 打开浏览器访问 http://localhost:3000")
        print("   2. 尝试注册或登录功能")
        print("   3. 检查浏览器控制台是否还有CORS错误")
    else:
        print("\n❌ CORS修复验证失败")
        print("🔧 建议检查:")
        print("   1. 确保后端服务已完全启动: docker compose logs backend")
        print("   2. 检查端口配置: frontend/.env 和 backend/.env")
        print("   3. 重启服务: docker compose restart")
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中出现错误: {e}")
        sys.exit(1)