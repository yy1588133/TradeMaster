"""
配置管理统一性测试

测试重点：
1. 配置转换和验证的一致性
2. 多文件配置的统一管理
3. 环境变量配置的正确性
4. 配置参数的类型安全性
5. 配置更新的同步机制

这些测试解决代码质量评审中发现的配置管理分散问题。
"""

import pytest
import os
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from app.core.config import Settings, get_settings
from app.core.trademaster_config import TradeMasterConfigAdapter, get_config_adapter


class TestConfigurationUnification:
    """配置统一性测试"""
    
    @pytest.fixture
    def settings(self):
        """创建设置实例"""
        return Settings()
    
    @pytest.fixture
    def config_adapter(self):
        """创建配置适配器"""
        return TradeMasterConfigAdapter()
    
    @pytest.fixture
    def sample_web_config(self):
        """示例Web配置"""
        return {
            "strategy_type": "algorithmic_trading",
            "agent_type": "dqn",
            "dataset_name": "BTC",
            "epochs": 100,
            "learning_rate": 0.001,
            "batch_size": 32,
            "gamma": 0.99,
            "epsilon_start": 1.0,
            "epsilon_end": 0.01,
            "epsilon_decay": 0.995,
            "memory_size": 10000,
            "target_update": 10
        }
    
    @pytest.fixture
    def expected_trademaster_config(self):
        """期望的TradeMaster配置格式"""
        return {
            "task": "algorithmic_trading",
            "dataset": {
                "type": "BTC",
                "train_start_date": "2020-01-01",
                "train_end_date": "2022-12-31",
                "valid_start_date": "2023-01-01", 
                "valid_end_date": "2023-12-31",
                "test_start_date": "2024-01-01",
                "test_end_date": "2024-12-31"
            },
            "agent": {
                "type": "dqn",
                "lr": 0.001,
                "batch_size": 32,
                "gamma": 0.99,
                "epsilon_start": 1.0,
                "epsilon_end": 0.01,
                "epsilon_decay": 0.995,
                "memory_size": 10000,
                "target_update": 10,
                "device": "cpu"
            },
            "environment": {
                "type": "algorithmic_trading",
                "max_step": 252,
                "initial_amount": 100000,
                "transaction_cost_pct": 0.001
            },
            "trainer": {
                "type": "dqn",
                "epochs": 100,
                "save_path": "./checkpoints",
                "load_path": "",
                "log_interval": 100
            }
        }
    
    def test_settings_initialization(self, settings):
        """测试设置初始化"""
        assert settings is not None
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'PROJECT_NAME')
    
    def test_database_url_generation(self, settings):
        """测试数据库URL生成"""
        # 测试异步URL
        async_url = settings.get_database_url(async_driver=True)
        assert async_url is not None
        if settings.DATABASE_URL and settings.DATABASE_URL.startswith('postgresql'):
            assert 'asyncpg' in async_url or 'postgresql+asyncpg' in async_url
        
        # 测试同步URL
        sync_url = settings.get_database_url(async_driver=False)
        assert sync_url is not None
    
    def test_environment_variable_override(self):
        """测试环境变量覆盖"""
        # 临时设置环境变量
        test_value = "test_secret_key_123"
        with patch.dict(os.environ, {'SECRET_KEY': test_value}):
            settings = Settings()
            assert settings.SECRET_KEY == test_value
    
    def test_config_validation(self, settings):
        """测试配置验证"""
        # 验证必需字段
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) >= 32  # 密钥长度检查
        
        # 验证数据库URL格式
        if settings.DATABASE_URL:
            assert any(db in settings.DATABASE_URL for db in ['postgresql', 'sqlite', 'mysql'])
    
    def test_get_settings_singleton(self):
        """测试设置单例模式"""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
        assert isinstance(settings1, Settings)


class TestTradeMasterConfigAdapter:
    """TradeMaster配置适配器测试"""
    
    @pytest.fixture
    def config_adapter(self):
        return TradeMasterConfigAdapter()
    
    def test_web_to_trademaster_conversion(self, config_adapter, sample_web_config, expected_trademaster_config):
        """测试Web配置到TradeMaster配置的转换"""
        result = config_adapter.convert_web_config_to_trademaster(sample_web_config)
        
        # 验证基本结构
        assert "task" in result
        assert "dataset" in result
        assert "agent" in result
        assert "environment" in result
        assert "trainer" in result
        
        # 验证任务类型转换
        assert result["task"] == expected_trademaster_config["task"]
        
        # 验证智能体配置转换
        agent_config = result["agent"]
        expected_agent = expected_trademaster_config["agent"]
        
        assert agent_config["type"] == expected_agent["type"]
        assert agent_config["lr"] == expected_agent["lr"]
        assert agent_config["batch_size"] == expected_agent["batch_size"]
        assert agent_config["gamma"] == expected_agent["gamma"]
        
        # 验证数据集配置
        dataset_config = result["dataset"]
        assert dataset_config["type"] == "BTC"
        
        # 验证训练器配置
        trainer_config = result["trainer"]
        assert trainer_config["epochs"] == 100
    
    def test_portfolio_management_conversion(self, config_adapter):
        """测试投资组合管理配置转换"""
        web_config = {
            "strategy_type": "portfolio_management",
            "agent_type": "eiie",
            "dataset_name": "dj30",
            "epochs": 50,
            "learning_rate": 0.001,
            "window_length": 50,
            "portfolio_value": 1000000
        }
        
        result = config_adapter.convert_web_config_to_trademaster(web_config)
        
        assert result["task"] == "portfolio_management"
        assert result["agent"]["type"] == "eiie"
        assert result["dataset"]["type"] == "dj30"
        assert result["agent"]["window_length"] == 50
        assert result["environment"]["initial_amount"] == 1000000
    
    def test_order_execution_conversion(self, config_adapter):
        """测试订单执行配置转换"""
        web_config = {
            "strategy_type": "order_execution",
            "agent_type": "eteo",
            "dataset_name": "AAPL",
            "epochs": 200,
            "learning_rate": 0.0003,
            "order_size": 1000,
            "price_impact": 0.01
        }
        
        result = config_adapter.convert_web_config_to_trademaster(web_config)
        
        assert result["task"] == "order_execution"
        assert result["agent"]["type"] == "eteo"
        assert result["environment"]["order_size"] == 1000
        assert result["environment"]["price_impact"] == 0.01
    
    def test_config_validation_success(self, config_adapter, expected_trademaster_config):
        """测试配置验证成功"""
        validation_result = config_adapter.validate_trademaster_config(expected_trademaster_config)
        
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0
    
    def test_config_validation_missing_required_fields(self, config_adapter):
        """测试缺少必需字段的配置验证"""
        invalid_config = {
            "task": "algorithmic_trading",
            # 缺少 dataset, agent, environment, trainer
        }
        
        validation_result = config_adapter.validate_trademaster_config(invalid_config)
        
        assert validation_result["valid"] is False
        assert len(validation_result["errors"]) > 0
        assert any("dataset" in error.lower() for error in validation_result["errors"])
        assert any("agent" in error.lower() for error in validation_result["errors"])
    
    def test_config_validation_invalid_values(self, config_adapter):
        """测试无效值的配置验证"""
        invalid_config = {
            "task": "invalid_task",
            "dataset": {"type": ""},  # 空数据集类型
            "agent": {
                "type": "dqn",
                "lr": -0.001,  # 负学习率
                "batch_size": 0,  # 无效批量大小
                "epochs": -10  # 负轮数
            },
            "environment": {"type": "test"},
            "trainer": {"type": "dqn", "epochs": 100}
        }
        
        validation_result = config_adapter.validate_trademaster_config(invalid_config)
        
        assert validation_result["valid"] is False
        assert len(validation_result["errors"]) > 0
        
        # 检查具体错误
        errors = validation_result["errors"]
        assert any("learning rate" in error.lower() for error in errors)
        assert any("batch size" in error.lower() for error in errors)
    
    def test_config_validation_with_warnings(self, config_adapter):
        """测试带警告的配置验证"""
        config_with_warnings = {
            "task": "algorithmic_trading",
            "dataset": {
                "type": "BTC",
                "train_start_date": "2020-01-01",
                "train_end_date": "2020-02-01"  # 很短的训练期间
            },
            "agent": {
                "type": "dqn",
                "lr": 0.1,  # 很高的学习率
                "batch_size": 1024,  # 很大的批量大小
                "epochs": 1  # 很少的轮数
            },
            "environment": {"type": "algorithmic_trading"},
            "trainer": {"type": "dqn", "epochs": 1}
        }
        
        validation_result = config_adapter.validate_trademaster_config(config_with_warnings)
        
        # 应该是有效的，但有警告
        assert validation_result["valid"] is True
        assert len(validation_result.get("warnings", [])) > 0
    
    def test_get_config_adapter_singleton(self):
        """测试配置适配器单例模式"""
        adapter1 = get_config_adapter()
        adapter2 = get_config_adapter()
        
        assert adapter1 is adapter2
        assert isinstance(adapter1, TradeMasterConfigAdapter)


class TestConfigurationFileManagement:
    """配置文件管理测试"""
    
    def test_yaml_config_loading(self):
        """测试YAML配置文件加载"""
        config_data = {
            "task": "algorithmic_trading",
            "dataset": {"type": "BTC", "train_start_date": "2020-01-01"},
            "agent": {"type": "dqn", "lr": 0.001},
            "trainer": {"epochs": 100}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 测试加载
            with open(temp_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            assert loaded_config == config_data
            assert loaded_config["task"] == "algorithmic_trading"
            assert loaded_config["agent"]["lr"] == 0.001
            
        finally:
            os.unlink(temp_path)
    
    def test_json_config_loading(self):
        """测试JSON配置文件加载"""
        config_data = {
            "strategy_type": "portfolio_management",
            "agent_type": "eiie",
            "dataset_name": "dj30",
            "learning_rate": 0.001,
            "epochs": 50
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 测试加载
            with open(temp_path, 'r') as f:
                loaded_config = json.load(f)
            
            assert loaded_config == config_data
            assert loaded_config["strategy_type"] == "portfolio_management"
            assert loaded_config["learning_rate"] == 0.001
            
        finally:
            os.unlink(temp_path)
    
    def test_config_file_validation(self):
        """测试配置文件验证"""
        # 有效配置文件
        valid_config = {
            "task": "algorithmic_trading",
            "dataset": {"type": "BTC"},
            "agent": {"type": "dqn", "lr": 0.001},
            "environment": {"type": "test"},
            "trainer": {"epochs": 100}
        }
        
        # 无效配置文件
        invalid_config = {
            "task": "invalid_task"
            # 缺少其他必需字段
        }
        
        config_adapter = TradeMasterConfigAdapter()
        
        # 验证有效配置
        valid_result = config_adapter.validate_trademaster_config(valid_config)
        assert valid_result["valid"] is True
        
        # 验证无效配置
        invalid_result = config_adapter.validate_trademaster_config(invalid_config)
        assert invalid_result["valid"] is False
    
    def test_config_template_generation(self):
        """测试配置模板生成"""
        config_adapter = TradeMasterConfigAdapter()
        
        # 测试不同策略类型的模板生成
        strategy_types = ["algorithmic_trading", "portfolio_management", "order_execution"]
        
        for strategy_type in strategy_types:
            template = config_adapter.generate_config_template(strategy_type)
            
            assert isinstance(template, dict)
            assert "task" in template
            assert template["task"] == strategy_type
            assert "dataset" in template
            assert "agent" in template
            assert "environment" in template
            assert "trainer" in template


class TestConfigurationConsistency:
    """配置一致性测试"""
    
    def test_environment_config_consistency(self):
        """测试环境配置一致性"""
        # 测试不同环境下的配置一致性
        env_configs = [
            {"ENV": "development"},
            {"ENV": "testing"},
            {"ENV": "production"}
        ]
        
        for env_config in env_configs:
            with patch.dict(os.environ, env_config):
                settings = Settings()
                
                # 验证基本配置存在
                assert hasattr(settings, 'PROJECT_NAME')
                assert hasattr(settings, 'SECRET_KEY')
                assert hasattr(settings, 'DATABASE_URL')
                
                # 验证配置合理性
                if env_config["ENV"] == "production":
                    # 生产环境特殊要求
                    assert settings.DEBUG is False if hasattr(settings, 'DEBUG') else True
                    assert len(settings.SECRET_KEY) >= 32
    
    def test_database_config_consistency(self):
        """测试数据库配置一致性"""
        # 测试不同数据库URL的一致性
        database_configs = [
            "postgresql://user:pass@localhost:5432/test",
            "sqlite:///./test.db",
            "postgresql+asyncpg://user:pass@localhost:5432/test"
        ]
        
        for db_url in database_configs:
            with patch.dict(os.environ, {'DATABASE_URL': db_url}):
                settings = Settings()
                
                # 验证URL处理一致性
                async_url = settings.get_database_url(async_driver=True)
                sync_url = settings.get_database_url(async_driver=False)
                
                assert async_url is not None
                assert sync_url is not None
                
                # 验证数据库类型识别
                if "postgresql" in db_url:
                    assert "postgresql" in async_url
                    assert "postgresql" in sync_url
                elif "sqlite" in db_url:
                    assert "sqlite" in async_url
                    assert "sqlite" in sync_url
    
    def test_config_parameter_type_safety(self):
        """测试配置参数类型安全"""
        config_adapter = TradeMasterConfigAdapter()
        
        # 测试类型转换
        web_config = {
            "strategy_type": "algorithmic_trading",
            "agent_type": "dqn",
            "epochs": "100",  # 字符串形式的数字
            "learning_rate": "0.001",  # 字符串形式的浮点数
            "batch_size": "32",
            "gamma": "0.99"
        }
        
        tm_config = config_adapter.convert_web_config_to_trademaster(web_config)
        
        # 验证类型转换正确性
        assert isinstance(tm_config["trainer"]["epochs"], int)
        assert isinstance(tm_config["agent"]["lr"], float)
        assert isinstance(tm_config["agent"]["batch_size"], int)
        assert isinstance(tm_config["agent"]["gamma"], float)
        
        # 验证数值合理性
        assert tm_config["trainer"]["epochs"] == 100
        assert tm_config["agent"]["lr"] == 0.001
        assert tm_config["agent"]["batch_size"] == 32
        assert tm_config["agent"]["gamma"] == 0.99
    
    def test_default_value_consistency(self):
        """测试默认值一致性"""
        config_adapter = TradeMasterConfigAdapter()
        
        # 测试最小配置
        minimal_config = {
            "strategy_type": "algorithmic_trading",
            "agent_type": "dqn",
            "dataset_name": "BTC"
        }
        
        tm_config = config_adapter.convert_web_config_to_trademaster(minimal_config)
        
        # 验证默认值设置
        assert tm_config["agent"]["lr"] > 0  # 学习率应该有合理默认值
        assert tm_config["agent"]["batch_size"] > 0  # 批量大小应该有默认值
        assert tm_config["trainer"]["epochs"] > 0  # 训练轮数应该有默认值
        assert tm_config["environment"]["initial_amount"] > 0  # 初始资金应该有默认值


class TestConfigurationUpdates:
    """配置更新测试"""
    
    def test_config_hot_reload(self):
        """测试配置热重载"""
        # 模拟配置更新场景
        original_config = {
            "strategy_type": "algorithmic_trading",
            "agent_type": "dqn",
            "learning_rate": 0.001,
            "epochs": 100
        }
        
        updated_config = {
            "strategy_type": "algorithmic_trading", 
            "agent_type": "dqn",
            "learning_rate": 0.005,  # 更新学习率
            "epochs": 200  # 更新轮数
        }
        
        config_adapter = TradeMasterConfigAdapter()
        
        # 转换原始配置
        tm_config_1 = config_adapter.convert_web_config_to_trademaster(original_config)
        
        # 转换更新配置
        tm_config_2 = config_adapter.convert_web_config_to_trademaster(updated_config)
        
        # 验证更新正确性
        assert tm_config_1["agent"]["lr"] == 0.001
        assert tm_config_2["agent"]["lr"] == 0.005
        assert tm_config_1["trainer"]["epochs"] == 100
        assert tm_config_2["trainer"]["epochs"] == 200
    
    def test_config_migration(self):
        """测试配置迁移"""
        # 模拟旧版本配置格式
        old_config = {
            "algo_type": "dqn",  # 旧字段名
            "data_source": "BTC",  # 旧字段名
            "train_epochs": 100,  # 旧字段名
            "lr": 0.001
        }
        
        config_adapter = TradeMasterConfigAdapter()
        
        # 模拟配置迁移逻辑
        migrated_config = config_adapter._migrate_legacy_config(old_config)
        
        # 验证迁移结果
        assert migrated_config["agent_type"] == "dqn"
        assert migrated_config["dataset_name"] == "BTC"
        assert migrated_config["epochs"] == 100
        assert migrated_config["learning_rate"] == 0.001
    
    def test_config_versioning(self):
        """测试配置版本管理"""
        config_adapter = TradeMasterConfigAdapter()
        
        # 测试配置版本检查
        v1_config = {"version": "1.0", "strategy_type": "algorithmic_trading"}
        v2_config = {"version": "2.0", "strategy_type": "algorithmic_trading"}
        
        # 验证版本兼容性
        v1_result = config_adapter.validate_config_version(v1_config)
        v2_result = config_adapter.validate_config_version(v2_config)
        
        assert v1_result["compatible"] is True
        assert v2_result["compatible"] is True
        
        # 测试不兼容版本
        future_config = {"version": "99.0", "strategy_type": "algorithmic_trading"}
        future_result = config_adapter.validate_config_version(future_config)
        assert future_result["compatible"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])