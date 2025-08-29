"""
用户相关的Pydantic模式定义

提供用户管理相关的数据验证和序列化模式，包括用户注册、登录、
个人资料管理等功能的API数据模式。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from email_validator import validate_email, EmailNotValidError

from pydantic import Field, field_validator, model_validator
import re

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.models.database import UserRole


# ==================== 用户基础模式 ====================

class UserBase(BaseSchema):
    """用户基础信息模式"""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        description="用户名，3-50个字符"
    )
    email: str = Field(..., max_length=100, description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """验证用户名格式"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线和短横线')
        return v.lower()
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """验证邮箱格式"""
        try:
            valid = validate_email(v)
            return valid.email
        except EmailNotValidError:
            raise ValueError('邮箱格式不正确')
    
    @field_validator('avatar_url')
    @classmethod
    def validate_avatar_url(cls, v):
        """验证头像URL格式"""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('头像URL必须以http://或https://开头')
        return v


class UserCreate(UserBase):
    """用户创建模式"""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128, 
        description="密码，至少8位"
    )
    confirm_password: str = Field(..., description="确认密码")
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        # 检查是否包含字母和数字
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        
        # 注意：特殊字符为可选，不再强制要求
        # 用户可以选择包含或不包含特殊字符
        
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """验证两次密码是否一致"""
        password = self.password
        confirm_password = self.confirm_password
        
        if password and confirm_password and password != confirm_password:
            raise ValueError('两次输入的密码不一致')
        
        return self


class UserUpdate(BaseSchema):
    """用户更新模式"""
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    settings: Optional[Dict[str, Any]] = Field(None, description="用户设置")
    
    @field_validator('avatar_url')
    @classmethod
    def validate_avatar_url(cls, v):
        """验证头像URL格式"""
        if v is not None and v.strip():
            if not v.startswith(('http://', 'https://')):
                raise ValueError('头像URL必须以http://或https://开头')
        return v


class UserPasswordUpdate(BaseSchema):
    """用户密码更新模式"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128, 
        description="新密码"
    )
    confirm_new_password: str = Field(..., description="确认新密码")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, v):
        """验证新密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        
        # 注意：特殊字符为可选，不再强制要求
        # 用户可以选择包含或不包含特殊字符
        
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """验证新密码确认"""
        new_password = self.new_password
        confirm_new_password = self.confirm_new_password
        current_password = self.current_password
        
        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise ValueError('新密码确认不一致')
        
        if new_password and current_password and new_password == current_password:
            raise ValueError('新密码不能与当前密码相同')
        
        return self


# ==================== 用户响应模式 ====================

class UserInDB(UserBase, TimestampSchema, UUIDSchema):
    """数据库中的用户模式"""
    id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    is_verified: bool = Field(..., description="是否已验证邮箱")
    role: UserRole = Field(..., description="用户角色")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")
    settings: Dict[str, Any] = Field(default_factory=dict, description="用户设置")


class UserResponse(BaseSchema):
    """用户响应模式（公开信息）"""
    id: int = Field(..., description="用户ID")
    uuid: str = Field(..., description="用户UUID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="真实姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证邮箱")
    role: UserRole = Field(..., description="用户角色")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class UserProfile(UserResponse):
    """用户个人资料模式（包含私人设置）"""
    settings: Dict[str, Any] = Field(default_factory=dict, description="用户设置")


class UserSummary(BaseSchema):
    """用户摘要信息模式"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    full_name: Optional[str] = Field(None, description="真实姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    role: UserRole = Field(..., description="用户角色")


# ==================== 认证相关模式 ====================

class LoginRequest(BaseSchema):
    """登录请求模式"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")


class LoginResponse(BaseSchema):
    """登录响应模式"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌") 
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间(秒)")
    user: UserResponse = Field(..., description="用户信息")


class RefreshTokenRequest(BaseSchema):
    """刷新令牌请求模式"""
    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseSchema):
    """刷新令牌响应模式"""
    access_token: str = Field(..., description="新的访问令牌")
    expires_in: int = Field(..., description="令牌过期时间(秒)")


class LogoutRequest(BaseSchema):
    """登出请求模式"""
    all_devices: bool = Field(False, description="是否登出所有设备")


# ==================== 邮箱验证模式 ====================

class EmailVerificationRequest(BaseSchema):
    """邮箱验证请求模式"""
    email: str = Field(..., description="邮箱地址")
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """验证邮箱格式"""
        try:
            valid = validate_email(v)
            return valid.email
        except EmailNotValidError:
            raise ValueError('邮箱格式不正确')


class EmailVerificationConfirm(BaseSchema):
    """邮箱验证确认模式"""
    token: str = Field(..., description="验证令牌")


class PasswordResetRequest(BaseSchema):
    """密码重置请求模式"""
    email: str = Field(..., description="邮箱地址")
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """验证邮箱格式"""
        try:
            valid = validate_email(v)
            return valid.email
        except EmailNotValidError:
            raise ValueError('邮箱格式不正确')


class PasswordResetConfirm(BaseSchema):
    """密码重置确认模式"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128, 
        description="新密码"
    )
    confirm_password: str = Field(..., description="确认新密码")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        
        # 注意：特殊字符为可选，不再强制要求
        # 用户可以选择包含或不包含特殊字符
        
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """验证密码确认"""
        new_password = self.new_password
        confirm_password = self.confirm_password
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValueError('两次输入的密码不一致')
        
        return self


# ==================== 用户管理模式 ====================

class UserAdminUpdate(UserUpdate):
    """管理员用户更新模式"""
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_verified: Optional[bool] = Field(None, description="是否已验证邮箱")
    role: Optional[UserRole] = Field(None, description="用户角色")


class UserListQuery(BaseSchema):
    """用户列表查询模式"""
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    role: Optional[UserRole] = Field(None, description="角色筛选")
    is_active: Optional[bool] = Field(None, description="激活状态筛选")
    is_verified: Optional[bool] = Field(None, description="验证状态筛选")
    sort: Optional[str] = Field("created_at:desc", description="排序字段")
    
    @field_validator('sort')
    @classmethod
    def validate_sort(cls, v):
        """验证排序参数"""
        if v is None:
            return "created_at:desc"
        
        allowed_fields = [
            'id', 'username', 'email', 'full_name', 'role',
            'is_active', 'is_verified', 'login_count',
            'last_login_at', 'created_at', 'updated_at'
        ]
        
        if ':' in v:
            field, order = v.split(':', 1)
            if field not in allowed_fields:
                raise ValueError(f'排序字段必须是: {", ".join(allowed_fields)}')
            if order.lower() not in ['asc', 'desc']:
                raise ValueError('排序方向必须是 asc 或 desc')
            return f"{field}:{order.lower()}"
        else:
            if v not in allowed_fields:
                raise ValueError(f'排序字段必须是: {", ".join(allowed_fields)}')
            return f"{v}:asc"


# ==================== 用户统计模式 ====================

class UserStats(BaseSchema):
    """用户统计信息模式"""
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    verified_users: int = Field(..., description="已验证用户数")
    admin_users: int = Field(..., description="管理员用户数")
    recent_registrations: int = Field(..., description="最近注册用户数")
    
    # 按角色分布
    role_distribution: Dict[str, int] = Field(..., description="角色分布")
    
    # 按时间分布
    registration_trend: List[Dict[str, Any]] = Field(..., description="注册趋势")
    login_trend: List[Dict[str, Any]] = Field(..., description="登录趋势")


# ==================== 用户活动模式 ====================

class UserActivity(BaseSchema):
    """用户活动记录模式"""
    action: str = Field(..., description="操作类型")
    resource: Optional[str] = Field(None, description="操作资源")
    resource_id: Optional[int] = Field(None, description="资源ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外信息")
    created_at: datetime = Field(..., description="操作时间")


class UserActivityQuery(BaseSchema):
    """用户活动查询模式"""
    user_id: Optional[int] = Field(None, description="用户ID")
    action: Optional[str] = Field(None, description="操作类型")
    resource: Optional[str] = Field(None, description="操作资源")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    ip_address: Optional[str] = Field(None, description="IP地址")


# ==================== 用户设置模式 ====================

class UserSettings(BaseSchema):
    """用户设置模式"""
    # 界面设置
    theme: str = Field("light", description="主题设置")
    language: str = Field("zh-CN", description="语言设置")
    timezone: str = Field("Asia/Shanghai", description="时区设置")
    
    # 通知设置
    email_notifications: bool = Field(True, description="邮件通知")
    push_notifications: bool = Field(True, description="推送通知")
    strategy_alerts: bool = Field(True, description="策略告警")
    training_alerts: bool = Field(True, description="训练告警")
    
    # 安全设置
    two_factor_enabled: bool = Field(False, description="双因素认证")
    session_timeout: int = Field(1440, description="会话超时时间(分钟)")
    
    # 个性化设置
    dashboard_layout: Dict[str, Any] = Field(default_factory=dict, description="仪表板布局")
    chart_preferences: Dict[str, Any] = Field(default_factory=dict, description="图表偏好")
    
    @field_validator('theme')
    @classmethod
    def validate_theme(cls, v):
        """验证主题设置"""
        allowed_themes = ['light', 'dark', 'auto']
        if v not in allowed_themes:
            raise ValueError(f'主题必须是: {", ".join(allowed_themes)}')
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """验证语言设置"""
        allowed_languages = ['zh-CN', 'zh-TW', 'en-US']
        if v not in allowed_languages:
            raise ValueError(f'语言必须是: {", ".join(allowed_languages)}')
        return v
    
    @field_validator('session_timeout')
    @classmethod
    def validate_session_timeout(cls, v):
        """验证会话超时设置"""
        if v < 30 or v > 10080:  # 30分钟到7天
            raise ValueError('会话超时时间必须在30分钟到7天之间')
        return v


# ==================== 会话管理模式 ====================

class UserSessionResponse(BaseSchema):
    """用户会话响应模式"""
    id: int = Field(..., description="会话ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    is_active: bool = Field(..., description="是否激活")
    is_current: bool = Field(..., description="是否为当前会话")
    expires_at: datetime = Field(..., description="过期时间")
    last_activity_at: datetime = Field(..., description="最后活动时间")
    created_at: datetime = Field(..., description="创建时间")
    is_expired: bool = Field(..., description="是否已过期")
    location: Optional[str] = Field(None, description="地理位置")


class SessionStatsResponse(BaseSchema):
    """会话统计响应模式"""
    active_sessions: int = Field(..., description="活跃会话数")
    max_sessions: int = Field(..., description="最大会话数")
    is_over_limit: bool = Field(..., description="是否超出限制")
    session_timeout_hours: int = Field(..., description="会话超时时间（小时）")


# 导出主要组件
__all__ = [
    # 基础模式
    "UserBase", "UserCreate", "UserUpdate", "UserPasswordUpdate",
    
    # 响应模式
    "UserInDB", "UserResponse", "UserProfile", "UserSummary",
    
    # 认证模式
    "LoginRequest", "LoginResponse", "RefreshTokenRequest", "RefreshTokenResponse", "LogoutRequest",
    
    # 邮箱验证模式
    "EmailVerificationRequest", "EmailVerificationConfirm",
    "PasswordResetRequest", "PasswordResetConfirm",
    
    # 管理模式
    "UserAdminUpdate", "UserListQuery", "UserStats",
    
    # 活动模式
    "UserActivity", "UserActivityQuery",
    
    # 设置模式
    "UserSettings",
    
    # 会话管理模式
    "UserSessionResponse", "SessionStatsResponse"
]