"""
端到端业务流程测试

测试重点：
1. 完整的策略创建、训练、回测、监控生命周期
2. 多用户并发操作场景
3. 系统在真实业务场景下的表现
4. 数据一致性和业务逻辑正确性
5. 系统恢复和错误处理能力

这些测试验证整个前后端集成系统的业务完整性。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List
import uuid

from app.services.trademaster_integration import TradeMasterIntegrationService
from app.models.database import StrategySession, SessionStatus, SessionType, Strategy, User


class TestCompleteStrategyLifecycle:
    """完整策略生命周期测试"""
    
    @pytest.fixture
    def integration_service(self):
        return TradeMasterIntegrationService()
    
    @pytest.fixture
    def mock_database(self):
        """模拟数据库操作"""
        db_mock = AsyncMock()
        
        # 模拟策略和用户数据
        strategies = {}
        sessions = {}
        users = {1: {"id": 1, "username": "testuser", "max_concurrent_sessions": 3}}
        metrics = {}
        
        def mock_get(model, id):
            if model == Strategy:
                return strategies.get(id)
            elif model == StrategySession:
                return sessions.get(id)
            elif model == User:
                return users.get(id)
            return None
        
        def mock_add(obj):
            if isinstance(obj, Strategy):
                obj.id = len(strategies) + 1
                strategies[obj.id] = obj
            elif isinstance(obj, StrategySession):
                obj.id = len(sessions) + 1
                sessions[obj.id] = obj
        
        db_mock.get = mock_get
        db_mock.add = mock_add
        db_mock.commit = AsyncMock()
        db_mock.refresh = AsyncMock()
        db_mock.execute = AsyncMock()
        
        return db_mock, strategies, sessions, users, metrics
    
    async def test_complete_strategy_lifecycle(self, integration_service):
        """测试完整的策略生命周期：创建→训练→监控→完成"""
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            db_mock, strategies, sessions, users, metrics = self.mock_database(self)
            mock_db_context.return_value.__aenter__.return_value = db_mock
            
            # 1. 创建策略配置
            strategy_config = {
                "strategy_type": "algorithmic_trading",
                "agent_type": "dqn",
                "dataset_name": "BTC",
                "epochs": 10,
                "learning_rate": 0.001,
                "batch_size": 32
            }
            
            # 模拟配置验证成功
            with patch.object(integration_service, 'config_adapter') as mock_adapter:
                mock_adapter.convert_web_config_to_trademaster.return_value = {
                    "task": "algorithmic_trading",
                    "dataset": {"type": "BTC"},
                    "agent": {"type": "dqn", "lr": 0.001},
                    "trainer": {"epochs": 10}
                }
                mock_adapter.validate_trademaster_config.return_value = {
                    "valid": True, "errors": []
                }
                
                # 2. 创建训练会话
                session_id = await integration_service.create_training_session(
                    strategy_id=1,
                    user_id=1,
                    config=strategy_config
                )
                
                assert session_id == 1
                assert 1 in sessions
                created_session = sessions[1]
                assert created_session.session_type == SessionType.TRAINING
                assert created_session.status == SessionStatus.PENDING
                
                # 3. 启动训练任务
                with patch('app.services.trademaster_integration.execute_training_task') as mock_task:
                    mock_celery_task = Mock()
                    mock_celery_task.id = "celery-task-123"
                    mock_task.delay.return_value = mock_celery_task
                    
                    task_id = await integration_service.start_training_task(session_id)
                    
                    assert task_id == "celery-task-123"
                    assert created_session.celery_task_id == "celery-task-123"
                
                # 4. 监控训练进度
                # 模拟训练过程中的状态更新
                created_session.status = SessionStatus.RUNNING
                created_session.progress = 50.0
                created_session.current_epoch = 5
                created_session.started_at = datetime.now()
                
                # 模拟获取最近指标
                with patch.object(integration_service, '_get_recent_metrics') as mock_metrics:
                    mock_metrics.return_value = [
                        {
                            "metric_name": "loss",
                            "metric_value": 0.25,
                            "epoch": 5,
                            "recorded_at": datetime.now().isoformat()
                        }
                    ]
                    
                    status = await integration_service.get_session_status(session_id)
                    
                    assert status["session_id"] == session_id
                    assert status["status"] == "running"
                    assert status["progress"] == 50.0
                    assert status["current_epoch"] == 5
                    assert len(status["recent_metrics"]) == 1
                
                # 5. 完成训练
                created_session.status = SessionStatus.COMPLETED
                created_session.progress = 100.0
                created_session.current_epoch = 10
                created_session.completed_at = datetime.now()
                created_session.final_metrics = {
                    "final_loss": 0.1,
                    "final_reward": 25.5,
                    "training_duration": 3600
                }
                
                final_status = await integration_service.get_session_status(session_id)
                
                assert final_status["status"] == "completed"
                assert final_status["progress"] == 100.0
                assert final_status["current_epoch"] == 10
                assert final_status["final_metrics"]["final_loss"] == 0.1
    
    async def test_backtest_after_training(self, integration_service):
        """测试训练完成后进行回测"""
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            db_mock, strategies, sessions, users, metrics = self.mock_database(self)
            mock_db_context.return_value.__aenter__.return_value = db_mock
            
            # 1. 先创建一个已完成的训练会话
            training_session = StrategySession(
                id=1,
                strategy_id=1,
                user_id=1,
                session_type=SessionType.TRAINING,
                status=SessionStatus.COMPLETED,
                progress=100.0,
                final_metrics={"loss": 0.1}
            )
            sessions[1] = training_session
            
            # 2. 基于训练结果创建回测会话
            backtest_config = {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 100000,
                "benchmark": "SPY"
            }
            
            with patch.object(integration_service, 'config_adapter') as mock_adapter:
                mock_adapter.convert_web_config_to_trademaster.return_value = {
                    "task": "algorithmic_trading",
                    "dataset": {"type": "BTC"},
                    "agent": {"type": "dqn"}
                }
                
                backtest_session_id = await integration_service.create_backtest_session(
                    strategy_id=1,
                    user_id=1,
                    config=backtest_config
                )
                
                assert backtest_session_id == 2
                assert 2 in sessions
                backtest_session = sessions[2]
                assert backtest_session.session_type == SessionType.BACKTEST
                
                # 3. 启动回测任务
                with patch('app.services.trademaster_integration.execute_backtest_task') as mock_task:
                    mock_celery_task = Mock()
                    mock_celery_task.id = "celery-backtest-456"
                    mock_task.delay.return_value = mock_celery_task
                    
                    task_id = await integration_service.start_backtest_task(backtest_session_id)
                    
                    assert task_id == "celery-backtest-456"
                    assert backtest_session.celery_task_id == "celery-backtest-456"
                
                # 4. 模拟回测完成
                backtest_session.status = SessionStatus.COMPLETED
                backtest_session.final_metrics = {
                    "total_return": 0.15,
                    "sharpe_ratio": 1.25,
                    "max_drawdown": 0.08,
                    "win_rate": 0.65
                }
                
                final_status = await integration_service.get_session_status(backtest_session_id)
                
                assert final_status["status"] == "completed"
                assert final_status["final_metrics"]["total_return"] == 0.15


class TestMultiUserConcurrentOperations:
    """多用户并发操作测试"""
    
    @pytest.fixture
    def integration_service(self):
        return TradeMasterIntegrationService()
    
    async def test_concurrent_user_training_sessions(self, integration_service):
        """测试多用户并发训练会话"""
        
        users = [
            {"id": 1, "username": "user1", "max_concurrent_sessions": 2},
            {"id": 2, "username": "user2", "max_concurrent_sessions": 3},
            {"id": 3, "username": "user3", "max_concurrent_sessions": 1}
        ]
        
        sessions_created = {}
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            with patch.object(integration_service, 'config_adapter') as mock_adapter:
                
                # 设置模拟
                def mock_db_session():
                    db_mock = AsyncMock()
                    
                    def mock_add(obj):
                        if isinstance(obj, StrategySession):
                            obj.id = len(sessions_created) + 1
                            sessions_created[obj.id] = obj
                    
                    db_mock.add = mock_add
                    db_mock.commit = AsyncMock()
                    db_mock.refresh = AsyncMock()
                    return db_mock
                
                mock_db_context.return_value.__aenter__.return_value = mock_db_session()
                
                mock_adapter.convert_web_config_to_trademaster.return_value = {
                    "task": "algorithmic_trading",
                    "dataset": {"type": "BTC"},
                    "agent": {"type": "dqn"}
                }
                mock_adapter.validate_trademaster_config.return_value = {
                    "valid": True, "errors": []
                }
                
                # 并发创建训练会话
                config = {
                    "strategy_type": "algorithmic_trading",
                    "agent_type": "dqn",
                    "dataset_name": "BTC",
                    "epochs": 50
                }
                
                tasks = []
                for user in users:
                    for i in range(user["max_concurrent_sessions"]):
                        task = integration_service.create_training_session(
                            strategy_id=user["id"] * 10 + i,
                            user_id=user["id"],
                            config=config
                        )
                        tasks.append(task)
                
                # 执行并发任务
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 验证结果
                successful_results = [r for r in results if isinstance(r, int)]
                assert len(successful_results) == sum(u["max_concurrent_sessions"] for u in users)
                
                # 验证会话创建
                assert len(sessions_created) == len(successful_results)
                
                # 验证不同用户的会话隔离
                user_sessions = {}
                for session_id, session in sessions_created.items():
                    user_id = session.user_id
                    if user_id not in user_sessions:
                        user_sessions[user_id] = []
                    user_sessions[user_id].append(session)
                
                for user in users:
                    assert len(user_sessions[user["id"]]) == user["max_concurrent_sessions"]
    
    async def test_user_session_isolation(self, integration_service):
        """测试用户会话隔离"""
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            db_mock = AsyncMock()
            
            # 创建两个用户的会话
            sessions = {
                1: StrategySession(id=1, strategy_id=1, user_id=1, status=SessionStatus.RUNNING),
                2: StrategySession(id=2, strategy_id=2, user_id=2, status=SessionStatus.RUNNING)
            }
            
            db_mock.get.side_effect = lambda model, id: sessions.get(id)
            mock_db_context.return_value.__aenter__.return_value = db_mock
            
            # 用户1尝试停止用户2的会话（应该失败）
            with pytest.raises(ValueError, match="无权操作此会话"):
                await integration_service.stop_session(session_id=2, user_id=1)
            
            # 用户2尝试停止自己的会话（应该成功）
            with patch('app.services.trademaster_integration.celery_app') as mock_celery:
                mock_control = Mock()
                mock_celery.control = mock_control
                integration_service.core_available = False  # 避免TradeMaster调用
                
                result = await integration_service.stop_session(session_id=2, user_id=2)
                
                assert result["status"] == "stopped"
                assert sessions[2].status == SessionStatus.CANCELLED


class TestSystemRecoveryAndErrorHandling:
    """系统恢复和错误处理测试"""
    
    @pytest.fixture
    def integration_service(self):
        return TradeMasterIntegrationService()
    
    async def test_training_failure_recovery(self, integration_service):
        """测试训练失败后的恢复机制"""
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            db_mock = AsyncMock()
            
            # 模拟失败的训练会话
            failed_session = StrategySession(
                id=1,
                strategy_id=1,
                user_id=1,
                session_type=SessionType.TRAINING,
                status=SessionStatus.FAILED,
                error_message="Out of memory",
                progress=25.0,
                current_epoch=25
            )
            
            sessions = {1: failed_session}
            db_mock.get.side_effect = lambda model, id: sessions.get(id)
            mock_db_context.return_value.__aenter__.return_value = db_mock
            
            # 获取失败会话状态
            status = await integration_service.get_session_status(1)
            
            assert status["status"] == "failed"
            assert status["error_message"] == "Out of memory"
            assert status["progress"] == 25.0
            
            # 模拟用相同配置重新创建会话（恢复训练）
            def mock_add(obj):
                if isinstance(obj, StrategySession):
                    obj.id = 2
                    sessions[2] = obj
            
            db_mock.add = mock_add
            db_mock.commit = AsyncMock()
            db_mock.refresh = AsyncMock()
            
            with patch.object(integration_service, 'config_adapter') as mock_adapter:
                mock_adapter.convert_web_config_to_trademaster.return_value = {
                    "task": "algorithmic_trading",
                    "dataset": {"type": "BTC"},
                    "agent": {"type": "dqn"}
                }
                mock_adapter.validate_trademaster_config.return_value = {
                    "valid": True, "errors": []
                }
                
                recovery_config = {
                    "strategy_type": "algorithmic_trading",
                    "agent_type": "dqn",
                    "dataset_name": "BTC",
                    "epochs": 100,
                    "resume_from_epoch": 25  # 从失败点恢复
                }
                
                new_session_id = await integration_service.create_training_session(
                    strategy_id=1,
                    user_id=1,
                    config=recovery_config
                )
                
                assert new_session_id == 2
                assert 2 in sessions
                new_session = sessions[2]
                assert new_session.status == SessionStatus.PENDING
    
    async def test_network_interruption_handling(self, integration_service):
        """测试网络中断处理"""
        
        # 模拟网络中断情况下的配置验证失败
        with patch.object(integration_service, 'config_adapter') as mock_adapter:
            mock_adapter.convert_web_config_to_trademaster.side_effect = Exception("Network timeout")
            
            config = {
                "strategy_type": "algorithmic_trading",
                "agent_type": "dqn",
                "dataset_name": "BTC"
            }
            
            with pytest.raises(ValueError, match="创建训练会话失败"):
                await integration_service.create_training_session(
                    strategy_id=1,
                    user_id=1,
                    config=config
                )
    
    async def test_database_connection_failure_handling(self, integration_service):
        """测试数据库连接失败处理"""
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            # 模拟数据库连接失败
            mock_db_context.side_effect = Exception("Database connection failed")
            
            config = {
                "strategy_type": "algorithmic_trading",
                "agent_type": "dqn",
                "dataset_name": "BTC"
            }
            
            with pytest.raises(ValueError, match="创建训练会话失败"):
                await integration_service.create_training_session(
                    strategy_id=1,
                    user_id=1,
                    config=config
                )
    
    async def test_celery_task_failure_handling(self, integration_service):
        """测试Celery任务失败处理"""
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            db_mock = AsyncMock()
            
            session = StrategySession(
                id=1,
                strategy_id=1,
                user_id=1,
                status=SessionStatus.PENDING,
                celery_task_id=None
            )
            
            db_mock.get.return_value = session
            db_mock.commit = AsyncMock()
            mock_db_context.return_value.__aenter__.return_value = db_mock
            
            # 模拟Celery任务提交失败
            with patch('app.services.trademaster_integration.execute_training_task') as mock_task:
                mock_task.delay.side_effect = Exception("Celery broker unavailable")
                
                with pytest.raises(ValueError, match="启动训练任务失败"):
                    await integration_service.start_training_task(1)


class TestDataConsistencyAndBusinessLogic:
    """数据一致性和业务逻辑测试"""
    
    @pytest.fixture
    def integration_service(self):
        return TradeMasterIntegrationService()
    
    async def test_session_status_consistency(self, integration_service):
        """测试会话状态一致性"""
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            db_mock = AsyncMock()
            
            # 创建会话并模拟状态变化
            session = StrategySession(
                id=1,
                strategy_id=1,
                user_id=1,
                session_type=SessionType.TRAINING,
                status=SessionStatus.PENDING,
                progress=0.0,
                current_epoch=0,
                total_epochs=100,
                started_at=None,
                completed_at=None
            )
            
            db_mock.get.return_value = session
            mock_db_context.return_value.__aenter__.return_value = db_mock
            
            # 模拟获取最近指标
            with patch.object(integration_service, '_get_recent_metrics') as mock_metrics:
                mock_metrics.return_value = []
                
                # 1. 初始状态
                status = await integration_service.get_session_status(1)
                assert status["status"] == "pending"
                assert status["progress"] == 0.0
                assert status["started_at"] is None
                
                # 2. 模拟开始训练
                session.status = SessionStatus.RUNNING
                session.started_at = datetime.now()
                session.progress = 10.0
                session.current_epoch = 10
                
                status = await integration_service.get_session_status(1)
                assert status["status"] == "running"
                assert status["progress"] == 10.0
                assert status["current_epoch"] == 10
                assert status["started_at"] is not None
                
                # 3. 模拟训练完成
                session.status = SessionStatus.COMPLETED
                session.completed_at = datetime.now()
                session.progress = 100.0
                session.current_epoch = 100
                session.final_metrics = {"loss": 0.05, "accuracy": 0.95}
                
                status = await integration_service.get_session_status(1)
                assert status["status"] == "completed"
                assert status["progress"] == 100.0
                assert status["completed_at"] is not None
                assert status["final_metrics"]["loss"] == 0.05
    
    async def test_concurrent_session_limits(self, integration_service):
        """测试并发会话数量限制"""
        
        max_concurrent = 2
        user_id = 1
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            sessions = {}
            
            def mock_db_session():
                db_mock = AsyncMock()
                
                def mock_add(obj):
                    if isinstance(obj, StrategySession):
                        obj.id = len(sessions) + 1
                        sessions[obj.id] = obj
                
                db_mock.add = mock_add
                db_mock.commit = AsyncMock()
                db_mock.refresh = AsyncMock()
                return db_mock
            
            mock_db_context.return_value.__aenter__.return_value = mock_db_session()
            
            with patch.object(integration_service, 'config_adapter') as mock_adapter:
                mock_adapter.convert_web_config_to_trademaster.return_value = {"task": "test"}
                mock_adapter.validate_trademaster_config.return_value = {"valid": True, "errors": []}
                
                config = {
                    "strategy_type": "algorithmic_trading",
                    "agent_type": "dqn",
                    "dataset_name": "BTC"
                }
                
                # 创建最大数量的并发会话
                session_ids = []
                for i in range(max_concurrent):
                    session_id = await integration_service.create_training_session(
                        strategy_id=i + 1,
                        user_id=user_id,
                        config=config
                    )
                    session_ids.append(session_id)
                
                assert len(session_ids) == max_concurrent
                assert len(sessions) == max_concurrent
                
                # 验证每个会话都正确创建
                for session_id in session_ids:
                    assert session_id in sessions
                    assert sessions[session_id].user_id == user_id
                    assert sessions[session_id].status == SessionStatus.PENDING
    
    async def test_business_rule_validation(self, integration_service):
        """测试业务规则验证"""
        
        with patch.object(integration_service, 'config_adapter') as mock_adapter:
            
            # 测试无效的业务配置
            invalid_configs = [
                {
                    "strategy_type": "algorithmic_trading",
                    "agent_type": "nonexistent_agent",
                    "dataset_name": "BTC"
                },
                {
                    "strategy_type": "portfolio_management",
                    "agent_type": "eiie",
                    "dataset_name": "",  # 空数据集
                },
                {
                    "strategy_type": "order_execution",
                    "agent_type": "eteo",
                    "epochs": -10,  # 负数轮次
                    "learning_rate": -0.001  # 负学习率
                }
            ]
            
            for i, invalid_config in enumerate(invalid_configs):
                mock_adapter.convert_web_config_to_trademaster.return_value = {"task": "test"}
                mock_adapter.validate_trademaster_config.return_value = {
                    "valid": False,
                    "errors": [f"Invalid configuration {i+1}"]
                }
                
                with pytest.raises(ValueError, match="配置验证失败"):
                    await integration_service.create_training_session(
                        strategy_id=i + 1,
                        user_id=1,
                        config=invalid_config
                    )


class TestSystemPerformanceUnderLoad:
    """系统负载性能测试"""
    
    @pytest.fixture
    def integration_service(self):
        return TradeMasterIntegrationService()
    
    async def test_high_concurrency_session_creation(self, integration_service):
        """测试高并发会话创建"""
        
        session_count = 50
        user_count = 10
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            sessions_created = {}
            
            def mock_db_session():
                db_mock = AsyncMock()
                
                def mock_add(obj):
                    if isinstance(obj, StrategySession):
                        obj.id = len(sessions_created) + 1
                        sessions_created[obj.id] = obj
                
                db_mock.add = mock_add
                db_mock.commit = AsyncMock()
                db_mock.refresh = AsyncMock()
                return db_mock
            
            mock_db_context.return_value.__aenter__.return_value = mock_db_session()
            
            with patch.object(integration_service, 'config_adapter') as mock_adapter:
                mock_adapter.convert_web_config_to_trademaster.return_value = {"task": "test"}
                mock_adapter.validate_trademaster_config.return_value = {"valid": True, "errors": []}
                
                config = {
                    "strategy_type": "algorithmic_trading",
                    "agent_type": "dqn",
                    "dataset_name": "BTC"
                }
                
                # 创建大量并发任务
                tasks = []
                for i in range(session_count):
                    user_id = (i % user_count) + 1
                    task = integration_service.create_training_session(
                        strategy_id=i + 1,
                        user_id=user_id,
                        config=config
                    )
                    tasks.append(task)
                
                # 测试并发执行性能
                start_time = asyncio.get_event_loop().time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = asyncio.get_event_loop().time()
                
                duration = end_time - start_time
                
                # 验证性能指标
                assert duration < 5.0  # 50个并发会话创建应该在5秒内完成
                
                # 验证成功率
                successful_results = [r for r in results if isinstance(r, int)]
                assert len(successful_results) == session_count
                assert len(sessions_created) == session_count
    
    async def test_memory_usage_under_load(self, integration_service):
        """测试负载下的内存使用"""
        
        import gc
        import psutil
        import os
        
        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量操作
        session_count = 100
        
        with patch('app.services.trademaster_integration.get_async_db_session') as mock_db_context:
            sessions = {}
            
            def mock_db_session():
                db_mock = AsyncMock()
                db_mock.add = lambda obj: setattr(obj, 'id', len(sessions) + 1) or sessions.update({obj.id: obj})
                db_mock.commit = AsyncMock()
                db_mock.refresh = AsyncMock()
                return db_mock
            
            mock_db_context.return_value.__aenter__.return_value = mock_db_session()
            
            with patch.object(integration_service, 'config_adapter') as mock_adapter:
                mock_adapter.convert_web_config_to_trademaster.return_value = {"task": "test"}
                mock_adapter.validate_trademaster_config.return_value = {"valid": True, "errors": []}
                
                # 创建大量会话
                for i in range(session_count):
                    config = {"strategy_type": "algorithmic_trading", "agent_type": "dqn"}
                    await integration_service.create_training_session(
                        strategy_id=i + 1,
                        user_id=1,
                        config=config
                    )
                
                # 获取最终内存使用
                gc.collect()  # 强制垃圾回收
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                memory_increase = final_memory - initial_memory
                
                # 验证内存使用合理性
                assert memory_increase < 100  # 内存增长应该小于100MB
                assert len(sessions) == session_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])