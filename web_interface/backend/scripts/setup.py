#!/usr/bin/env python3
"""
TradeMaster Web Interface Backend 开发环境初始化脚本

这个脚本用于设置后端开发环境，包括：
- Python版本检查
- 虚拟环境创建
- 依赖包安装
- 数据库初始化
- 配置文件创建
- 开发工具安装

使用方法:
    python scripts/setup.py [--skip-venv] [--skip-db] [--force]
"""

import os
import sys
import subprocess
import shutil
import argparse
import platform
from pathlib import Path
from typing import Optional, List, Tuple

# 颜色输出
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

def run_command(command: List[str], cwd: Optional[Path] = None, check: bool = True) -> Tuple[bool, str]:
    """
    运行命令并返回结果
    
    Args:
        command: 要执行的命令列表
        cwd: 工作目录
        check: 是否检查返回码
        
    Returns:
        (success, output): 成功状态和输出
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, f"Command not found: {command[0]}"

def check_python_version() -> bool:
    """检查Python版本"""
    print_header("检查Python版本")
    
    required_version = (3, 9)
    current_version = sys.version_info[:2]
    
    print_info(f"当前Python版本: {sys.version}")
    
    if current_version >= required_version:
        print_success(f"Python版本满足要求 (>= {required_version[0]}.{required_version[1]})")
        return True
    else:
        print_error(f"Python版本过低，需要 >= {required_version[0]}.{required_version[1]}")
        return False

def check_system_dependencies() -> bool:
    """检查系统依赖"""
    print_header("检查系统依赖")
    
    dependencies = {
        'git': 'Git版本控制',
        'curl': 'HTTP客户端工具',  
    }
    
    # 检查PostgreSQL客户端
    pg_commands = ['psql', 'pg_config']
    postgres_available = any(shutil.which(cmd) for cmd in pg_commands)
    
    missing_deps = []
    
    for cmd, desc in dependencies.items():
        if shutil.which(cmd):
            print_success(f"{desc} 已安装")
        else:
            print_warning(f"{desc} 未安装")
            missing_deps.append(cmd)
    
    if postgres_available:
        print_success("PostgreSQL客户端工具已安装")
    else:
        print_warning("PostgreSQL客户端工具未安装")
        print_info("请安装PostgreSQL客户端: sudo apt-get install postgresql-client")
    
    if missing_deps:
        print_warning(f"缺少依赖: {', '.join(missing_deps)}")
        print_info("这些依赖不是必需的，但建议安装以获得更好的开发体验")
    
    return True

def create_virtual_environment(skip_venv: bool = False) -> bool:
    """创建虚拟环境"""
    if skip_venv:
        print_info("跳过虚拟环境创建")
        return True
        
    print_header("创建Python虚拟环境")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_info("虚拟环境已存在")
        response = input("是否重新创建？(y/N): ").strip().lower()
        if response == 'y':
            print_info("删除现有虚拟环境...")
            shutil.rmtree(venv_path)
        else:
            print_info("使用现有虚拟环境")
            return True
    
    print_info("创建虚拟环境...")
    success, output = run_command([sys.executable, "-m", "venv", str(venv_path)])
    
    if success:
        print_success("虚拟环境创建成功")
        
        # 检查虚拟环境激活脚本
        if platform.system() == "Windows":
            activate_script = venv_path / "Scripts" / "activate.bat"
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            activate_script = venv_path / "bin" / "activate"
            pip_path = venv_path / "bin" / "pip"
            
        if activate_script.exists():
            print_success("虚拟环境激活脚本已创建")
            print_info(f"激活命令: source {activate_script}")
        
        return True
    else:
        print_error(f"虚拟环境创建失败: {output}")
        return False

def get_pip_command() -> List[str]:
    """获取pip命令路径"""
    venv_path = Path("venv")
    
    if platform.system() == "Windows":
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    if pip_path.exists():
        return [str(pip_path)]
    elif python_path.exists():
        return [str(python_path), "-m", "pip"]
    else:
        return [sys.executable, "-m", "pip"]

def install_dependencies() -> bool:
    """安装Python依赖"""
    print_header("安装Python依赖包")
    
    requirements_files = [
        "requirements.txt",
        "requirements-dev.txt"
    ]
    
    pip_cmd = get_pip_command()
    
    # 升级pip
    print_info("升级pip...")
    success, output = run_command(pip_cmd + ["install", "--upgrade", "pip", "setuptools", "wheel"])
    if success:
        print_success("pip升级成功")
    else:
        print_warning(f"pip升级失败: {output}")
    
    # 安装依赖
    for req_file in requirements_files:
        if Path(req_file).exists():
            print_info(f"安装 {req_file}...")
            success, output = run_command(pip_cmd + ["install", "-r", req_file])
            if success:
                print_success(f"{req_file} 安装成功")
            else:
                print_error(f"{req_file} 安装失败: {output}")
                if req_file == "requirements.txt":
                    return False
        else:
            print_warning(f"{req_file} 不存在")
    
    return True

def create_env_file() -> bool:
    """创建环境配置文件"""
    print_header("创建环境配置文件")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print_warning(".env.example 文件不存在")
        return False
    
    if env_file.exists():
        print_info(".env 文件已存在")
        response = input("是否覆盖？(y/N): ").strip().lower()
        if response != 'y':
            print_info("保留现有.env文件")
            return True
    
    try:
        shutil.copy2(env_example, env_file)
        print_success("环境配置文件创建成功")
        print_info("请编辑 .env 文件以配置数据库连接等参数")
        return True
    except Exception as e:
        print_error(f"创建环境配置文件失败: {e}")
        return False

def check_database_connection() -> bool:
    """检查数据库连接"""
    print_header("检查数据库连接")
    
    try:
        # 尝试导入数据库相关模块
        python_cmd = get_pip_command()[0] if get_pip_command()[0].endswith(('python', 'python.exe')) else sys.executable
        
        # 简单的数据库连接测试
        test_script = """
import os
from pathlib import Path

# 加载环境变量
env_file = Path('.env')
if env_file.exists():
    from python_decouple import config
    try:
        db_url = config('DATABASE_URL', default=None)
        postgres_server = config('POSTGRES_SERVER', default='localhost')
        postgres_port = config('POSTGRES_PORT', default='5432')
        print(f'数据库配置: {postgres_server}:{postgres_port}')
        print('环境配置加载成功')
    except Exception as e:
        print(f'环境配置加载失败: {e}')
else:
    print('未找到.env文件')
"""
        
        success, output = run_command([python_cmd, "-c", test_script])
        if success:
            print_success("数据库配置检查通过")
            print_info(output.strip())
        else:
            print_warning("数据库配置检查失败，请确保数据库服务正在运行")
            
        return True
        
    except Exception as e:
        print_warning(f"数据库连接检查失败: {e}")
        return True  # 不阻断安装过程

def initialize_database(skip_db: bool = False) -> bool:
    """初始化数据库"""
    if skip_db:
        print_info("跳过数据库初始化")
        return True
        
    print_header("初始化数据库")
    
    python_cmd = get_pip_command()[0] if get_pip_command()[0].endswith(('python', 'python.exe')) else sys.executable
    
    # 检查Alembic配置
    alembic_ini = Path("alembic.ini")
    if not alembic_ini.exists():
        print_warning("alembic.ini 不存在，跳过数据库迁移")
        return True
    
    # 运行数据库迁移
    print_info("运行数据库迁移...")
    success, output = run_command([python_cmd, "-m", "alembic", "upgrade", "head"])
    
    if success:
        print_success("数据库迁移完成")
    else:
        print_warning(f"数据库迁移失败: {output}")
        print_info("请确保数据库服务正在运行，并且连接配置正确")
    
    # 运行初始数据脚本
    init_script = Path("app/scripts/init_database.py")
    if init_script.exists():
        print_info("运行数据库初始化脚本...")
        success, output = run_command([python_cmd, str(init_script)])
        if success:
            print_success("数据库初始化完成")
        else:
            print_warning(f"数据库初始化失败: {output}")
    
    return True

def install_development_tools() -> bool:
    """安装开发工具"""
    print_header("安装开发工具")
    
    pip_cmd = get_pip_command()
    
    # 开发工具列表
    dev_tools = [
        "pre-commit",
        "black", 
        "isort",
        "flake8",
        "mypy",
        "bandit",
        "safety"
    ]
    
    print_info("安装代码质量工具...")
    for tool in dev_tools:
        success, output = run_command(pip_cmd + ["install", tool], check=False)
        if success:
            print_success(f"{tool} 安装成功")
        else:
            print_warning(f"{tool} 安装失败")
    
    # 安装pre-commit钩子
    pre_commit_config = Path("../.pre-commit-config.yaml")
    if pre_commit_config.exists():
        print_info("安装pre-commit钩子...")
        success, output = run_command([pip_cmd[0], "-m", "pre_commit", "install"])
        if success:
            print_success("pre-commit钩子安装成功")
        else:
            print_warning("pre-commit钩子安装失败")
    
    return True

def create_directory_structure() -> bool:
    """创建目录结构"""
    print_header("创建项目目录结构")
    
    directories = [
        "logs",
        "uploads", 
        "temp",
        "tests/reports",
        "scripts",
        "docs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"创建目录: {directory}")
        else:
            print_info(f"目录已存在: {directory}")
    
    # 创建.gitkeep文件
    gitkeep_dirs = ["logs", "uploads", "temp", "tests/reports"]
    for directory in gitkeep_dirs:
        gitkeep_file = Path(directory) / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.touch()
    
    return True

def verify_installation() -> bool:
    """验证安装"""
    print_header("验证安装")
    
    python_cmd = get_pip_command()[0] if get_pip_command()[0].endswith(('python', 'python.exe')) else sys.executable
    
    # 检查关键模块
    critical_modules = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "pydantic",
        "alembic"
    ]
    
    for module in critical_modules:
        success, output = run_command([python_cmd, "-c", f"import {module}; print('{module} 版本: ' + getattr({module}, '__version__', 'unknown'))"], check=False)
        if success:
            print_success(output.strip())
        else:
            print_error(f"模块 {module} 导入失败")
            return False
    
    print_success("所有关键模块验证通过")
    return True

def print_next_steps() -> None:
    """打印后续步骤"""
    print_header("后续步骤")
    
    venv_path = Path("venv")
    if platform.system() == "Windows":
        activate_cmd = f"venv\\Scripts\\activate"
    else:
        activate_cmd = f"source venv/bin/activate"
    
    steps = [
        f"1. 激活虚拟环境: {activate_cmd}",
        "2. 编辑 .env 文件配置数据库连接",
        "3. 启动数据库服务 (PostgreSQL, Redis)",
        "4. 运行数据库迁移: alembic upgrade head",
        "5. 启动开发服务器: python app/main.py",
        "6. 访问API文档: http://localhost:8000/docs"
    ]
    
    for step in steps:
        print_info(step)
    
    print_success("\n🎉 后端开发环境设置完成！")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradeMaster Backend 开发环境初始化")
    parser.add_argument("--skip-venv", action="store_true", help="跳过虚拟环境创建")
    parser.add_argument("--skip-db", action="store_true", help="跳过数据库初始化")
    parser.add_argument("--force", action="store_true", help="强制重新安装")
    
    args = parser.parse_args()
    
    print_header("TradeMaster Web Interface Backend 开发环境初始化")
    
    # 切换到脚本所在目录的上级目录（backend目录）
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    os.chdir(backend_dir)
    
    print_info(f"工作目录: {backend_dir.absolute()}")
    
    # 执行安装步骤
    steps = [
        ("检查Python版本", lambda: check_python_version()),
        ("检查系统依赖", lambda: check_system_dependencies()),
        ("创建虚拟环境", lambda: create_virtual_environment(args.skip_venv)),
        ("安装Python依赖", lambda: install_dependencies()),
        ("创建环境配置文件", lambda: create_env_file()),
        ("创建目录结构", lambda: create_directory_structure()),
        ("检查数据库连接", lambda: check_database_connection()),
        ("初始化数据库", lambda: initialize_database(args.skip_db)),
        ("安装开发工具", lambda: install_development_tools()),
        ("验证安装", lambda: verify_installation()),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
                if step_name in ["检查Python版本", "安装Python依赖"]:
                    print_error(f"关键步骤失败: {step_name}")
                    sys.exit(1)
        except KeyboardInterrupt:
            print_error("\n用户中断安装")
            sys.exit(1)
        except Exception as e:
            print_error(f"步骤 '{step_name}' 执行失败: {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print_warning(f"\n以下步骤执行失败: {', '.join(failed_steps)}")
        print_info("您可以稍后手动执行这些步骤")
    
    print_next_steps()

if __name__ == "__main__":
    main()