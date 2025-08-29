"""
测试运行和配置脚本

提供便捷的测试执行、覆盖率统计和测试报告生成功能。
支持不同类型的测试运行模式和性能基准测试。
"""

import pytest
import sys
import os
import subprocess
from pathlib import Path


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行TradeMaster前后端集成测试套件...")
    
    # 设置测试环境
    os.environ["TESTING"] = "1"
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)
    
    # 测试参数
    args = [
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误回溯
        "--strict-markers",  # 严格标记检查
        "--disable-warnings",  # 禁用警告
        f"--rootdir={Path(__file__).parent}",
        "--asyncio-mode=auto",  # 自动异步模式
        Path(__file__).parent  # 测试目录
    ]
    
    return pytest.main(args)


def run_unit_tests():
    """只运行单元测试"""
    print("🧪 运行单元测试...")
    
    args = [
        "-v",
        "-k", "not (integration or end_to_end)",
        Path(__file__).parent
    ]
    
    return pytest.main(args)


def run_integration_tests():
    """只运行集成测试"""
    print("🔗 运行集成测试...")
    
    args = [
        "-v", 
        "-k", "integration",
        Path(__file__).parent
    ]
    
    return pytest.main(args)


def run_end_to_end_tests():
    """只运行端到端测试"""
    print("🎯 运行端到端测试...")
    
    args = [
        "-v",
        "-k", "end_to_end",
        Path(__file__).parent
    ]
    
    return pytest.main(args)


def run_performance_tests():
    """运行性能测试"""
    print("⚡ 运行性能测试...")
    
    args = [
        "-v",
        "-k", "performance",
        "--timeout=60",  # 性能测试超时60秒
        Path(__file__).parent
    ]
    
    return pytest.main(args)


def run_security_tests():
    """运行安全测试"""
    print("🔒 运行安全和错误处理测试...")
    
    args = [
        "-v",
        Path(__file__).parent / "test_security_and_errors.py"
    ]
    
    return pytest.main(args)


def run_with_coverage():
    """运行测试并生成覆盖率报告"""
    print("📊 运行测试并生成覆盖率报告...")
    
    try:
        import coverage
    except ImportError:
        print("❌ 需要安装 coverage 包: pip install coverage")
        return 1
    
    # 启动覆盖率收集
    cov = coverage.Coverage(
        source=[str(Path(__file__).parent.parent / "app")],
        omit=[
            "*/tests/*",
            "*/test_*.py",
            "*/__init__.py",
            "*/venv/*",
            "*/env/*"
        ]
    )
    
    cov.start()
    
    try:
        # 运行测试
        exit_code = run_all_tests()
        
        # 停止覆盖率收集
        cov.stop()
        cov.save()
        
        # 生成报告
        print("\n📈 覆盖率报告:")
        cov.report()
        
        # 生成HTML报告
        htmlcov_dir = Path(__file__).parent / "htmlcov"
        cov.html_report(directory=str(htmlcov_dir))
        print(f"📋 HTML覆盖率报告已生成: {htmlcov_dir}/index.html")
        
        return exit_code
        
    except Exception as e:
        print(f"❌ 覆盖率测试失败: {e}")
        return 1


def run_specific_test_file(file_name: str):
    """运行指定的测试文件"""
    test_file = Path(__file__).parent / file_name
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return 1
    
    print(f"🎪 运行测试文件: {file_name}")
    
    args = ["-v", str(test_file)]
    return pytest.main(args)


def run_tests_with_markers(*markers):
    """运行带有特定标记的测试"""
    if not markers:
        print("❌ 请指定至少一个测试标记")
        return 1
    
    marker_expr = " or ".join(markers)
    print(f"🏷️  运行标记为 '{marker_expr}' 的测试...")
    
    args = [
        "-v",
        "-m", marker_expr,
        Path(__file__).parent
    ]
    
    return pytest.main(args)


def generate_test_report():
    """生成详细的测试报告"""
    print("📝 生成详细测试报告...")
    
    try:
        import pytest_html
    except ImportError:
        print("❌ 需要安装 pytest-html 包: pip install pytest-html")
        return 1
    
    report_file = Path(__file__).parent / "test_report.html"
    
    args = [
        "-v",
        "--html", str(report_file),
        "--self-contained-html",
        Path(__file__).parent
    ]
    
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print(f"📋 测试报告已生成: {report_file}")
    
    return exit_code


def run_benchmark_tests():
    """运行基准性能测试"""
    print("🏃 运行基准性能测试...")
    
    try:
        import pytest_benchmark
    except ImportError:
        print("❌ 需要安装 pytest-benchmark 包: pip install pytest-benchmark")
        return 1
    
    args = [
        "-v",
        "--benchmark-only",
        "--benchmark-sort=mean",
        "-k", "benchmark",
        Path(__file__).parent
    ]
    
    return pytest.main(args)


def validate_test_environment():
    """验证测试环境配置"""
    print("🔍 验证测试环境...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "sqlalchemy",
        "fastapi"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必需的包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    # 检查测试数据库
    test_db_path = Path(__file__).parent / "test.db"
    if test_db_path.exists():
        print("🗂️  发现现有测试数据库，将自动清理")
    
    print("✅ 测试环境验证完成")
    return True


def clean_test_artifacts():
    """清理测试产生的临时文件"""
    print("🧹 清理测试产生的文件...")
    
    patterns = [
        "test.db*",
        "*.pyc",
        "__pycache__",
        ".pytest_cache",
        "htmlcov",
        "test_report.html",
        ".coverage"
    ]
    
    base_dir = Path(__file__).parent
    
    for pattern in patterns:
        for item in base_dir.rglob(pattern):
            try:
                if item.is_file():
                    item.unlink()
                    print(f"🗑️  删除文件: {item}")
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item)
                    print(f"🗑️  删除目录: {item}")
            except (OSError, PermissionError) as e:
                print(f"⚠️  无法删除 {item}: {e}")
    
    print("✅ 清理完成")


def main():
    """主函数 - 命令行接口"""
    if len(sys.argv) < 2:
        print("""
🧪 TradeMaster 测试套件运行器

使用方法:
  python test_runner.py <command> [args]

可用命令:
  all                    运行所有测试
  unit                   只运行单元测试
  integration            只运行集成测试
  e2e                    只运行端到端测试
  performance            只运行性能测试
  security               只运行安全测试
  coverage               运行测试并生成覆盖率报告
  report                 生成HTML测试报告
  benchmark              运行基准性能测试
  file <filename>        运行指定测试文件
  marker <markers...>    运行带有指定标记的测试
  validate               验证测试环境
  clean                  清理测试产生的文件

示例:
  python test_runner.py all
  python test_runner.py file test_trademaster_integration.py
  python test_runner.py marker slow integration
  python test_runner.py coverage
        """)
        return 0
    
    command = sys.argv[1].lower()
    
    # 验证环境（除了clean和validate命令）
    if command not in ["clean", "validate"]:
        if not validate_test_environment():
            return 1
    
    if command == "all":
        return run_all_tests()
    elif command == "unit":
        return run_unit_tests()
    elif command in ["integration", "int"]:
        return run_integration_tests()
    elif command in ["e2e", "end_to_end"]:
        return run_end_to_end_tests()
    elif command in ["performance", "perf"]:
        return run_performance_tests()
    elif command in ["security", "sec"]:
        return run_security_tests()
    elif command == "coverage":
        return run_with_coverage()
    elif command == "report":
        return generate_test_report()
    elif command in ["benchmark", "bench"]:
        return run_benchmark_tests()
    elif command == "file":
        if len(sys.argv) < 3:
            print("❌ 请指定测试文件名")
            return 1
        return run_specific_test_file(sys.argv[2])
    elif command == "marker":
        if len(sys.argv) < 3:
            print("❌ 请指定至少一个测试标记")
            return 1
        return run_tests_with_markers(*sys.argv[2:])
    elif command == "validate":
        return 0 if validate_test_environment() else 1
    elif command == "clean":
        clean_test_artifacts()
        return 0
    else:
        print(f"❌ 未知命令: {command}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)