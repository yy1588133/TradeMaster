"""
API密钥Pydantic模式

定义API密钥相关的请求和响应数据结构。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class APIKeyBase(BaseModel):
    """API密钥基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="密钥名称")
    permissions: Optional[List[str]] = Field(default=None, description="权限列表")
    ip_whitelist: Optional[List[str]] = Field(default=None, description="IP白名单")
    rate_limit: int = Field(default=1000, ge=1, le=10000, description="每小时请求限制")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")


class APIKeyCreate(APIKeyBase):
    """API密钥创建模式"""
    pass


class APIKeyUpdate(BaseModel):
    """API密钥更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="密钥名称")
    permissions: Optional[List[str]] = Field(None, description="权限列表")
    ip_whitelist: Optional[List[str]] = Field(None, description="IP白名单")
    rate_limit: Optional[int] = Field(None, ge=1, le=10000, description="每小时请求限制")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否激活")


class APIKeyResponse(APIKeyBase):
    """API密钥响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    key_prefix: str = Field(..., description="密钥前缀")
    display_key: str = Field(..., description="显示用的密钥")
    user_id: int
    usage_count: int = Field(..., description="使用次数")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db_model(cls, api_key) -> "APIKeyResponse":
        """从数据库模型创建响应对象"""
        import json
        
        permissions = None
        if api_key.permissions:
            try:
                permissions = json.loads(api_key.permissions)
            except (json.JSONDecodeError, TypeError):
                permissions = []
        
        ip_whitelist = None
        if api_key.ip_whitelist:
            try:
                ip_whitelist = json.loads(api_key.ip_whitelist)
            except (json.JSONDecodeError, TypeError):
                ip_whitelist = []
        
        return cls(
            id=api_key.id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            display_key=api_key.get_display_key(),
            user_id=api_key.user_id,
            permissions=permissions,
            ip_whitelist=ip_whitelist,
            rate_limit=api_key.rate_limit,
            usage_count=api_key.usage_count,
            last_used_at=api_key.last_used_at,
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )


class APIKeyCreateResponse(APIKeyResponse):
    """API密钥创建响应模式（包含完整密钥）"""
    full_key: str = Field(..., description="完整密钥（仅创建时返回）")


class APIKeyUsageLogResponse(BaseModel):
    """API密钥使用日志响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    api_key_id: int
    endpoint: Optional[str] = Field(None, description="请求端点")
    method: Optional[str] = Field(None, description="请求方法")
    ip_address: Optional[str] = Field(None, description="客户端IP")
    user_agent: Optional[str] = Field(None, description="用户代理")
    status_code: Optional[int] = Field(None, description="响应状态码")
    response_time: Optional[int] = Field(None, description="响应时间（毫秒）")
    created_at: datetime


class APIKeyStatsResponse(BaseModel):
    """API密钥统计响应模式"""
    total_requests: int = Field(..., description="总请求数")
    success_requests: int = Field(..., description="成功请求数")
    error_requests: int = Field(..., description="错误请求数")
    success_rate: float = Field(..., description="成功率")
    avg_response_time: float = Field(..., description="平均响应时间")
    daily_stats: List[Dict[str, Any]] = Field(..., description="每日统计")
    endpoint_stats: List[Dict[str, Any]] = Field(..., description="端点统计")


class APIKeyRateLimitResponse(BaseModel):
    """API密钥速率限制响应模式"""
    limit: int = Field(..., description="速率限制")
    current_usage: int = Field(..., description="当前使用量")
    remaining: int = Field(..., description="剩余配额")
    reset_time: datetime = Field(..., description="重置时间")
    is_exceeded: bool = Field(..., description="是否超出限制")


class APIKeyListQuery(BaseModel):
    """API密钥列表查询模式"""
    skip: int = Field(default=0, ge=0, description="跳过数量")
    limit: int = Field(default=100, ge=1, le=1000, description="限制数量")
    active_only: bool = Field(default=True, description="仅显示激活的密钥")


class APIKeyUsageQuery(BaseModel):
    """API密钥使用查询模式"""
    api_key_id: int = Field(..., description="API密钥ID")
    skip: int = Field(default=0, ge=0, description="跳过数量")
    limit: int = Field(default=100, ge=1, le=1000, description="限制数量")
    days: int = Field(default=7, ge=1, le=90, description="查询天数")


class APIKeyStatsQuery(BaseModel):
    """API密钥统计查询模式"""
    api_key_id: int = Field(..., description="API密钥ID")
    days: int = Field(default=30, ge=1, le=365, description="统计天数")