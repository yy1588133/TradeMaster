#!/usr/bin/env python3
"""
TradeMaster Web Interface Backend 开发服务器启动脚本

这个脚本用于启动后端开发服务器，包括：
- 自动重载功能
- 详细日志输出
- 开发环境配置
- 健康检查
- 数据库连接验证

使用方法:
    python scripts/dev.py [--host HOST] [--port PORT] [--reload] [--debug]
"""

import os
import sys
import asyncio
import argparse
import signal
import threading
import time
from pathlib import Path
from typing import Optional

import uvicorn
from loguru import logger

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.core.config import get_settings
    from app.core.database import test_database_connection
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装所有依赖包，并且在backend目录下运行此脚本")
    sys.exit(1)

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message: str) -> None:
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message: str) -> None:
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message: str) -> None:
    """打印错误消息"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str) -> None:
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_header(message: str) -> None:
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 {message}{Colors.END}")

class HealthChecker:
    """健康检查器"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """启动健康检查"""
        self.running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """停止健康检查"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            
    def _check_loop(self):
        """健康检查循环"""
        import httpx
        
        # 等待服务器启动
        time.sleep(3)
        
        base_url = f"http://{self.host}:{self.port}"
        
        while self.running:
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"{base_url}/health")
                    if response.status_code == 200:
                        logger.info(f"健康检查通过: {response.json()}")
                    else:
                        logger.warning(f"健康检查失败: {response.status_code}")
            except Exception as e:
                logger.error(f"健康检查异常: {e}")
                
            time.sleep(30)  # 每30秒检查一次

def setup_logging(debug: bool = False):
    """设置日志配置"""
    # 移除默认handler
    logger.remove()
    
    # 控制台输出
    log_level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
    )
    
    # 文件输出
    log_dir = backend_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "dev.log",
        level="DEBUG",
        rotation="100 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )
    
    logger.info("日志系统初始化完成")

async def check_dependencies():
    """检查依赖服务"""
    print_header("检查依赖服务")
    
    settings = get_settings()
    
    # 检查数据库连接
    try:
        print_info("检查数据库连接...")
        await test_database_connection()
        print_success("数据库连接正常")
    except Exception as e:
        print_error(f"数据库连接失败: {e}")
        print_warning("请确保PostgreSQL服务正在运行")
        return False
    
    # 检查Redis连接
    try:
        print_info("检查Redis连接...")
        import redis.asyncio as redis
        
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        await redis_client.ping()
        print_success("Redis连接正常")
        await redis_client.close()
        
    except Exception as e:
        print_warning(f"Redis连接失败: {e}")
        print_info("Redis不是必需的，但建议启动以获得更好的性能")
    
    return True

def check_environment():
    """检查环境配置"""
    print_header("检查环境配置")
    
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print_warning(".env文件不存在")
        print_info("将使用默认配置，建议创建.env文件")
    else:
        print_success(".env文件存在")
    
    # 检查关键环境变量
    settings = get_settings()
    
    config_checks = [
        ("SECRET_KEY", settings.SECRET_KEY, "JWT密钥配置"),
        ("POSTGRES_SERVER", settings.POSTGRES_SERVER, "数据库服务器"),
        ("POSTGRES_DB", settings.POSTGRES_DB, "数据库名称"),
    ]
    
    for var_name, value, description in config_checks:
        if value:
            print_success(f"{description}: ✓")
        else:
            print_error(f"{description}: 未配置")
    
    return True

def print_server_info(host: str, port: int):
    """打印服务器信息"""
    print_header("TradeMaster Web Interface Backend 开发服务器")
    
    urls = [
        ("🌐 应用地址", f"http://{host}:{port}"),
        ("📚 API文档", f"http://{host}:{port}/docs"),
        ("📋 ReDoc文档", f"http://{host}:{port}/redoc"),
        ("💊 健康检查", f"http://{host}:{port}/health"),
        ("📊 OpenAPI规范", f"http://{host}:{port}/openapi.json"),
    ]
    
    for desc, url in urls:
        print_info(f"{desc}: {url}")
    
    print_info("按 Ctrl+C 停止服务器")

def signal_handler(signum, frame):
    """信号处理器"""
    print_info("\n收到停止信号，正在关闭服务器...")
    sys.exit(0)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradeMaster Backend 开发服务器")
    parser.add_argument("--host", default="0.0.0.0", help="绑定主机地址")
    parser.add_argument("--port", type=int, default=8000, help="绑定端口")
    parser.add_argument("--reload", action="store_true", default=True, help="启用自动重载")
    parser.add_argument("--no-reload", action="store_true", help="禁用自动重载")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--access-log", action="store_true", help="启用访问日志")
    parser.add_argument("--skip-checks", action="store_true", help="跳过环境检查")
    
    args = parser.parse_args()
    
    # 处理重载选项
    reload = args.reload and not args.no_reload
    
    # 设置工作目录
    os.chdir(backend_dir)
    
    # 设置日志
    setup_logging(args.debug)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if not args.skip_checks:
        # 检查环境
        if not check_environment():
            print_error("环境检查失败")
            sys.exit(1)
        
        # 检查依赖服务
        if not await check_dependencies():
            print_error("依赖服务检查失败")
            response = input("是否继续启动服务器？(y/N): ").strip().lower()
            if response != 'y':
                sys.exit(1)
    
    # 打印服务器信息
    print_server_info(args.host, args.port)
    
    # 启动健康检查器
    health_checker = None
    if not args.skip_checks:
        health_checker = HealthChecker(args.host, args.port)
        health_checker.start()
    
    try:
        # Uvicorn配置
        uvicorn_config = {
            "app": "app.main:app",
            "host": args.host,
            "port": args.port,
            "reload": reload,
            "reload_dirs": [str(backend_dir / "app")] if reload else None,
            "reload_includes": ["*.py"] if reload else None,
            "log_level": "debug" if args.debug else "info",
            "access_log": args.access_log,
            "use_colors": True,
            "workers": args.workers if not reload else 1,  # 重载模式下只能使用1个worker
        }
        
        # 启动服务器
        logger.info("启动开发服务器...")
        await uvicorn.Server(uvicorn.Config(**uvicorn_config)).serve()
        
    except KeyboardInterrupt:
        print_info("用户中断服务器")
    except Exception as e:
        print_error(f"服务器启动失败: {e}")
        sys.exit(1)
    finally:
        if health_checker:
            health_checker.stop()
        logger.info("开发服务器已停止")

if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 9):
        print_error("需要Python 3.9或更高版本")
        sys.exit(1)
    
    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_info("服务器已停止")
    except Exception as e:
        print_error(f"启动失败: {e}")
        sys.exit(1)