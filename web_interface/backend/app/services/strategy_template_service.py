"""
策略模板服务

提供策略模板的管理、验证和配置生成功能。
支持多种策略类型的模板，与TradeMaster配置系统集成。
"""

from typing import Dict, Any, List, Optional
from enum import Enum

from loguru import logger

from app.models.database import StrategyType
from app.core.trademaster_config import TaskType, AgentType, DatasetType


class TemplateCategory(str, Enum):
    """模板分类枚举"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    CUSTOM = "custom"


class StrategyTemplate:
    """策略模板类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        strategy_type: StrategyType,
        category: TemplateCategory,
        config_template: Dict[str, Any],
        parameters_template: Dict[str, Any],
        example_values: Dict[str, Any],
        requirements: List[str] = None,
        tags: List[str] = None
    ):
        self.name = name
        self.description = description
        self.strategy_type = strategy_type
        self.category = category
        self.config_template = config_template
        self.parameters_template = parameters_template
        self.example_values = example_values
        self.requirements = requirements or []
        self.tags = tags or []
    
    def generate_config(self, custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成策略配置
        
        Args:
            custom_params: 自定义参数
            
        Returns:
            Dict[str, Any]: 生成的配置
        """
        config = self.config_template.copy()
        
        # 合并自定义参数
        if custom_params:
            config.update(custom_params)
        
        return config
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置
        
        Args:
            config: 待验证的配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查必需字段
        required_fields = self.config_template.keys()
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查数据类型
        for field, template_value in self.config_template.items():
            if field in config:
                config_value = config[field]
                if not isinstance(config_value, type(template_value)):
                    errors.append(f"字段 {field} 类型错误，期望 {type(template_value).__name__}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "strategy_type": self.strategy_type.value,
            "category": self.category.value,
            "config_template": self.config_template,
            "parameters_template": self.parameters_template,
            "example_values": self.example_values,
            "requirements": self.requirements,
            "tags": self.tags
        }


class StrategyTemplateService:
    """策略模板服务"""
    
    def __init__(self):
        """初始化模板服务"""
        self._templates: Dict[str, StrategyTemplate] = {}
        self._initialize_builtin_templates()
        logger.info("策略模板服务初始化完成")
    
    def _initialize_builtin_templates(self):
        """初始化内置模板"""
        # 算法交易模板
        self._add_algorithmic_trading_templates()
        
        # 投资组合管理模板
        self._add_portfolio_management_templates()
        
        # 订单执行模板
        self._add_order_execution_templates()
        
        # 高频交易模板
        self._add_high_frequency_trading_templates()
    
    def _add_algorithmic_trading_templates(self):
        """添加算法交易模板"""
        # DQN算法交易策略 - 初级
        dqn_template = StrategyTemplate(
            name="DQN算法交易策略",
            description="基于深度Q网络的算法交易策略，适用于单资产交易，适合初学者",
            strategy_type=StrategyType.ALGORITHMIC_TRADING,
            category=TemplateCategory.BEGINNER,
            config_template={
                "task_name": "algorithmic_trading",
                "dataset_name": "BTC",
                "agent_name": "dqn",
                "trainer_name": "algorithmic_trading",
                "net_name": "dqn",
                "optimizer_name": "adam",
                "loss_name": "mse"
            },
            parameters_template={
                "learning_rate": 0.001,
                "batch_size": 32,
                "memory_size": 10000,
                "epsilon_start": 1.0,
                "epsilon_end": 0.01,
                "epsilon_decay": 0.995,
                "target_update_freq": 100,
                "train_episodes": 1000
            },
            example_values={
                "symbol": "BTC-USDT",
                "timeframe": "1h",
                "lookback_window": 30,
                "initial_balance": 10000
            },
            requirements=[
                "需要历史价格数据",
                "适合单一资产交易",
                "建议使用GPU加速训练"
            ],
            tags=["DQN", "深度学习", "单资产", "初级"]
        )
        self._templates[dqn_template.name] = dqn_template
        
        # PPO算法交易策略 - 中级
        ppo_template = StrategyTemplate(
            name="PPO算法交易策略",
            description="基于近端策略优化的算法交易策略，适用于连续动作空间",
            strategy_type=StrategyType.ALGORITHMIC_TRADING,
            category=TemplateCategory.INTERMEDIATE,
            config_template={
                "task_name": "algorithmic_trading",
                "dataset_name": "BTC",
                "agent_name": "ppo",
                "trainer_name": "algorithmic_trading",
                "net_name": "ppo",
                "optimizer_name": "adam",
                "loss_name": "ppo_loss"
            },
            parameters_template={
                "learning_rate": 0.0003,
                "batch_size": 64,
                "n_steps": 2048,
                "clip_range": 0.2,
                "entropy_coef": 0.01,
                "value_coef": 0.5,
                "max_grad_norm": 0.5,
                "train_epochs": 10
            },
            example_values={
                "symbol": "ETH-USDT",
                "timeframe": "15m",
                "max_position": 1.0,
                "transaction_cost": 0.001
            },
            requirements=[
                "需要连续动作空间",
                "适合复杂策略逻辑",
                "需要较多计算资源"
            ],
            tags=["PPO", "强化学习", "连续动作", "中级"]
        )
        self._templates[ppo_template.name] = ppo_template
        
        # DDPG算法交易策略 - 高级
        ddpg_template = StrategyTemplate(
            name="DDPG算法交易策略",
            description="基于深度确定性策略梯度的高级算法交易策略",
            strategy_type=StrategyType.ALGORITHMIC_TRADING,
            category=TemplateCategory.ADVANCED,
            config_template={
                "task_name": "algorithmic_trading",
                "dataset_name": "BTC",
                "agent_name": "ddpg",
                "trainer_name": "algorithmic_trading",
                "net_name": "ddpg",
                "optimizer_name": "adam",
                "loss_name": "ddpg_loss"
            },
            parameters_template={
                "actor_lr": 0.0001,
                "critic_lr": 0.001,
                "batch_size": 128,
                "memory_size": 100000,
                "tau": 0.005,
                "gamma": 0.99,
                "noise_scale": 0.1,
                "noise_decay": 0.99
            },
            example_values={
                "symbol": "BTC-USDT",
                "timeframe": "5m",
                "features": ["price", "volume", "volatility"],
                "risk_threshold": 0.02
            },
            requirements=[
                "需要大量历史数据",
                "适合高频交易场景",
                "需要专业参数调优"
            ],
            tags=["DDPG", "确定性策略", "高频", "高级"]
        )
        self._templates[ddpg_template.name] = ddpg_template
    
    def _add_portfolio_management_templates(self):
        """添加投资组合管理模板"""
        # EIIE投资组合策略
        eiie_template = StrategyTemplate(
            name="EIIE投资组合策略",
            description="基于集成投资组合优化的多资产配置策略",
            strategy_type=StrategyType.PORTFOLIO_MANAGEMENT,
            category=TemplateCategory.INTERMEDIATE,
            config_template={
                "task_name": "portfolio_management",
                "dataset_name": "dj30",
                "agent_name": "eiie",
                "trainer_name": "portfolio_management",
                "net_name": "eiie",
                "optimizer_name": "adam",
                "loss_name": "portfolio_loss"
            },
            parameters_template={
                "learning_rate": 0.001,
                "batch_size": 128,
                "window_size": 50,
                "portfolio_size": 10,
                "transaction_cost": 0.0025,
                "cash_bias_init": 1.0,
                "training_steps": 10000
            },
            example_values={
                "assets": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
                "rebalance_frequency": "daily",
                "risk_tolerance": "medium",
                "benchmark": "SPY"
            },
            requirements=[
                "需要多资产价格数据",
                "适合长期投资策略",
                "需要考虑交易成本"
            ],
            tags=["EIIE", "投资组合", "多资产", "长期"]
        )
        self._templates[eiie_template.name] = eiie_template
        
        # SARL投资组合策略
        sarl_template = StrategyTemplate(
            name="SARL投资组合策略",
            description="基于状态增强强化学习的投资组合管理策略",
            strategy_type=StrategyType.PORTFOLIO_MANAGEMENT,
            category=TemplateCategory.ADVANCED,
            config_template={
                "task_name": "portfolio_management",
                "dataset_name": "dj30",
                "agent_name": "sarl",
                "trainer_name": "portfolio_management",
                "net_name": "sarl",
                "optimizer_name": "adam",
                "loss_name": "sarl_loss"
            },
            parameters_template={
                "learning_rate": 0.0005,
                "batch_size": 256,
                "state_dim": 128,
                "action_dim": 30,
                "hidden_dims": [256, 128, 64],
                "dropout_rate": 0.1,
                "regularization": 0.001
            },
            example_values={
                "universe": "dow_jones_30",
                "lookback_days": 60,
                "rebalance_period": 5,
                "risk_aversion": 2.0
            },
            requirements=[
                "需要大规模资产数据",
                "适合机构投资者",
                "需要高级风险管理"
            ],
            tags=["SARL", "状态增强", "机构级", "高级"]
        )
        self._templates[sarl_template.name] = sarl_template
    
    def _add_order_execution_templates(self):
        """添加订单执行模板"""
        # ETEO订单执行策略
        eteo_template = StrategyTemplate(
            name="ETEO订单执行策略",
            description="基于强化学习的最优订单执行策略，最小化市场冲击",
            strategy_type=StrategyType.ORDER_EXECUTION,
            category=TemplateCategory.INTERMEDIATE,
            config_template={
                "task_name": "order_execution",
                "dataset_name": "BTC",
                "agent_name": "eteo",
                "trainer_name": "order_execution",
                "net_name": "eteo",
                "optimizer_name": "adam",
                "loss_name": "execution_loss"
            },
            parameters_template={
                "learning_rate": 0.0001,
                "batch_size": 64,
                "memory_size": 50000,
                "update_frequency": 4,
                "target_update": 1000,
                "exploration_noise": 0.1,
                "policy_noise": 0.2
            },
            example_values={
                "order_size": 1000,
                "execution_horizon": 60,  # minutes
                "market_impact": 0.001,
                "urgency": "normal"
            },
            requirements=[
                "需要高频订单簿数据",
                "适合大额订单执行",
                "需要实时市场数据"
            ],
            tags=["ETEO", "订单执行", "市场冲击", "实时"]
        )
        self._templates[eteo_template.name] = eteo_template
        
        # TWP订单执行策略
        twp_template = StrategyTemplate(
            name="TWP订单执行策略",
            description="基于时间加权价格的订单执行策略",
            strategy_type=StrategyType.ORDER_EXECUTION,
            category=TemplateCategory.BEGINNER,
            config_template={
                "task_name": "order_execution",
                "dataset_name": "BTC",
                "agent_name": "twp",
                "trainer_name": "order_execution",
                "net_name": "twp",
                "optimizer_name": "sgd",
                "loss_name": "twp_loss"
            },
            parameters_template={
                "learning_rate": 0.01,
                "batch_size": 32,
                "execution_time": 30,  # minutes
                "slice_size": 100,
                "participation_rate": 0.1,
                "price_limit": 0.005
            },
            example_values={
                "total_quantity": 10000,
                "time_horizon": 120,  # minutes
                "benchmark": "twap",
                "slippage_tolerance": 0.002
            },
            requirements=[
                "适合中等规模订单",
                "需要历史执行数据",
                "简单易用"
            ],
            tags=["TWP", "TWAP", "简单", "中等规模"]
        )
        self._templates[twp_template.name] = twp_template
    
    def _add_high_frequency_trading_templates(self):
        """添加高频交易模板"""
        # DDQN高频交易策略
        ddqn_hft_template = StrategyTemplate(
            name="DDQN高频交易策略",
            description="基于双重深度Q网络的高频交易策略，适用于毫秒级交易",
            strategy_type=StrategyType.HIGH_FREQUENCY_TRADING,
            category=TemplateCategory.ADVANCED,
            config_template={
                "task_name": "high_frequency_trading",
                "dataset_name": "small_BTC",
                "agent_name": "ddqn",
                "trainer_name": "high_frequency_trading",
                "net_name": "ddqn",
                "optimizer_name": "adam",
                "loss_name": "ddqn_loss"
            },
            parameters_template={
                "learning_rate": 0.0005,
                "batch_size": 32,
                "target_update_freq": 1000,
                "double_q": True,
                "dueling": True,
                "priority_replay": True,
                "noise_net": False
            },
            example_values={
                "tick_size": 0.01,
                "latency": 1,  # milliseconds
                "spread_threshold": 0.0001,
                "inventory_limit": 100
            },
            requirements=[
                "需要超低延迟基础设施",
                "需要实时市场数据",
                "适合专业交易员"
            ],
            tags=["DDQN", "高频", "毫秒级", "专业"]
        )
        self._templates[ddqn_hft_template.name] = ddqn_hft_template
    
    def get_template(self, name: str) -> Optional[StrategyTemplate]:
        """获取指定模板
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[StrategyTemplate]: 模板对象或None
        """
        return self._templates.get(name)
    
    def list_templates(
        self,
        strategy_type: Optional[StrategyType] = None,
        category: Optional[TemplateCategory] = None,
        tags: Optional[List[str]] = None
    ) -> List[StrategyTemplate]:
        """列出模板
        
        Args:
            strategy_type: 策略类型过滤
            category: 分类过滤
            tags: 标签过滤
            
        Returns:
            List[StrategyTemplate]: 模板列表
        """
        templates = list(self._templates.values())
        
        # 应用过滤条件
        if strategy_type:
            templates = [t for t in templates if t.strategy_type == strategy_type]
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [
                t for t in templates 
                if any(tag in t.tags for tag in tags)
            ]
        
        return templates
    
    def register_template(self, template: StrategyTemplate) -> bool:
        """注册自定义模板
        
        Args:
            template: 模板对象
            
        Returns:
            bool: 注册是否成功
        """
        try:
            # 验证模板
            errors = self._validate_template(template)
            if errors:
                logger.error(f"模板验证失败: {errors}")
                return False
            
            self._templates[template.name] = template
            logger.info(f"模板注册成功: {template.name}")
            return True
            
        except Exception as e:
            logger.error(f"模板注册失败: {str(e)}")
            return False
    
    def unregister_template(self, name: str) -> bool:
        """注销模板
        
        Args:
            name: 模板名称
            
        Returns:
            bool: 注销是否成功
        """
        if name in self._templates:
            del self._templates[name]
            logger.info(f"模板注销成功: {name}")
            return True
        return False
    
    def _validate_template(self, template: StrategyTemplate) -> List[str]:
        """验证模板
        
        Args:
            template: 模板对象
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查必需字段
        if not template.name:
            errors.append("模板名称不能为空")
        
        if not template.description:
            errors.append("模板描述不能为空")
        
        if not template.config_template:
            errors.append("配置模板不能为空")
        
        # 检查配置模板必需字段
        required_config_fields = ["task_name", "agent_name"]
        for field in required_config_fields:
            if field not in template.config_template:
                errors.append(f"配置模板缺少必需字段: {field}")
        
        return errors


# 全局模板服务实例
_template_service = None

def get_template_service() -> StrategyTemplateService:
    """获取模板服务实例
    
    Returns:
        StrategyTemplateService: 模板服务实例
    """
    global _template_service
    if _template_service is None:
        _template_service = StrategyTemplateService()
    return _template_service


# 导出主要类和函数
__all__ = [
    "TemplateCategory",
    "StrategyTemplate",
    "StrategyTemplateService",
    "get_template_service"
]