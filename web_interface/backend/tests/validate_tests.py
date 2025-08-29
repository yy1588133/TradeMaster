"""
简化的测试套件验证脚本 - 修复版

用于验证测试文件结构和基本配置，无需安装额外依赖。
兼容Windows控制台编码。
"""

import os
import sys
from pathlib import Path


def validate_test_structure():
    """验证测试文件结构"""
    print("验证测试文件结构...")
    
    test_dir = Path(__file__).parent
    expected_files = [
        "__init__.py",
        "conftest.py",
        "test_trademaster_integration.py",
        "test_celery_tasks.py", 
        "test_websocket.py",
        "test_api_integration.py",
        "test_configuration.py",
        "test_end_to_end.py",
        "test_security_and_errors.py",
        "test_runner.py",
        "README.md"
    ]
    
    missing_files = []
    for file_name in expected_files:
        file_path = test_dir / file_name
        if file_path.exists():
            print(f"[OK] {file_name}")
        else:
            print(f"[MISSING] {file_name}")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n缺少 {len(missing_files)} 个测试文件")
        return False
    else:
        print(f"\n所有 {len(expected_files)} 个测试文件都存在")
        return True


def validate_file_contents():
    """验证测试文件内容完整性"""
    print("\n验证测试文件内容...")
    
    test_dir = Path(__file__).parent
    test_files = [
        ("test_trademaster_integration.py", ["TestTradeMasterIntegrationService", "pytest"]),
        ("test_celery_tasks.py", ["TestTrainingTaskExecution", "TestBacktestTaskExecution"]),
        ("test_websocket.py", ["TestWebSocketConnectionManager", "TestWebSocketMessageHandler"]),
        ("test_api_integration.py", ["TestStrategyAPI", "TestWebSocketAPI"]),
        ("test_configuration.py", ["TestConfigurationUnification", "TestTradeMasterConfigAdapter"]),
        ("test_end_to_end.py", ["TestCompleteStrategyLifecycle", "TestMultiUserConcurrentOperations"]),
        ("test_security_and_errors.py", ["TestBusinessErrorHandling", "TestSecurityAndPermissions"])
    ]
    
    validation_passed = True
    
    for file_name, required_content in test_files:
        file_path = test_dir / file_name
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                missing_content = []
                
                for item in required_content:
                    if item not in content:
                        missing_content.append(item)
                
                if missing_content:
                    print(f"[WARNING] {file_name} - 缺少内容: {', '.join(missing_content)}")
                    validation_passed = False
                else:
                    print(f"[OK] {file_name} - 内容完整")
                    
            except Exception as e:
                print(f"[ERROR] {file_name} - 读取失败: {e}")
                validation_passed = False
        else:
            print(f"[ERROR] {file_name} - 文件不存在")
            validation_passed = False
    
    return validation_passed


def count_test_functions():
    """统计测试函数数量"""
    print("\n统计测试函数...")
    
    test_dir = Path(__file__).parent
    total_tests = 0
    
    for test_file in test_dir.glob("test_*.py"):
        if test_file.name == "test_runner.py":
            continue
            
        try:
            content = test_file.read_text(encoding='utf-8')
            test_count = content.count("def test_")
            async_test_count = content.count("async def test_")
            file_total = test_count + async_test_count
            
            print(f"[FILE] {test_file.name}: {file_total} 个测试函数")
            total_tests += file_total
            
        except Exception as e:
            print(f"[ERROR] 读取 {test_file.name} 失败: {e}")
    
    print(f"\n[TOTAL] 总计: {total_tests} 个测试函数")
    return total_tests


def validate_imports():
    """验证关键导入是否正确"""
    print("\n验证关键导入...")
    
    test_dir = Path(__file__).parent
    required_imports = [
        "pytest",
        "asyncio", 
        "unittest.mock",
        "httpx",
        "datetime"
    ]
    
    validation_passed = True
    
    for test_file in test_dir.glob("test_*.py"):
        if test_file.name == "test_runner.py":
            continue
            
        try:
            content = test_file.read_text(encoding='utf-8')
            missing_imports = []
            
            for imp in required_imports:
                if f"import {imp}" not in content and f"from {imp}" not in content:
                    missing_imports.append(imp)
            
            if missing_imports:
                print(f"[WARNING] {test_file.name} - 可能缺少导入: {', '.join(missing_imports)}")
            else:
                print(f"[OK] {test_file.name} - 导入正常")
                
        except Exception as e:
            print(f"[ERROR] 读取 {test_file.name} 失败: {e}")
            validation_passed = False
    
    return validation_passed


def generate_summary():
    """生成测试套件总结"""
    print("\n" + "="*60)
    print("TradeMaster前后端深度集成测试套件总结")
    print("="*60)
    
    # 文件结构验证
    structure_ok = validate_test_structure()
    
    # 文件内容验证
    content_ok = validate_file_contents()
    
    # 测试函数统计
    test_count = count_test_functions()
    
    # 导入验证
    imports_ok = validate_imports()
    
    print("\n" + "="*60)
    print("验证结果总结:")
    print(f"文件结构: {'[OK] 完整' if structure_ok else '[ERROR] 不完整'}")
    print(f"文件内容: {'[OK] 完整' if content_ok else '[ERROR] 不完整'}")
    print(f"测试函数: {test_count} 个")
    print(f"导入验证: {'[OK] 正常' if imports_ok else '[WARNING] 需检查'}")
    
    overall_status = structure_ok and content_ok and test_count > 0
    print(f"\n总体状态: {'[SUCCESS] 测试套件就绪' if overall_status else '[FAILED] 需要修复'}")
    
    if overall_status:
        print("\n后续步骤:")
        print("1. 安装测试依赖: pip install pytest pytest-asyncio httpx")
        print("2. 运行测试: python test_runner.py all")
        print("3. 生成覆盖率报告: python test_runner.py coverage")
    
    return overall_status


def main():
    """主函数"""
    print("TradeMaster前后端深度集成测试套件验证")
    print("专门针对代码质量评审中识别的关键问题设计\n")
    
    try:
        return generate_summary()
    except Exception as e:
        print(f"[ERROR] 验证过程出错: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)