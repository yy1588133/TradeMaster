"""
设置管理API端点

提供用户设置、TradeMaster设置和系统设置的管理功能。
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_db,
    get_current_active_user,
    require_permission,
    CurrentUser,
    DatabaseSession
)
from app.core.security import Permission
from app.services.trademaster_integration import get_integration_service


router = APIRouter()


# ==================== 请求/响应模型 ====================

class UserSettingsResponse(BaseModel):
    """用户设置响应模型"""
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    language: str = Field(default="zh-CN", description="语言")
    theme: str = Field(default="light", description="主题")
    notifications_enabled: bool = Field(default=True, description="启用通知")
    email_notifications: bool = Field(default=False, description="邮件通知")


class UserSettingsUpdate(BaseModel):
    """用户设置更新模型"""
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    timezone: str = Field(..., description="时区")
    language: str = Field(..., description="语言")
    theme: str = Field(..., description="主题")
    notifications_enabled: bool = Field(..., description="启用通知")
    email_notifications: bool = Field(..., description="邮件通知")


class TradeMasterSettingsResponse(BaseModel):
    """TradeMaster设置响应模型"""
    api_endpoint: str = Field(default="http://localhost:8080/api", description="API端点")
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    max_concurrent_sessions: int = Field(default=5, description="最大并发会话数")
    default_initial_capital: float = Field(default=100000.0, description="默认初始资金")
    default_commission_rate: float = Field(default=0.001, description="默认手续费率")
    enable_gpu: bool = Field(default=False, description="启用GPU加速")
    log_level: str = Field(default="INFO", description="日志级别")


class TradeMasterSettingsUpdate(BaseModel):
    """TradeMaster设置更新模型"""
    api_endpoint: str = Field(..., description="API端点")
    timeout: int = Field(..., ge=1, le=3600, description="请求超时时间(秒)")
    max_concurrent_sessions: int = Field(..., ge=1, le=100, description="最大并发会话数")
    default_initial_capital: float = Field(..., ge=1000, description="默认初始资金")
    default_commission_rate: float = Field(..., ge=0, le=0.01, description="默认手续费率")
    enable_gpu: bool = Field(..., description="启用GPU加速")
    log_level: str = Field(..., description="日志级别")


class SystemSettingsResponse(BaseModel):
    """系统设置响应模型"""
    websocket_enabled: bool = Field(default=True, description="启用WebSocket")
    websocket_reconnect: bool = Field(default=True, description="自动重连")
    cache_enabled: bool = Field(default=True, description="启用缓存")
    session_timeout: int = Field(default=30, description="会话超时时间(分钟)")
    max_file_size: int = Field(default=50, description="最大文件大小(MB)")


class SystemSettingsUpdate(BaseModel):
    """系统设置更新模型"""
    websocket_enabled: bool = Field(..., description="启用WebSocket")
    websocket_reconnect: bool = Field(..., description="自动重连")
    cache_enabled: bool = Field(..., description="启用缓存")
    session_timeout: int = Field(..., ge=5, le=1440, description="会话超时时间(分钟)")
    max_file_size: int = Field(..., ge=1, le=1024, description="最大文件大小(MB)")


class TradeMasterTestResponse(BaseModel):
    """TradeMaster连接测试响应"""
    success: bool = Field(..., description="测试是否成功")
    error: str = Field(default="", description="错误信息")
    version: str = Field(default="", description="TradeMaster版本")
    available_strategies: int = Field(default=0, description="可用策略数量")


# ==================== API端点 ====================

@router.get("/users/settings", response_model=UserSettingsResponse, summary="获取用户设置")
async def get_user_settings(
    current_user: CurrentUser,
    db: DatabaseSession
) -> UserSettingsResponse:
    """获取当前用户的设置信息"""
    try:
        # 从用户信息获取设置，实际应该从专门的用户设置表获取
        user_data = current_user
        
        return UserSettingsResponse(
            username=user_data.get("username", ""),
            email=user_data.get("email", ""),
            timezone=user_data.get("timezone", "Asia/Shanghai"),
            language=user_data.get("language", "zh-CN"),
            theme=user_data.get("theme", "light"),
            notifications_enabled=user_data.get("notifications_enabled", True),
            email_notifications=user_data.get("email_notifications", False)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户设置失败: {str(e)}"
        )


@router.put("/users/settings", response_model=UserSettingsResponse, summary="更新用户设置")
async def update_user_settings(
    settings: UserSettingsUpdate,
    current_user: CurrentUser,
    db: DatabaseSession
) -> UserSettingsResponse:
    """更新当前用户的设置信息"""
    try:
        # TODO: 实际实现应该更新数据库中的用户设置
        # 这里只是返回更新后的设置作为示例
        
        return UserSettingsResponse(
            username=settings.username,
            email=settings.email,
            timezone=settings.timezone,
            language=settings.language,
            theme=settings.theme,
            notifications_enabled=settings.notifications_enabled,
            email_notifications=settings.email_notifications
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户设置失败: {str(e)}"
        )


@router.get("/settings/trademaster", response_model=TradeMasterSettingsResponse, summary="获取TradeMaster设置")
async def get_trademaster_settings(
    current_user: CurrentUser,
    db: DatabaseSession
) -> TradeMasterSettingsResponse:
    """获取TradeMaster集成设置"""
    try:
        # TODO: 实际实现应该从配置文件或数据库获取设置
        return TradeMasterSettingsResponse()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取TradeMaster设置失败: {str(e)}"
        )


@router.put("/settings/trademaster", response_model=TradeMasterSettingsResponse, summary="更新TradeMaster设置")
async def update_trademaster_settings(
    settings: TradeMasterSettingsUpdate,
    current_user: CurrentUser,
    db: DatabaseSession
) -> TradeMasterSettingsResponse:
    """更新TradeMaster集成设置"""
    try:
        # TODO: 实际实现应该更新配置文件或数据库
        
        return TradeMasterSettingsResponse(
            api_endpoint=settings.api_endpoint,
            timeout=settings.timeout,
            max_concurrent_sessions=settings.max_concurrent_sessions,
            default_initial_capital=settings.default_initial_capital,
            default_commission_rate=settings.default_commission_rate,
            enable_gpu=settings.enable_gpu,
            log_level=settings.log_level
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新TradeMaster设置失败: {str(e)}"
        )


@router.post("/settings/trademaster/test", response_model=TradeMasterTestResponse, summary="测试TradeMaster连接")
async def test_trademaster_connection(
    settings: TradeMasterSettingsUpdate,
    current_user: CurrentUser,
    db: DatabaseSession
) -> TradeMasterTestResponse:
    """测试TradeMaster服务连接"""
    try:
        integration_service = get_integration_service()
        
        # 测试连接
        test_result = await integration_service.test_connection(
            api_endpoint=settings.api_endpoint,
            timeout=settings.timeout
        )
        
        if test_result["success"]:
            return TradeMasterTestResponse(
                success=True,
                version=test_result.get("version", "unknown"),
                available_strategies=test_result.get("available_strategies", 0)
            )
        else:
            return TradeMasterTestResponse(
                success=False,
                error=test_result.get("error", "连接失败")
            )
        
    except Exception as e:
        return TradeMasterTestResponse(
            success=False,
            error=f"连接测试失败: {str(e)}"
        )


@router.get("/settings/system", response_model=SystemSettingsResponse, summary="获取系统设置")
async def get_system_settings(
    current_user: CurrentUser,
    db: DatabaseSession
) -> SystemSettingsResponse:
    """获取系统设置"""
    try:
        # TODO: 实际实现应该从配置文件或数据库获取系统设置
        return SystemSettingsResponse()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统设置失败: {str(e)}"
        )


@router.put(
    "/settings/system", 
    response_model=SystemSettingsResponse, 
    summary="更新系统设置",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))]
)
async def update_system_settings(
    settings: SystemSettingsUpdate,
    current_user: CurrentUser,
    db: DatabaseSession
) -> SystemSettingsResponse:
    """更新系统设置（需要管理员权限）"""
    try:
        # TODO: 实际实现应该更新配置文件或数据库，并可能需要重启某些服务
        
        return SystemSettingsResponse(
            websocket_enabled=settings.websocket_enabled,
            websocket_reconnect=settings.websocket_reconnect,
            cache_enabled=settings.cache_enabled,
            session_timeout=settings.session_timeout,
            max_file_size=settings.max_file_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新系统设置失败: {str(e)}"
        )