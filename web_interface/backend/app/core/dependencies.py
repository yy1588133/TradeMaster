"""
依赖注入系统

提供FastAPI依赖注入函数，包括数据库会话、用户认证、权限验证、
缓存连接等。实现清洁的依赖管理和资源生命周期控制。
"""

from typing import Generator, Optional, Dict, Any, Annotated
from functools import lru_cache
import asyncio

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import redis.asyncio as redis
import httpx

from app.core.config import settings
from app.core.security import (
    verify_token, 
    TokenType, 
    UserRole, 
    Permission,
    check_user_permission,
    verify_api_key
)


# ==================== 数据库依赖 ====================

# 创建异步数据库引擎
@lru_cache()
def get_async_engine():
    """获取异步数据库引擎（单例）"""
    return create_async_engine(
        settings.get_database_url(async_driver=True),
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,
        echo=settings.DEBUG,  # 开发环境启用SQL日志
        future=True,
        poolclass=NullPool if settings.DEBUG else None,  # 开发环境不使用连接池
    )


# 创建异步会话工厂
@lru_cache()
def get_async_sessionmaker():
    """获取异步会话工厂（单例）"""
    engine = get_async_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False,
    )


async def get_db() -> AsyncSession:
    """获取数据库会话依赖
    
    提供异步数据库会话，自动处理会话的创建和关闭。
    支持事务回滚和异常处理。
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    async_session = get_async_sessionmaker()
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==================== Redis缓存依赖 ====================

@lru_cache()
def get_redis_client():
    """获取Redis客户端（单例）"""
    return redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )


async def get_redis() -> redis.Redis:
    """获取Redis连接依赖
    
    提供Redis异步连接，用于缓存和会话存储。
    
    Returns:
        redis.Redis: Redis客户端实例
    """
    client = get_redis_client()
    try:
        # 测试连接
        await client.ping()
        return client
    except Exception as e:
        # Redis连接失败时的降级处理
        print(f"Redis连接失败: {e}")
        return None


# ==================== HTTP客户端依赖 ====================

@lru_cache()
def get_http_client():
    """获取HTTP客户端（单例）"""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
        follow_redirects=True,
    )


async def get_httpx_client() -> httpx.AsyncClient:
    """获取HTTP客户端依赖
    
    提供异步HTTP客户端，用于外部API调用。
    
    Returns:
        httpx.AsyncClient: HTTP客户端实例
    """
    return get_http_client()


# ==================== 认证依赖 ====================

# HTTP Bearer认证方案
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """获取当前用户ID依赖
    
    从JWT令牌中提取用户ID，验证令牌有效性。
    
    Args:
        credentials: HTTP Bearer认证凭据
        
    Returns:
        str: 用户ID
        
    Raises:
        HTTPException: 当认证失败时抛出异常
    """
    token = credentials.credentials
    
    try:
        payload = verify_token(token, TokenType.ACCESS)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌：缺少用户信息",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"令牌验证失败: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取当前用户信息依赖
    
    根据用户ID从数据库中获取完整的用户信息。
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 用户信息字典
        
    Raises:
        HTTPException: 当用户不存在时抛出异常
    """
    from app.crud.user import user_crud
    
    try:
        # 转换用户ID为整数
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID格式"
        )
    
    # 从数据库获取用户信息
    user = await user_crud.get(db, user_id=user_id_int)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 转换为字典格式
    return {
        "id": str(user.id),
        "uuid": user.uuid,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login_at": user.last_login_at,
        "login_count": user.login_count,
        "settings": user.settings
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前活跃用户依赖
    
    确保用户账户处于活跃状态。
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        Dict[str, Any]: 活跃用户信息
        
    Raises:
        HTTPException: 当用户账户被禁用时抛出异常
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    return current_user


async def get_current_superuser(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """获取当前超级用户依赖
    
    确保用户具有超级用户权限。
    
    Args:
        current_user: 当前活跃用户信息
        
    Returns:
        Dict[str, Any]: 超级用户信息
        
    Raises:
        HTTPException: 当用户不是超级用户时抛出异常
    """
    if not current_user.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要超级用户权限"
        )
    
    return current_user


# ==================== API密钥认证依赖 ====================

async def get_api_key_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """通过API密钥获取用户信息依赖
    
    支持API密钥认证方式，用于API客户端访问。
    
    Args:
        credentials: HTTP Bearer认证凭据
        
    Returns:
        Dict[str, Any]: 用户信息字典
        
    Raises:
        HTTPException: 当API密钥无效时抛出异常
    """
    api_key = credentials.credentials
    
    try:
        payload = verify_api_key(api_key)
        user_id = payload.get("sub")
        api_key_name = payload.get("name", "未命名")
        
        # TODO: 从数据库获取用户信息
        # 这里暂时返回模拟数据
        mock_user = {
            "id": user_id,
            "username": f"api_user_{user_id}",
            "email": f"api_user_{user_id}@example.com",
            "role": UserRole.USER,
            "is_active": True,
            "is_superuser": False,
            "api_key_name": api_key_name,
            "auth_method": "api_key"
        }
        
        return mock_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"API密钥验证失败: {str(e)}"
        )


# ==================== 权限依赖工厂 ====================

def require_permission(permission: Permission):
    """权限检查依赖工厂
    
    创建一个检查特定权限的依赖函数。
    
    Args:
        permission: 所需的权限
        
    Returns:
        依赖函数
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """检查用户是否具有所需权限
        
        Args:
            current_user: 当前活跃用户
            
        Returns:
            Dict[str, Any]: 用户信息
            
        Raises:
            HTTPException: 当权限不足时抛出异常
        """
        user_role = current_user.get("role", UserRole.VIEWER)
        
        if not check_user_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {permission.value} 权限"
            )
        
        return current_user
    
    return permission_checker


def require_role(required_role: UserRole):
    """角色检查依赖工厂
    
    创建一个检查特定角色的依赖函数。
    
    Args:
        required_role: 所需的角色
        
    Returns:
        依赖函数
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """检查用户是否具有所需角色
        
        Args:
            current_user: 当前活跃用户
            
        Returns:
            Dict[str, Any]: 用户信息
            
        Raises:
            HTTPException: 当角色不匹配时抛出异常
        """
        user_role = current_user.get("role", UserRole.VIEWER)
        
        # 角色等级检查（ADMIN > USER > ANALYST > VIEWER）
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.USER: 3,
            UserRole.ANALYST: 2,
            UserRole.VIEWER: 1
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {required_role.value} 或更高级别的角色"
            )
        
        return current_user
    
    return role_checker


# ==================== 分页依赖 ====================

class PaginationParams:
    """分页参数类"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        max_limit: int = 100
    ):
        # 验证分页参数
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="skip参数必须大于等于0"
            )
        
        if limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit参数必须大于0"
            )
        
        if limit > max_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"limit参数不能超过{max_limit}"
            )
        
        self.skip = skip
        self.limit = limit


def get_pagination_params(
    skip: int = 0,
    limit: int = 20
) -> PaginationParams:
    """获取分页参数依赖
    
    Args:
        skip: 跳过的记录数
        limit: 限制返回的记录数
        
    Returns:
        PaginationParams: 分页参数对象
    """
    return PaginationParams(skip=skip, limit=limit)


# ==================== 排序依赖 ====================

class SortParams:
    """排序参数类"""
    
    def __init__(self, sort_by: str = "created_at", order: str = "desc"):
        allowed_orders = ["asc", "desc"]
        if order.lower() not in allowed_orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"order参数必须是{allowed_orders}中的一个"
            )
        
        self.sort_by = sort_by
        self.order = order.lower()


def get_sort_params(
    sort_by: str = "created_at",
    order: str = "desc"
) -> SortParams:
    """获取排序参数依赖
    
    Args:
        sort_by: 排序字段
        order: 排序顺序（asc/desc）
        
    Returns:
        SortParams: 排序参数对象
    """
    return SortParams(sort_by=sort_by, order=order)


# ==================== 搜索依赖 ====================

class SearchParams:
    """搜索参数类"""
    
    def __init__(self, q: Optional[str] = None):
        if q is not None:
            # 清理搜索查询
            q = q.strip()
            if len(q) > 100:  # 限制搜索查询长度
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="搜索查询长度不能超过100个字符"
                )
            if len(q) == 0:
                q = None
        
        self.query = q


def get_search_params(q: Optional[str] = None) -> SearchParams:
    """获取搜索参数依赖
    
    Args:
        q: 搜索查询字符串
        
    Returns:
        SearchParams: 搜索参数对象
    """
    return SearchParams(q=q)


# ==================== 常用依赖组合 ====================

# 常用依赖类型别名
CurrentUser = Annotated[Dict[str, Any], Depends(get_current_active_user)]
SuperUser = Annotated[Dict[str, Any], Depends(get_current_superuser)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
RedisClient = Annotated[redis.Redis, Depends(get_redis)]
HttpClient = Annotated[httpx.AsyncClient, Depends(get_httpx_client)]
PaginationDeps = Annotated[PaginationParams, Depends(get_pagination_params)]
SortDeps = Annotated[SortParams, Depends(get_sort_params)]
SearchDeps = Annotated[SearchParams, Depends(get_search_params)]


# 导出主要依赖
__all__ = [
    "get_db",
    "get_redis", 
    "get_httpx_client",
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "get_api_key_user",
    "require_permission",
    "require_role",
    "get_pagination_params",
    "get_sort_params", 
    "get_search_params",
    "CurrentUser",
    "SuperUser",
    "DatabaseSession",
    "RedisClient",
    "HttpClient",
    "PaginationDeps",
    "SortDeps",
    "SearchDeps",
    "PaginationParams",
    "SortParams",
    "SearchParams"
]