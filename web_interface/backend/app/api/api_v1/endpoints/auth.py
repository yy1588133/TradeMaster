"""
认证API端点

提供用户认证相关的API接口，包括登录、注册、令牌刷新、
密码重置、用户信息查询等功能。
"""

import time
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import (
    get_db,
    get_current_user,
    get_current_active_user,
    CurrentUser,
    DatabaseSession
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    verify_token,
    verify_password,
    get_password_hash,
    validate_password_strength,
    TokenType,
    UserRole
)
from app.services.user_service import user_service
from app.schemas.user import UserResponse


router = APIRouter()


# ==================== CORS 预检处理 ====================

@router.options("/{path:path}")
async def handle_options(request: Request):
    """处理所有OPTIONS预检请求"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )


# ==================== 请求模型 ====================

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=1, description="密码")
    remember_me: bool = Field(default=False, description="记住登录状态")


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, description="密码")
    full_name: str = Field(None, max_length=100, description="全名")
    agree_terms: bool = Field(..., description="同意服务条款")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr = Field(..., description="邮箱地址")


class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, description="新密码")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str = Field(..., min_length=1, description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


# ==================== 响应模型 ====================

class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserResponseModel(BaseModel):
    """用户响应模型"""
    id: int = Field(..., description="用户ID")
    uuid: str = Field(..., description="用户UUID")  
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: str = Field(None, description="全名")
    role: UserRole = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证邮箱")
    created_at: str = Field(..., description="创建时间")
    last_login_at: str = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")


class LoginResponse(BaseModel):
    """登录响应模型"""
    user: UserResponseModel = Field(..., description="用户信息")
    tokens: TokenResponse = Field(..., description="令牌信息")
    message: str = Field(default="登录成功", description="响应消息")


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    # 优先从X-Forwarded-For头获取真实IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # 从X-Real-IP头获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 最后从客户端地址获取
    return request.client.host if request.client else "unknown"


def format_user_response(user) -> UserResponseModel:
    """格式化用户响应数据"""
    return UserResponseModel(
        id=user.id,
        uuid=user.uuid,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        login_count=user.login_count or 0
    )


# ==================== API端点 ====================

@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: DatabaseSession
) -> LoginResponse:
    """用户登录
    
    支持用户名或邮箱登录，验证成功后返回访问令牌和刷新令牌。
    """
    from app.core.security_middleware import login_tracker
    
    # 获取客户端信息
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    # 检查是否被锁定
    is_locked = await login_tracker.is_locked(login_data.username, ip_address)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="账户已被暂时锁定，请稍后重试"
        )
    
    try:
        # 调用用户服务进行认证
        user, token_data = await user_service.authenticate_user(
            db,
            username=login_data.username,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=login_data.remember_me
        )
        
        # 记录成功登录
        await login_tracker.record_successful_login(login_data.username, ip_address)
        
        # 格式化响应数据
        user_info = format_user_response(user)
        token_info = TokenResponse(**token_data)
        
        return LoginResponse(
            user=user_info,
            tokens=token_info,
            message="登录成功"
        )
        
    except HTTPException as e:
        # 记录失败尝试
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            await login_tracker.record_failed_login(login_data.username, ip_address)
        raise


@router.post("/register", response_model=UserResponseModel, summary="用户注册")
async def register(
    register_data: RegisterRequest,
    db: DatabaseSession
) -> UserResponseModel:
    """用户注册
    
    创建新用户账户，验证用户名和邮箱的唯一性。
    """
    # 验证用户是否同意服务条款
    if not register_data.agree_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须同意服务条款才能注册"
        )
    
    # 调用用户服务进行注册
    user = await user_service.register_user(
        db,
        username=register_data.username,
        email=register_data.email,
        password=register_data.password,
        full_name=register_data.full_name,
        auto_verify=False  # 默认需要邮箱验证
    )
    
    return format_user_response(user)


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: DatabaseSession
) -> TokenResponse:
    """刷新访问令牌
    
    使用刷新令牌获取新的访问令牌。
    """
    user, token_data = await user_service.refresh_user_token(
        db,
        refresh_token=refresh_data.refresh_token
    )
    
    return TokenResponse(**token_data)


@router.post("/logout", summary="用户登出")
async def logout(
    request: Request,
    current_user: CurrentUser,
    db: DatabaseSession,
    all_devices: bool = Body(default=False, embed=True)
) -> Dict[str, Any]:
    """用户登出
    
    撤销当前用户的令牌。可选择登出所有设备。
    """
    # 从Authorization头获取当前session token
    auth_header = request.headers.get("Authorization", "")
    session_token = None
    if auth_header.startswith("Bearer "):
        session_token = auth_header[7:]
    
    # 调用用户服务进行登出
    success = await user_service.logout_user(
        db,
        session_token=session_token,
        user_id=int(current_user["id"]),
        all_devices=all_devices
    )
    
    if success:
        return {
            "message": "登出成功",
            "timestamp": int(time.time())
        }
    else:
        return {
            "message": "登出处理完成",
            "timestamp": int(time.time())
        }


@router.get("/me", response_model=UserResponseModel, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: CurrentUser,
    db: DatabaseSession
) -> UserResponseModel:
    """获取当前用户信息
    
    返回当前登录用户的详细信息。
    """
    user = await user_service.get_user_profile(
        db,
        user_id=int(current_user["id"])
    )
    
    return format_user_response(user)


@router.put("/me", response_model=UserResponseModel, summary="更新用户信息")
async def update_user_info(
    current_user: CurrentUser,
    db: DatabaseSession,
    user_update: Dict[str, Any] = Body(...)
) -> UserResponseModel:
    """更新用户信息
    
    允许用户更新自己的基本信息（用户名、邮箱、全名等）。
    """
    # 过滤允许更新的字段
    allowed_fields = {"username", "email", "full_name", "avatar_url"}
    update_data = {k: v for k, v in user_update.items() if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有提供有效的更新字段"
        )
    
    # 调用用户服务更新信息
    user = await user_service.update_user_profile(
        db,
        user_id=int(current_user["id"]),
        update_data=update_data
    )
    
    return format_user_response(user)


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DatabaseSession
) -> Dict[str, Any]:
    """修改密码
    
    用户修改自己的密码，需要验证当前密码。
    """
    # 调用用户服务修改密码
    await user_service.change_user_password(
        db,
        user_id=int(current_user["id"]),
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    return {
        "message": "密码修改成功，请重新登录",
        "timestamp": int(time.time())
    }


@router.post("/forgot-password", summary="忘记密码")
async def forgot_password(
    reset_data: PasswordResetRequest,
    db: DatabaseSession
) -> Dict[str, Any]:
    """忘记密码
    
    发送密码重置邮件到用户邮箱。
    """
    # 检查邮箱是否存在（不暴露用户是否存在的信息）
    from app.crud.user import user_crud
    user = await user_crud.get_by_email(db, email=reset_data.email)
    
    if user:
        # 生成密码重置令牌
        reset_token = create_password_reset_token(reset_data.email)
        
        # TODO: 发送重置邮件
        # await send_password_reset_email(reset_data.email, reset_token)
        pass
    
    # 无论邮箱是否存在，都返回相同的消息（安全考虑）
    return {
        "message": "如果该邮箱已注册，您将收到密码重置邮件",
        "timestamp": int(time.time())
    }


@router.post("/reset-password", summary="重置密码")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: DatabaseSession
) -> Dict[str, Any]:
    """重置密码
    
    使用重置令牌设置新密码。
    """
    try:
        # 验证重置令牌
        payload = verify_token(reset_data.token, TokenType.RESET_PASSWORD)
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的重置令牌"
            )
        
        # 调用用户服务重置密码
        await user_service.reset_user_password(
            db,
            email=email,
            new_password=reset_data.new_password,
            reset_token=reset_data.token
        )
        
        return {
            "message": "密码重置成功，请使用新密码登录",
            "timestamp": int(time.time())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"密码重置失败: {str(e)}"
        )


@router.post("/verify-token", summary="验证令牌")
async def verify_access_token(
    token: str = Body(..., embed=True)
) -> Dict[str, Any]:
    """验证访问令牌
    
    检查令牌的有效性，返回令牌信息。
    """
    try:
        payload = verify_token(token, TokenType.ACCESS)
        
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "expires_at": payload.get("exp"),
            "issued_at": payload.get("iat"),
            "token_id": payload.get("jti")
        }
        
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail
        }


# ==================== 管理员端点 ====================

@router.get("/users", summary="获取用户列表")
async def get_user_list(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
    search: str = None,
    role: UserRole = None,
    is_active: bool = None
) -> Dict[str, Any]:
    """获取用户列表（管理员功能）"""
    # 检查管理员权限
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要管理员权限"
        )
    
    users, total = await user_service.get_user_list(
        db,
        skip=skip,
        limit=limit,
        search=search,
        role=role,
        is_active=is_active
    )
    
    return {
        "users": [format_user_response(user) for user in users],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats", summary="获取用户统计信息")
async def get_user_stats(
    db: DatabaseSession,
    current_user: CurrentUser
) -> Dict[str, Any]:
    """获取用户统计信息（管理员功能）"""
    # 检查管理员权限
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要管理员权限"
        )
    
    return await user_service.get_user_statistics(db)