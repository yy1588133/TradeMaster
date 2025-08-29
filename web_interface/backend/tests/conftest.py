"""
测试配置文件

包含所有测试运行的全局配置、装夹器（fixtures）和工具函数。
设置测试环境、模拟数据和通用测试辅助功能。
"""

import asyncio
import pytest
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Generator
from unittest.mock import Mock, AsyncMock, patch

# 设置测试环境变量
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"  # 使用异步SQLite
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-secure"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_url():
    """测试数据库URL"""
    return "sqlite:///./test.db"


@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False,
        "max_concurrent_sessions": 3,
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_strategy():
    """示例策略数据"""
    return {
        "id": 1,
        "name": "测试策略",
        "description": "这是一个用于测试的策略",
        "strategy_type": "algorithmic_trading",
        "status": "active",
        "owner_id": 1,
        "config": {
            "agent_type": "dqn",
            "dataset_name": "BTC",
            "epochs": 100,
            "learning_rate": 0.001,
            "batch_size": 32
        },
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_training_session():
    """示例训练会话数据"""
    return {
        "id": 1,
        "strategy_id": 1,
        "user_id": 1,
        "session_type": "training",
        "status": "pending",
        "progress": 0.0,
        "current_epoch": 0,
        "total_epochs": 100,
        "trademaster_config": {
            "task": "algorithmic_trading",
            "dataset": {"type": "BTC"},
            "agent": {"type": "dqn", "lr": 0.001},
            "trainer": {"epochs": 100}
        },
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_performance_metrics():
    """示例性能指标数据"""
    return [
        {
            "id": 1,
            "session_id": 1,
            "metric_name": "loss",
            "metric_value": 0.5,
            "epoch": 1,
            "step": 100,
            "recorded_at": "2024-01-01T01:00:00Z"
        },
        {
            "id": 2,
            "session_id": 1,
            "metric_name": "reward",
            "metric_value": 10.5,
            "epoch": 1,
            "step": 100,
            "recorded_at": "2024-01-01T01:00:00Z"
        },
        {
            "id": 3,
            "session_id": 1,
            "metric_name": "loss",
            "metric_value": 0.4,
            "epoch": 2,
            "step": 200,
            "recorded_at": "2024-01-01T01:01:00Z"
        }
    ]


@pytest.fixture
def mock_trademaster_config():
    """模拟TradeMaster配置"""
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


@pytest.fixture
def mock_websocket_message():
    """模拟WebSocket消息"""
    return {
        "type": "session_metrics_update",
        "data": {
            "session_id": 1,
            "metrics": {
                "loss": 0.25,
                "reward": 15.5,
                "accuracy": 0.85
            },
            "epoch": 50,
            "progress": 50.0
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }


@pytest.fixture
def temp_config_file():
    """临时配置文件"""
    config_content = """
    task: algorithmic_trading
    dataset:
      type: BTC
      train_start_date: "2020-01-01"
    agent:
      type: dqn
      lr: 0.001
    trainer:
      epochs: 100
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    yield temp_path
    
    # 清理
    os.unlink(temp_path)


@pytest.fixture
def mock_celery_task():
    """模拟Celery任务"""
    task = Mock()
    task.id = "test-task-123"
    task.status = "PENDING"
    task.result = None
    task.traceback = None
    return task


@pytest.fixture
def mock_database_session():
    """模拟数据库会话"""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    return session


class MockTradeMasterCore:
    """模拟TradeMaster核心模块"""
    
    def __init__(self):
        self.available = True
        self.sessions = {}
    
    async def start_training(self, config, callback=None):
        session_id = f"tm_session_{len(self.sessions) + 1}"
        self.sessions[session_id] = {
            "config": config,
            "status": "running",
            "progress": 0.0
        }
        return session_id
    
    async def stop_training(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "stopped"
        return {"status": "stopped"}
    
    async def get_training_status(self, session_id):
        return self.sessions.get(session_id, {"status": "not_found"})


@pytest.fixture
def mock_trademaster_core():
    """模拟TradeMaster核心实例"""
    return MockTradeMasterCore()


class MockWebSocketConnectionManager:
    """模拟WebSocket连接管理器"""
    
    def __init__(self):
        self.connections = {}
        self.user_connections = {}
        self.session_subscriptions = {}
    
    async def connect(self, websocket, user_id, **kwargs):
        connection_id = f"conn_{len(self.connections) + 1}"
        self.connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            **kwargs
        }
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        return connection_id
    
    async def disconnect(self, connection_id):
        if connection_id in self.connections:
            user_id = self.connections[connection_id]["user_id"]
            del self.connections[connection_id]
            
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
    
    async def subscribe_to_session(self, connection_id, session_id):
        if session_id not in self.session_subscriptions:
            self.session_subscriptions[session_id] = set()
        self.session_subscriptions[session_id].add(connection_id)
    
    async def send_personal_message(self, connection_id, message):
        if connection_id in self.connections:
            websocket = self.connections[connection_id]["websocket"]
            await websocket.send_text(str(message))
    
    async def broadcast_to_session(self, session_id, message):
        if session_id in self.session_subscriptions:
            for connection_id in self.session_subscriptions[session_id]:
                await self.send_personal_message(connection_id, message)


@pytest.fixture
def mock_websocket_manager():
    """模拟WebSocket连接管理器实例"""
    return MockWebSocketConnectionManager()


# 全局Mock配置
@pytest.fixture(autouse=True)
def setup_test_environment():
    """设置测试环境（自动应用到所有测试）"""
    
    # 设置测试环境变量
    test_env = {
        "TESTING": "1",
        "DATABASE_URL": "sqlite:///./test.db",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "REDIS_URL": "redis://localhost:6379/15",  # 使用测试Redis数据库
        "CELERY_BROKER_URL": "redis://localhost:6379/15",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/15"
    }
    
    with patch.dict(os.environ, test_env):
        yield


# 性能测试辅助函数
def assert_performance(duration: float, max_duration: float, operation: str):
    """断言性能指标"""
    assert duration <= max_duration, f"{operation} took {duration:.2f}s, expected <= {max_duration}s"


def create_large_dataset(size: int) -> List[Dict[str, Any]]:
    """创建大数据集用于性能测试"""
    return [
        {
            "id": i,
            "name": f"item_{i}",
            "value": i * 0.1,
            "timestamp": f"2024-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z"
        }
        for i in range(size)
    ]


# 测试数据验证函数
def validate_session_data(session_data: Dict[str, Any]) -> bool:
    """验证会话数据完整性"""
    required_fields = ["id", "strategy_id", "user_id", "status", "session_type"]
    return all(field in session_data for field in required_fields)


def validate_metrics_data(metrics_data: List[Dict[str, Any]]) -> bool:
    """验证指标数据完整性"""
    if not metrics_data:
        return True
    
    required_fields = ["metric_name", "metric_value", "session_id"]
    return all(
        all(field in metric for field in required_fields)
        for metric in metrics_data
    )


# 异步测试辅助装饰器
def async_test_timeout(seconds: int):
    """异步测试超时装饰器"""
    def decorator(func):
        return pytest.mark.timeout(seconds)(func)
    return decorator


# 参数化测试数据
STRATEGY_TYPES = ["algorithmic_trading", "portfolio_management", "order_execution", "high_frequency_trading"]
AGENT_TYPES = {
    "algorithmic_trading": ["dqn", "ppo", "sac"],
    "portfolio_management": ["eiie", "deeptrader"],
    "order_execution": ["eteo"],
    "high_frequency_trading": ["ddqn"]
}
DATASET_NAMES = ["BTC", "ETH", "AAPL", "MSFT", "dj30", "sp500"]


@pytest.fixture(params=STRATEGY_TYPES)
def strategy_type(request):
    """参数化策略类型"""
    return request.param


@pytest.fixture(params=["BTC", "ETH", "AAPL"])
def dataset_name(request):
    """参数化数据集名称"""
    return request.param


# 测试标记
pytestmark = [
    pytest.mark.asyncio,  # 默认异步测试标记
]


# 清理函数
def cleanup_test_files():
    """清理测试文件"""
    test_files = [
        "./test.db",
        "./test.db-shm", 
        "./test.db-wal"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except (OSError, PermissionError):
                pass  # 忽略删除失败


# 在测试会话结束时清理
@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    """测试结束后清理"""
    yield
    cleanup_test_files()