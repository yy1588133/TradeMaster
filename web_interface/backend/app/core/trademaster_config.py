"""
TradeMaster配置适配器

提供Web界面配置与TradeMaster原生配置之间的转换功能。
支持所有策略类型的配置模板、验证和双向转换。
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from loguru import logger

from app.core.config import settings


class StrategyType(str, Enum):
    """策略类型枚举"""
    ALGORITHMIC_TRADING = "algorithmic_trading"
    PORTFOLIO_MANAGEMENT = "portfolio_management" 
    ORDER_EXECUTION = "order_execution"
    HIGH_FREQUENCY_TRADING = "high_frequency_trading"


class ConfigFormat(str, Enum):
    """配置格式枚举"""
    JSON = "json"
    YAML = "yaml"
    PYTHON = "python"


class TradeMasterConfigError(Exception):
    """TradeMaster配置异常"""
    pass


class WebStrategyConfig(BaseModel):
    """Web界面策略配置模型"""
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    
    # 基础参数
    dataset: str = Field(..., description="数据集")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    initial_capital: float = Field(1000000, description="初始资金")
    
    # 策略特定参数
    strategy_params: Dict[str, Any] = Field({}, description="策略参数")
    
    # 训练参数
    training_params: Dict[str, Any] = Field({}, description="训练参数")
    
    # 环境参数
    environment_params: Dict[str, Any] = Field({}, description="环境参数")
    
    # 智能体参数（如果适用）
    agent_params: Dict[str, Any] = Field({}, description="智能体参数")
    
    # 其他配置
    tags: List[str] = Field([], description="标签")
    metadata: Dict[str, Any] = Field({}, description="元数据")


class TradeMasterNativeConfig(BaseModel):
    """TradeMaster原生配置模型"""
    # 基础配置
    config_name: str
    work_dir: str
    
    # 数据配置
    data: Dict[str, Any]
    
    # 环境配置
    environment: Dict[str, Any]
    
    # 智能体配置（如果适用）
    agent: Optional[Dict[str, Any]] = None
    
    # 训练器配置
    trainer: Optional[Dict[str, Any]] = None
    
    # 其他配置
    custom: Dict[str, Any] = {}


class TradeMasterConfigAdapter:
    """TradeMaster配置适配器
    
    负责Web配置与TradeMaster原生配置之间的转换
    """
    
    def __init__(self):
        """初始化配置适配器"""
        # TradeMaster根路径
        self.trademaster_root = Path(__file__).resolve().parents[4]
        
        # 配置模板路径
        self.config_templates_dir = self.trademaster_root / "configs"
        
        # 策略类型到配置模板的映射
        self.strategy_type_mapping = {
            StrategyType.ALGORITHMIC_TRADING: {
                "template_dir": "algorithmic_trading",
                "default_config": "dqn_BTC.py"
            },
            StrategyType.PORTFOLIO_MANAGEMENT: {
                "template_dir": "portfolio_management",
                "default_config": "sac_portfolio_management.py"
            },
            StrategyType.ORDER_EXECUTION: {
                "template_dir": "order_execution",
                "default_config": "eteo_BTC.py"
            },
            StrategyType.HIGH_FREQUENCY_TRADING: {
                "template_dir": "high_frequency_trading",
                "default_config": "algorithmic_trading_BTC.py"
            }
        }
        
        logger.info("TradeMaster配置适配器初始化完成")
    
    # ==================== 配置转换 ====================
    
    def convert_web_config_to_trademaster(
        self,
        web_config: Union[WebStrategyConfig, Dict[str, Any]],
        output_format: ConfigFormat = ConfigFormat.PYTHON
    ) -> Dict[str, Any]:
        """将Web配置转换为TradeMaster配置
        
        Args:
            web_config: Web界面配置
            output_format: 输出格式
            
        Returns:
            Dict[str, Any]: TradeMaster配置
        """
        try:
            # 确保输入是WebStrategyConfig对象
            if isinstance(web_config, dict):
                web_config = WebStrategyConfig(**web_config)
            
            # 获取基础模板
            base_template = self._get_base_template(web_config.strategy_type)
            
            # 构建TradeMaster配置
            trademaster_config = self._build_trademaster_config(web_config, base_template)
            
            # 根据输出格式处理
            if output_format == ConfigFormat.PYTHON:
                return self._convert_to_python_config(trademaster_config)
            elif output_format == ConfigFormat.JSON:
                return trademaster_config
            elif output_format == ConfigFormat.YAML:
                return self._convert_to_yaml_config(trademaster_config)
            else:
                raise TradeMasterConfigError(f"不支持的输出格式: {output_format}")
                
        except Exception as e:
            logger.error(f"Web配置转换失败: {str(e)}")
            raise TradeMasterConfigError(f"Web配置转换失败: {str(e)}")
    
    def convert_trademaster_config_to_web(
        self,
        trademaster_config: Union[str, Path, Dict[str, Any]],
        config_format: Optional[ConfigFormat] = None
    ) -> WebStrategyConfig:
        """将TradeMaster配置转换为Web配置
        
        Args:
            trademaster_config: TradeMaster配置（文件路径或字典）
            config_format: 配置格式（如果是文件路径则自动检测）
            
        Returns:
            WebStrategyConfig: Web配置
        """
        try:
            # 解析输入配置
            if isinstance(trademaster_config, (str, Path)):
                config_dict = self._load_config_file(trademaster_config, config_format)
            else:
                config_dict = trademaster_config
            
            # 提取Web配置字段
            web_config_dict = self._extract_web_config_fields(config_dict)
            
            return WebStrategyConfig(**web_config_dict)
            
        except Exception as e:
            logger.error(f"TradeMaster配置转换失败: {str(e)}")
            raise TradeMasterConfigError(f"TradeMaster配置转换失败: {str(e)}")
    
    # ==================== 配置模板管理 ====================
    
    def get_strategy_config_template(
        self,
        strategy_type: StrategyType,
        template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取策略配置模板
        
        Args:
            strategy_type: 策略类型
            template_name: 模板名称（可选）
            
        Returns:
            Dict[str, Any]: 配置模板
        """
        try:
            if template_name is None:
                # 使用默认模板
                template_info = self.strategy_type_mapping.get(strategy_type)
                if not template_info:
                    raise TradeMasterConfigError(f"不支持的策略类型: {strategy_type}")
                
                template_dir = self.config_templates_dir / template_info["template_dir"]
                template_file = template_dir / template_info["default_config"]
            else:
                # 使用指定模板
                template_file = self.config_templates_dir / strategy_type.value / template_name
            
            if not template_file.exists():
                raise TradeMasterConfigError(f"模板文件不存在: {template_file}")
            
            return self._load_config_file(template_file)
            
        except Exception as e:
            logger.error(f"获取配置模板失败: {strategy_type}, {str(e)}")
            raise TradeMasterConfigError(f"获取配置模板失败: {str(e)}")
    
    def list_available_templates(
        self,
        strategy_type: Optional[StrategyType] = None
    ) -> Dict[str, List[str]]:
        """列出可用的配置模板
        
        Args:
            strategy_type: 策略类型（可选，None表示所有类型）
            
        Returns:
            Dict[str, List[str]]: 按策略类型分组的模板列表
        """
        try:
            templates = {}
            
            strategy_types = [strategy_type] if strategy_type else list(StrategyType)
            
            for st in strategy_types:
                template_info = self.strategy_type_mapping.get(st)
                if not template_info:
                    continue
                
                template_dir = self.config_templates_dir / template_info["template_dir"]
                if template_dir.exists():
                    template_files = []
                    for file_path in template_dir.glob("*.py"):
                        template_files.append(file_path.name)
                    templates[st.value] = template_files
                else:
                    templates[st.value] = []
            
            return templates
            
        except Exception as e:
            logger.error(f"列出可用模板失败: {str(e)}")
            raise TradeMasterConfigError(f"列出可用模板失败: {str(e)}")
    
    # ==================== 配置验证 ====================
    
    def validate_web_config(self, web_config: Union[WebStrategyConfig, Dict[str, Any]]) -> Dict[str, Any]:
        """验证Web配置
        
        Args:
            web_config: Web配置
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 确保输入是WebStrategyConfig对象
            if isinstance(web_config, dict):
                web_config = WebStrategyConfig(**web_config)
            
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            
            # 基础字段验证
            self._validate_basic_fields(web_config, validation_result)
            
            # 策略特定验证
            self._validate_strategy_specific_fields(web_config, validation_result)
            
            # 参数一致性验证
            self._validate_parameter_consistency(web_config, validation_result)
            
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
            return validation_result
            
        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return {
                "valid": False,
                "errors": [f"验证过程失败: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }
    
    def validate_trademaster_config(self, trademaster_config: Dict[str, Any]) -> Dict[str, Any]:
        """验证TradeMaster配置
        
        Args:
            trademaster_config: TradeMaster配置
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            
            # 检查必需字段
            required_fields = ["config_name", "work_dir", "data", "environment"]
            for field in required_fields:
                if field not in trademaster_config:
                    validation_result["errors"].append(f"缺少必需字段: {field}")
            
            # 检查数据配置
            if "data" in trademaster_config:
                data_config = trademaster_config["data"]
                if "data_path" not in data_config:
                    validation_result["warnings"].append("数据配置中缺少data_path字段")
            
            # 检查环境配置
            if "environment" in trademaster_config:
                env_config = trademaster_config["environment"]
                if "name" not in env_config:
                    validation_result["warnings"].append("环境配置中缺少name字段")
            
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
            return validation_result
            
        except Exception as e:
            logger.error(f"TradeMaster配置验证失败: {str(e)}")
            return {
                "valid": False,
                "errors": [f"验证过程失败: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }
    
    # ==================== 私有方法 ====================
    
    def _get_base_template(self, strategy_type: StrategyType) -> Dict[str, Any]:
        """获取基础配置模板"""
        return self.get_strategy_config_template(strategy_type)
    
    def _build_trademaster_config(
        self,
        web_config: WebStrategyConfig,
        base_template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建TradeMaster配置"""
        config = base_template.copy()
        
        # 更新基础配置
        config["config_name"] = web_config.name
        config["work_dir"] = f"./work_dir/{web_config.name}_{int(datetime.utcnow().timestamp())}"
        
        # 更新数据配置
        if "data" in config:
            config["data"].update({
                "data_path": f"./data/{web_config.dataset}",
                "start_date": web_config.start_date,
                "end_date": web_config.end_date
            })
        
        # 更新环境配置
        if "environment" in config:
            config["environment"].update({
                "initial_capital": web_config.initial_capital,
                **web_config.environment_params
            })
        
        # 更新智能体配置
        if "agent" in config and web_config.agent_params:
            config["agent"].update(web_config.agent_params)
        
        # 更新训练器配置
        if "trainer" in config and web_config.training_params:
            config["trainer"].update(web_config.training_params)
        
        # 添加策略参数
        config.update(web_config.strategy_params)
        
        return config
    
    def _convert_to_python_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为Python配置格式"""
        # Python配置通常直接返回字典
        return config
    
    def _convert_to_yaml_config(self, config: Dict[str, Any]) -> str:
        """转换为YAML配置格式"""
        return yaml.dump(config, default_flow_style=False, allow_unicode=True)
    
    def _load_config_file(
        self,
        file_path: Union[str, Path],
        config_format: Optional[ConfigFormat] = None
    ) -> Dict[str, Any]:
        """加载配置文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise TradeMasterConfigError(f"配置文件不存在: {file_path}")
        
        # 自动检测格式
        if config_format is None:
            if file_path.suffix == ".json":
                config_format = ConfigFormat.JSON
            elif file_path.suffix in [".yaml", ".yml"]:
                config_format = ConfigFormat.YAML
            elif file_path.suffix == ".py":
                config_format = ConfigFormat.PYTHON
            else:
                raise TradeMasterConfigError(f"无法确定配置文件格式: {file_path}")
        
        # 加载配置
        if config_format == ConfigFormat.JSON:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif config_format == ConfigFormat.YAML:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif config_format == ConfigFormat.PYTHON:
            # 对于Python配置文件，需要特殊处理
            return self._load_python_config(file_path)
        else:
            raise TradeMasterConfigError(f"不支持的配置格式: {config_format}")
    
    def _load_python_config(self, file_path: Path) -> Dict[str, Any]:
        """加载Python配置文件"""
        try:
            # 简单的Python配置解析
            # 这里可以根据实际的TradeMaster配置文件格式进行调整
            config_dict = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 执行Python配置文件并提取变量
            namespace = {}
            exec(content, namespace)
            
            # 提取配置变量（排除内置变量和导入的模块）
            for key, value in namespace.items():
                if not key.startswith('__') and not callable(value):
                    config_dict[key] = value
            
            return config_dict
            
        except Exception as e:
            logger.error(f"加载Python配置失败: {file_path}, {str(e)}")
            raise TradeMasterConfigError(f"加载Python配置失败: {str(e)}")
    
    def _extract_web_config_fields(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """从TradeMaster配置中提取Web配置字段"""
        web_config = {
            "name": config_dict.get("config_name", "unnamed_strategy"),
            "description": config_dict.get("description", ""),
            "strategy_type": StrategyType.ALGORITHMIC_TRADING,  # 默认值，需要根据实际配置推断
            "dataset": "default",
            "start_date": "2020-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 1000000,
            "strategy_params": {},
            "training_params": {},
            "environment_params": {},
            "agent_params": {},
            "tags": [],
            "metadata": {}
        }
        
        # 从数据配置中提取信息
        if "data" in config_dict:
            data_config = config_dict["data"]
            web_config.update({
                "dataset": data_config.get("data_path", "default").split("/")[-1],
                "start_date": data_config.get("start_date", "2020-01-01"),
                "end_date": data_config.get("end_date", "2023-12-31")
            })
        
        # 从环境配置中提取信息
        if "environment" in config_dict:
            env_config = config_dict["environment"]
            web_config["initial_capital"] = env_config.get("initial_capital", 1000000)
            web_config["environment_params"] = {
                k: v for k, v in env_config.items() 
                if k not in ["initial_capital"]
            }
        
        # 从智能体配置中提取信息
        if "agent" in config_dict:
            web_config["agent_params"] = config_dict["agent"]
        
        # 从训练器配置中提取信息
        if "trainer" in config_dict:
            web_config["training_params"] = config_dict["trainer"]
        
        return web_config
    
    def _validate_basic_fields(self, web_config: WebStrategyConfig, result: Dict[str, Any]):
        """验证基础字段"""
        # 验证日期格式
        try:
            datetime.strptime(web_config.start_date, "%Y-%m-%d")
        except ValueError:
            result["errors"].append("开始日期格式错误，应为YYYY-MM-DD")
        
        try:
            datetime.strptime(web_config.end_date, "%Y-%m-%d")
        except ValueError:
            result["errors"].append("结束日期格式错误，应为YYYY-MM-DD")
        
        # 验证日期逻辑
        try:
            start_dt = datetime.strptime(web_config.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(web_config.end_date, "%Y-%m-%d")
            if start_dt >= end_dt:
                result["errors"].append("开始日期必须早于结束日期")
        except ValueError:
            pass  # 日期格式错误已在上面检查
        
        # 验证初始资金
        if web_config.initial_capital <= 0:
            result["errors"].append("初始资金必须大于0")
        
        # 验证策略名称
        if not web_config.name or len(web_config.name.strip()) == 0:
            result["errors"].append("策略名称不能为空")
    
    def _validate_strategy_specific_fields(self, web_config: WebStrategyConfig, result: Dict[str, Any]):
        """验证策略特定字段"""
        # 根据策略类型进行特定验证
        if web_config.strategy_type == StrategyType.ALGORITHMIC_TRADING:
            # 算法交易策略验证
            if "agent_type" not in web_config.agent_params:
                result["warnings"].append("建议指定智能体类型")
        
        elif web_config.strategy_type == StrategyType.PORTFOLIO_MANAGEMENT:
            # 投资组合管理策略验证
            if "rebalance_frequency" not in web_config.strategy_params:
                result["warnings"].append("建议指定重平衡频率")
        
        elif web_config.strategy_type == StrategyType.ORDER_EXECUTION:
            # 订单执行策略验证
            if "execution_style" not in web_config.strategy_params:
                result["warnings"].append("建议指定执行风格")
        
        elif web_config.strategy_type == StrategyType.HIGH_FREQUENCY_TRADING:
            # 高频交易策略验证
            if "latency_threshold" not in web_config.strategy_params:
                result["warnings"].append("建议设置延迟阈值")
    
    def _validate_parameter_consistency(self, web_config: WebStrategyConfig, result: Dict[str, Any]):
        """验证参数一致性"""
        # 检查参数之间的一致性
        if web_config.training_params.get("episodes", 0) > 10000:
            result["warnings"].append("训练轮次较多，可能需要较长时间")
        
        if web_config.initial_capital > 10000000:  # 1000万
            result["warnings"].append("初始资金较大，请确认是否正确")


# 全局配置适配器实例
_config_adapter = None

def get_config_adapter() -> TradeMasterConfigAdapter:
    """获取配置适配器实例
    
    Returns:
        TradeMasterConfigAdapter: 配置适配器实例
    """
    global _config_adapter
    if _config_adapter is None:
        _config_adapter = TradeMasterConfigAdapter()
    return _config_adapter


# 导出主要类和函数
__all__ = [
    "TradeMasterConfigAdapter",
    "WebStrategyConfig", 
    "TradeMasterNativeConfig",
    "StrategyType",
    "ConfigFormat",
    "TradeMasterConfigError",
    "get_config_adapter"
]