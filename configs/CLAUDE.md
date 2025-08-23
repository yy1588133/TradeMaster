[根目录](../CLAUDE.md) > **configs**

# Configs - 策略配置管理中心

## 模块职责

Configs模块是TradeMaster平台的配置管理中心，包含各类交易任务的策略配置文件和参数模板：

- **交易策略配置**: 各种交易算法的参数配置和超参数模板
- **数据集配置**: 不同金融数据集的预处理和特征工程配置  
- **模型配置**: 神经网络架构和训练参数配置
- **环境配置**: 交易环境设置和仿真参数配置
- **实验配置**: 实验设计和评估指标配置

## 入口与启动

### 配置文件使用示例
```python
# 加载投资组合管理PPO策略配置
import importlib.util

config_path = "configs/portfolio_management/portfolio_management_dj30_ppo_ppo_adam_mse.py"
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

# 使用配置创建组件
from trademaster import agents_builder, environments_builder

agent = agents_builder(config.config)
env = environments_builder(config.config)
```

### 配置文件命名规则
```
{task}_{dataset}_{agent}_{net}_{optimizer}_{loss}.py

示例:
- portfolio_management_dj30_ppo_ppo_adam_mse.py
- high_frequency_trading_BTC_dqn_dqn_adam_mse.py
- algorithmic_trading_BTC_deepscalper_deepscalper_adam_mse.py
```

## 对外接口

### 配置文件结构

#### 标准配置模板
```python
# 示例: portfolio_management配置
config = {
    # 基础配置
    "task": "portfolio_management",
    "dataset": "dj30",
    "agent": "ppo",
    "net": "ppo", 
    "optimizer": "adam",
    "loss": "mse",
    
    # 工作目录和设备
    "work_dir": "./work_dir/portfolio_management_dj30_ppo",
    "device": "cpu",  # or "cuda"
    
    # 实验配置
    "seeds": [12345, 23451, 34512, 45123, 51234],
    "num_threads": 8,
    
    # 数据配置
    "data": {
        "data_path": "data/dj30",
        "train_ratio": 0.8,
        "validation_ratio": 0.1,
        "test_ratio": 0.1,
        "tech_indicator_list": [
            "zopen", "zhigh", "zlow", "zadjcp", "zclose", "zd_5", 
            "zd_10", "zd_15", "zd_20", "zd_25", "zd_30"
        ],
        "initial_amount": 1000000,
        "transaction_cost_pct": 0.001
    },
    
    # 智能体配置
    "agent": {
        "lr": 3e-4,
        "batch_size": 32,
        "gamma": 0.99,
        "eps_clip": 0.2,
        "k_epochs": 4,
        "entropy_coef": 0.01
    },
    
    # 网络架构配置
    "net": {
        "hidden_dim": 128,
        "num_layers": 3,
        "activation": "relu",
        "dropout_rate": 0.1
    },
    
    # 训练配置
    "trainer": {
        "max_training_epoch": 10,
        "episodes_per_epoch": 100,
        "update_frequency": 100,
        "save_frequency": 5
    },
    
    # 评估配置
    "evaluator": {
        "eval_frequency": 5,
        "eval_episodes": 50,
        "eval_env_config": {
            "mode": "test"
        }
    }
}
```

### 任务分类配置

#### 投资组合管理 (`portfolio_management/`)
支持的策略配置：
- **PPO**: `portfolio_management_dj30_ppo_ppo_adam_mse.py`
- **EIIE**: `portfolio_management_dj30_eiie_eiie_adam_mse.py`  
- **DeepTrader**: `portfolio_management_dj30_deeptrader_deeptrader_adam_mse.py`
- **SARL**: `portfolio_management_dj30_sarl_sarl_adam_mse.py`
- **Investor Imitator**: `portfolio_management_dj30_investor_imitator_investor_imitator_adam_mse.py`

#### 高频交易 (`high_frequency_trading/`)
- **DQN**: `high_frequency_trading_BTC_dqn_dqn_adam_mse.py`

#### 算法交易 (`algorithmic_trading/`)
- **DeepScalper BTC**: `algorithmic_trading_BTC_deepscalper_deepscalper_adam_mse.py`
- **DeepScalper FX**: `algorithmic_trading_FX_deepscalper_deepscalper_adam_mse.py`

#### 订单执行优化 (`order_execution/`)
- **ETEO**: `order_execution_BTC_eteo_eteo_adam_mse.py`
- **PD**: `order_execution_PD_BTC_pd_pd_adam_mse.py`

#### 市场动态建模 (`market_dynamics_modeling/`)
支持数据集：
- **AAPL**: `AAPL.py`
- **BTC**: `BTC.py`  
- **DJI**: `DJI.py`
- **FX**: `FX.py`
- **HFT_BTC**: `HFT_BTC.py`
- **OE_BTC**: `OE_BTC.py`
- **PD_BTC**: `PD_BTC.py`

#### EarnMore集成 (`earnmore/`)
强化学习策略配置：
- **DDPG**: `ddpg_portfolio_management.py`
- **DQN**: `dqn_portfolio_management.py`
- **PPO**: `ppo_portfolio_management.py`
- **SAC**: `sac_portfolio_management.py`
- **TD3**: `td3_portfolio_management.py`
- **Masked版本**: 支持masked_ddqn, masked_sac, masked_dqn等

## 关键依赖与配置

### 配置文件依赖
```python
# 配置文件通常依赖以下模块
import os
import sys
from pathlib import Path

# TradeMaster核心组件
from trademaster.utils import get_attr
from trademaster.nets import net_builder
from trademaster.optimizers import optimizer_builder
from trademaster.losses import loss_builder
```

### 配置验证工具
```python
def validate_config(config: dict) -> bool:
    """
    验证配置文件完整性和有效性
    
    Args:
        config: 配置字典
        
    Returns:
        bool: 配置是否有效
    """
    required_keys = ["task", "dataset", "agent", "net", "optimizer", "loss"]
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    return True

def merge_configs(base_config: dict, override_config: dict) -> dict:
    """
    合并配置文件，支持覆盖和扩展
    
    Args:
        base_config: 基础配置
        override_config: 覆盖配置
        
    Returns:
        dict: 合并后的配置
    """
    merged = base_config.copy()
    merged.update(override_config)
    return merged
```

### 环境变量配置
```bash
# 数据路径配置
TRADEMASTER_DATA_PATH=/path/to/data
TRADEMASTER_WORK_DIR=/path/to/work_dir

# GPU设备配置
CUDA_VISIBLE_DEVICES=0,1
TRADEMASTER_DEVICE=cuda

# 实验配置
TRADEMASTER_SEEDS=12345,23451,34512
TRADEMASTER_NUM_THREADS=8
```

## 数据模型

### 配置数据结构
```python
from typing import Dict, List, Union, Any
from dataclasses import dataclass

@dataclass
class DataConfig:
    """数据配置"""
    data_path: str
    train_ratio: float
    validation_ratio: float  
    test_ratio: float
    tech_indicator_list: List[str]
    initial_amount: float
    transaction_cost_pct: float

@dataclass  
class AgentConfig:
    """智能体配置"""
    lr: float
    batch_size: int
    gamma: float
    eps_clip: float
    k_epochs: int
    entropy_coef: float

@dataclass
class NetConfig:
    """网络配置"""
    hidden_dim: int
    num_layers: int
    activation: str
    dropout_rate: float

@dataclass
class ExperimentConfig:
    """实验配置"""
    task: str
    dataset: str
    agent: str
    net: str
    optimizer: str
    loss: str
    work_dir: str
    device: str
    seeds: List[int]
    data: DataConfig
    agent_config: AgentConfig
    net_config: NetConfig
```

### 配置继承和模板
```python
# 基础配置模板
BASE_CONFIG = {
    "device": "cpu",
    "num_threads": 8,
    "seeds": [12345, 23451, 34512, 45123, 51234],
    "work_dir": "./work_dir",
}

# 任务特定模板
PORTFOLIO_MANAGEMENT_BASE = {
    **BASE_CONFIG,
    "task": "portfolio_management",
    "data": {
        "initial_amount": 1000000,
        "transaction_cost_pct": 0.001
    }
}

HIGH_FREQUENCY_TRADING_BASE = {
    **BASE_CONFIG,
    "task": "high_frequency_trading",
    "data": {
        "lookback_window": 100,
        "trade_frequency": "1min"
    }
}
```

## 测试与质量

### 配置文件验证
```bash
# 验证所有配置文件语法
python scripts/validate_configs.py

# 测试特定配置文件
python -c "import configs.portfolio_management.portfolio_management_dj30_ppo_ppo_adam_mse as cfg; print('Config loaded successfully')"
```

### 自动化测试
```python
# 配置文件集成测试
def test_all_configs():
    """测试所有配置文件能否正确加载"""
    config_dirs = [
        "portfolio_management",
        "high_frequency_trading", 
        "algorithmic_trading",
        "order_execution",
        "market_dynamics_modeling"
    ]
    
    for config_dir in config_dirs:
        config_path = f"configs/{config_dir}"
        for config_file in os.listdir(config_path):
            if config_file.endswith(".py"):
                # 测试配置文件加载
                assert load_config(f"{config_path}/{config_file}")
```

## 常见问题 (FAQ)

### Q: 如何创建新的策略配置？
A: 复制相似的配置文件，按照命名规则重命名，修改相应的参数和路径。

### Q: 配置文件中的路径如何设置？
A: 使用相对路径，基于项目根目录。可通过环境变量 `TRADEMASTER_DATA_PATH` 覆盖默认路径。

### Q: 如何调整超参数？
A: 修改配置文件中 `agent` 和 `net` 部分的参数，如学习率、批大小、隐藏层维度等。

### Q: 多GPU训练如何配置？
A: 设置 `device: "cuda"`，通过 `CUDA_VISIBLE_DEVICES` 环境变量指定GPU设备。

### Q: 如何添加新的技术指标？
A: 在配置文件的 `tech_indicator_list` 中添加新指标名称，确保数据处理代码支持该指标。

### Q: 实验种子如何设置？
A: 修改配置文件中的 `seeds` 列表，建议使用5个不同的种子进行多次实验。

## 相关文件清单

### 基础配置文件
- `_base_/__init__.py` - 基础配置模块初始化
- `__init__.py` - 配置模块初始化

### 投资组合管理配置
- `portfolio_management/portfolio_management_dj30_ppo_ppo_adam_mse.py` - PPO策略配置
- `portfolio_management/portfolio_management_dj30_eiie_eiie_adam_mse.py` - EIIE策略配置  
- `portfolio_management/portfolio_management_dj30_deeptrader_deeptrader_adam_mse.py` - DeepTrader配置
- `portfolio_management/portfolio_management_dj30_sarl_sarl_adam_mse.py` - SARL配置
- `portfolio_management/portfolio_management_dj30_investor_imitator_investor_imitator_adam_mse.py` - 投资者模仿策略
- `portfolio_management/portfolio_management_exchange_*.py` - 交易所数据配置系列

### 高频交易配置
- `high_frequency_trading/high_frequency_trading_BTC_dqn_dqn_adam_mse.py` - 比特币高频交易DQN配置

### 算法交易配置  
- `algorithmic_trading/algorithmic_trading_BTC_deepscalper_deepscalper_adam_mse.py` - 比特币DeepScalper配置
- `algorithmic_trading/algorithmic_trading_FX_deepscalper_deepscalper_adam_mse.py` - 外汇DeepScalper配置

### 订单执行优化配置
- `order_execution/order_execution_BTC_eteo_eteo_adam_mse.py` - ETEO策略配置
- `order_execution/order_execution_PD_BTC_pd_pd_adam_mse.py` - 价格发现策略配置

### 市场动态建模配置
- `market_dynamics_modeling/AAPL.py` - 苹果股票建模配置
- `market_dynamics_modeling/BTC.py` - 比特币建模配置
- `market_dynamics_modeling/DJI.py` - 道琼斯指数建模配置
- `market_dynamics_modeling/FX.py` - 外汇建模配置
- `market_dynamics_modeling/HFT_BTC.py` - 高频交易比特币配置
- `market_dynamics_modeling/OE_BTC.py` - 订单执行比特币配置
- `market_dynamics_modeling/PD_BTC.py` - 价格发现比特币配置

### EarnMore集成配置
- `earnmore/ddpg_portfolio_management.py` - DDPG投资组合管理
- `earnmore/dqn_portfolio_management.py` - DQN投资组合管理
- `earnmore/ppo_portfolio_management.py` - PPO投资组合管理
- `earnmore/sac_portfolio_management.py` - SAC投资组合管理
- `earnmore/td3_portfolio_management.py` - TD3投资组合管理
- `earnmore/mask_*.py` - 各种Masked版本策略配置

### FinAgent配置
- `finagent/openai_config.json` - OpenAI API配置

## 变更记录 (Changelog)

### 2025-08-22 21:16:30 - 初始模块文档
- 创建Configs模块文档
- 建立配置文件结构和使用规范
- 建立配置验证和测试机制

---

**模块维护者**: TradeMaster Config Team  
**最后更新**: 2025-08-22 21:16:30  
**文档版本**: v1.0.0