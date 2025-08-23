#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradeMaster Web Interface 环境变量配置验证脚本
验证所有环境变量配置文件的一致性和完整性
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


class EnvConfigValidator:
    """环境变量配置验证器"""
    
    def __init__(self, web_interface_root: str):
        self.root = Path(web_interface_root)
        self.config_files = {
            'main_example': self.root / '.env.example',
            'dev_config': self.root / '.env.dev',
            'prod_config': self.root / '.env.prod',
            'prod_template': self.root / '.env.prod.template',
            'backend_example': self.root / 'backend' / '.env.example',
            'frontend_example': self.root / 'frontend' / '.env.example',
        }
        
        self.docker_compose_files = {
            'dev_compose': self.root / 'docker-compose.dev.yml',
            'prod_compose': self.root / 'docker-compose.prod.yml',
        }
        
        # 关键环境变量列表
        self.critical_vars = {
            'SECRET_KEY', 'POSTGRES_PASSWORD', 'REDIS_PASSWORD',
            'POSTGRES_USER', 'POSTGRES_DB', 'DATABASE_URL',
            'REDIS_URL', 'BACKEND_CORS_ORIGINS'
        }
        
        # 需要强密码的变量
        self.password_vars = {
            'SECRET_KEY', 'POSTGRES_PASSWORD', 'REDIS_PASSWORD',
            'WEB_SECRET_KEY', 'WEB_POSTGRES_PASSWORD', 'GRAFANA_ADMIN_PASSWORD'
        }

    def parse_env_file(self, file_path: Path) -> Dict[str, str]:
        """解析环境变量文件"""
        env_vars = {}
        if not file_path.exists():
            return env_vars
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue
                    
                    # 匹配环境变量格式
                    match = re.match(r'^([A-Z_]+[A-Z0-9_]*)\s*=\s*(.*)$', line)
                    if match:
                        key, value = match.groups()
                        env_vars[key] = value
        except Exception as e:
            print(f"解析文件 {file_path} 时出错: {e}")
        
        return env_vars

    def extract_compose_vars(self, file_path: Path) -> Set[str]:
        """从Docker Compose文件中提取环境变量引用"""
        referenced_vars = set()
        if not file_path.exists():
            return referenced_vars
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 查找 ${VAR_NAME} 格式的变量引用
                matches = re.findall(r'\$\{([A-Z_]+[A-Z0-9_]*)[^}]*\}', content)
                referenced_vars.update(matches)
        except Exception as e:
            print(f"解析Compose文件 {file_path} 时出错: {e}")
        
        return referenced_vars

    def validate_password_strength(self, var_name: str, value: str) -> List[str]:
        """验证密码强度"""
        issues = []
        
        if var_name in self.password_vars:
            # 检查是否是占位符
            if 'CHANGE_THIS' in value:
                issues.append(f"{var_name}: 仍使用占位符值，需要设置实际密码")
                return issues
            
            # 检查密码长度
            if var_name == 'SECRET_KEY':
                if len(value) < 64:
                    issues.append(f"{var_name}: 长度不足64位 (当前: {len(value)})")
            elif len(value) < 12:
                issues.append(f"{var_name}: 密码长度不足12位 (当前: {len(value)})")
            
            # 检查密码复杂度
            if var_name != 'SECRET_KEY':  # SECRET_KEY通常是base64编码的
                has_upper = any(c.isupper() for c in value)
                has_lower = any(c.islower() for c in value)
                has_digit = any(c.isdigit() for c in value)
                has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in value)
                
                if not has_upper:
                    issues.append(f"{var_name}: 缺少大写字母")
                if not has_lower:
                    issues.append(f"{var_name}: 缺少小写字母")
                if not has_digit:
                    issues.append(f"{var_name}: 缺少数字")
                if not has_special:
                    issues.append(f"{var_name}: 缺少特殊字符")
        
        return issues

    def validate_config_consistency(self) -> ValidationResult:
        """验证配置文件一致性"""
        errors = []
        warnings = []
        info = []
        
        # 解析所有配置文件
        configs = {}
        for name, path in self.config_files.items():
            if path.exists():
                configs[name] = self.parse_env_file(path)
                info.append(f"✓ 已解析 {name}: {path} ({len(configs[name])} 个变量)")
            else:
                warnings.append(f"⚠ 配置文件不存在: {path}")
        
        # 解析Docker Compose文件
        compose_vars = set()
        for name, path in self.docker_compose_files.items():
            if path.exists():
                vars_in_compose = self.extract_compose_vars(path)
                compose_vars.update(vars_in_compose)
                info.append(f"✓ 已解析 {name}: {path} ({len(vars_in_compose)} 个变量引用)")
            else:
                warnings.append(f"⚠ Compose文件不存在: {path}")
        
        # 验证关键变量是否存在
        for config_name, config_vars in configs.items():
            missing_critical = self.critical_vars - set(config_vars.keys())
            if missing_critical and config_name in ['dev_config', 'prod_config']:
                errors.extend([f"{config_name}: 缺少关键变量 {var}" for var in missing_critical])
        
        # 验证密码强度
        for config_name, config_vars in configs.items():
            for var_name, value in config_vars.items():
                password_issues = self.validate_password_strength(var_name, value)
                if password_issues:
                    if config_name == 'prod_config':
                        errors.extend([f"{config_name}: {issue}" for issue in password_issues])
                    else:
                        warnings.extend([f"{config_name}: {issue}" for issue in password_issues])
        
        # 验证Docker Compose变量引用
        if 'dev_config' in configs:
            missing_in_dev = compose_vars - set(configs['dev_config'].keys())
            if missing_in_dev:
                warnings.extend([f"开发环境缺少Compose引用的变量: {var}" for var in missing_in_dev])
        
        if 'prod_config' in configs:
            missing_in_prod = compose_vars - set(configs['prod_config'].keys())
            if missing_in_prod:
                errors.extend([f"生产环境缺少Compose引用的变量: {var}" for var in missing_in_prod])
        
        # 验证端口配置一致性
        self._validate_port_consistency(configs, errors, warnings)
        
        # 验证数据库配置一致性
        self._validate_database_consistency(configs, errors, warnings)
        
        # 验证CORS配置
        self._validate_cors_consistency(configs, errors, warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info
        )

    def _validate_port_consistency(self, configs: Dict[str, Dict[str, str]], 
                                 errors: List[str], warnings: List[str]):
        """验证端口配置一致性"""
        port_vars = ['SERVER_PORT', 'BACKEND_PORT', 'FRONTEND_PORT', 'POSTGRES_PORT', 'REDIS_PORT']
        
        for var in port_vars:
            values = {}
            for config_name, config_vars in configs.items():
                if var in config_vars:
                    values[config_name] = config_vars[var]
            
            if len(set(values.values())) > 1:
                warnings.append(f"端口配置不一致 {var}: {values}")

    def _validate_database_consistency(self, configs: Dict[str, Dict[str, str]], 
                                     errors: List[str], warnings: List[str]):
        """验证数据库配置一致性"""
        db_vars = ['POSTGRES_USER', 'POSTGRES_DB']
        
        for var in db_vars:
            values = set()
            for config_name, config_vars in configs.items():
                if var in config_vars and config_name in ['dev_config', 'prod_config']:
                    values.add(config_vars[var])
            
            if len(values) > 1:
                warnings.append(f"数据库配置不一致 {var}: {values}")

    def _validate_cors_consistency(self, configs: Dict[str, Dict[str, str]], 
                                 errors: List[str], warnings: List[str]):
        """验证CORS配置"""
        if 'prod_config' in configs:
            cors_origins = configs['prod_config'].get('BACKEND_CORS_ORIGINS', '')
            if 'localhost' in cors_origins or '127.0.0.1' in cors_origins:
                errors.append("生产环境CORS配置包含localhost地址")
        
        if 'dev_config' in configs:
            cors_origins = configs['dev_config'].get('BACKEND_CORS_ORIGINS', '')
            if not ('localhost' in cors_origins or '127.0.0.1' in cors_origins):
                warnings.append("开发环境CORS配置可能缺少localhost地址")

    def generate_report(self, result: ValidationResult) -> str:
        """生成验证报告"""
        report = []
        report.append("=" * 80)
        report.append("TradeMaster Web Interface 环境变量配置验证报告")
        report.append("=" * 80)
        
        # 基本信息
        if result.info:
            report.append("\n📋 配置文件信息:")
            for info in result.info:
                report.append(f"  {info}")
        
        # 错误信息
        if result.errors:
            report.append(f"\n❌ 发现 {len(result.errors)} 个错误:")
            for error in result.errors:
                report.append(f"  • {error}")
        
        # 警告信息
        if result.warnings:
            report.append(f"\n⚠️  发现 {len(result.warnings)} 个警告:")
            for warning in result.warnings:
                report.append(f"  • {warning}")
        
        # 验证结果
        report.append(f"\n{'='*80}")
        if result.is_valid:
            report.append("✅ 配置验证通过! 所有关键配置项都正确设置。")
        else:
            report.append("❌ 配置验证失败! 请修复上述错误后重新验证。")
        
        # 建议
        report.append(f"\n📝 配置建议:")
        report.append("  • 生产环境部署前，请确保所有占位符都已替换为实际值")
        report.append("  • 定期轮换密码和密钥以确保安全性")
        report.append("  • 验证所有外部服务连接是否正常")
        report.append("  • 在不同环境中测试配置的有效性")
        
        report.append("=" * 80)
        return "\n".join(report)


def main():
    """主函数"""
    if len(sys.argv) > 1:
        web_interface_root = sys.argv[1]
    else:
        web_interface_root = "."
    
    validator = EnvConfigValidator(web_interface_root)
    result = validator.validate_config_consistency()
    
    # 生成并打印报告
    report = validator.generate_report(result)
    print(report)
    
    # 保存报告到文件
    report_file = Path(web_interface_root) / "env_validation_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 完整报告已保存到: {report_file}")
    
    # 返回适当的退出码
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()