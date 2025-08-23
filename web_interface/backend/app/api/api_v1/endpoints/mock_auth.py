"""
模拟认证API端点 - 无需数据库依赖
用于开发和测试环境
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import hashlib
import time
from datetime import datetime, timedelta

router = APIRouter()

# 模拟用户数据存储（内存中）
mock_users_db = {}
mock_sessions = {}

def hash_password(password: str) -> str:
    """简单的密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password

def create_access_token(user_data: Dict[str, Any]) -> str:
    """创建访问令牌"""
    token = hashlib.md5(f"{user_data['username']}{time.time()}".encode()).hexdigest()
    mock_sessions[token] = {
        "user": user_data,
        "expires_at": datetime.now() + timedelta(hours=1)
    }
    return token

def get_current_user(token: str) -> Dict[str, Any]:
    """根据令牌获取当前用户"""
    if token not in mock_sessions:
        raise HTTPException(status_code=401, detail="令牌无效")
    
    session = mock_sessions[token]
    if datetime.now() > session["expires_at"]:
        del mock_sessions[token]
        raise HTTPException(status_code=401, detail="令牌已过期")
    
    return session["user"]

@router.post("/register")
async def register():
    """用户注册"""
    return {
        "message": "注册成功",
        "user": {
            "id": "mock_user_" + str(int(time.time())),
            "username": "test_user",
            "email": "test@example.com",
            "role": "user",
            "created_at": datetime.now().isoformat()
        },
        "access_token": create_access_token({
            "id": "mock_user_" + str(int(time.time())),
            "username": "test_user",
            "email": "test@example.com",
            "role": "user"
        }),
        "token_type": "bearer"
    }

@router.post("/login")
async def login():
    """用户登录"""
    user_data = {
        "id": "mock_user_1",
        "uuid": "mock-uuid-123",
        "username": "demo_user",
        "email": "demo@example.com",
        "full_name": "Demo User",
        "role": "admin",
        "is_active": True,
        "is_verified": True,
        "created_at": "2023-01-01T00:00:00Z",
        "last_login_at": datetime.now().isoformat() + "Z",
        "login_count": 1
    }
    
    access_token = create_access_token(user_data)
    
    return {
        "user": user_data,
        "tokens": {
            "access_token": access_token,
            "refresh_token": "mock_refresh_token_" + str(int(time.time())),
            "token_type": "bearer",
            "expires_in": 3600
        },
        "message": "登录成功"
    }

@router.get("/me")
async def get_current_user_info():
    """获取当前用户信息"""
    return {
        "id": "mock_user_1",
        "username": "demo_user",
        "email": "demo@example.com",
        "role": "admin",
        "full_name": "Demo User",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00",
        "last_login": datetime.now().isoformat()
    }

@router.post("/logout")
async def logout():
    """用户退出"""
    return {
        "message": "退出成功"
    }

@router.post("/refresh")
async def refresh_token():
    """刷新令牌"""
    user_data = {
        "id": "mock_user_1",
        "username": "demo_user",
        "email": "demo@example.com",
        "role": "admin"
    }
    
    return {
        "access_token": create_access_token(user_data),
        "refresh_token": "mock_refresh_token_" + str(int(time.time())),
        "token_type": "bearer",
        "expires_in": 3600
    }

@router.post("/forgot-password")
async def forgot_password():
    """忘记密码"""
    return {
        "message": "密码重置邮件已发送",
        "reset_token": "mock_reset_token_" + str(int(time.time())),
        "expires_in": 3600
    }

@router.post("/reset-password")
async def reset_password():
    """重置密码"""
    return {
        "message": "密码重置成功"
    }

@router.post("/change-password")
async def change_password():
    """修改密码"""
    return {
        "message": "密码修改成功"
    }

@router.post("/verify-token")
async def verify_token():
    """验证令牌"""
    return {
        "valid": True,
        "user": {
            "id": "mock_user_1",
            "username": "demo_user",
            "role": "admin"
        },
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
    }