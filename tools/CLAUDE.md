[根目录](../CLAUDE.md) > **tools**

# Tools - 工具集模块

## 变更记录 (Changelog)

### 2025-08-22 - 初始化工具集文档
- 创建工具集模块详细文档
- 分析所有工具脚本功能和用途
- 建立工具分类和依赖关系

## 模块职责

Tools模块是TradeMaster项目的工具集合，提供各种量化交易场景下的实用工具和脚本，包括：

- **算法交易工具**: 深度学习交易策略训练和测试
- **数据预处理器**: 金融数据获取和预处理管道
- **智能投资顾问**: EarnMore和FinAgent智能代理系统
- **投资组合管理**: 多种投资组合优化策略工具
- **高频交易**: 高频交易策略实现
- **市场动态标注**: 市场趋势和动态识别工具
- **缺失值填补**: 数据质量改善工具
- **订单执行**: 智能订单执行策略

## 入口与启动

### 核心入口文件
- `__init__.py` - 模块初始化文件（当前为空）

### 主要启动脚本
- `algorithmic_trading/train.py` - 算法交易策略训练主脚本
- `algorithmic_trading/auto_train.py` - 自动调参训练脚本
- `finagent/main.py` - FinAgent智能金融代理主程序
- `earnmore/train.py` - EarnMore强化学习投资组合管理训练
- `portfolio_management/train.py` - 投资组合管理策略训练

## 对外接口

### 1. 算法交易模块 (`algorithmic_trading/`)
```python
# 标准训练接口
python tools/algorithmic_trading/train.py \
    --config configs/algorithmic_trading/xxx.py \
    --task_name train \
    --test_dynamic -1

# 自动调参接口  
python tools/algorithmic_trading/auto_train.py \
    --config configs/algorithmic_trading/xxx.py \
    --auto_tuning True \
    --n_trials 10
```

### 2. 数据预处理模块 (`data_preprocessor/`)
```python
# Yahoo Finance数据下载
python tools/data_preprocessor/yahoofinance/dj30.py
python tools/data_preprocessor/yahoofinance/sp500.py  
python tools/data_preprocessor/yahoofinance/sse50.py
```

### 3. EarnMore智能投资模块 (`earnmore/`)
```python
# 生成训练脚本
python tools/earnmore/make_scripts.py --config configs/xxx.py

# 生成执行管道
python tools/earnmore/make_pipeline.py

# 强化学习训练
python tools/earnmore/train.py --config configs/xxx.py
```

### 4. FinAgent智能代理模块 (`finagent/`)
```python
# 数据收集
python tools/finagent/download_prices.py
python tools/finagent/download_news.py
python tools/finagent/download_sentiment.py

# 数据处理
python tools/finagent/data_process.py

# 智能代理运行
python tools/finagent/main.py --config configs/finagent/xxx.py
```

### 5. 投资组合管理模块 (`portfolio_management/`)
```python
# 基础投资组合管理
python tools/portfolio_management/train.py

# 特定策略训练
python tools/portfolio_management/train_deeptrader.py
python tools/portfolio_management/train_eiie.py
python tools/portfolio_management/train_sarl.py
```

## 关键依赖与配置

### EarnMore依赖
```bash
conda install pytorch==1.13.0 torchvision==0.14.0 torchaudio==0.13.0 pytorch-cuda=11.7 -c pytorch -c nvidia
git clone https://github.com/microsoft/qlib.git && cd qlib
python setup.py install
pip install -r tools/earnmore/requirements.txt
```

**主要依赖**:
- scipy==1.8.0
- einops==0.3.0
- timm==0.9.2
- mmengine==0.7.2
- pandas==1.2.4
- gym==0.21.0
- scikit-learn==1.2.1

### FinAgent依赖
```bash
conda create -n finagent python=3.10
conda activate finagent
apt-get update && apt-get install -y libmagic-dev
conda install -c pytorch faiss-cpu=1.7.4 mkl=2021 blas=1.0=mkl
pip install -r tools/finagent/requirements.txt
playwright install
```

**主要依赖**:
- mmengine
- langchain & openai
- finnhub-python & yfinance
- polygon-api-client
- pandas_ta
- unstructured
- playwright

**环境变量配置**:
```bash
OA_OPENAI_KEY = "your_openai_key"
OA_FMP_KEY = "your_fmp_key"
OA_POLYGON_KEY = "your_polygon_key"
ALPHA_VANTAGE_KEY = "your_alpha_vantage_key"
```

### 通用依赖
- **PyTorch**: 深度学习框架
- **mmcv/mmengine**: 配置管理和构建系统
- **optuna**: 自动超参数优化
- **numpy & pandas**: 数据处理
- **gym**: 强化学习环境

## 数据模型

### 1. 交易环境状态
```python
# 状态空间维度
state_dim = environment.state_dim
action_dim = environment.action_dim

# 状态包含：价格序列、技术指标、市场特征
state_shape = (batch_size, num_stocks, time_steps, num_features)
```

### 2. 训练配置
```python
# 训练参数
cfg = {
    'num_episodes': 2000,
    'batch_size': 128,  
    'buffer_size': 10000,
    'horizon_len': 128,
    'learning_rate': 1e-5,
    'seed': 42
}
```

### 3. FinAgent数据结构
```python
# 交易记录
trading_records = {
    "symbol": [], "day": [], "value": [], "cash": [],
    "position": [], "ret": [], "date": [], "price": [],
    "action": [], "reasoning": []
}
```

## 测试与质量

### 1. 算法交易测试
```python
# 动态测试模式
python tools/algorithmic_trading/train.py \
    --task_name dynamics_test \
    --test_dynamic 0

# 策略对比测试（包含Blind_Bid和Do_Nothing基准）
```

### 2. 自动化测试流程
```bash
# EarnMore管道测试
sh tools/earnmore/pipeline_mask_sac_dj30_example.sh

# 生成批量测试脚本
python tools/earnmore/make_pipeline.py
```

### 3. 性能评估指标
- **算法交易**: 日收益率、胜率、夏普比率、最大回撤
- **投资组合**: ARR%（年化收益率）、波动率、风险调整收益
- **FinAgent**: 决策准确性、交易执行效率

## 常见问题 (FAQ)

### Q1: 如何选择合适的交易策略配置？
**A**: 根据交易场景选择：
- **高频交易**: 使用`high_frequency_trading/train.py`，关注延迟和执行效率
- **算法交易**: 使用`algorithmic_trading/train.py`，支持多种深度强化学习策略
- **投资组合**: 使用`portfolio_management/`下的特定策略脚本

### Q2: EarnMore和FinAgent的区别？
**A**: 
- **EarnMore**: 专注于强化学习的投资组合管理，使用掩码注意力机制
- **FinAgent**: 集成LLM的智能金融代理，支持多模态数据和自然语言决策

### Q3: 如何处理训练过程中的数据缺失？
**A**: 使用`missing_value_imputation/run.py`进行缺失值填补，支持多种插值方法

### Q4: 自动调参如何配置？
**A**: 
```python
# 在auto_train.py中配置Optuna参数
def sample_params(trial):
    lr = trial.suggest_float("lr", 1e-4, 1e-3, log=True)
    explore_rate = trial.suggest_float("explore_rate", 0.15, 0.3)
    return dict(lr=lr, explore_rate=explore_rate)
```

### Q5: 如何扩展自定义策略？
**A**: 
1. 继承对应的基础类（Agent、Environment、Dataset）
2. 在configs/目录下创建配置文件
3. 使用builder模式注册新组件
4. 在tools/对应目录下创建训练脚本

## 相关文件清单

### 核心训练脚本
```
tools/
├── algorithmic_trading/
│   ├── train.py                 # 标准算法交易训练
│   └── auto_train.py           # 自动调参训练
├── earnmore/
│   ├── train.py                # 强化学习投资组合训练
│   ├── make_scripts.py         # 批量脚本生成
│   ├── make_pipeline.py        # 管道脚本生成
│   └── preprocess.py           # 数据预处理
├── finagent/
│   ├── main.py                 # 智能代理主程序
│   ├── data_process.py         # 数据处理管道
│   ├── download_*.py           # 各类数据下载器
│   └── get_stock_infos.py      # 股票信息获取
└── portfolio_management/
    ├── train.py                # 基础投资组合训练
    ├── train_deeptrader.py     # DeepTrader策略
    ├── train_eiie.py          # EIIE策略
    ├── train_sarl.py          # SARL策略
    └── train_investor_imitator.py # 投资者模仿策略
```

### 数据处理工具
```
tools/
├── data_preprocessor/yahoofinance/
│   ├── dj30.py                 # 道琼斯30指数数据
│   ├── sp500.py               # 标普500指数数据
│   └── sse50.py               # 上证50指数数据
├── market_dynamics_labeling/
│   ├── run.py                 # 市场动态标注
│   └── run_PM.py              # 投资组合市场动态
├── missing_value_imputation/
│   └── run.py                 # 缺失值填补
└── order_execution/
    ├── train_eteo.py          # ETEO订单执行
    └── train_pd.py            # PD订单执行
```

### 配置与依赖文件
```
tools/
├── earnmore/
│   ├── requirements.txt        # EarnMore依赖
│   ├── README.md              # EarnMore说明
│   └── pipeline_*.sh          # 示例执行脚本
├── finagent/
│   ├── requirements.txt        # FinAgent依赖  
│   └── README.md              # FinAgent说明
└── __init__.py                # 模块初始化
```

## 与其他模块的集成点

### 1. 与TradeMaster核心的集成
```python
# 使用核心构建器
from trademaster.agents.builder import build_agent
from trademaster.environments.builder import build_environment
from trademaster.datasets.builder import build_dataset
from trademaster.nets.builder import build_net
from trademaster.trainers.builder import build_trainer
```

### 2. 与配置系统的集成
```python  
# 配置文件位置
configs/algorithmic_trading/
configs/portfolio_management/ 
configs/finagent/
configs/earnmore/
```

### 3. 与数据流的集成
- **输入**: `data/` 目录下的各种金融数据集
- **输出**: 训练好的模型权重、性能指标、可视化图表
- **日志**: 实验结果和训练日志记录

### 4. 与Web界面的集成
- 训练任务可通过Web界面提交和监控
- 结果可视化集成到Web dashboard
- 模型部署和推理服务集成

---

**最后更新**: 2025-08-22  
**文档版本**: v1.0.0  
**维护状态**: ✅ 活跃开发