"""
用户数据库操作层 (CRUD)

提供用户相关的数据库操作接口，包括创建、查询、更新、删除等操作。
使用异步SQLAlchemy操作，支持复杂查询和事务管理。
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.database import User, UserSession, UserRole
from app.core.security import get_password_hash, verify_password


class UserCRUD:
    """用户CRUD操作类"""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        is_verified: bool = False,
        settings: Optional[Dict[str, Any]] = None
    ) -> User:
        """创建新用户
        
        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱地址
            password: 明文密码
            full_name: 真实姓名
            role: 用户角色
            is_active: 是否激活
            is_verified: 是否已验证邮箱
            settings: 用户设置
            
        Returns:
            User: 创建的用户对象
            
        Raises:
            HTTPException: 当用户名或邮箱已存在时抛出异常
        """
        # 检查用户名是否已存在
        existing_user = await self.get_by_username(db, username=username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = await self.get_by_email(db, email=email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱地址已存在"
            )
        
        # 创建用户对象
        hashed_password = get_password_hash(password)
        user = User(
            username=username.lower(),
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            settings=settings or {},
            login_count=0
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def get(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """根据ID获取用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户对象或None
        """
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_uuid(self, db: AsyncSession, uuid: str) -> Optional[User]:
        """根据UUID获取用户
        
        Args:
            db: 数据库会话
            uuid: 用户UUID
            
        Returns:
            Optional[User]: 用户对象或None
        """
        stmt = select(User).where(User.uuid == uuid)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            Optional[User]: 用户对象或None
        """
        stmt = select(User).where(User.username == username.lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户
        
        Args:
            db: 数据库会话
            email: 邮箱地址
            
        Returns:
            Optional[User]: 用户对象或None
        """
        stmt = select(User).where(User.email == email.lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username_or_email(
        self, 
        db: AsyncSession, 
        identifier: str
    ) -> Optional[User]:
        """根据用户名或邮箱获取用户
        
        Args:
            db: 数据库会话
            identifier: 用户名或邮箱
            
        Returns:
            Optional[User]: 用户对象或None
        """
        identifier = identifier.lower()
        stmt = select(User).where(
            or_(User.username == identifier, User.email == identifier)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def authenticate(
        self, 
        db: AsyncSession, 
        username: str, 
        password: str
    ) -> Optional[User]:
        """用户认证
        
        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 明文密码
            
        Returns:
            Optional[User]: 认证成功的用户对象或None
        """
        user = await self.get_by_username_or_email(db, identifier=username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def update(
        self,
        db: AsyncSession,
        *,
        user: User,
        update_data: Dict[str, Any]
    ) -> User:
        """更新用户信息
        
        Args:
            db: 数据库会话
            user: 用户对象
            update_data: 更新数据字典
            
        Returns:
            User: 更新后的用户对象
        """
        # 过滤允许更新的字段
        allowed_fields = {
            'username', 'email', 'full_name', 'avatar_url', 
            'is_active', 'is_verified', 'role', 'settings'
        }
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(user, field):
                # 特殊处理需要验证唯一性的字段
                if field == 'username' and value != user.username:
                    existing = await self.get_by_username(db, username=value)
                    if existing and existing.id != user.id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="用户名已存在"
                        )
                    setattr(user, field, value.lower())
                
                elif field == 'email' and value != user.email:
                    existing = await self.get_by_email(db, email=value)
                    if existing and existing.id != user.id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="邮箱地址已存在"
                        )
                    setattr(user, field, value.lower())
                
                else:
                    setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    async def update_password(
        self,
        db: AsyncSession,
        *,
        user: User,
        new_password: str
    ) -> User:
        """更新用户密码
        
        Args:
            db: 数据库会话
            user: 用户对象
            new_password: 新密码明文
            
        Returns:
            User: 更新后的用户对象
        """
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        
        await db.commit()
        await db.refresh(user)
        return user
    
    async def update_last_login(
        self,
        db: AsyncSession,
        *,
        user: User,
        login_time: Optional[datetime] = None
    ) -> User:
        """更新用户最后登录时间
        
        Args:
            db: 数据库会话
            user: 用户对象
            login_time: 登录时间，默认为当前时间
            
        Returns:
            User: 更新后的用户对象
        """
        if login_time is None:
            login_time = datetime.utcnow()
        
        user.last_login_at = login_time
        user.login_count += 1
        
        await db.commit()
        await db.refresh(user)
        return user
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[User]:
        """获取用户列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回的记录数
            search: 搜索关键词
            role: 角色筛选
            is_active: 激活状态筛选
            is_verified: 验证状态筛选
            sort_by: 排序字段
            sort_order: 排序顺序
            
        Returns:
            List[User]: 用户列表
        """
        stmt = select(User)
        
        # 构建查询条件
        conditions = []
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )
        
        if role is not None:
            conditions.append(User.role == role)
        
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        
        if is_verified is not None:
            conditions.append(User.is_verified == is_verified)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 排序
        if hasattr(User, sort_by):
            order_column = getattr(User, sort_by)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(order_column.desc())
            else:
                stmt = stmt.order_by(order_column.asc())
        
        # 分页
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def count(
        self,
        db: AsyncSession,
        *,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> int:
        """统计用户数量
        
        Args:
            db: 数据库会话
            search: 搜索关键词
            role: 角色筛选
            is_active: 激活状态筛选
            is_verified: 验证状态筛选
            
        Returns:
            int: 用户数量
        """
        stmt = select(func.count(User.id))
        
        # 构建查询条件
        conditions = []
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )
        
        if role is not None:
            conditions.append(User.role == role)
        
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        
        if is_verified is not None:
            conditions.append(User.is_verified == is_verified)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        result = await db.execute(stmt)
        return result.scalar()
    
    async def delete(self, db: AsyncSession, *, user_id: int) -> bool:
        """删除用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        stmt = delete(User).where(User.id == user_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    
    async def get_user_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """获取用户统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        # 总用户数
        total_users = await db.scalar(select(func.count(User.id)))
        
        # 活跃用户数
        active_users = await db.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )
        
        # 已验证用户数
        verified_users = await db.scalar(
            select(func.count(User.id)).where(User.is_verified == True)
        )
        
        # 按角色分布
        role_stats = {}
        for role in UserRole:
            count = await db.scalar(
                select(func.count(User.id)).where(User.role == role)
            )
            role_stats[role.value] = count
        
        # 最近30天注册用户数
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = await db.scalar(
            select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
        )
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "admin_users": role_stats.get("admin", 0),
            "recent_registrations": recent_registrations,
            "role_distribution": role_stats
        }


class UserSessionCRUD:
    """用户会话CRUD操作类"""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        session_token: str,
        refresh_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_at: datetime
    ) -> UserSession:
        """创建用户会话
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            session_token: 会话token
            refresh_token: 刷新token
            ip_address: IP地址
            user_agent: 用户代理
            expires_at: 过期时间
            
        Returns:
            UserSession: 创建的会话对象
        """
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    async def get_by_token(
        self, 
        db: AsyncSession, 
        session_token: str
    ) -> Optional[UserSession]:
        """根据session token获取会话
        
        Args:
            db: 数据库会话
            session_token: 会话token
            
        Returns:
            Optional[UserSession]: 会话对象或None
        """
        stmt = select(UserSession).where(
            and_(
                UserSession.session_token == session_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> Optional[UserSession]:
        """根据refresh token获取会话
        
        Args:
            db: 数据库会话
            refresh_token: 刷新token
            
        Returns:
            Optional[UserSession]: 会话对象或None
        """
        stmt = select(UserSession).where(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_activity(
        self,
        db: AsyncSession,
        *,
        session: UserSession
    ) -> UserSession:
        """更新会话活动时间
        
        Args:
            db: 数据库会话
            session: 会话对象
            
        Returns:
            UserSession: 更新后的会话对象
        """
        session.last_activity_at = datetime.utcnow()
        await db.commit()
        await db.refresh(session)
        return session
    
    async def revoke_session(
        self,
        db: AsyncSession,
        *,
        session_token: str
    ) -> bool:
        """撤销会话
        
        Args:
            db: 数据库会话
            session_token: 会话token
            
        Returns:
            bool: 是否撤销成功
        """
        stmt = update(UserSession).where(
            UserSession.session_token == session_token
        ).values(is_active=False)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    
    async def revoke_user_sessions(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        exclude_session: Optional[str] = None
    ) -> int:
        """撤销用户的所有会话
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            exclude_session: 排除的会话token
            
        Returns:
            int: 撤销的会话数量
        """
        conditions = [UserSession.user_id == user_id]
        
        if exclude_session:
            conditions.append(UserSession.session_token != exclude_session)
        
        stmt = update(UserSession).where(
            and_(*conditions)
        ).values(is_active=False)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
    
    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """清理过期会话
        
        Args:
            db: 数据库会话
            
        Returns:
            int: 清理的会话数量
        """
        stmt = delete(UserSession).where(
            UserSession.expires_at < datetime.utcnow()
        )
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount


# 全局实例
user_crud = UserCRUD()
user_session_crud = UserSessionCRUD()

# 导出
__all__ = [
    "UserCRUD", "UserSessionCRUD", 
    "user_crud", "user_session_crud"
]