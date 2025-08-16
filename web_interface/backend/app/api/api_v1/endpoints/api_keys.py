"""
API密钥管理端点

提供API密钥的创建、查询、更新、删除等接口。
支持密钥使用统计、速率限制检查等功能。
"""

from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.deps import get_current_user
from app.crud.api_key import api_key_crud
from app.models.database import User
from app.schemas.api_key import (
    APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyCreateResponse,
    APIKeyUsageLogResponse, APIKeyStatsResponse, APIKeyRateLimitResponse,
    APIKeyListQuery, APIKeyUsageQuery, APIKeyStatsQuery
)

router = APIRouter()


@router.post("/", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_in: APIKeyCreate
) -> Any:
    """
    创建新的API密钥
    
    - **name**: 密钥名称
    - **permissions**: 权限列表（可选）
    - **ip_whitelist**: IP白名单（可选）
    - **rate_limit**: 每小时请求限制
    - **expires_at**: 过期时间（可选）
    """
    # 检查用户API密钥数量限制
    current_key_count = await api_key_crud.get_user_key_count(db, user_id=current_user.id)
    max_keys = 10  # 每个用户最多10个API密钥
    
    if current_key_count >= max_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户最多只能创建 {max_keys} 个API密钥"
        )
    
    # 创建API密钥
    api_key = await api_key_crud.create(db, obj_in=api_key_in, user_id=current_user.id)
    
    # 构建响应
    response = APIKeyResponse.from_db_model(api_key)
    return APIKeyCreateResponse(
        **response.model_dump(),
        full_key=api_key.full_key  # 仅此次返回完整密钥
    )


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    query: APIKeyListQuery = Depends()
) -> Any:
    """
    获取用户的API密钥列表
    
    - **skip**: 跳过数量
    - **limit**: 限制数量
    - **active_only**: 仅显示激活的密钥
    """
    api_keys = await api_key_crud.get_by_user_id(
        db,
        user_id=current_user.id,
        skip=query.skip,
        limit=query.limit,
        active_only=query.active_only
    )
    
    return [APIKeyResponse.from_db_model(key) for key in api_keys]


@router.get("/{api_key_id}", response_model=APIKeyResponse)
async def get_api_key(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_id: int
) -> Any:
    """
    获取指定的API密钥详情
    """
    api_key = await api_key_crud.get_by_id(db, id=api_key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此API密钥"
        )
    
    return APIKeyResponse.from_db_model(api_key)


@router.put("/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_id: int,
    api_key_in: APIKeyUpdate
) -> Any:
    """
    更新API密钥
    
    - **name**: 密钥名称
    - **permissions**: 权限列表
    - **ip_whitelist**: IP白名单
    - **rate_limit**: 每小时请求限制
    - **expires_at**: 过期时间
    - **is_active**: 是否激活
    """
    api_key = await api_key_crud.get_by_id(db, id=api_key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此API密钥"
        )
    
    api_key = await api_key_crud.update(db, db_obj=api_key, obj_in=api_key_in)
    return APIKeyResponse.from_db_model(api_key)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_id: int
) -> None:
    """
    删除API密钥
    """
    success = await api_key_crud.delete(db, id=api_key_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在或无权删除"
        )


@router.post("/{api_key_id}/deactivate", response_model=APIKeyResponse)
async def deactivate_api_key(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_id: int
) -> Any:
    """
    停用API密钥
    """
    success = await api_key_crud.deactivate(db, id=api_key_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在或无权操作"
        )
    
    api_key = await api_key_crud.get_by_id(db, id=api_key_id)
    return APIKeyResponse.from_db_model(api_key)


@router.post("/{api_key_id}/activate", response_model=APIKeyResponse)
async def activate_api_key(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_id: int
) -> Any:
    """
    激活API密钥
    """
    success = await api_key_crud.activate(db, id=api_key_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在或无权操作"
        )
    
    api_key = await api_key_crud.get_by_id(db, id=api_key_id)
    return APIKeyResponse.from_db_model(api_key)


@router.get("/{api_key_id}/stats", response_model=APIKeyStatsResponse)
async def get_api_key_stats(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_id: int,
    query: APIKeyStatsQuery = Depends()
) -> Any:
    """
    获取API密钥使用统计
    
    - **days**: 统计天数（默认30天）
    """
    api_key = await api_key_crud.get_by_id(db, id=api_key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此API密钥统计"
        )
    
    stats = await api_key_crud.get_usage_stats(db, api_key_id=api_key_id, days=query.days)
    return APIKeyStatsResponse(**stats)


@router.get("/{api_key_id}/usage", response_model=List[APIKeyUsageLogResponse])
async def get_api_key_usage(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_id: int,
    query: APIKeyUsageQuery = Depends()
) -> Any:
    """
    获取API密钥使用日志
    
    - **skip**: 跳过数量
    - **limit**: 限制数量
    - **days**: 查询天数
    """
    api_key = await api_key_crud.get_by_id(db, id=api_key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此API密钥使用日志"
        )
    
    usage_logs = await api_key_crud.get_usage_logs(
        db,
        api_key_id=api_key_id,
        skip=query.skip,
        limit=query.limit,
        days=query.days
    )
    
    return [APIKeyUsageLogResponse.model_validate(log) for log in usage_logs]


@router.get("/{api_key_id}/rate-limit", response_model=APIKeyRateLimitResponse)
async def get_api_key_rate_limit(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    api_key_id: int
) -> Any:
    """
    获取API密钥当前速率限制状态
    """
    api_key = await api_key_crud.get_by_id(db, id=api_key_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此API密钥速率限制信息"
        )
    
    rate_limit_info = await api_key_crud.check_rate_limit(db, api_key=api_key)
    return APIKeyRateLimitResponse(**rate_limit_info)