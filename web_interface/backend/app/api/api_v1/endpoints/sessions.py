"""
会话管理端点

提供用户会话的查询、管理和监控接口。
支持会话终止、并发控制和活动监控。
"""

from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.deps import get_current_user, get_current_session
from app.models.database import User, UserSession
from app.services.session_service import session_service
from app.schemas.user import UserSessionResponse, SessionStatsResponse

router = APIRouter()


@router.get("/", response_model=List[UserSessionResponse])
async def get_user_sessions(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    include_inactive: bool = False
) -> Any:
    """
    获取当前用户的所有会话
    
    - **include_inactive**: 是否包含非活跃会话
    """
    sessions = await session_service.get_user_sessions(
        db,
        user_id=current_user.id,
        include_inactive=include_inactive
    )
    
    result = []
    for session in sessions:
        session_info = await session_service.get_session_info(
            db,
            session_token=session.session_token
        )
        
        result.append(UserSessionResponse(
            id=session.id,
            ip_address=str(session.ip_address) if session.ip_address else None,
            user_agent=session.user_agent,
            is_active=session.is_active,
            is_current=session.session_token == getattr(current_user, '_current_session_token', None),
            expires_at=session.expires_at,
            last_activity_at=session.last_activity_at,
            created_at=session.created_at,
            is_expired=session_info.get('is_expired', False) if session_info else True,
            location=None  # TODO: 可以通过IP地址获取地理位置
        ))
    
    return result


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_session(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    session_id: int
) -> None:
    """
    终止指定的会话
    """
    success = await session_service.terminate_session(
        db,
        session_id=session_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或无权操作"
        )


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_all_sessions(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_session: UserSession = Depends(get_current_session),
    keep_current: bool = True
) -> None:
    """
    终止所有会话
    
    - **keep_current**: 是否保留当前会话
    """
    except_session_id = current_session.id if keep_current else None
    
    await session_service.terminate_all_sessions(
        db,
        user_id=current_user.id,
        except_session_id=except_session_id
    )


@router.get("/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    获取用户会话统计信息
    """
    stats = await session_service.get_concurrent_sessions_stats(
        db,
        user_id=current_user.id
    )
    
    active_count = await session_service.get_active_sessions_count(
        db,
        user_id=current_user.id
    )
    
    return SessionStatsResponse(
        active_sessions=active_count,
        max_sessions=session_service.max_sessions_per_user,
        is_over_limit=active_count > session_service.max_sessions_per_user,
        session_timeout_hours=session_service.session_timeout_hours
    )


@router.post("/cleanup", status_code=status.HTTP_204_NO_CONTENT)
async def cleanup_expired_sessions(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    清理过期会话
    """
    await session_service.cleanup_expired_sessions(
        db,
        user_id=current_user.id
    )


@router.get("/current", response_model=UserSessionResponse)
async def get_current_session(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_session: UserSession = Depends(get_current_session)
) -> Any:
    """
    获取当前会话信息
    """
    session_info = await session_service.get_session_info(
        db,
        session_token=current_session.session_token
    )
    
    return UserSessionResponse(
        id=current_session.id,
        ip_address=str(current_session.ip_address) if current_session.ip_address else None,
        user_agent=current_session.user_agent,
        is_active=current_session.is_active,
        is_current=True,
        expires_at=current_session.expires_at,
        last_activity_at=current_session.last_activity_at,
        created_at=current_session.created_at,
        is_expired=session_info.get('is_expired', False) if session_info else True,
        location=None  # TODO: 可以通过IP地址获取地理位置
    )


@router.post("/refresh-activity", status_code=status.HTTP_204_NO_CONTENT)
async def refresh_session_activity(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_session: UserSession = Depends(get_current_session)
) -> None:
    """
    刷新当前会话活动时间
    """
    await session_service.update_activity(
        db,
        session_token=current_session.session_token
    )