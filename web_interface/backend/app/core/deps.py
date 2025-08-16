"""
FastAPI依赖项

提供用于API端点的依赖注入函数，包括认证、授权、数据库连接等。
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.crud.user import user_crud, user_session_crud
from app.models.database import User, UserSession, UserRole


# HTTP Bearer token security
security = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """获取当前认证用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # 解码JWT令牌
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户信息
    user = await user_crud.get(db, id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )

    return user


async def get_current_session(
    db: AsyncSession = Depends(get_async_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserSession:
    """获取当前用户会话"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 通过token获取会话信息
    session = await user_session_crud.get_by_token(db, token=credentials.credentials)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话不存在或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户（已验证邮箱）"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先验证邮箱地址"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要超级用户权限"
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户"""
    if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user


def require_roles(*allowed_roles: UserRole):
    """创建角色权限检查依赖"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
        
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下角色之一: {', '.join([role.value for role in allowed_roles])}"
            )
        return current_user
    
    return role_checker


async def get_optional_current_user(
    db: AsyncSession = Depends(get_async_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """获取可选的当前用户（用于可选认证的端点）"""
    if not credentials:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user = await user_crud.get(db, id=user_id)
    if user is None or not user.is_active:
        return None

    return user


class CommonQueryParams:
    """通用查询参数"""
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        sort: Optional[str] = None
    ):
        self.skip = max(0, skip)
        self.limit = min(1000, max(1, limit))  # 限制在1-1000之间
        self.search = search.strip() if search else None
        self.sort = sort


def get_query_params() -> CommonQueryParams:
    """获取通用查询参数依赖"""
    return Depends(CommonQueryParams)


# 导出所有依赖函数
__all__ = [
    "get_current_user",
    "get_current_session", 
    "get_current_active_user",
    "get_current_superuser",
    "get_current_admin_user",
    "require_roles",
    "get_optional_current_user",
    "CommonQueryParams",
    "get_query_params"
]