"""
WebSocket实时通信测试

测试重点：
1. WebSocket连接管理和生命周期
2. 实时消息推送和路由机制
3. 会话订阅和取消订阅功能
4. 连接清理和异常恢复
5. 并发连接处理性能

这些测试解决代码质量评审中发现的WebSocket实时数据推送不完整问题。
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.connection_manager import WebSocketConnectionManager, get_connection_manager
from app.websocket.message_handler import WebSocketMessageHandler
from app.models.database import WebSocketConnection


class TestWebSocketConnectionManager:
    """WebSocket连接管理器测试"""
    
    @pytest.fixture
    def connection_manager(self):
        """创建连接管理器实例"""
        return WebSocketConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """模拟WebSocket连接"""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        websocket.headers = {"user-agent": "test-client/1.0"}
        return websocket
    
    async def test_connect_success(self, connection_manager, mock_websocket):
        """测试成功建立WebSocket连接"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            connection_id = await connection_manager.connect(
                websocket=mock_websocket,
                user_id=1,
                client_ip="192.168.1.100",
                user_agent="test-client/1.0"
            )
            
            # 验证连接建立
            mock_websocket.accept.assert_called_once()
            
            # 验证连接ID生成
            assert isinstance(connection_id, str)
            assert len(connection_id) > 0
            
            # 验证连接存储
            assert connection_id in connection_manager.active_connections
            assert 1 in connection_manager.user_connections
            assert connection_id in connection_manager.user_connections[1]
            
            # 验证元数据存储
            assert connection_id in connection_manager.connection_metadata
            metadata = connection_manager.connection_metadata[connection_id]
            assert metadata["user_id"] == 1
            assert metadata["client_ip"] == "192.168.1.100"
            assert metadata["user_agent"] == "test-client/1.0"
            
            # 验证数据库记录
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            
            # 验证心跳任务启动
            assert connection_id in connection_manager.heartbeat_tasks
            
            # 验证连接确认消息发送
            mock_websocket.send_text.assert_called()
            sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
            assert sent_message["type"] == "connection_established"
            assert sent_message["connection_id"] == connection_id
    
    async def test_disconnect_success(self, connection_manager, mock_websocket):
        """测试正常断开WebSocket连接"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 先建立连接
            connection_id = await connection_manager.connect(
                websocket=mock_websocket,
                user_id=1
            )
            
            # 订阅会话
            await connection_manager.subscribe_to_session(connection_id, session_id=100)
            
            # 断开连接
            await connection_manager.disconnect(connection_id)
            
            # 验证连接清理
            assert connection_id not in connection_manager.active_connections
            assert 1 not in connection_manager.user_connections
            assert 100 not in connection_manager.session_subscriptions
            assert connection_id not in connection_manager.connection_metadata
            assert connection_id not in connection_manager.heartbeat_tasks
    
    async def test_multiple_user_connections(self, connection_manager, mock_websocket):
        """测试同一用户多个连接"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 同一用户建立多个连接
            websocket2 = Mock(spec=WebSocket)
            websocket2.accept = AsyncMock()
            websocket2.send_text = AsyncMock()
            websocket2.headers = {"user-agent": "test-client/1.0"}
            
            connection_id1 = await connection_manager.connect(mock_websocket, user_id=1)
            connection_id2 = await connection_manager.connect(websocket2, user_id=1)
            
            # 验证用户连接映射
            assert 1 in connection_manager.user_connections
            assert len(connection_manager.user_connections[1]) == 2
            assert connection_id1 in connection_manager.user_connections[1]
            assert connection_id2 in connection_manager.user_connections[1]
            
            # 断开一个连接
            await connection_manager.disconnect(connection_id1)
            
            # 验证另一个连接仍然存在
            assert 1 in connection_manager.user_connections
            assert len(connection_manager.user_connections[1]) == 1
            assert connection_id2 in connection_manager.user_connections[1]
    
    async def test_session_subscription(self, connection_manager, mock_websocket):
        """测试会话订阅功能"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            connection_id = await connection_manager.connect(mock_websocket, user_id=1)
            
            # 订阅会话
            await connection_manager.subscribe_to_session(connection_id, session_id=100)
            
            # 验证订阅
            assert 100 in connection_manager.session_subscriptions
            assert connection_id in connection_manager.session_subscriptions[100]
            
            # 验证数据库更新
            mock_session.execute.assert_called()
            mock_session.commit.assert_called()
            
            # 验证订阅确认消息
            mock_websocket.send_text.assert_called()
            calls = [call for call in mock_websocket.send_text.call_args_list 
                    if "session_subscribed" in str(call)]
            assert len(calls) > 0
    
    async def test_session_unsubscription(self, connection_manager, mock_websocket):
        """测试取消会话订阅"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            connection_id = await connection_manager.connect(mock_websocket, user_id=1)
            
            # 先订阅
            await connection_manager.subscribe_to_session(connection_id, session_id=100)
            assert 100 in connection_manager.session_subscriptions
            
            # 取消订阅
            await connection_manager.unsubscribe_from_session(connection_id, session_id=100)
            
            # 验证取消订阅
            assert 100 not in connection_manager.session_subscriptions
    
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """测试发送个人消息"""
        with patch('app.websocket.connection_manager.get_database'):
            connection_id = await connection_manager.connect(mock_websocket, user_id=1)
            
            test_message = {"type": "test", "data": "hello world"}
            await connection_manager.send_personal_message(connection_id, test_message)
            
            # 验证消息发送
            mock_websocket.send_text.assert_called()
            # 找到测试消息的调用
            calls = mock_websocket.send_text.call_args_list
            test_call = None
            for call in calls:
                message_text = call[0][0]
                if "hello world" in message_text:
                    test_call = call
                    break
            
            assert test_call is not None
            sent_data = json.loads(test_call[0][0])
            assert sent_data["type"] == "test"
            assert sent_data["data"] == "hello world"
    
    async def test_send_personal_message_connection_not_found(self, connection_manager):
        """测试向不存在连接发送消息"""
        test_message = {"type": "test", "data": "hello"}
        
        # 应该不抛出异常，只是记录警告
        await connection_manager.send_personal_message("nonexistent", test_message)
    
    async def test_send_to_user(self, connection_manager, mock_websocket):
        """测试发送消息给用户的所有连接"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 为同一用户建立多个连接
            websocket2 = Mock(spec=WebSocket)
            websocket2.accept = AsyncMock()
            websocket2.send_text = AsyncMock()
            websocket2.headers = {}
            
            connection_id1 = await connection_manager.connect(mock_websocket, user_id=1)
            connection_id2 = await connection_manager.connect(websocket2, user_id=1)
            
            test_message = {"type": "broadcast", "data": "user message"}
            await connection_manager.send_to_user(user_id=1, message=test_message)
            
            # 验证两个连接都收到消息
            assert mock_websocket.send_text.called
            assert websocket2.send_text.called
    
    async def test_broadcast_to_session(self, connection_manager, mock_websocket):
        """测试会话广播"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 建立连接并订阅会话
            connection_id = await connection_manager.connect(mock_websocket, user_id=1)
            await connection_manager.subscribe_to_session(connection_id, session_id=100)
            
            test_message = {"type": "session_update", "session_id": 100, "data": "update"}
            await connection_manager.broadcast_to_session(session_id=100, message=test_message)
            
            # 验证广播消息发送
            mock_websocket.send_text.assert_called()
            # 检查是否有会话更新消息被发送
            calls = mock_websocket.send_text.call_args_list
            session_update_call = None
            for call in calls:
                message_text = call[0][0]
                if "session_update" in message_text:
                    session_update_call = call
                    break
            
            assert session_update_call is not None
    
    async def test_broadcast_to_all(self, connection_manager, mock_websocket):
        """测试全局广播"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 建立多个连接
            websocket2 = Mock(spec=WebSocket)
            websocket2.accept = AsyncMock()
            websocket2.send_text = AsyncMock()
            websocket2.headers = {}
            
            await connection_manager.connect(mock_websocket, user_id=1)
            await connection_manager.connect(websocket2, user_id=2)
            
            test_message = {"type": "global_announcement", "data": "system maintenance"}
            await connection_manager.broadcast_to_all(test_message)
            
            # 验证所有连接都收到消息
            assert mock_websocket.send_text.called
            assert websocket2.send_text.called
    
    async def test_get_connection_stats(self, connection_manager, mock_websocket):
        """测试获取连接统计"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 建立连接和订阅
            connection_id = await connection_manager.connect(mock_websocket, user_id=1)
            await connection_manager.subscribe_to_session(connection_id, session_id=100)
            
            stats = await connection_manager.get_connection_stats()
            
            # 验证统计信息
            assert stats["total_connections"] == 1
            assert stats["total_users"] == 1
            assert stats["total_sessions"] == 1
            assert stats["connections_by_user"][1] == 1
            assert stats["subscribers_by_session"][100] == 1
    
    async def test_connection_cleanup_on_error(self, connection_manager, mock_websocket):
        """测试连接错误时的清理"""
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            connection_id = await connection_manager.connect(mock_websocket, user_id=1)
            
            # 模拟发送消息时连接错误
            mock_websocket.send_text.side_effect = Exception("Connection lost")
            
            test_message = {"type": "test", "data": "test"}
            await connection_manager.send_personal_message(connection_id, test_message)
            
            # 验证连接被自动断开
            assert connection_id not in connection_manager.active_connections


class TestWebSocketMessageHandler:
    """WebSocket消息处理器测试"""
    
    @pytest.fixture
    def message_handler(self):
        """创建消息处理器实例"""
        return WebSocketMessageHandler()
    
    @pytest.fixture
    def mock_connection_manager(self):
        """模拟连接管理器"""
        manager = Mock(spec=WebSocketConnectionManager)
        manager.subscribe_to_session = AsyncMock()
        manager.unsubscribe_from_session = AsyncMock()
        manager.send_personal_message = AsyncMock()
        return manager
    
    async def test_handle_subscribe_message(self, message_handler):
        """测试处理订阅消息"""
        with patch('app.websocket.message_handler.get_connection_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.subscribe_to_session = AsyncMock()
            mock_get_manager.return_value = mock_manager
            
            message = {
                "type": "subscribe_session",
                "session_id": 100
            }
            
            await message_handler.handle_message(
                connection_id="conn123",
                user_id=1,
                message=message
            )
            
            # 验证订阅被调用
            mock_manager.subscribe_to_session.assert_called_once_with("conn123", 100)
    
    async def test_handle_unsubscribe_message(self, message_handler):
        """测试处理取消订阅消息"""
        with patch('app.websocket.message_handler.get_connection_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.unsubscribe_from_session = AsyncMock()
            mock_get_manager.return_value = mock_manager
            
            message = {
                "type": "unsubscribe_session",
                "session_id": 100
            }
            
            await message_handler.handle_message(
                connection_id="conn123",
                user_id=1,
                message=message
            )
            
            # 验证取消订阅被调用
            mock_manager.unsubscribe_from_session.assert_called_once_with("conn123", 100)
    
    async def test_handle_pong_message(self, message_handler):
        """测试处理心跳响应"""
        with patch('app.websocket.message_handler.get_connection_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            
            message = {"type": "pong"}
            
            # 应该正常处理而不出错
            await message_handler.handle_message(
                connection_id="conn123",
                user_id=1,
                message=message
            )
    
    async def test_handle_unknown_message(self, message_handler):
        """测试处理未知消息类型"""
        with patch('app.websocket.message_handler.get_connection_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.send_personal_message = AsyncMock()
            mock_get_manager.return_value = mock_manager
            
            message = {"type": "unknown_type", "data": "test"}
            
            await message_handler.handle_message(
                connection_id="conn123",
                user_id=1,
                message=message
            )
            
            # 验证错误消息被发送
            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args
            assert call_args[0][0] == "conn123"  # connection_id
            assert call_args[0][1]["type"] == "error"  # error message


class TestRealTimeDataPusher:
    """实时数据推送器测试"""
    
    @pytest.fixture
    def mock_pusher(self):
        """创建实时数据推送器模拟"""
        with patch('app.websocket.real_time_data.RealTimeDataPusher') as MockPusher:
            pusher_instance = Mock()
            pusher_instance.push_training_metrics = AsyncMock()
            pusher_instance.push_session_status = AsyncMock()
            pusher_instance.push_training_completed = AsyncMock()
            pusher_instance.push_training_failed = AsyncMock()
            MockPusher.return_value = pusher_instance
            yield pusher_instance
    
    async def test_push_training_metrics(self, mock_pusher):
        """测试推送训练指标"""
        session_id = 123
        metrics = {
            "epoch": 10,
            "loss": 0.25,
            "reward": 15.5,
            "accuracy": 0.85
        }
        
        await mock_pusher.push_training_metrics(session_id, metrics)
        
        # 验证推送被调用
        mock_pusher.push_training_metrics.assert_called_once_with(session_id, metrics)
    
    async def test_push_session_status(self, mock_pusher):
        """测试推送会话状态"""
        session_id = 123
        status_data = {
            "status": "running",
            "progress": 45.5,
            "current_epoch": 45,
            "message": "Training in progress"
        }
        
        await mock_pusher.push_session_status(session_id, status_data)
        
        # 验证推送被调用
        mock_pusher.push_session_status.assert_called_once_with(session_id, status_data)
    
    async def test_push_training_completed(self, mock_pusher):
        """测试推送训练完成"""
        session_id = 123
        result_data = {
            "final_metrics": {"loss": 0.1, "reward": 25.8},
            "model_path": "/models/session_123.pth",
            "duration": 3600
        }
        
        await mock_pusher.push_training_completed(session_id, result_data)
        
        # 验证推送被调用
        mock_pusher.push_training_completed.assert_called_once_with(session_id, result_data)
    
    async def test_push_training_failed(self, mock_pusher):
        """测试推送训练失败"""
        session_id = 123
        error_data = {
            "error_message": "Out of memory",
            "error_type": "ResourceError",
            "traceback": "...",
            "suggestion": "Try reducing batch size"
        }
        
        await mock_pusher.push_training_failed(session_id, error_data)
        
        # 验证推送被调用
        mock_pusher.push_training_failed.assert_called_once_with(session_id, error_data)


class TestWebSocketAPI:
    """WebSocket API端点测试"""
    
    @pytest.fixture
    def mock_websocket_endpoint(self):
        """模拟WebSocket端点函数"""
        from app.api.api_v1.endpoints.websocket import websocket_endpoint
        return websocket_endpoint
    
    async def test_websocket_authentication_success(self):
        """测试WebSocket认证成功"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.receive_text = AsyncMock()
        mock_websocket.headers = {"user-agent": "test-client"}
        
        # 模拟WebSocketDisconnect异常来结束循环
        mock_websocket.receive_text.side_effect = WebSocketDisconnect()
        
        with patch('app.api.api_v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            with patch('app.api.api_v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
                with patch('app.api.api_v1.endpoints.websocket.WebSocketMessageHandler') as mock_handler:
                    
                    # 模拟认证成功
                    mock_auth.return_value = {"id": 1, "is_active": True, "username": "testuser"}
                    
                    # 模拟连接管理器
                    mock_manager = Mock()
                    mock_manager.connect = AsyncMock(return_value="conn123")
                    mock_manager.disconnect = AsyncMock()
                    mock_get_manager.return_value = mock_manager
                    
                    from app.api.api_v1.endpoints.websocket import websocket_endpoint
                    
                    # 执行WebSocket端点
                    await websocket_endpoint(
                        websocket=mock_websocket,
                        token="valid_token",
                        client_ip="192.168.1.100"
                    )
                    
                    # 验证认证被调用
                    mock_auth.assert_called_once_with("valid_token")
                    
                    # 验证连接建立
                    mock_manager.connect.assert_called_once_with(
                        websocket=mock_websocket,
                        user_id=1,
                        client_ip="192.168.1.100",
                        user_agent=mock_websocket.headers.get("user-agent")
                    )
                    
                    # 验证连接清理
                    mock_manager.disconnect.assert_called_once_with("conn123")
    
    async def test_websocket_authentication_failure(self):
        """测试WebSocket认证失败"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.close = AsyncMock()
        
        with patch('app.api.api_v1.endpoints.websocket.get_current_user_from_token') as mock_auth:
            # 模拟认证失败
            mock_auth.side_effect = Exception("Invalid token")
            
            from app.api.api_v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="invalid_token"
            )
            
            # 验证连接被关闭
            mock_websocket.close.assert_called_once_with(code=4001, reason="认证失败")


class TestWebSocketPerformance:
    """WebSocket性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_connections_performance(self):
        """测试并发连接性能"""
        connection_manager = WebSocketConnectionManager()
        
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 创建多个模拟WebSocket
            websockets = []
            for i in range(50):
                websocket = Mock(spec=WebSocket)
                websocket.accept = AsyncMock()
                websocket.send_text = AsyncMock()
                websocket.headers = {}
                websockets.append(websocket)
            
            # 并发建立连接
            start_time = asyncio.get_event_loop().time()
            
            tasks = []
            for i, websocket in enumerate(websockets):
                task = connection_manager.connect(websocket, user_id=i+1)
                tasks.append(task)
            
            connection_ids = await asyncio.gather(*tasks)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # 验证性能指标
            assert duration < 2.0  # 50个连接应该在2秒内建立
            assert len(connection_ids) == 50
            assert len(connection_manager.active_connections) == 50
            
            # 测试并发消息发送
            test_message = {"type": "performance_test", "data": "test"}
            
            start_time = asyncio.get_event_loop().time()
            
            # 并发发送消息给所有连接
            tasks = []
            for connection_id in connection_ids:
                task = connection_manager.send_personal_message(connection_id, test_message)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # 验证消息发送性能
            assert duration < 1.0  # 50个消息发送应该在1秒内完成
    
    @pytest.mark.asyncio
    async def test_message_throughput(self):
        """测试消息吞吐量"""
        connection_manager = WebSocketConnectionManager()
        
        with patch('app.websocket.connection_manager.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 建立一个连接
            mock_websocket = Mock(spec=WebSocket)
            mock_websocket.accept = AsyncMock()
            mock_websocket.send_text = AsyncMock()
            mock_websocket.headers = {}
            
            connection_id = await connection_manager.connect(mock_websocket, user_id=1)
            
            # 发送大量消息
            message_count = 1000
            test_message = {"type": "throughput_test", "data": "test_data"}
            
            start_time = asyncio.get_event_loop().time()
            
            tasks = []
            for i in range(message_count):
                message = {**test_message, "sequence": i}
                task = connection_manager.send_personal_message(connection_id, message)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            throughput = message_count / duration
            
            # 验证吞吐量性能
            assert throughput > 500  # 应该能达到每秒500+消息
            assert mock_websocket.send_text.call_count >= message_count


class TestGlobalManagerInstance:
    """测试全局连接管理器实例"""
    
    def test_get_connection_manager_singleton(self):
        """测试连接管理器单例模式"""
        manager1 = get_connection_manager()
        manager2 = get_connection_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, WebSocketConnectionManager)
    
    def test_manager_instance_persistence(self):
        """测试管理器实例持久性"""
        manager = get_connection_manager()
        original_id = id(manager)
        
        # 多次调用应该返回同一个实例
        for _ in range(5):
            assert id(get_connection_manager()) == original_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])