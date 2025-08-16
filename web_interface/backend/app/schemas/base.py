"""
Pydantic基础模式定义

提供所有API接口的基础数据模式，包括通用响应格式、分页、错误处理等。
确保数据验证的一致性和类型安全。
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic import BaseModel as GenericModel


# ==================== 基础配置 ====================

class BaseSchema(BaseModel):
    """所有Pydantic模式的基类
    
    提供统一的配置和通用方法。
    """
    model_config = ConfigDict(
        # 允许从ORM对象构建
        from_attributes=True,
        # 验证赋值
        validate_assignment=True,
        # 使用枚举值而不是枚举对象
        use_enum_values=True,
        # 允许额外字段但发出警告
        extra='forbid',
        # JSON编码器配置
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        }
    )


class TimestampSchema(BaseSchema):
    """包含时间戳的基础模式"""
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class UUIDSchema(BaseSchema):
    """包含UUID的基础模式"""
    uuid: str = Field(..., description="全局唯一标识符")


# ==================== 通用响应模式 ====================

DataT = TypeVar('DataT')

class BaseResponse(GenericModel, Generic[DataT]):
    """基础API响应模式
    
    所有API接口的统一响应格式。
    """
    success: bool = Field(True, description="请求是否成功")
    data: Optional[DataT] = Field(None, description="响应数据")
    message: str = Field("Success", description="响应消息")
    code: int = Field(200, description="响应状态码")
    timestamp: int = Field(..., description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求唯一标识")
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def set_timestamp(cls, v):
        """自动设置时间戳"""
        if v is None:
            return int(datetime.utcnow().timestamp())
        return v


class SuccessResponse(BaseResponse[DataT]):
    """成功响应模式"""
    success: bool = Field(True, description="请求成功")
    

class ErrorDetail(BaseSchema):
    """错误详情模式"""
    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")


class ErrorInfo(BaseSchema):
    """错误信息模式"""
    code: int = Field(..., description="错误状态码")
    message: str = Field(..., description="错误消息")
    type: str = Field(..., description="错误类型")
    details: Optional[List[ErrorDetail]] = Field(None, description="错误详情列表")


class ErrorResponse(BaseSchema):
    """错误响应模式"""
    success: bool = Field(False, description="请求失败")
    error: ErrorInfo = Field(..., description="错误信息")
    timestamp: int = Field(..., description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求唯一标识")
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def set_timestamp(cls, v):
        """自动设置时间戳"""
        if v is None:
            return int(datetime.utcnow().timestamp())
        return v


# ==================== 分页模式 ====================

class PaginationParams(BaseSchema):
    """分页参数模式"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(20, ge=1, le=100, description="每页数量，最大100")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginationInfo(BaseSchema):
    """分页信息模式"""
    total: int = Field(..., ge=0, description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页数量")
    pages: int = Field(..., ge=0, description="总页数")
    has_prev: bool = Field(..., description="是否有上一页")
    has_next: bool = Field(..., description="是否有下一页")
    
    @field_validator('pages', mode='before')
    @classmethod
    def calculate_pages(cls, v, info):
        """计算总页数"""
        if info.data and 'total' in info.data and 'size' in info.data:
            total = info.data['total']
            size = info.data['size']
            return (total + size - 1) // size if total > 0 else 0
        return v
    
    @field_validator('has_prev', mode='before')
    @classmethod
    def calculate_has_prev(cls, v, info):
        """计算是否有上一页"""
        if info.data and 'page' in info.data:
            return info.data['page'] > 1
        return v
    
    @field_validator('has_next', mode='before')
    @classmethod
    def calculate_has_next(cls, v, info):
        """计算是否有下一页"""
        if info.data and 'page' in info.data and 'pages' in info.data:
            return info.data['page'] < info.data['pages']
        return v


class PaginatedData(GenericModel, Generic[DataT]):
    """分页数据模式"""
    items: List[DataT] = Field(..., description="数据项列表")
    pagination: PaginationInfo = Field(..., description="分页信息")


class PaginatedResponse(BaseResponse[PaginatedData[DataT]]):
    """分页响应模式"""
    pass


# ==================== 查询和排序模式 ====================

class SortOrder(str):
    """排序方向"""
    ASC = "asc"
    DESC = "desc"


class SortField(BaseSchema):
    """排序字段模式"""
    field: str = Field(..., description="排序字段名")
    order: str = Field(SortOrder.ASC, description="排序方向")
    
    @field_validator('order')
    @classmethod
    def validate_order(cls, v):
        """验证排序方向"""
        if v.lower() not in [SortOrder.ASC, SortOrder.DESC]:
            raise ValueError(f"排序方向必须是 {SortOrder.ASC} 或 {SortOrder.DESC}")
        return v.lower()


class QueryParams(BaseSchema):
    """通用查询参数模式"""
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    sort: Optional[str] = Field(None, description="排序字段，格式：field:order")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    
    @field_validator('sort')
    @classmethod
    def validate_sort(cls, v):
        """验证排序参数格式"""
        if v is None:
            return v
        
        if ':' in v:
            field, order = v.split(':', 1)
            if order.lower() not in [SortOrder.ASC, SortOrder.DESC]:
                raise ValueError(f"排序方向必须是 {SortOrder.ASC} 或 {SortOrder.DESC}")
            return f"{field}:{order.lower()}"
        else:
            return f"{v}:{SortOrder.ASC}"


# ==================== 操作结果模式 ====================

class OperationResult(BaseSchema):
    """操作结果模式"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果消息")
    affected_rows: Optional[int] = Field(None, description="影响的记录数")
    operation_id: Optional[str] = Field(None, description="操作ID")


class BulkOperationResult(BaseSchema):
    """批量操作结果模式"""
    total: int = Field(..., ge=0, description="总数量")
    success_count: int = Field(..., ge=0, description="成功数量")
    failure_count: int = Field(..., ge=0, description="失败数量")
    errors: List[ErrorDetail] = Field(default_factory=list, description="错误详情列表")
    
    @field_validator('failure_count', mode='before')
    @classmethod
    def calculate_failure_count(cls, v, info):
        """计算失败数量"""
        if info.data and 'total' in info.data and 'success_count' in info.data:
            return info.data['total'] - info.data['success_count']
        return v


# ==================== 状态更新模式 ====================

class StatusUpdate(BaseSchema):
    """状态更新模式"""
    status: str = Field(..., description="新状态")
    reason: Optional[str] = Field(None, description="状态变更原因")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class ProgressUpdate(BaseSchema):
    """进度更新模式"""
    progress: float = Field(..., ge=0, le=100, description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤")
    total_steps: Optional[int] = Field(None, description="总步骤数")
    eta: Optional[int] = Field(None, description="预计剩余时间(秒)")
    message: Optional[str] = Field(None, description="进度消息")


# ==================== 文件上传模式 ====================

class FileInfo(BaseSchema):
    """文件信息模式"""
    filename: str = Field(..., description="文件名")
    size: int = Field(..., ge=0, description="文件大小(字节)")
    content_type: str = Field(..., description="文件MIME类型")
    checksum: Optional[str] = Field(None, description="文件校验和")


class UploadResponse(BaseSchema):
    """上传响应模式"""
    file_id: str = Field(..., description="文件ID")
    file_info: FileInfo = Field(..., description="文件信息")
    upload_url: Optional[str] = Field(None, description="上传URL")
    status: str = Field("uploaded", description="上传状态")


# ==================== 健康检查模式 ====================

class HealthStatus(BaseSchema):
    """健康状态模式"""
    service: str = Field(..., description="服务名称")
    status: str = Field(..., description="健康状态")
    version: str = Field(..., description="版本号")
    timestamp: int = Field(..., description="检查时间戳")
    uptime: Optional[str] = Field(None, description="运行时间")
    dependencies: Optional[Dict[str, str]] = Field(None, description="依赖服务状态")


class DatabaseHealth(BaseSchema):
    """数据库健康状态模式"""
    connected: bool = Field(..., description="是否连接正常")
    version: Optional[str] = Field(None, description="数据库版本")
    active_connections: Optional[int] = Field(None, description="活跃连接数")
    pool_size: Optional[int] = Field(None, description="连接池大小")
    response_time: Optional[float] = Field(None, description="响应时间(毫秒)")


class SystemInfo(BaseSchema):
    """系统信息模式"""
    name: str = Field(..., description="系统名称")
    version: str = Field(..., description="版本号")
    environment: str = Field(..., description="运行环境")
    api_version: str = Field(..., description="API版本")
    features: Dict[str, bool] = Field(..., description="功能特性")
    endpoints: Dict[str, str] = Field(..., description="接口端点")


# ==================== WebSocket消息模式 ====================

class WebSocketMessage(BaseSchema):
    """WebSocket消息基础模式"""
    type: str = Field(..., description="消息类型")
    data: Optional[Dict[str, Any]] = Field(None, description="消息数据")
    timestamp: int = Field(..., description="消息时间戳")
    message_id: Optional[str] = Field(None, description="消息ID")
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def set_timestamp(cls, v):
        """自动设置时间戳"""
        if v is None:
            return int(datetime.utcnow().timestamp())
        return v


class SubscriptionMessage(WebSocketMessage):
    """订阅消息模式"""
    type: str = Field("subscribe", description="消息类型")
    channel: str = Field(..., description="订阅频道")
    filters: Optional[Dict[str, Any]] = Field(None, description="订阅过滤条件")


class UnsubscriptionMessage(WebSocketMessage):
    """取消订阅消息模式"""
    type: str = Field("unsubscribe", description="消息类型")
    channel: str = Field(..., description="取消订阅频道")


class NotificationMessage(WebSocketMessage):
    """通知消息模式"""
    type: str = Field("notification", description="消息类型")
    level: str = Field("info", description="通知级别")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")


# ==================== 验证和工具函数 ====================

def create_response(
    data: Any = None,
    message: str = "Success",
    code: int = 200,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建标准响应格式
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码
        request_id: 请求ID
        
    Returns:
        标准格式的响应字典
    """
    return {
        "success": True,
        "data": data,
        "message": message,
        "code": code,
        "timestamp": int(datetime.utcnow().timestamp()),
        "request_id": request_id
    }


def create_error_response(
    message: str,
    code: int = 400,
    error_type: str = "client_error",
    details: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建错误响应格式
    
    Args:
        message: 错误消息
        code: 错误状态码
        error_type: 错误类型
        details: 错误详情
        request_id: 请求ID
        
    Returns:
        标准格式的错误响应字典
    """
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "type": error_type,
            "details": details or []
        },
        "timestamp": int(datetime.utcnow().timestamp()),
        "request_id": request_id
    }


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    size: int,
    message: str = "Success",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建分页响应格式
    
    Args:
        items: 数据项列表
        total: 总记录数
        page: 当前页码
        size: 每页数量
        message: 响应消息
        request_id: 请求ID
        
    Returns:
        标准格式的分页响应字典
    """
    pages = (total + size - 1) // size if total > 0 else 0
    
    return create_response(
        data={
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
                "has_prev": page > 1,
                "has_next": page < pages
            }
        },
        message=message,
        request_id=request_id
    )


# 导出主要组件
__all__ = [
    # 基础模式
    "BaseSchema", "TimestampSchema", "UUIDSchema",
    
    # 响应模式
    "BaseResponse", "SuccessResponse", "ErrorResponse", 
    "ErrorDetail", "ErrorInfo",
    
    # 分页模式
    "PaginationParams", "PaginationInfo", "PaginatedData", "PaginatedResponse",
    
    # 查询模式
    "SortOrder", "SortField", "QueryParams",
    
    # 操作结果模式
    "OperationResult", "BulkOperationResult",
    
    # 状态模式
    "StatusUpdate", "ProgressUpdate",
    
    # 文件模式
    "FileInfo", "UploadResponse",
    
    # 健康检查模式
    "HealthStatus", "DatabaseHealth", "SystemInfo",
    
    # WebSocket模式
    "WebSocketMessage", "SubscriptionMessage", "UnsubscriptionMessage", "NotificationMessage",
    
    # 工具函数
    "create_response", "create_error_response", "create_paginated_response"
]