"""
WebSocket API端点

提供WebSocket实时通信的API端点，支持会话订阅、实时数据推送等功能。
"""

import json
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from loguru import logger

from app.core.dependencies import get_current_active_user
from app.services.websocket_service import get_websocket_manager


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
    user_id: int = None
):
    """WebSocket连接端点
    
    建立WebSocket连接，支持实时数据推送。
    
    连接URL格式: ws://localhost:8000/api/v1/ws?token=<jwt_token>&user_id=<user_id>
    """
    ws_manager = get_websocket_manager()
    connection_id = None
    
    try:
        # 简化的用户验证（实际项目中应该验证JWT token）
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # 获取客户端IP
        client_ip = websocket.client.host if websocket.client else None
        
        # 建立连接
        connection_id = await ws_manager.connect(
            websocket=websocket,
            user_id=user_id,
            client_ip=client_ip
        )
        
        logger.info(f"WebSocket连接建立: user_id={user_id}, connection_id={connection_id}")
        
        # 处理客户端消息
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理不同类型的消息
                await handle_websocket_message(connection_id, message, ws_manager)
                
            except WebSocketDisconnect:
                logger.info(f"客户端主动断开连接: {connection_id}")
                break
            except json.JSONDecodeError:
                # 发送错误消息
                from datetime import datetime
                await ws_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "消息格式错误，必须是有效的JSON",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"处理WebSocket消息时发生错误: {str(e)}")
                from datetime import datetime
                await ws_manager.send_to_connection(connection_id, {
                    "type": "error", 
                    "message": f"处理消息时发生错误: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
    
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
    
    finally:
        # 断开连接
        if connection_id:
            await ws_manager.disconnect(connection_id)
            logger.info(f"WebSocket连接已断开: {connection_id}")


async def handle_websocket_message(
    connection_id: str, 
    message: Dict[str, Any], 
    ws_manager
):
    """处理WebSocket消息
    
    Args:
        connection_id: 连接ID
        message: 客户端消息
        ws_manager: WebSocket管理器
    """
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # 订阅会话更新
        session_id = message.get("session_id")
        if session_id:
            success = await ws_manager.subscribe_to_session(connection_id, session_id)
            if success:
                logger.info(f"连接 {connection_id} 成功订阅会话 {session_id}")
            else:
                logger.warning(f"连接 {connection_id} 订阅会话 {session_id} 失败")
        else:
            from datetime import datetime
            await ws_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": "缺少session_id参数",
                "timestamp": datetime.now().isoformat()
            })
    
    elif message_type == "unsubscribe":
        # 取消订阅会话
        session_id = message.get("session_id")
        if session_id:
            success = await ws_manager.unsubscribe_from_session(connection_id, session_id)
            if success:
                logger.info(f"连接 {connection_id} 成功取消订阅会话 {session_id}")
            else:
                logger.warning(f"连接 {connection_id} 取消订阅会话 {session_id} 失败")
        else:
            from datetime import datetime
            await ws_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": "缺少session_id参数",
                "timestamp": datetime.now().isoformat()
            })
    
    elif message_type == "ping":
        # 心跳消息
        from datetime import datetime
        await ws_manager.send_to_connection(connection_id, {
            "type": "pong",
            "message": "心跳响应",
            "timestamp": datetime.now().isoformat()
        })
    
    elif message_type == "get_status":
        # 获取连接状态
        from datetime import datetime
        await ws_manager.send_to_connection(connection_id, {
            "type": "connection_status",
            "connection_id": connection_id,
            "active_connections": ws_manager.get_connection_count(),
            "timestamp": datetime.now().isoformat()
        })
    
    else:
        # 未知消息类型
        from datetime import datetime
        await ws_manager.send_to_connection(connection_id, {
            "type": "error",
            "message": f"未知的消息类型: {message_type}",
            "timestamp": datetime.now().isoformat()
        })


@router.get("/connections/count")
async def get_connection_count(
    current_user: dict = Depends(get_current_active_user)
):
    """获取当前WebSocket连接统计
    
    需要管理员权限。
    """
    # 简化权限检查
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    ws_manager = get_websocket_manager()
    
    from datetime import datetime
    return {
        "total_connections": ws_manager.get_connection_count(),
        "user_connections": len(ws_manager.user_connections),
        "session_subscriptions": len(ws_manager.session_subscriptions),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/broadcast/{user_id}")
async def broadcast_to_user(
    user_id: int,
    message: Dict[str, Any],
    current_user: dict = Depends(get_current_active_user)
):
    """向指定用户广播消息
    
    需要管理员权限或者是用户本人。
    """
    # 权限检查
    if not current_user.get("is_superuser") and current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限向此用户发送消息"
        )
    
    ws_manager = get_websocket_manager()
    
    # 添加系统消息标识
    from datetime import datetime
    broadcast_message = {
        **message,
        "type": "system_broadcast",
        "timestamp": datetime.now().isoformat()
    }
    
    await ws_manager.broadcast_to_user(user_id, broadcast_message)
    
    connection_count = ws_manager.get_user_connection_count(user_id)
    
    from datetime import datetime
    return {
        "message": "消息已发送",
        "user_id": user_id,
        "connections_reached": connection_count,
        "timestamp": datetime.now().isoformat()
    }