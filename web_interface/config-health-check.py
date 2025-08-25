#!/usr/bin/env python3
"""
TradeMaster 配置健康检查工具
用于检测并预防CORS和其他配置问题
"""

import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Optional
import sys
from pathlib import Path


class ConfigHealthChecker:
    """配置健康检查器"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.issues = []
        self.warnings = []
        
    async def check_all(self):
        """执行所有检查"""
        print("🔍 TradeMaster 配置健康检查开始...")
        print("=" * 50)
        
        # 配置文件检查
        self.check_env_files()
        self.check_cors_config()
        self.check_port_consistency()
        
        # 服务连接检查
        await self.check_backend_health()
        await self.check_cors_preflight()
        
        # 输出检查结果
        self.print_results()
        
        return len(self.issues) == 0
    
    def check_env_files(self):
        """检查环境配置文件"""
        print("\n📁 检查环境配置文件...")
        
        # 检查必需的env文件
        required_files = [
            "frontend/.env",
            "backend/.env",
        ]
        
        for file_path in required_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                self.issues.append(f"缺失环境配置文件: {file_path}")
            else:
                print(f"✅ 发现配置文件: {file_path}")
    
    def check_cors_config(self):
        """检查CORS配置"""
        print("\n🌍 检查CORS配置...")
        
        backend_env = self.base_path / "backend/.env"
        if backend_env.exists():
            with open(backend_env, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 检查CORS配置格式
                for line in content.split('\n'):
                    if line.startswith('BACKEND_CORS_ORIGINS='):
                        cors_value = line.split('=', 1)[1]
                        
                        # 检查是否为JSON格式（不推荐在环境变量中）
                        if cors_value.strip().startswith('['):
                            self.warnings.append("CORS配置使用JSON格式，建议使用逗号分隔格式")
                        
                        # 检查是否包含localhost:3000
                        if 'localhost:3000' not in cors_value:
                            self.warnings.append("CORS配置未包含localhost:3000，可能影响前端开发")
                        
                        print(f"✅ CORS配置: {cors_value}")
                        break
                else:
                    self.issues.append("未找到BACKEND_CORS_ORIGINS配置")
    
    def check_port_consistency(self):
        """检查端口配置一致性"""
        print("\n🔌 检查端口配置一致性...")
        
        # 读取前端配置
        frontend_env = self.base_path / "frontend/.env"
        backend_port = None
        
        if frontend_env.exists():
            with open(frontend_env, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('VITE_API_BASE_URL='):
                        url = line.split('=', 1)[1].strip()
                        if ':8000' in url:
                            backend_port = 8000
                        elif ':8001' in url:
                            backend_port = 8001
                            self.warnings.append("前端配置使用8001端口，应该使用8000端口")
                        print(f"📱 前端API配置: {url}")
                        break
        
        # 读取后端配置
        backend_env = self.base_path / "backend/.env"
        if backend_env.exists():
            with open(backend_env, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('SERVER_PORT='):
                        server_port = int(line.split('=', 1)[1].strip())
                        print(f"🔧 后端服务端口: {server_port}")
                        
                        if backend_port and backend_port != server_port:
                            self.issues.append(f"端口配置不匹配: 前端期望{backend_port}，后端配置{server_port}")
                        break
    
    async def check_backend_health(self):
        """检查后端健康状态"""
        print("\n❤️ 检查后端服务健康状态...")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get('http://localhost:8000/health') as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ 后端服务健康: {data.get('status', 'unknown')}")
                    else:
                        self.issues.append(f"后端健康检查失败: HTTP {response.status}")
        except asyncio.TimeoutError:
            self.issues.append("后端服务连接超时")
        except Exception as e:
            self.issues.append(f"后端服务连接失败: {str(e)}")
    
    async def check_cors_preflight(self):
        """检查CORS预检请求"""
        print("\n🚀 检查CORS预检请求...")
        
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.options(
                    'http://localhost:8000/api/v1/auth/register',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        print("✅ CORS预检请求成功")
                        
                        # 检查响应头
                        allow_origin = response.headers.get('Access-Control-Allow-Origin')
                        if allow_origin:
                            print(f"   允许源: {allow_origin}")
                        else:
                            self.warnings.append("CORS响应头缺少Access-Control-Allow-Origin")
                            
                    else:
                        self.issues.append(f"CORS预检请求失败: HTTP {response.status}")
                        
        except Exception as e:
            self.issues.append(f"CORS预检请求测试失败: {str(e)}")
    
    def print_results(self):
        """打印检查结果"""
        print("\n" + "=" * 50)
        print("📊 检查结果总结")
        
        if self.issues:
            print(f"\n❌ 发现 {len(self.issues)} 个问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if self.warnings:
            print(f"\n⚠️ 发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        if not self.issues and not self.warnings:
            print("\n✅ 所有检查均通过！配置健康。")
        elif not self.issues:
            print("\n✅ 核心配置正常，仅有一些建议优化项。")
        else:
            print(f"\n❌ 检查完成，需要修复 {len(self.issues)} 个问题。")


async def main():
    """主函数"""
    checker = ConfigHealthChecker()
    success = await checker.check_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 检查过程中出现错误: {e}")
        sys.exit(1)