"""WebSocket服务 - 简化版本用于测试"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket

from loguru import logger


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, Dict[str, Any]] = {}
        self.user_connections: Dict[int, Set[str]] = {}
        self.session_subscriptions: Dict[int, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int) -> bool:
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            
            self.active_connections[connection_id] = websocket
            self.connection_info[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.now(),
                "last_activity": datetime.now()
            }
            
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            logger.info(f"用户 {user_id} 建立WebSocket连接: {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {str(e)}")
            return False
    
    async def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        try:
            # 清理连接记录
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            if connection_id in self.connection_info:
                user_id = self.connection_info[connection_id]["user_id"]
                del self.connection_info[connection_id]
                
                # 清理用户连接记录
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(connection_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
            
            # 清理会话订阅
            for session_id in list(self.session_subscriptions.keys()):
                self.session_subscriptions[session_id].discard(connection_id)
                if not self.session_subscriptions[session_id]:
                    del self.session_subscriptions[session_id]
            
            logger.info(f"断开WebSocket连接: {connection_id}")
            
        except Exception as e:
            logger.error(f"断开连接时发生错误: {str(e)}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """向指定连接发送消息"""
        try:
            websocket = self.active_connections.get(connection_id)
            if not websocket:
                return False
            
            # 更新最后活动时间
            if connection_id in self.connection_info:
                self.connection_info[connection_id]["last_activity"] = datetime.now()
            
            # 发送消息
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败: {connection_id}, {str(e)}")
            await self.disconnect(connection_id)
            return False
    
    async def push_training_progress(self, session_id: int, progress_data: Dict[str, Any]):
        """推送训练进度更新"""
        message = {
            "type": "training_progress",
            "session_id": session_id,
            "data": progress_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 向订阅该会话的连接推送消息
        connection_ids = self.session_subscriptions.get(session_id, set()).copy()
        for connection_id in connection_ids:
            await self.send_to_connection(connection_id, message)
    
    async def push_session_status_update(self, session_id: int, status_data: Dict[str, Any]):
        """推送会话状态更新"""
        message = {
            "type": "session_status_update", 
            "session_id": session_id,
            "data": status_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 向订阅该会话的连接推送消息
        connection_ids = self.session_subscriptions.get(session_id, set()).copy()
        for connection_id in connection_ids:
            await self.send_to_connection(connection_id, message)
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: int) -> int:
        """获取指定用户的连接数"""
        return len(self.user_connections.get(user_id, set()))


# 全局WebSocket管理器实例
_websocket_manager = None


def get_websocket_manager() -> WebSocketManager:
    """获取WebSocket管理器实例"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


async def get_connection_manager():
    """获取连接管理器（用于API调用）"""
    return get_websocket_manager()