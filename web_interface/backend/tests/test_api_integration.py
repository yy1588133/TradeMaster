"""
API端点集成测试

测试重点：
1. 策略管理API的完整CRUD操作
2. 训练和回测任务的端到端流程
3. 实时监控API的数据准确性
4. 错误处理和用户权限验证
5. API响应时间和性能指标

这些测试验证前后端集成的完整性和功能正确性。
"""

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta

from app.main import app
from app.models.database import StrategySession, SessionStatus, SessionType, Strategy
from app.core.dependencies import get_current_active_user


class TestStrategyAPI:
    """策略管理API测试"""
    
    @pytest.fixture
    def auth_headers(self):
        """认证头"""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def mock_user(self):
        """模拟用户"""
        return {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "is_superuser": False,
            "max_concurrent_sessions": 3
        }
    
    async def test_create_strategy_success(self, auth_headers, mock_user):
        """测试成功创建策略"""
        strategy_data = {
            "name": "测试策略",
            "description": "集成测试策略",
            "strategy_type": "algorithmic_trading",
            "config": {
                "agent_type": "dqn",
                "dataset_name": "BTC",
                "epochs": 100,
                "learning_rate": 0.001
            }
        }
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.api.api_v1.endpoints.strategies.get_integration_service') as mock_service:
                with patch('app.crud.strategy.strategy_crud.create') as mock_create:
                    
                    mock_auth.return_value = mock_user
                    
                    # 模拟集成服务配置验证
                    mock_integration = Mock()
                    mock_integration._validate_strategy_config = AsyncMock(return_value={
                        "valid": True,
                        "errors": []
                    })
                    mock_service.return_value = mock_integration
                    
                    # 模拟策略创建
                    mock_strategy = Mock()
                    mock_strategy.id = 1
                    mock_strategy.name = strategy_data["name"]
                    mock_strategy.strategy_type = strategy_data["strategy_type"]
                    mock_create.return_value = mock_strategy
                    
                    async with AsyncClient(app=app, base_url="http://test") as client:
                        response = await client.post(
                            "/api/v1/strategies",
                            json=strategy_data,
                            headers=auth_headers
                        )
                    
                    assert response.status_code == 200
                    result = response.json()
                    assert result["name"] == strategy_data["name"]
                    assert result["strategy_type"] == strategy_data["strategy_type"]
    
    async def test_create_strategy_invalid_config(self, auth_headers, mock_user):
        """测试配置验证失败时的策略创建"""
        strategy_data = {
            "name": "无效策略",
            "strategy_type": "algorithmic_trading",
            "config": {
                "agent_type": "invalid_agent",
                "learning_rate": -0.001  # 无效学习率
            }
        }
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.api.api_v1.endpoints.strategies.get_integration_service') as mock_service:
                
                mock_auth.return_value = mock_user
                
                # 模拟配置验证失败
                mock_integration = Mock()
                mock_integration._validate_strategy_config = AsyncMock(return_value={
                    "valid": False,
                    "errors": ["Agent type 'invalid_agent' not supported", "Learning rate must be positive"]
                })
                mock_service.return_value = mock_integration
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategies",
                        json=strategy_data,
                        headers=auth_headers
                    )
                
                assert response.status_code == 400
                assert "配置验证失败" in response.json()["detail"]
    
    async def test_list_strategies_with_sessions(self, auth_headers, mock_user):
        """测试获取策略列表及其会话信息"""
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.crud.strategy.strategy_crud.get_multi') as mock_get_strategies:
                with patch('app.core.dependencies.get_pagination_params') as mock_pagination:
                    
                    mock_auth.return_value = mock_user
                    mock_pagination.return_value = Mock(skip=0, limit=50)
                    
                    # 模拟策略数据
                    mock_strategies = []
                    for i in range(3):
                        strategy = Mock()
                        strategy.id = i + 1
                        strategy.name = f"策略{i+1}"
                        strategy.strategy_type = "algorithmic_trading"
                        strategy.last_training_at = datetime.now() if i == 0 else None
                        mock_strategies.append(strategy)
                    
                    mock_get_strategies.return_value = mock_strategies
                    
                    with patch('app.core.database.get_database') as mock_db:
                        mock_session = AsyncMock()
                        
                        # 模拟会话查询结果
                        def mock_execute(query):
                            result = Mock()
                            if "StrategySession" in str(query):
                                if "func.count" in str(query):
                                    # 总会话数查询
                                    result.scalar.return_value = 2
                                else:
                                    # 活跃会话查询
                                    sessions = []
                                    if "strategy_id == 1" in str(query):  # 第一个策略有活跃会话
                                        session = Mock()
                                        session.id = 1
                                        session.session_type = SessionType.TRAINING
                                        session.status = SessionStatus.RUNNING
                                        session.progress = 45.5
                                        session.current_epoch = 45
                                        session.total_epochs = 100
                                        session.started_at = datetime.now()
                                        session.error_message = None
                                        sessions.append(session)
                                    result.scalars.return_value.all.return_value = sessions
                            return result
                        
                        mock_session.execute = mock_execute
                        mock_db.return_value.__aenter__.return_value = mock_session
                        
                        async with AsyncClient(app=app, base_url="http://test") as client:
                            response = await client.get(
                                "/api/v1/strategies",
                                headers=auth_headers
                            )
                        
                        assert response.status_code == 200
                        strategies = response.json()
                        assert len(strategies) == 3
                        
                        # 验证第一个策略有活跃会话
                        first_strategy = strategies[0]
                        assert len(first_strategy["active_sessions"]) == 1
                        assert first_strategy["active_sessions"][0]["status"] == "running"
                        assert first_strategy["total_sessions"] == 2
    
    async def test_start_training_success(self, auth_headers, mock_user):
        """测试成功启动策略训练"""
        training_request = {
            "dataset_name": "BTC",
            "agent_type": "dqn",
            "epochs": 50,
            "learning_rate": 0.001,
            "batch_size": 32,
            "parameters": {}
        }
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.api.api_v1.endpoints.strategies.get_integration_service') as mock_service:
                with patch('app.crud.strategy.strategy_crud.get') as mock_get_strategy:
                    
                    mock_auth.return_value = mock_user
                    
                    # 模拟策略存在
                    mock_strategy = Mock()
                    mock_strategy.id = 1
                    mock_strategy.owner_id = 1
                    mock_strategy.strategy_type = "algorithmic_trading"
                    mock_get_strategy.return_value = mock_strategy
                    
                    # 模拟集成服务
                    mock_integration = Mock()
                    mock_integration.create_training_session = AsyncMock(return_value=123)
                    mock_integration.start_training_task = AsyncMock(return_value="celery-task-123")
                    mock_integration.get_session_status = AsyncMock(return_value={
                        "session_id": 123,
                        "status": "running",
                        "progress": 0.0,
                        "current_epoch": 0,
                        "total_epochs": 50
                    })
                    mock_service.return_value = mock_integration
                    
                    with patch('app.core.database.get_database') as mock_db:
                        mock_session = AsyncMock()
                        # 模拟并发会话数查询
                        mock_session.execute.return_value.scalar.return_value = 1  # 当前1个会话
                        mock_db.return_value.__aenter__.return_value = mock_session
                        
                        async with AsyncClient(app=app, base_url="http://test") as client:
                            response = await client.post(
                                "/api/v1/strategies/1/train",
                                json=training_request,
                                headers=auth_headers
                            )
                        
                        assert response.status_code == 200
                        result = response.json()
                        assert result["session_id"] == 123
                        assert result["status"] == "running"
                        assert result["total_epochs"] == 50
    
    async def test_start_training_concurrent_limit(self, auth_headers, mock_user):
        """测试并发训练数量限制"""
        training_request = {
            "dataset_name": "BTC",
            "agent_type": "dqn",
            "epochs": 50
        }
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.crud.strategy.strategy_crud.get') as mock_get_strategy:
                
                mock_auth.return_value = mock_user
                
                # 模拟策略存在
                mock_strategy = Mock()
                mock_strategy.owner_id = 1
                mock_get_strategy.return_value = mock_strategy
                
                with patch('app.core.database.get_database') as mock_db:
                    mock_session = AsyncMock()
                    # 模拟已达到最大并发数
                    mock_session.execute.return_value.scalar.return_value = 3
                    mock_db.return_value.__aenter__.return_value = mock_session
                    
                    async with AsyncClient(app=app, base_url="http://test") as client:
                        response = await client.post(
                            "/api/v1/strategies/1/train",
                            json=training_request,
                            headers=auth_headers
                        )
                    
                    assert response.status_code == 429
                    assert "最大并发训练数量限制" in response.json()["detail"]
    
    async def test_start_backtest_success(self, auth_headers, mock_user):
        """测试成功启动策略回测"""
        backtest_request = {
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000,
            "benchmark": "SPY",
            "parameters": {}
        }
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.api.api_v1.endpoints.strategies.get_integration_service') as mock_service:
                with patch('app.crud.strategy.strategy_crud.get') as mock_get_strategy:
                    
                    mock_auth.return_value = mock_user
                    
                    # 模拟策略存在
                    mock_strategy = Mock()
                    mock_strategy.owner_id = 1
                    mock_get_strategy.return_value = mock_strategy
                    
                    # 模拟集成服务
                    mock_integration = Mock()
                    mock_integration.create_backtest_session = AsyncMock(return_value=456)
                    mock_integration.start_backtest_task = AsyncMock(return_value="celery-backtest-456")
                    mock_integration.get_session_status = AsyncMock(return_value={
                        "session_id": 456,
                        "status": "running",
                        "progress": 0.0
                    })
                    mock_service.return_value = mock_integration
                    
                    async with AsyncClient(app=app, base_url="http://test") as client:
                        response = await client.post(
                            "/api/v1/strategies/1/backtest",
                            json=backtest_request,
                            headers=auth_headers
                        )
                    
                    assert response.status_code == 200
                    result = response.json()
                    assert result["session_id"] == 456
                    assert result["status"] == "running"
    
    async def test_get_session_status(self, auth_headers, mock_user):
        """测试获取会话状态"""
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.api.api_v1.endpoints.strategies.get_integration_service') as mock_service:
                
                mock_auth.return_value = mock_user
                
                # 模拟会话存在且属于当前用户
                with patch('app.core.database.get_database') as mock_db:
                    mock_session = AsyncMock()
                    
                    # 模拟会话查询
                    strategy_session = Mock()
                    strategy_session.id = 123
                    strategy_session.strategy_id = 1
                    
                    strategy = Mock()
                    strategy.owner_id = 1
                    
                    mock_session.get.side_effect = lambda model, id: {
                        StrategySession: strategy_session,
                        Strategy: strategy
                    }.get(model)
                    
                    mock_db.return_value.__aenter__.return_value = mock_session
                    
                    # 模拟集成服务状态查询
                    mock_integration = Mock()
                    mock_integration.get_session_status = AsyncMock(return_value={
                        "session_id": 123,
                        "status": "running",
                        "progress": 65.5,
                        "current_epoch": 65,
                        "total_epochs": 100,
                        "recent_metrics": [
                            {"metric_name": "loss", "metric_value": 0.25, "epoch": 65}
                        ]
                    })
                    mock_service.return_value = mock_integration
                    
                    async with AsyncClient(app=app, base_url="http://test") as client:
                        response = await client.get(
                            "/api/v1/strategies/sessions/123/status",
                            headers=auth_headers
                        )
                    
                    assert response.status_code == 200
                    result = response.json()
                    assert result["session_id"] == 123
                    assert result["status"] == "running"
                    assert result["progress"] == 65.5
                    assert len(result["recent_metrics"]) == 1
    
    async def test_stop_session(self, auth_headers, mock_user):
        """测试停止会话"""
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.api.api_v1.endpoints.strategies.get_integration_service') as mock_service:
                
                mock_auth.return_value = mock_user
                
                # 模拟会话存在且属于当前用户
                with patch('app.core.database.get_database') as mock_db:
                    mock_session = AsyncMock()
                    
                    strategy_session = Mock()
                    strategy_session.strategy_id = 1
                    
                    strategy = Mock()
                    strategy.owner_id = 1
                    
                    mock_session.get.side_effect = lambda model, id: {
                        StrategySession: strategy_session,
                        Strategy: strategy
                    }.get(model)
                    
                    mock_db.return_value.__aenter__.return_value = mock_session
                    
                    # 模拟集成服务停止会话
                    mock_integration = Mock()
                    mock_integration.stop_session = AsyncMock(return_value={
                        "status": "stopped",
                        "message": "会话已停止"
                    })
                    mock_service.return_value = mock_integration
                    
                    async with AsyncClient(app=app, base_url="http://test") as client:
                        response = await client.post(
                            "/api/v1/strategies/sessions/123/stop",
                            headers=auth_headers
                        )
                    
                    assert response.status_code == 200
                    result = response.json()
                    assert result["status"] == "stopped"
    
    async def test_get_session_metrics(self, auth_headers, mock_user):
        """测试获取会话指标"""
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            
            mock_auth.return_value = mock_user
            
            # 模拟会话和权限验证
            with patch('app.core.database.get_database') as mock_db:
                mock_session = AsyncMock()
                
                # 模拟会话查询
                strategy_session = Mock()
                strategy_session.strategy_id = 1
                
                strategy = Mock()
                strategy.owner_id = 1
                
                mock_session.get.side_effect = lambda model, id: {
                    StrategySession: strategy_session,
                    Strategy: strategy
                }.get(model)
                
                # 模拟指标查询
                mock_metrics = []
                for i in range(5):
                    metric = Mock()
                    metric.metric_name = "loss" if i % 2 == 0 else "reward"
                    metric.metric_value = 0.5 - i * 0.05 if metric.metric_name == "loss" else 10 + i * 2
                    metric.epoch = i + 1
                    metric.step = (i + 1) * 100
                    metric.recorded_at = datetime.now() - timedelta(minutes=i)
                    mock_metrics.append(metric)
                
                mock_result = Mock()
                mock_result.scalars.return_value.all.return_value = mock_metrics
                mock_session.execute.return_value = mock_result
                
                mock_db.return_value.__aenter__.return_value = mock_session
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/strategies/sessions/123/metrics?limit=5",
                        headers=auth_headers
                    )
                
                assert response.status_code == 200
                result = response.json()
                assert result["session_id"] == 123
                assert "metrics" in result
                assert "loss" in result["metrics"]
                assert "reward" in result["metrics"]
                assert len(result["metrics"]["loss"]) >= 1
                assert len(result["metrics"]["reward"]) >= 1


class TestWebSocketAPI:
    """WebSocket API测试"""
    
    async def test_websocket_stats_admin_only(self):
        """测试WebSocket统计信息需要管理员权限"""
        # 模拟非管理员用户
        mock_user = {"id": 1, "is_superuser": False}
        
        with patch('app.api.api_v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            mock_auth.return_value = mock_user
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/ws/stats")
            
            assert response.status_code == 403
            assert "权限不足" in response.json()["detail"]
    
    async def test_websocket_stats_admin_success(self):
        """测试管理员成功获取WebSocket统计"""
        # 模拟管理员用户
        mock_user = {"id": 1, "is_superuser": True}
        
        with patch('app.api.api_v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            with patch('app.api.api_v1.endpoints.websocket.get_connection_manager') as mock_manager:
                
                mock_auth.return_value = mock_user
                
                # 模拟连接统计
                mock_conn_manager = Mock()
                mock_conn_manager.get_connection_stats = AsyncMock(return_value={
                    "total_connections": 25,
                    "total_users": 20,
                    "total_sessions": 10,
                    "connections_by_user": {1: 2, 2: 1},
                    "subscribers_by_session": {100: 3, 101: 2}
                })
                mock_manager.return_value = mock_conn_manager
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get("/api/v1/ws/stats")
                
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert result["data"]["total_connections"] == 25
                assert result["data"]["total_users"] == 20


class TestAPIPerformance:
    """API性能测试"""
    
    async def test_strategy_list_performance(self):
        """测试策略列表API性能"""
        auth_headers = {"Authorization": "Bearer test-token"}
        mock_user = {"id": 1, "is_active": True}
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.crud.strategy.strategy_crud.get_multi') as mock_get_strategies:
                with patch('app.core.dependencies.get_pagination_params') as mock_pagination:
                    
                    mock_auth.return_value = mock_user
                    mock_pagination.return_value = Mock(skip=0, limit=50)
                    
                    # 模拟大量策略
                    mock_strategies = []
                    for i in range(100):
                        strategy = Mock()
                        strategy.id = i + 1
                        strategy.name = f"策略{i+1}"
                        strategy.strategy_type = "algorithmic_trading"
                        strategy.last_training_at = None
                        mock_strategies.append(strategy)
                    
                    mock_get_strategies.return_value = mock_strategies
                    
                    with patch('app.core.database.get_database') as mock_db:
                        mock_session = AsyncMock()
                        
                        # 模拟快速数据库查询
                        def fast_execute(query):
                            result = Mock()
                            if "func.count" in str(query):
                                result.scalar.return_value = 0
                            else:
                                result.scalars.return_value.all.return_value = []
                            return result
                        
                        mock_session.execute = fast_execute
                        mock_db.return_value.__aenter__.return_value = mock_session
                        
                        # 性能测试
                        start_time = asyncio.get_event_loop().time()
                        
                        async with AsyncClient(app=app, base_url="http://test") as client:
                            response = await client.get(
                                "/api/v1/strategies",
                                headers=auth_headers
                            )
                        
                        end_time = asyncio.get_event_loop().time()
                        duration = end_time - start_time
                        
                        # 验证性能要求
                        assert response.status_code == 200
                        assert duration < 1.0  # API响应应该在1秒内
                        
                        strategies = response.json()
                        assert len(strategies) == 100
    
    async def test_concurrent_api_requests(self):
        """测试并发API请求性能"""
        auth_headers = {"Authorization": "Bearer test-token"}
        mock_user = {"id": 1, "is_active": True}
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.api.api_v1.endpoints.strategies.get_integration_service') as mock_service:
                
                mock_auth.return_value = mock_user
                
                # 模拟集成服务
                mock_integration = Mock()
                mock_integration.get_session_status = AsyncMock(return_value={
                    "session_id": 1,
                    "status": "running",
                    "progress": 50.0
                })
                mock_service.return_value = mock_integration
                
                # 模拟数据库查询
                with patch('app.core.database.get_database') as mock_db:
                    mock_session = AsyncMock()
                    
                    strategy_session = Mock()
                    strategy_session.strategy_id = 1
                    
                    strategy = Mock()
                    strategy.owner_id = 1
                    
                    mock_session.get.side_effect = lambda model, id: {
                        StrategySession: strategy_session,
                        Strategy: strategy
                    }.get(model)
                    
                    mock_db.return_value.__aenter__.return_value = mock_session
                    
                    # 并发请求测试
                    async with AsyncClient(app=app, base_url="http://test") as client:
                        tasks = []
                        for i in range(20):
                            task = client.get(
                                f"/api/v1/strategies/sessions/{i+1}/status",
                                headers=auth_headers
                            )
                            tasks.append(task)
                        
                        start_time = asyncio.get_event_loop().time()
                        responses = await asyncio.gather(*tasks, return_exceptions=True)
                        end_time = asyncio.get_event_loop().time()
                        
                        duration = end_time - start_time
                        
                        # 验证并发性能
                        assert duration < 2.0  # 20个并发请求应该在2秒内完成
                        
                        # 验证成功响应数量
                        successful_responses = [
                            r for r in responses 
                            if hasattr(r, 'status_code') and r.status_code == 200
                        ]
                        assert len(successful_responses) == 20


class TestAPIErrorHandling:
    """API错误处理测试"""
    
    async def test_authentication_required(self):
        """测试需要认证的API"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/strategies")
        
        assert response.status_code == 401
    
    async def test_invalid_strategy_id(self):
        """测试无效策略ID"""
        auth_headers = {"Authorization": "Bearer test-token"}
        mock_user = {"id": 1, "is_active": True}
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.crud.strategy.strategy_crud.get') as mock_get_strategy:
                
                mock_auth.return_value = mock_user
                mock_get_strategy.return_value = None  # 策略不存在
                
                training_request = {"dataset_name": "BTC", "agent_type": "dqn"}
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategies/999/train",
                        json=training_request,
                        headers=auth_headers
                    )
                
                assert response.status_code == 404
                assert "策略不存在" in response.json()["detail"]
    
    async def test_unauthorized_strategy_access(self):
        """测试未授权策略访问"""
        auth_headers = {"Authorization": "Bearer test-token"}
        mock_user = {"id": 1, "is_active": True}
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.crud.strategy.strategy_crud.get') as mock_get_strategy:
                
                mock_auth.return_value = mock_user
                
                # 模拟策略属于其他用户
                mock_strategy = Mock()
                mock_strategy.owner_id = 2  # 不同用户
                mock_get_strategy.return_value = mock_strategy
                
                training_request = {"dataset_name": "BTC", "agent_type": "dqn"}
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategies/1/train",
                        json=training_request,
                        headers=auth_headers
                    )
                
                assert response.status_code == 404
                assert "策略不存在" in response.json()["detail"]
    
    async def test_internal_server_error_handling(self):
        """测试内部服务器错误处理"""
        auth_headers = {"Authorization": "Bearer test-token"}
        mock_user = {"id": 1, "is_active": True}
        
        with patch('app.api.api_v1.endpoints.strategies.get_current_active_user') as mock_auth:
            with patch('app.crud.strategy.strategy_crud.get_multi') as mock_get_strategies:
                
                mock_auth.return_value = mock_user
                
                # 模拟数据库异常
                mock_get_strategies.side_effect = Exception("Database connection failed")
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/strategies",
                        headers=auth_headers
                    )
                
                assert response.status_code == 500
                assert "获取策略列表失败" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])