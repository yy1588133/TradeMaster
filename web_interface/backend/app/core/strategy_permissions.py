"""
策略权限控制模块

提供细粒度的策略权限管理，支持基于角色和资源的访问控制。
集成FastAPI依赖注入系统，提供灵活的权限验证机制。
"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from functools import wraps

from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.models.database import User, UserRole, Strategy, StrategyStatus
from app.crud.strategy import strategy_crud
from app.exceptions.strategy import StrategyAccessDeniedError, StrategyNotFoundError


class StrategyPermission(str, Enum):
    """策略权限枚举"""
    # 基础权限
    VIEW = "strategy:view"
    CREATE = "strategy:create"
    UPDATE = "strategy:update"
    DELETE = "strategy:delete"
    
    # 执行权限
    EXECUTE = "strategy:execute"
    STOP = "strategy:stop"
    PAUSE = "strategy:pause"
    RESUME = "strategy:resume"
    
    # 高级权限
    CLONE = "strategy:clone"
    EXPORT = "strategy:export"
    IMPORT = "strategy:import"
    SHARE = "strategy:share"
    
    # 管理权限
    MANAGE_ALL = "strategy:manage_all"
    VIEW_ALL = "strategy:view_all"
    MODERATE = "strategy:moderate"


class ResourcePermission:
    """资源权限类"""
    
    def __init__(
        self,
        resource_id: int,
        resource_type: str,
        owner_id: int,
        permissions: List[StrategyPermission]
    ):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.owner_id = owner_id
        self.permissions = permissions


class PermissionChecker:
    """权限检查器"""
    
    # 角色权限映射
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            StrategyPermission.VIEW, StrategyPermission.CREATE, StrategyPermission.UPDATE,
            StrategyPermission.DELETE, StrategyPermission.EXECUTE, StrategyPermission.STOP,
            StrategyPermission.PAUSE, StrategyPermission.RESUME, StrategyPermission.CLONE,
            StrategyPermission.EXPORT, StrategyPermission.IMPORT, StrategyPermission.SHARE,
            StrategyPermission.MANAGE_ALL, StrategyPermission.VIEW_ALL, StrategyPermission.MODERATE
        ],
        UserRole.USER: [
            StrategyPermission.VIEW, StrategyPermission.CREATE, StrategyPermission.UPDATE,
            StrategyPermission.DELETE, StrategyPermission.EXECUTE, StrategyPermission.STOP,
            StrategyPermission.PAUSE, StrategyPermission.RESUME, StrategyPermission.CLONE,
            StrategyPermission.EXPORT
        ],
        UserRole.ANALYST: [
            StrategyPermission.VIEW, StrategyPermission.CREATE, StrategyPermission.EXECUTE,
            StrategyPermission.CLONE, StrategyPermission.EXPORT, StrategyPermission.VIEW_ALL
        ],
        UserRole.VIEWER: [
            StrategyPermission.VIEW
        ]
    }
    
    @classmethod
    def has_permission(
        cls,
        user: User,
        permission: StrategyPermission,
        resource: Optional[ResourcePermission] = None
    ) -> bool:
        """检查用户是否有指定权限
        
        Args:
            user: 用户对象
            permission: 权限
            resource: 资源权限信息
            
        Returns:
            bool: 是否有权限
        """
        # 超级用户拥有所有权限
        if user.is_superuser:
            return True
        
        # 检查用户是否激活
        if not user.is_active:
            return False
        
        # 获取用户角色权限
        role_permissions = cls.ROLE_PERMISSIONS.get(user.role, [])
        
        # 检查角色权限
        if permission not in role_permissions:
            return False
        
        # 资源级权限检查
        if resource:
            return cls._check_resource_permission(user, permission, resource)
        
        return True
    
    @classmethod
    def _check_resource_permission(
        cls,
        user: User,
        permission: StrategyPermission,
        resource: ResourcePermission
    ) -> bool:
        """检查资源级权限
        
        Args:
            user: 用户对象
            permission: 权限
            resource: 资源权限信息
            
        Returns:
            bool: 是否有权限
        """
        # 管理员拥有所有资源权限
        if user.role == UserRole.ADMIN:
            return True
        
        # 资源所有者权限检查
        if resource.owner_id == user.id:
            return permission in resource.permissions
        
        # 查看所有策略的权限
        if permission == StrategyPermission.VIEW and StrategyPermission.VIEW_ALL in cls.ROLE_PERMISSIONS.get(user.role, []):
            return True
        
        # 其他情况无权限
        return False
    
    @classmethod
    def check_strategy_status_permission(
        cls,
        user: User,
        strategy: Strategy,
        permission: StrategyPermission
    ) -> bool:
        """检查策略状态相关权限
        
        Args:
            user: 用户对象
            strategy: 策略对象
            permission: 权限
            
        Returns:
            bool: 是否有权限
        """
        # 基础权限检查
        resource = ResourcePermission(
            resource_id=strategy.id,
            resource_type="strategy",
            owner_id=strategy.owner_id,
            permissions=[permission]
        )
        
        if not cls.has_permission(user, permission, resource):
            return False
        
        # 状态相关权限检查
        if permission == StrategyPermission.EXECUTE:
            # 只有草稿和停止状态的策略可以执行
            return strategy.status in [StrategyStatus.DRAFT, StrategyStatus.STOPPED]
        
        elif permission == StrategyPermission.STOP:
            # 只有运行中的策略可以停止
            return strategy.status == StrategyStatus.ACTIVE
        
        elif permission == StrategyPermission.PAUSE:
            # 只有运行中的策略可以暂停
            return strategy.status == StrategyStatus.ACTIVE
        
        elif permission == StrategyPermission.RESUME:
            # 只有暂停的策略可以恢复
            return strategy.status == StrategyStatus.PAUSED
        
        elif permission in [StrategyPermission.UPDATE, StrategyPermission.DELETE]:
            # 运行中的策略不能修改或删除
            return strategy.status != StrategyStatus.ACTIVE
        
        return True


# 权限验证依赖项
async def require_strategy_permission(
    permission: StrategyPermission,
    strategy_id: Optional[int] = None
) -> Callable:
    """创建策略权限验证依赖项
    
    Args:
        permission: 所需权限
        strategy_id: 策略ID（可选）
        
    Returns:
        Callable: 依赖项函数
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """权限验证依赖项
        
        Args:
            current_user: 当前用户
            db: 数据库会话
            
        Returns:
            User: 验证通过的用户
            
        Raises:
            StrategyAccessDeniedError: 权限不足
            StrategyNotFoundError: 策略不存在
        """
        # 如果指定了策略ID，需要检查策略权限
        if strategy_id:
            strategy = await strategy_crud.get(db, strategy_id=strategy_id)
            if not strategy:
                raise StrategyNotFoundError(strategy_id=strategy_id, user_id=current_user.id)
            
            # 检查策略状态权限
            if not PermissionChecker.check_strategy_status_permission(
                current_user, strategy, permission
            ):
                raise StrategyAccessDeniedError(
                    strategy_id=strategy_id,
                    user_id=current_user.id,
                    required_permission=permission.value
                )
        else:
            # 检查基础权限
            if not PermissionChecker.has_permission(current_user, permission):
                raise StrategyAccessDeniedError(
                    strategy_id=0,
                    user_id=current_user.id,
                    required_permission=permission.value
                )
        
        return current_user
    
    return permission_dependency


def require_strategy_owner(strategy_id: int) -> Callable:
    """创建策略所有者验证依赖项
    
    Args:
        strategy_id: 策略ID
        
    Returns:
        Callable: 依赖项函数
    """
    async def owner_dependency(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> tuple[User, Strategy]:
        """所有者验证依赖项
        
        Args:
            current_user: 当前用户
            db: 数据库会话
            
        Returns:
            tuple[User, Strategy]: 用户和策略对象
            
        Raises:
            StrategyNotFoundError: 策略不存在
            StrategyAccessDeniedError: 非策略所有者
        """
        strategy = await strategy_crud.get(db, strategy_id=strategy_id)
        if not strategy:
            raise StrategyNotFoundError(strategy_id=strategy_id, user_id=current_user.id)
        
        # 检查是否为策略所有者或管理员
        if strategy.owner_id != current_user.id and not current_user.is_admin:
            raise StrategyAccessDeniedError(
                strategy_id=strategy_id,
                user_id=current_user.id,
                required_permission="owner"
            )
        
        return current_user, strategy
    
    return owner_dependency


# 权限装饰器
def require_permissions(*permissions: StrategyPermission):
    """权限验证装饰器
    
    Args:
        *permissions: 所需权限列表
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供用户信息"
                )
            
            # 检查所有权限
            for permission in permissions:
                if not PermissionChecker.has_permission(current_user, permission):
                    raise StrategyAccessDeniedError(
                        strategy_id=0,
                        user_id=current_user.id,
                        required_permission=permission.value
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 配额管理
class QuotaManager:
    """配额管理器"""
    
    # 用户配额限制
    USER_QUOTAS = {
        UserRole.ADMIN: {
            "max_strategies": -1,  # 无限制
            "max_running_strategies": -1,
            "max_training_jobs": -1,
            "max_storage_mb": -1
        },
        UserRole.USER: {
            "max_strategies": 50,
            "max_running_strategies": 5,
            "max_training_jobs": 10,
            "max_storage_mb": 1024  # 1GB
        },
        UserRole.ANALYST: {
            "max_strategies": 20,
            "max_running_strategies": 3,
            "max_training_jobs": 5,
            "max_storage_mb": 512  # 512MB
        },
        UserRole.VIEWER: {
            "max_strategies": 5,
            "max_running_strategies": 1,
            "max_training_jobs": 2,
            "max_storage_mb": 256  # 256MB
        }
    }
    
    @classmethod
    async def check_quota(
        cls,
        user: User,
        db: AsyncSession,
        quota_type: str
    ) -> bool:
        """检查用户配额
        
        Args:
            user: 用户对象
            db: 数据库会话
            quota_type: 配额类型
            
        Returns:
            bool: 是否在配额范围内
        """
        quotas = cls.USER_QUOTAS.get(user.role, {})
        limit = quotas.get(quota_type, 0)
        
        # -1 表示无限制
        if limit == -1:
            return True
        
        # 查询当前使用量
        current_usage = await cls._get_current_usage(user, db, quota_type)
        
        return current_usage < limit
    
    @classmethod
    async def _get_current_usage(
        cls,
        user: User,
        db: AsyncSession,
        quota_type: str
    ) -> int:
        """获取当前使用量
        
        Args:
            user: 用户对象
            db: 数据库会话
            quota_type: 配额类型
            
        Returns:
            int: 当前使用量
        """
        if quota_type == "max_strategies":
            return await strategy_crud.count(db, owner_id=user.id)
        
        elif quota_type == "max_running_strategies":
            return await strategy_crud.count(
                db, 
                owner_id=user.id, 
                status=StrategyStatus.ACTIVE
            )
        
        elif quota_type == "max_training_jobs":
            # TODO: 实现训练任务计数
            return 0
        
        elif quota_type == "max_storage_mb":
            # TODO: 实现存储使用量计算
            return 0
        
        return 0


# 导出主要组件
__all__ = [
    "StrategyPermission",
    "ResourcePermission",
    "PermissionChecker",
    "require_strategy_permission",
    "require_strategy_owner",
    "require_permissions",
    "QuotaManager"
]