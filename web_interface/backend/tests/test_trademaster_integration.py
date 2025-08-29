"""
TradeMaster核心集成服务测试

测试重点：
1. TradeMaster核心模块的集成完整性
2. 配置转换和验证逻辑
3. 训练会话生命周期管理
4. 错误处理和异常恢复机制
5. 资源管理和清理机制

这些测试直接针对代码质量评审中发现的TradeMaster核心集成不完整问题。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.services.trademaster_integration import (
    TradeMasterIntegrationService, get_integration_service
)
from app.services.trademaster_core import TradeMasterCore, TradeMasterCoreError
from app.models.database import StrategySession, SessionStatus, SessionType
from app.core.trademaster_config import TradeMasterConfigAdapter


class TestTradeMasterIntegrationService:
    """TradeMaster集成服务核心功能测试"""
    
    @pytest.fixture
    def integration_service(self):
        """创建集成服务实例"""
        return TradeMasterIntegrationService()
    
    @pytest.fixture
    def mock_config_adapter(self):
        """模拟配置适配器"""
        adapter = Mock(spec=TradeMasterConfigAdapter)
        adapter.convert_web_config_to_trademaster.return_value = {
            "task": "algorithmic_trading",
            "dataset": {"type": "BTC", "train_start_date": "2020-01-01"},
            "agent": {"type": "dqn", "lr": 0.001},
            "environment": {"type": "market"}
        }
        adapter.validate_trademaster_config.return_value = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        return adapter
    
    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        strategy_session = Mock(spec=StrategySession)
        strategy_session.id = 123
        strategy_session.strategy_id = 1
        strategy_session.user_id = 1
        strategy_session.status = SessionStatus.PENDING
        strategy_session.session_type = SessionType.TRAINING
        strategy_session.celery_task_id = None
        strategy_session.progress = 0.0
        
        session.get.return_value = strategy_session
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session, strategy_session
    
    async def test_create_training_session_success(self, integration_service, mock_config_adapter):
        """测试成功创建训练会话"""
        with patch.object(integration_service, 'config_adapter', mock_config_adapter):
            with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
                db_session, strategy_session = self.mock_db_session(self)
                mock_db.return_value.__aenter__.return_value = db_session
                
                config = {
                    "agent_type": "dqn",
                    "dataset_name": "BTC",
                    "epochs": 100,
                    "learning_rate": 0.001
                }
                
                session_id = await integration_service.create_training_session(
                    strategy_id=1,
                    user_id=1,
                    config=config
                )
                
                # 验证配置转换被调用
                mock_config_adapter.convert_web_config_to_trademaster.assert_called_once_with(config)
                
                # 验证配置验证被调用
                mock_config_adapter.validate_trademaster_config.assert_called_once()
                
                # 验证数据库操作
                db_session.add.assert_called_once()
                db_session.commit.assert_called_once()
                db_session.refresh.assert_called_once()
                
                # 验证返回的会话ID
                assert session_id == 123
    
    async def test_create_training_session_invalid_config(self, integration_service, mock_config_adapter):
        """测试配置验证失败时的错误处理"""
        mock_config_adapter.validate_trademaster_config.return_value = {
            "valid": False,
            "errors": ["Agent type 'invalid_agent' not supported", "Learning rate must be positive"]
        }
        
        with patch.object(integration_service, 'config_adapter', mock_config_adapter):
            config = {
                "agent_type": "invalid_agent",
                "learning_rate": -0.001
            }
            
            with pytest.raises(ValueError, match="配置验证失败"):
                await integration_service.create_training_session(
                    strategy_id=1,
                    user_id=1,
                    config=config
                )
    
    async def test_start_training_task_success(self, integration_service):
        """测试成功启动训练任务"""
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
            db_session, strategy_session = self.mock_db_session(self)
            mock_db.return_value.__aenter__.return_value = db_session
            
            # 模拟Celery任务
            mock_task = Mock()
            mock_task.id = "celery-task-123"
            
            with patch('app.services.trademaster_integration.execute_training_task') as mock_celery_task:
                mock_celery_task.delay.return_value = mock_task
                
                task_id = await integration_service.start_training_task(session_id=123)
                
                # 验证Celery任务被启动
                mock_celery_task.delay.assert_called_once_with(123)
                
                # 验证数据库更新
                assert db_session.commit.call_count >= 1
                assert strategy_session.celery_task_id == "celery-task-123"
                
                # 验证返回任务ID
                assert task_id == "celery-task-123"
    
    async def test_start_training_task_session_not_found(self, integration_service):
        """测试会话不存在时的错误处理"""
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
            db_session = AsyncMock()
            db_session.get.return_value = None  # 会话不存在
            mock_db.return_value.__aenter__.return_value = db_session
            
            with pytest.raises(ValueError, match="会话不存在"):
                await integration_service.start_training_task(session_id=999)
    
    async def test_start_training_task_invalid_status(self, integration_service):
        """测试会话状态错误时的错误处理"""
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
            db_session, strategy_session = self.mock_db_session(self)
            strategy_session.status = SessionStatus.RUNNING  # 错误状态
            mock_db.return_value.__aenter__.return_value = db_session
            
            with pytest.raises(ValueError, match="会话状态错误"):
                await integration_service.start_training_task(session_id=123)
    
    async def test_stop_session_success(self, integration_service):
        """测试成功停止会话"""
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
            db_session, strategy_session = self.mock_db_session(self)
            strategy_session.celery_task_id = "celery-task-123"
            strategy_session.trademaster_session_id = "tm-session-456"
            mock_db.return_value.__aenter__.return_value = db_session
            
            # 模拟Celery撤销
            with patch('app.services.trademaster_integration.celery_app') as mock_celery:
                mock_control = Mock()
                mock_celery.control = mock_control
                
                # 模拟TradeMaster核心
                mock_core = AsyncMock()
                integration_service.trademaster_core = mock_core
                integration_service.core_available = True
                
                result = await integration_service.stop_session(session_id=123, user_id=1)
                
                # 验证Celery任务被撤销
                mock_control.revoke.assert_called_once_with("celery-task-123", terminate=True)
                
                # 验证TradeMaster会话被停止
                mock_core.stop_training.assert_called_once_with("tm-session-456")
                
                # 验证会话状态更新
                assert strategy_session.status == SessionStatus.CANCELLED
                assert strategy_session.completed_at is not None
                
                # 验证返回结果
                assert result["status"] == "stopped"
                assert result["message"] == "会话已停止"
    
    async def test_stop_session_permission_denied(self, integration_service):
        """测试权限不足时的错误处理"""
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
            db_session, strategy_session = self.mock_db_session(self)
            strategy_session.user_id = 2  # 不同用户ID
            mock_db.return_value.__aenter__.return_value = db_session
            
            with pytest.raises(ValueError, match="无权操作此会话"):
                await integration_service.stop_session(session_id=123, user_id=1)
    
    async def test_get_session_status_success(self, integration_service):
        """测试获取会话状态"""
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
            db_session, strategy_session = self.mock_db_session(self)
            strategy_session.status = SessionStatus.RUNNING
            strategy_session.progress = 45.5
            strategy_session.current_epoch = 45
            strategy_session.total_epochs = 100
            strategy_session.started_at = datetime.now()
            strategy_session.completed_at = None
            strategy_session.error_message = None
            strategy_session.final_metrics = {"loss": 0.123}
            mock_db.return_value.__aenter__.return_value = db_session
            
            # 模拟最近指标
            with patch.object(integration_service, '_get_recent_metrics') as mock_metrics:
                mock_metrics.return_value = [
                    {"metric_name": "loss", "metric_value": 0.123, "epoch": 45}
                ]
                
                status = await integration_service.get_session_status(session_id=123)
                
                # 验证返回的状态信息
                assert status["session_id"] == 123
                assert status["status"] == "running"
                assert status["progress"] == 45.5
                assert status["current_epoch"] == 45
                assert status["total_epochs"] == 100
                assert status["recent_metrics"] == [
                    {"metric_name": "loss", "metric_value": 0.123, "epoch": 45}
                ]
                assert status["started_at"] is not None
                assert status["completed_at"] is None
                assert status["error_message"] is None
                assert status["final_metrics"] == {"loss": 0.123}
    
    async def test_get_user_sessions(self, integration_service):
        """测试获取用户会话列表"""
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
            db_session = AsyncMock()
            
            # 模拟查询结果
            mock_sessions = []
            for i in range(3):
                session = Mock()
                session.id = i + 1
                session.session_type = SessionType.TRAINING if i % 2 == 0 else SessionType.BACKTEST
                session.status = SessionStatus.COMPLETED if i == 0 else SessionStatus.RUNNING
                session.progress = 100.0 if i == 0 else 50.0
                session.strategy_id = 1
                session.created_at = datetime.now() - timedelta(days=i)
                session.started_at = datetime.now() - timedelta(days=i, hours=1) if i < 2 else None
                session.completed_at = datetime.now() - timedelta(hours=1) if i == 0 else None
                mock_sessions.append(session)
            
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = mock_sessions
            db_session.execute.return_value = mock_result
            mock_db.return_value.__aenter__.return_value = db_session
            
            sessions = await integration_service.get_user_sessions(user_id=1)
            
            # 验证返回的会话列表
            assert len(sessions) == 3
            assert sessions[0]["session_id"] == 1
            assert sessions[0]["session_type"] == "training"
            assert sessions[0]["status"] == "completed"
            assert sessions[1]["session_id"] == 2
            assert sessions[1]["session_type"] == "backtest"
            assert sessions[1]["status"] == "running"
    
    async def test_validate_strategy_config_success(self, integration_service, mock_config_adapter):
        """测试策略配置验证成功"""
        mock_config_adapter.validate_trademaster_config.return_value = {
            "valid": True,
            "errors": [],
            "warnings": ["Dataset might be outdated"],
            "suggestions": ["Consider using more recent data"]
        }
        
        with patch.object(integration_service, 'config_adapter', mock_config_adapter):
            config = {"agent_type": "dqn", "dataset_name": "BTC"}
            
            result = await integration_service.validate_strategy_config(
                config=config,
                strategy_type="algorithmic_trading"
            )
            
            assert result["valid"] is True
            assert result["errors"] == []
            assert result["warnings"] == ["Dataset might be outdated"]
            assert result["suggestions"] == ["Consider using more recent data"]
    
    async def test_validate_strategy_config_failure(self, integration_service, mock_config_adapter):
        """测试策略配置验证失败"""
        mock_config_adapter.validate_trademaster_config.return_value = {
            "valid": False,
            "errors": ["Invalid agent type", "Missing required dataset"]
        }
        
        with patch.object(integration_service, 'config_adapter', mock_config_adapter):
            config = {"agent_type": "invalid"}
            
            result = await integration_service.validate_strategy_config(
                config=config,
                strategy_type="algorithmic_trading"
            )
            
            assert result["valid"] is False
            assert len(result["errors"]) == 2
            assert "Invalid agent type" in result["errors"]
    
    async def test_get_available_strategies(self, integration_service):
        """测试获取可用策略模板"""
        strategies = await integration_service.get_available_strategies()
        
        assert len(strategies) >= 3
        
        # 验证DQN策略
        dqn_strategy = next(s for s in strategies if s["name"] == "DQN Algorithm Trading")
        assert dqn_strategy["strategy_type"] == "algorithmic_trading"
        assert "dqn" in dqn_strategy["default_config"]["agent"]
        
        # 验证PPO策略
        ppo_strategy = next(s for s in strategies if s["name"] == "PPO Algorithm Trading")
        assert ppo_strategy["strategy_type"] == "algorithmic_trading"
        assert "ppo" in ppo_strategy["default_config"]["agent"]
        
        # 验证EIIE策略
        eiie_strategy = next(s for s in strategies if s["name"] == "EIIE Portfolio Management")
        assert eiie_strategy["strategy_type"] == "portfolio_management"
        assert "eiie" in eiie_strategy["default_config"]["agent"]
    
    async def test_test_connection_success(self, integration_service):
        """测试TradeMaster连接测试成功"""
        integration_service.core_available = True
        
        result = await integration_service.test_connection()
        
        assert result["success"] is True
        assert "version" in result
        assert "available_strategies" in result
    
    async def test_test_connection_core_unavailable(self, integration_service):
        """测试TradeMaster核心模块不可用时的连接测试"""
        integration_service.core_available = False
        
        result = await integration_service.test_connection()
        
        assert result["success"] is False
        assert "TradeMaster核心模块不可用" in result["error"]
    
    async def test_test_connection_network_failure(self, integration_service):
        """测试网络连接失败"""
        integration_service.core_available = True
        
        result = await integration_service.test_connection(
            api_endpoint="http://invalid-endpoint:9999/api"
        )
        
        assert result["success"] is False
        assert "无法连接到" in result["error"]


class TestTradeMasterCoreIntegration:
    """TradeMaster核心模块集成测试"""
    
    @pytest.fixture
    def mock_trademaster_available(self):
        """模拟TradeMaster模块可用"""
        with patch('app.services.trademaster_core.TRADEMASTER_AVAILABLE', True):
            yield
    
    async def test_core_service_initialization(self, mock_trademaster_available):
        """测试核心服务初始化"""
        with patch('app.services.trademaster_core.get_config_adapter') as mock_adapter:
            mock_adapter.return_value = Mock()
            
            core = TradeMasterCore()
            
            assert core.config_adapter is not None
            assert core.sessions == {}
            assert core.executor is not None
    
    async def test_core_service_unavailable(self):
        """测试TradeMaster核心模块不可用时的异常处理"""
        with patch('app.services.trademaster_core.TRADEMASTER_AVAILABLE', False):
            with pytest.raises(TradeMasterCoreError, match="TradeMaster核心模块不可用"):
                TradeMasterCore()


class TestGlobalServiceInstance:
    """测试全局服务实例管理"""
    
    def test_get_integration_service_singleton(self):
        """测试集成服务单例模式"""
        service1 = get_integration_service()
        service2 = get_integration_service()
        
        assert service1 is service2
        assert isinstance(service1, TradeMasterIntegrationService)
    
    def test_service_instance_persistence(self):
        """测试服务实例持久性"""
        service = get_integration_service()
        original_id = id(service)
        
        # 多次调用应该返回同一个实例
        for _ in range(5):
            assert id(get_integration_service()) == original_id


# 性能和压力测试
class TestTradeMasterIntegrationPerformance:
    """TradeMaster集成服务性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self):
        """测试并发会话创建性能"""
        integration_service = TradeMasterIntegrationService()
        
        with patch.object(integration_service, 'config_adapter') as mock_adapter:
            mock_adapter.convert_web_config_to_trademaster.return_value = {"task": "test"}
            mock_adapter.validate_trademaster_config.return_value = {"valid": True, "errors": []}
            
            with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
                # 模拟数据库会话
                sessions = []
                for i in range(10):
                    db_session = AsyncMock()
                    strategy_session = Mock()
                    strategy_session.id = i + 1
                    db_session.get.return_value = strategy_session
                    db_session.add = Mock()
                    db_session.commit = AsyncMock()
                    db_session.refresh = AsyncMock()
                    sessions.append((db_session, strategy_session))
                
                mock_db.return_value.__aenter__.side_effect = [s[0] for s in sessions]
                
                # 并发创建10个会话
                tasks = []
                for i in range(10):
                    config = {"agent_type": "dqn", "dataset_name": f"TEST_{i}"}
                    task = integration_service.create_training_session(
                        strategy_id=i + 1,
                        user_id=1,
                        config=config
                    )
                    tasks.append(task)
                
                start_time = asyncio.get_event_loop().time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = asyncio.get_event_loop().time()
                
                # 验证性能指标
                duration = end_time - start_time
                assert duration < 2.0  # 应该在2秒内完成
                
                # 验证所有任务都成功完成
                successful_results = [r for r in results if isinstance(r, int)]
                assert len(successful_results) == 10
    
    @pytest.mark.asyncio
    async def test_status_query_performance(self):
        """测试状态查询性能"""
        integration_service = TradeMasterIntegrationService()
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db:
            db_session = AsyncMock()
            strategy_session = Mock()
            strategy_session.id = 1
            strategy_session.status = SessionStatus.RUNNING
            strategy_session.progress = 50.0
            strategy_session.current_epoch = 50
            strategy_session.total_epochs = 100
            strategy_session.started_at = datetime.now()
            strategy_session.completed_at = None
            strategy_session.error_message = None
            strategy_session.final_metrics = {}
            
            db_session.get.return_value = strategy_session
            mock_db.return_value.__aenter__.return_value = db_session
            
            with patch.object(integration_service, '_get_recent_metrics') as mock_metrics:
                mock_metrics.return_value = []
                
                # 执行100次状态查询
                start_time = asyncio.get_event_loop().time()
                
                tasks = []
                for _ in range(100):
                    tasks.append(integration_service.get_session_status(session_id=1))
                
                results = await asyncio.gather(*tasks)
                
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                
                # 验证性能指标
                assert duration < 1.0  # 100次查询应该在1秒内完成
                assert len(results) == 100
                assert all(r["session_id"] == 1 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])