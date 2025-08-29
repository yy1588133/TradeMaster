"""
TradeMaster配置适配器

负责Web界面配置与TradeMaster原生配置格式之间的转换和验证。
"""

from typing import Dict, Any, List, Tuple
from functools import lru_cache
from enum import Enum
from loguru import logger

from app.core.config import get_settings


# ==================== 枚举定义 ====================

class TaskType(str, Enum):
    """任务类型枚举"""
    STRATEGY_TRAINING = "strategy_training"
    DATA_PROCESSING = "data_processing" 
    BACKTEST_ANALYSIS = "backtest_analysis"
    PERFORMANCE_EVALUATION = "performance_evaluation"


class AgentType(str, Enum):
    """智能体类型枚举"""
    DQN = "dqn"
    DDPG = "ddpg"
    PPO = "ppo"
    SAC = "sac"
    TD3 = "td3"
    A2C = "a2c"


class DatasetType(str, Enum):
    """数据集类型枚举"""
    STOCK_DAILY = "stock_daily"
    STOCK_MINUTE = "stock_minute" 
    CRYPTO_HOURLY = "crypto_hourly"
    CRYPTO_MINUTE = "crypto_minute"
    FUTURES = "futures"
    FOREX = "forex"


class TradeMasterConfigError(Exception):
    """TradeMaster配置错误"""
    pass


class TradeMasterConfigAdapter:
    """TradeMaster配置适配器
    
    处理Web界面配置到TradeMaster原生配置的转换，
    以及配置参数的验证和优化建议。
    """
    
    def __init__(self):
        # 获取主配置实例
        self.settings = get_settings()
        
        # TradeMaster任务配置映射
        self.task_mapping = {
            "algorithmic_trading": {
                "task_name": "algorithmic_trading",
                "trainer_name": "algorithmic_trading",
                "valid_agents": ["dqn", "ppo", "a2c", "sacd", "td3", "ddpg"],
                "valid_datasets": ["BTC", "ETH", "LTC", "BCH", "ADA"]
            },
            "portfolio_management": {
                "task_name": "portfolio_management", 
                "trainer_name": "portfolio_management",
                "valid_agents": ["eiie", "sarl", "tic"],
                "valid_datasets": ["dj30", "crypto", "portfolio"]
            },
            "order_execution": {
                "task_name": "order_execution",
                "trainer_name": "order_execution", 
                "valid_agents": ["eteo", "pd"],
                "valid_datasets": ["BTCUSDT", "ETHUSDT"]
            },
            "high_frequency_trading": {
                "task_name": "high_frequency_trading",
                "trainer_name": "high_frequency_trading",
                "valid_agents": ["dqn", "ppo"],
                "valid_datasets": ["BTCUSDT_1min", "ETHUSDT_1min"]
            }
        }
        
        # 网络架构映射
        self.net_mapping = {
            "dqn": "dqn",
            "ppo": "ppo", 
            "a2c": "a2c",
            "sacd": "sacd",
            "td3": "td3",
            "ddpg": "ddpg",
            "eiie": "eiie",
            "sarl": "sarl",
            "tic": "tic"
        }
        
        # 优化器映射
        self.optimizer_mapping = {
            "adam": "adam",
            "adamw": "adamw",
            "sgd": "sgd",
            "rmsprop": "rmsprop"
        }
    
    def convert_web_config_to_trademaster(self, web_config: Dict[str, Any]) -> Dict[str, Any]:
        """转换Web配置到TradeMaster格式"""
        try:
            strategy_type = web_config.get("strategy_type", "algorithmic_trading")
            task_config = self.task_mapping.get(strategy_type)
            if not task_config:
                raise TradeMasterConfigError(f"不支持的策略类型: {strategy_type}")
            
            # 构建基础配置
            tm_config = {
                "task_name": task_config["task_name"],
                "trainer_name": task_config["trainer_name"],
                "dataset_name": web_config.get("dataset", task_config["valid_datasets"][0]),
                "agent_name": web_config.get("agent", task_config["valid_agents"][0]),
                "net_name": self._get_net_name(web_config.get("agent", task_config["valid_agents"][0])),
                "optimizer_name": web_config.get("optimizer", "adam")
            }
            
            # 添加训练参数 - 集成主配置中的训练设置
            training_params = {
                "epochs": web_config.get("epochs", 100),
                "learning_rate": web_config.get("learning_rate", 0.001),
                "batch_size": web_config.get("batch_size", 32),
                "if_remove": web_config.get("if_remove", True),
                "if_store": web_config.get("if_store", True),
                # 从主配置中获取训练相关设置
                "checkpoint_interval": self.settings.TRAINING_CHECKPOINT_INTERVAL,
                "early_stopping_patience": self.settings.TRAINING_EARLY_STOPPING_PATIENCE,
                "max_workers": self.settings.DATA_PROCESSING_MAX_WORKERS
            }
            tm_config.update(training_params)
            
            # 添加任务特定参数
            if strategy_type == "algorithmic_trading":
                tm_config.update({
                    "train_start_date": web_config.get("train_start_date", "2020-01-01"),
                    "train_end_date": web_config.get("train_end_date", "2021-12-31"),
                    "test_start_date": web_config.get("test_start_date", "2022-01-01"),
                    "test_end_date": web_config.get("test_end_date", "2022-12-31"),
                    "initial_capital": web_config.get("initial_capital", 100000)
                })
            
            # 添加文件存储路径（从主配置获取）
            tm_config.update({
                "data_dir": self.settings.DATA_DIR,
                "model_dir": self.settings.MODEL_DIR,
                "log_dir": self.settings.LOG_DIR,
                "upload_dir": self.settings.UPLOAD_DIR
            })
            
            # 添加API集成设置
            tm_config.update({
                "api_url": self.settings.TRADEMASTER_API_URL,
                "api_timeout": self.settings.TRADEMASTER_API_TIMEOUT,
                "api_retry_attempts": self.settings.TRADEMASTER_API_RETRY_ATTEMPTS,
                "api_retry_delay": self.settings.TRADEMASTER_API_RETRY_DELAY
            })
            
            return tm_config
            
        except Exception as e:
            logger.error(f"配置转换失败: {str(e)}")
            raise TradeMasterConfigError(f"配置转换失败: {str(e)}")
    
    def validate_trademaster_config(self, tm_config: Dict[str, Any]) -> Dict[str, Any]:
        """验证TradeMaster配置"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # 验证必需参数
            required_params = ["task_name", "trainer_name", "dataset_name", "agent_name"]
            for param in required_params:
                if param not in tm_config:
                    errors.append(f"缺少必需参数: {param}")
            
            # 验证任务类型和代理兼容性
            task_name = tm_config.get("task_name")
            agent_name = tm_config.get("agent_name")
            
            if task_name and task_name in self.task_mapping:
                valid_agents = self.task_mapping[task_name]["valid_agents"]
                if agent_name not in valid_agents:
                    errors.append(f"代理 '{agent_name}' 不支持任务 '{task_name}'，支持的代理: {valid_agents}")
                
                valid_datasets = self.task_mapping[task_name]["valid_datasets"]
                dataset_name = tm_config.get("dataset_name")
                if dataset_name not in valid_datasets:
                    warnings.append(f"数据集 '{dataset_name}' 可能不适合任务 '{task_name}'，建议使用: {valid_datasets}")
            
            # 验证训练参数范围
            epochs = tm_config.get("epochs", 0)
            if not (1 <= epochs <= 10000):
                errors.append(f"训练轮数必须在1-10000之间，当前值: {epochs}")
            
            learning_rate = tm_config.get("learning_rate", 0)
            if not (0.00001 <= learning_rate <= 1.0):
                errors.append(f"学习率必须在0.00001-1.0之间，当前值: {learning_rate}")
            
            batch_size = tm_config.get("batch_size", 0)
            if not (1 <= batch_size <= 1024):
                errors.append(f"批次大小必须在1-1024之间，当前值: {batch_size}")
            
            # 验证文件路径
            required_paths = ["data_dir", "model_dir", "log_dir"]
            for path_key in required_paths:
                if path_key not in tm_config:
                    warnings.append(f"建议设置路径: {path_key}")
            
            # 性能优化建议
            if epochs > 1000:
                suggestions.append("训练轮数较多，建议启用早停机制")
            
            if batch_size < 16:
                suggestions.append("批次大小较小，可能影响训练效率")
            
            # 集成主配置的验证
            if self.settings.is_production:
                if tm_config.get("api_url", "").startswith("http://localhost"):
                    warnings.append("生产环境不应使用localhost API地址")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"配置验证异常: {str(e)}")
            return {
                "valid": False,
                "errors": [f"验证异常: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }
    
    def _get_net_name(self, agent_name: str) -> str:
        """获取网络架构名称"""
        return self.net_mapping.get(agent_name, agent_name)
    
    def get_default_config(self, strategy_type: str) -> Dict[str, Any]:
        """获取默认配置"""
        task_config = self.task_mapping.get(strategy_type)
        if not task_config:
            raise TradeMasterConfigError(f"不支持的策略类型: {strategy_type}")
        
        default_config = {
            "strategy_type": strategy_type,
            "agent": task_config["valid_agents"][0],
            "dataset": task_config["valid_datasets"][0],
            "optimizer": "adam",
            "epochs": 100,
            "learning_rate": 0.001,
            "batch_size": 32,
            # 集成主配置中的默认设置
            "checkpoint_interval": self.settings.TRAINING_CHECKPOINT_INTERVAL,
            "early_stopping_patience": self.settings.TRAINING_EARLY_STOPPING_PATIENCE,
            "max_workers": self.settings.DATA_PROCESSING_MAX_WORKERS
        }
        
        # 添加任务特定默认值
        if strategy_type == "algorithmic_trading":
            default_config.update({
                "train_start_date": "2020-01-01",
                "train_end_date": "2021-12-31",
                "test_start_date": "2022-01-01",
                "test_end_date": "2022-12-31",
                "initial_capital": 100000
            })
        
        return default_config
    
    def get_available_configs(self) -> Dict[str, Any]:
        """获取所有可用的配置选项"""
        return {
            "strategy_types": list(self.task_mapping.keys()),
            "agents_by_strategy": {
                strategy: config["valid_agents"]
                for strategy, config in self.task_mapping.items()
            },
            "datasets_by_strategy": {
                strategy: config["valid_datasets"] 
                for strategy, config in self.task_mapping.items()
            },
            "optimizers": list(self.optimizer_mapping.keys()),
            "training_limits": {
                "min_epochs": 1,
                "max_epochs": 10000,
                "min_learning_rate": 0.00001,
                "max_learning_rate": 1.0,
                "min_batch_size": 1,
                "max_batch_size": 1024
            },
            "paths": {
                "data_dir": self.settings.DATA_DIR,
                "model_dir": self.settings.MODEL_DIR,
                "log_dir": self.settings.LOG_DIR,
                "upload_dir": self.settings.UPLOAD_DIR
            }
        }


# 全局配置适配器实例缓存
@lru_cache()
def get_config_adapter() -> TradeMasterConfigAdapter:
    """获取TradeMaster配置适配器实例
    
    使用LRU缓存确保单例，提高性能。
    
    Returns:
        TradeMasterConfigAdapter实例
    """
    return TradeMasterConfigAdapter()


# 便捷函数
def convert_web_to_trademaster_config(web_config: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：转换Web配置到TradeMaster格式
    
    Args:
        web_config: Web界面配置
        
    Returns:
        TradeMaster格式配置
        
    Raises:
        TradeMasterConfigError: 转换失败时抛出
    """
    adapter = get_config_adapter()
    return adapter.convert_web_config_to_trademaster(web_config)


def validate_trademaster_config(tm_config: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：验证TradeMaster配置
    
    Args:
        tm_config: TradeMaster配置
        
    Returns:
        验证结果字典
    """
    adapter = get_config_adapter()
    return adapter.validate_trademaster_config(tm_config)


def get_default_strategy_config(strategy_type: str) -> Dict[str, Any]:
    """便捷函数：获取策略默认配置
    
    Args:
        strategy_type: 策略类型
        
    Returns:
        默认配置字典
        
    Raises:
        TradeMasterConfigError: 策略类型不支持时抛出
    """
    adapter = get_config_adapter()
    return adapter.get_default_config(strategy_type)


# 导出主要类和函数
__all__ = [
    "TradeMasterConfigAdapter",
    "TradeMasterConfigError", 
    "get_config_adapter",
    "convert_web_to_trademaster_config",
    "validate_trademaster_config",
    "get_default_strategy_config"
]