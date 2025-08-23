[根目录](../CLAUDE.md) > **trademaster**

# TradeMaster Core - 量化交易核心引擎

## 模块职责

TradeMaster Core是整个平台的核心算法引擎，提供量化交易所需的各类算法、环境、数据集、神经网络和训练器等核心组件：

- **智能体框架**: 多种强化学习和深度学习交易智能体
- **交易环境**: 模拟真实交易环境，支持多种交易任务
- **数据处理**: 金融数据预处理、特征工程和数据集管理
- **神经网络**: 各类交易策略神经网络架构
- **训练框架**: 模型训练、评估和优化框架

## 入口与启动

### 主要入口点
```python
# 从builder模块创建组件
from trademaster.agents import agents_builder
from trademaster.environments import environments_builder
from trademaster.datasets import datasets_builder
from trademaster.nets import nets_builder
from trademaster.trainers import trainers_builder

# 创建交易智能体
agent = agents_builder(task="portfolio_management", type="ppo")

# 创建交易环境
env = environments_builder(task="portfolio_management", dataset="dj30")

# 创建数据集
dataset = datasets_builder(dataset="dj30")
```

### 典型使用流程
```python
# 1. 构建数据集
dataset = datasets_builder(dataset="dj30")
train_data, test_data = dataset.split_data()

# 2. 构建环境
env = environments_builder(task="portfolio_management", dataset=train_data)

# 3. 构建智能体
agent = agents_builder(task="portfolio_management", type="ppo")

# 4. 构建训练器
trainer = trainers_builder(task="portfolio_management")

# 5. 开始训练
trainer.train(agent, env)

# 6. 模型评估
evaluator = evaluation_builder()
results = evaluator.evaluate(agent, env)
```

## 对外接口

### 智能体接口 (`trademaster.agents`)

#### 支持的智能体类型
- **PPO**: Proximal Policy Optimization
- **DDPG**: Deep Deterministic Policy Gradient  
- **SAC**: Soft Actor-Critic
- **A2C**: Advantage Actor-Critic
- **DQN**: Deep Q-Network
- **SARL**: State-Augmented Reinforcement Learning
- **EIIE**: Ensemble of Identical Independent Evaluators
- **DeepTrader**: Deep Learning Trading Agent

#### 智能体构建接口
```python
def agents_builder(task: str, type: str, **kwargs):
    """
    构建交易智能体
    
    Args:
        task: 交易任务类型 (portfolio_management, high_frequency_trading, etc.)
        type: 智能体类型 (ppo, ddpg, sac, etc.)
        **kwargs: 其他配置参数
    
    Returns:
        Agent: 配置好的智能体实例
    """
```

### 环境接口 (`trademaster.environments`)

#### 支持的交易任务
- **portfolio_management**: 投资组合管理
- **high_frequency_trading**: 高频交易
- **algorithmic_trading**: 算法交易
- **order_execution**: 订单执行优化
- **market_dynamics_modeling**: 市场动力学建模

#### 环境构建接口  
```python
def environments_builder(task: str, dataset: str, **kwargs):
    """
    构建交易环境
    
    Args:
        task: 交易任务类型
        dataset: 数据集名称或数据
        **kwargs: 环境配置参数
    
    Returns:
        Environment: 交易环境实例
    """
```

### 数据集接口 (`trademaster.datasets`)

#### 支持的数据集
- **DJ30**: 道琼斯30指数成分股
- **AAPL**: 苹果公司股票数据
- **BTC**: 比特币价格数据
- **FX**: 外汇数据
- **HFT_BTC**: 高频交易比特币数据
- **OE_BTC**: 订单执行比特币数据
- **PD_BTC**: 价格发现比特币数据

#### 数据集构建接口
```python
def datasets_builder(dataset: str, **kwargs):
    """
    构建数据集
    
    Args:
        dataset: 数据集名称
        **kwargs: 数据集配置参数
    
    Returns:
        Dataset: 数据集实例
    """
```

## 关键依赖与配置

### 核心依赖
```txt
# 机器学习框架
tensorflow==2.11.0
torch>=1.9.0
numpy==1.23.5

# 数据处理
pandas==2.0.3
scipy==1.9.3
scikit-learn==1.3.2

# 强化学习
gym==0.26.2
gymnasium==0.29.1
ray[rllib]==1.13.0

# 金融数据
yfinance==0.2.28
tslearn==0.6.3

# 可视化
matplotlib==3.7.5
plotly==5.17.0
```

### 配置文件结构
```python
# 典型配置文件 (configs/portfolio_management/portfolio_management_dj30_ppo_ppo_adam_mse.py)
{
    "task": "portfolio_management",
    "dataset": "dj30", 
    "agent": "ppo",
    "net": "ppo",
    "optimizer": "adam",
    "loss": "mse",
    "work_dir": "./work_dir",
    "seeds": [12345, 23451, 34512, 45123, 51234],
    "device": "cpu"
}
```

## 数据模型

### 交易环境状态空间
```python
class TradingState:
    """交易状态定义"""
    price: np.ndarray          # 价格数据
    technical_indicators: np.ndarray  # 技术指标
    portfolio_weights: np.ndarray     # 投资组合权重
    cash: float                # 现金余额
    positions: np.ndarray      # 持仓信息
    timestamp: datetime        # 时间戳
```

### 动作空间定义
```python
class TradingAction:
    """交易动作定义"""
    # 投资组合管理: 资产权重分配
    weights: np.ndarray        # 形状: (n_assets,)
    
    # 高频交易: 买/卖/持有决策  
    decisions: np.ndarray      # 形状: (n_assets, 3)
    
    # 订单执行: 下单数量和时机
    orders: List[Order]
```

### 奖励函数设计
```python
def calculate_reward(prev_portfolio_value: float, 
                    curr_portfolio_value: float,
                    transaction_cost: float,
                    risk_penalty: float) -> float:
    """
    计算交易奖励
    
    Args:
        prev_portfolio_value: 上一时刻组合价值
        curr_portfolio_value: 当前时刻组合价值  
        transaction_cost: 交易成本
        risk_penalty: 风险惩罚
    
    Returns:
        reward: 标准化奖励值
    """
    return (curr_portfolio_value - prev_portfolio_value) - transaction_cost - risk_penalty
```

## 测试与质量

### 单元测试
```bash
# 运行核心模块测试
pytest unit_testing/test_core.py -v

# 测试特定组件
pytest unit_testing/ -k "test_agents" -v
pytest unit_testing/ -k "test_environments" -v
pytest unit_testing/ -k "test_datasets" -v
```

### 性能测试
```python
# 基准测试脚本示例
from trademaster.utils import benchmark

# 测试智能体性能
agent_performance = benchmark.test_agent_performance(agent, env)

# 测试环境执行效率  
env_efficiency = benchmark.test_environment_efficiency(env)

# 测试数据加载速度
data_loading_speed = benchmark.test_dataset_loading(dataset)
```

### 代码质量
- **类型注解**: 所有公共接口都有完整类型注解
- **文档字符串**: 遵循Google Python风格指南
- **单元测试覆盖率**: >85%
- **集成测试**: 各模块间集成测试

## 常见问题 (FAQ)

### Q: 如何添加自定义交易智能体？
A: 继承 `trademaster.agents.base.BaseAgent`，实现 `act()` 和 `learn()` 方法，然后在 `agents_builder` 中注册。

### Q: 如何使用自定义数据集？
A: 继承 `trademaster.datasets.base.BaseDataset`，实现数据加载和预处理逻辑，在 `datasets_builder` 中注册。

### Q: 训练过程中出现梯度爆炸怎么办？
A: 调整学习率、使用梯度裁剪、检查奖励函数的缩放，或尝试不同的网络架构。

### Q: 如何并行训练多个智能体？
A: 使用 Ray 分布式训练框架，或者多进程方式训练多个种子的实验。

### Q: 环境重置后状态异常怎么办？
A: 检查数据集的时间索引、确保环境初始化参数正确、验证状态空间维度匹配。

### Q: 如何评估策略的风险指标？
A: 使用 `trademaster.evaluation` 模块，计算夏普比率、最大回撤、VaR等风险指标。

## 相关文件清单

### 核心模块文件
- `__init__.py` - 模块初始化和导出
- `agents/` - 交易智能体实现目录
  - `builder.py` - 智能体构建工厂
  - `custom.py` - 自定义智能体实现
- `environments/` - 交易环境实现目录
  - `builder.py` - 环境构建工厂
  - `custom.py` - 自定义环境实现
- `datasets/` - 数据集管理目录
  - `builder.py` - 数据集构建工厂
  - `custom.py` - 自定义数据集实现
- `nets/` - 神经网络架构目录
  - `eiie.py` - EIIE网络架构
  - `deeptrader.py` - DeepTrader网络
  - `dqn.py` - DQN网络架构
  - `sarl.py` - SARL网络架构
- `trainers/` - 训练器实现目录
  - `builder.py` - 训练器构建工厂
  - `custom.py` - 自定义训练器
- `utils/` - 工具函数目录
  - `utils.py` - 通用工具函数
  - `replay_buffer.py` - 经验回放缓冲区
  - `labeling_util.py` - 数据标注工具

### 算法实现文件
- `nets/ASU.py` - ASU网络架构
- `nets/MSU.py` - MSU网络架构  
- `nets/eteo.py` - ETEO算法实现
- `nets/pd.py` - 价格发现算法
- `nets/investor_imitator.py` - 投资者模仿算法
- `nets/high_frequency_trading_dqn.py` - 高频交易DQN

### 配置和工具文件
- `losses/` - 损失函数实现目录
- `optimizers/` - 优化器实现目录  
- `preprocessor/` - 数据预处理目录
- `transition/` - 状态转移实现目录
- `imputation/` - 数据插值实现目录
- `evaluation/` - 评估框架目录

## 变更记录 (Changelog)

### 2025-08-22 21:16:30 - 初始模块文档
- 创建TradeMaster Core模块文档
- 建立算法架构和接口规范
- 配置开发和测试环境指南

---

**模块维护者**: TradeMaster Core Team  
**最后更新**: 2025-08-22 21:16:30  
**文档版本**: v1.0.0