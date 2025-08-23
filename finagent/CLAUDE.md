[根目录](../CLAUDE.md) > **finagent**

# FinAgent - 智能金融代理系统

## 模块职责

FinAgent是TradeMaster平台的智能金融代理系统，集成了大语言模型(LLM)、检索增强生成(RAG)等AI技术，为量化交易提供智能决策支持：

- **智能查询**: 自然语言交互的金融数据查询和分析
- **策略推荐**: 基于历史数据和市场分析的交易策略建议
- **风险评估**: 智能风险识别和投资组合优化建议
- **知识库**: 金融领域知识图谱和专家经验库
- **多模态分析**: 支持文本、图表、数值等多种数据类型分析

## 入口与启动

### 基本使用示例
```python
from finagent import FinAgent
from finagent.provider import provider_builder
from finagent.memory import memory_builder

# 创建LLM提供者
provider = provider_builder(
    provider_type="openai",
    config_path="configs/finagent/openai_config.json"
)

# 创建记忆模块
memory = memory_builder(memory_type="faiss")

# 初始化FinAgent
agent = FinAgent(
    llm_provider=provider,
    memory=memory,
    tools=["rapid_apis", "strategy_agents"]
)

# 智能对话
response = agent.chat("请分析一下当前市场的投资机会")
print(response)
```

### 交易环境集成
```python
from finagent.environment import TradingEnvironment
from finagent.tools import strategy_agents

# 创建交易环境
trading_env = TradingEnvironment(
    market_data=market_data,
    portfolio=portfolio
)

# 策略代理分析
strategy_agent = strategy_agents.StrategyAgent()
recommendation = strategy_agent.analyze_market(trading_env)
```

## 对外接口

### 核心组件接口

#### LLM提供者 (`finagent.provider`)
```python
class BaseLLMProvider:
    """大语言模型提供者基类"""
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """生成文本响应"""
        
    def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        
    def estimate_tokens(self, text: str) -> int:
        """估算token数量"""

# 支持的提供者
- OpenAI GPT (GPT-3.5, GPT-4)
- Anthropic Claude
- 本地模型 (LLaMA, ChatGLM等)
```

#### 记忆系统 (`finagent.memory`)
```python
class BaseMemory:
    """记忆系统基类"""
    
    def store(self, content: str, metadata: dict) -> str:
        """存储信息"""
        
    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """检索相关信息"""
        
    def update(self, memory_id: str, content: str) -> bool:
        """更新记忆内容"""

# 支持的记忆类型
- FAISS向量检索
- 基础内存存储
- 分布式内存系统
```

#### 工具系统 (`finagent.tools`)
```python
class BaseTool:
    """工具基类"""
    
    def execute(self, *args, **kwargs) -> dict:
        """执行工具功能"""

# 内置工具
- RapidAPI金融数据接口
- 策略分析代理
- 市场数据获取工具
- 技术指标计算工具
```

### 查询接口 (`finagent.query`)

#### 多样化查询类型
```python
from finagent.query import diverse_query

# 市场分析查询
market_query = diverse_query.MarketAnalysisQuery(
    symbol="AAPL",
    time_range="1M",
    analysis_type="technical"
)

# 投资组合优化查询
portfolio_query = diverse_query.PortfolioOptimizationQuery(
    assets=["AAPL", "GOOGL", "MSFT"],
    risk_tolerance="moderate",
    investment_horizon="long_term"
)

# 风险评估查询
risk_query = diverse_query.RiskAssessmentQuery(
    portfolio=current_portfolio,
    market_conditions=current_market
)
```

### 数据处理接口 (`finagent.data`)

#### 数据集管理
```python
from finagent.data import dataset

# 创建金融数据集
fin_dataset = dataset.FinancialDataset(
    data_sources=["yahoo", "alpha_vantage"],
    symbols=["AAPL", "GOOGL", "TSLA"],
    features=["price", "volume", "technical_indicators"]
)

# 数据预处理
processed_data = fin_dataset.preprocess(
    normalization="z_score",
    feature_engineering=True,
    missing_value_handling="interpolation"
)
```

## 关键依赖与配置

### 核心依赖
```txt
# AI和机器学习
openai>=1.0.0
anthropic>=0.3.0
langchain>=0.0.350
transformers>=4.30.0

# 向量检索和存储
faiss-cpu>=1.7.0
chromadb>=0.4.0
pinecone-client>=2.2.0

# 金融数据
yfinance>=0.2.0
alpha_vantage>=2.3.0
pandas_datareader>=0.10.0

# 数据处理
pandas>=2.0.0
numpy>=1.23.0
scikit-learn>=1.3.0

# API和网络
requests>=2.31.0
httpx>=0.24.0
aiohttp>=3.8.0
```

### 配置文件示例
```json
// configs/finagent/openai_config.json
{
    "provider": "openai",
    "model": "gpt-4-1106-preview",
    "api_key": "${OPENAI_API_KEY}",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 30,
    "retry_attempts": 3,
    "embedding_model": "text-embedding-ada-002"
}
```

### 环境变量配置
```bash
# AI模型API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# 金融数据API Keys  
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
RAPIDAPI_KEY=your_rapidapi_key

# 向量数据库配置
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_pinecone_env

# 代理配置(可选)
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=https://proxy:port
```

## 数据模型

### 智能体对话记录
```python
class ConversationRecord:
    """对话记录模型"""
    conversation_id: str
    user_id: str
    timestamp: datetime
    user_message: str
    agent_response: str
    context: Dict[str, Any]
    tools_used: List[str]
    confidence_score: float
```

### 市场分析结果
```python
class MarketAnalysis:
    """市场分析结果模型"""
    symbol: str
    analysis_type: str  # technical, fundamental, sentiment
    timestamp: datetime
    key_insights: List[str]
    recommendations: List[dict]
    risk_level: str  # low, medium, high
    confidence_score: float
    supporting_data: Dict[str, Any]
```

### 策略推荐模型
```python
class StrategyRecommendation:
    """策略推荐模型"""
    strategy_id: str
    strategy_name: str
    description: str
    target_assets: List[str]
    expected_return: float
    risk_level: str
    time_horizon: str
    entry_conditions: List[str]
    exit_conditions: List[str]
    parameters: Dict[str, Any]
    backtesting_results: Dict[str, Any]
```

## 测试与质量

### 单元测试
```bash
# 运行FinAgent测试
pytest unit_testing/ -k "finagent" -v

# 测试特定组件
pytest -k "test_llm_provider" -v
pytest -k "test_memory_system" -v  
pytest -k "test_tool_execution" -v
```

### 集成测试
```python
# API集成测试
def test_openai_integration():
    provider = provider_builder("openai", config)
    response = provider.generate_response("Analyze AAPL stock")
    assert len(response) > 0

# 端到端测试
def test_end_to_end_analysis():
    agent = FinAgent(config)
    result = agent.analyze_portfolio(sample_portfolio)
    assert "recommendations" in result
```

### 性能指标
- **响应时间**: < 5秒 (简单查询)
- **准确率**: >85% (基于人工评估)
- **可用性**: >99% (API调用成功率)
- **并发支持**: >100 用户同时使用

## 常见问题 (FAQ)

### Q: 如何配置OpenAI API？
A: 在 `configs/finagent/openai_config.json` 中配置API密钥和模型参数，确保环境变量 `OPENAI_API_KEY` 已设置。

### Q: 如何添加自定义工具？
A: 继承 `finagent.tools.BaseTool` 类，实现 `execute()` 方法，然后在工具注册表中注册。

### Q: 记忆系统如何工作？
A: FinAgent使用向量相似性搜索来检索相关历史对话和知识，支持FAISS等向量数据库。

### Q: 如何处理API限流？
A: 内置指数退避重试机制，可在配置中调整重试次数和间隔时间。

### Q: 支持哪些金融数据源？
A: 支持Yahoo Finance、Alpha Vantage、RapidAPI等多种数据源，可通过插件扩展。

### Q: 如何评估回答质量？
A: 使用置信度评分、用户反馈、专家评估等多维度质量评价体系。

## 相关文件清单

### 核心模块文件
- `__init__.py` - 模块初始化
- `registry.py` - 组件注册表

### AI提供者模块
- `provider/` - LLM提供者实现
  - `base_llm.py` - LLM基类定义
  - `base_embedding.py` - 嵌入模型基类
  - `provider.py` - 提供者工厂类

### 记忆系统模块
- `memory/` - 记忆系统实现
  - `base.py` - 记忆系统基类
  - `basic_memory.py` - 基础记忆实现
  - `faiss.py` - FAISS向量检索实现
  - `interface.py` - 记忆接口定义

### 工具系统模块
- `tools/` - 工具集合
  - `rapid_apis.py` - RapidAPI金融工具
  - `strategy_agents.py` - 策略分析代理

### 查询处理模块
- `query/` - 查询处理
  - `diverse_query.py` - 多样化查询类型
  - `query_types.py` - 查询类型定义

### 数据处理模块
- `data/` - 数据管理
  - `base.py` - 数据基类
  - `dataset.py` - 数据集管理

### 环境集成模块
- `environment/` - 交易环境
  - `trading.py` - 交易环境实现

### 其他组件模块
- `processor/` - 数据处理器
- `trajectory/` - 轨迹优化
- `plots/` - 可视化图表
- `metrics/` - 评估指标
- `utils/` - 工具函数

### 配置文件
- `configs/finagent/openai_config.json` - OpenAI配置

## 变更记录 (Changelog)

### 2025-08-22 21:16:30 - 初始模块文档
- 创建FinAgent模块文档
- 建立智能代理架构和接口规范
- 配置AI集成和数据处理指南

---

**模块维护者**: TradeMaster AI Team  
**最后更新**: 2025-08-22 21:16:30  
**文档版本**: v1.0.0