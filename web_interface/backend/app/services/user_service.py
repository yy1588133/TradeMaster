"""
用户服务层

提供用户管理的业务逻辑，包括用户注册、认证、权限管理等高级功能。
在CRUD层基础上封装业务规则，提供给API层调用。
"""

import secrets
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.crud.user import user_crud, user_session_crud
from app.models.database import User, UserSession, UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    validate_password_strength,
    get_password_hash,
    TokenType
)
from app.core.config import settings


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.user_crud = user_crud
        self.session_crud = user_session_crud
    
    async def register_user(
        self,
        db: AsyncSession,
        *,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        auto_verify: bool = False
    ) -> User:
        """用户注册
        
        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱地址
            password: 明文密码
            full_name: 真实姓名
            auto_verify: 是否自动验证邮箱
            
        Returns:
            User: 创建的用户对象
            
        Raises:
            HTTPException: 当注册失败时抛出异常
        """
        # 验证密码强度
        password_validation = validate_password_strength(password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "密码强度不符合要求",
                    "errors": password_validation["errors"]
                }
            )
        
        # 创建用户
        user = await self.user_crud.create(
            db,
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=UserRole.USER,
            is_active=True,
            is_verified=auto_verify
        )
        
        # TODO: 发送邮箱验证邮件
        # if not auto_verify:
        #     await self.send_verification_email(user)
        
        return user
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False
    ) -> Tuple[User, Dict[str, Any]]:
        """用户认证和登录
        
        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码
            ip_address: IP地址
            user_agent: 用户代理
            remember_me: 是否记住登录
            
        Returns:
            Tuple[User, Dict[str, Any]]: 用户对象和令牌信息
            
        Raises:
            HTTPException: 当认证失败时抛出异常
        """
        # 验证用户凭据
        user = await self.user_crud.authenticate(db, username=username, password=password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用"
            )
        
        # 创建令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        if remember_me:
            access_token_expires = timedelta(days=1)  # 记住登录状态时延长有效期
        
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
            additional_claims={
                "username": user.username,
                "role": user.role.value
            }
        )
        
        refresh_token = create_refresh_token(
            subject=str(user.id),
            additional_claims={
                "username": user.username
            }
        )
        
        # 创建会话记录
        session_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.session_crud.create(
            db,
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=session_expires
        )
        
        # 更新最后登录时间
        await self.user_crud.update_last_login(db, user=user)
        
        # 构建令牌响应
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
        
        return user, token_data
    
    async def refresh_user_token(
        self,
        db: AsyncSession,
        *,
        refresh_token: str
    ) -> Tuple[User, Dict[str, Any]]:
        """刷新用户令牌
        
        Args:
            db: 数据库会话
            refresh_token: 刷新令牌
            
        Returns:
            Tuple[User, Dict[str, Any]]: 用户对象和新令牌信息
            
        Raises:
            HTTPException: 当刷新失败时抛出异常
        """
        # 验证会话
        session = await self.session_crud.get_by_refresh_token(db, refresh_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 获取用户信息
        user = await self.user_crud.get(db, user_id=session.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
            additional_claims={
                "username": user.username,
                "role": user.role.value
            }
        )
        
        # 可选：创建新的刷新令牌（滚动刷新）
        new_refresh_token = create_refresh_token(
            subject=str(user.id),
            additional_claims={
                "username": user.username
            }
        )
        
        # 更新会话
        session.session_token = access_token
        session.refresh_token = new_refresh_token
        await self.session_crud.update_activity(db, session=session)
        
        # 构建令牌响应
        token_data = {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
        
        return user, token_data
    
    async def logout_user(
        self,
        db: AsyncSession,
        *,
        session_token: Optional[str] = None,
        user_id: Optional[int] = None,
        all_devices: bool = False
    ) -> bool:
        """用户登出
        
        Args:
            db: 数据库会话
            session_token: 会话令牌
            user_id: 用户ID
            all_devices: 是否登出所有设备
            
        Returns:
            bool: 是否登出成功
        """
        if all_devices and user_id:
            # 撤销用户的所有会话
            revoked_count = await self.session_crud.revoke_user_sessions(
                db, 
                user_id=user_id
            )
            return revoked_count > 0
        elif session_token:
            # 撤销指定会话
            return await self.session_crud.revoke_session(
                db,
                session_token=session_token
            )
        
        return False
    
    async def get_user_profile(
        self,
        db: AsyncSession,
        *,
        user_id: int
    ) -> User:
        """获取用户资料
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            User: 用户对象
            
        Raises:
            HTTPException: 当用户不存在时抛出异常
        """
        user = await self.user_crud.get(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return user
    
    async def update_user_profile(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> User:
        """更新用户资料
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            update_data: 更新数据
            
        Returns:
            User: 更新后的用户对象
            
        Raises:
            HTTPException: 当更新失败时抛出异常
        """
        user = await self.user_crud.get(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return await self.user_crud.update(db, user=user, update_data=update_data)
    
    async def change_user_password(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """修改用户密码
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            current_password: 当前密码
            new_password: 新密码
            
        Returns:
            bool: 是否修改成功
            
        Raises:
            HTTPException: 当修改失败时抛出异常
        """
        user = await self.user_crud.get(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证当前密码
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 验证新密码强度
        password_validation = validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "新密码强度不符合要求",
                    "errors": password_validation["errors"]
                }
            )
        
        # 检查新密码是否与当前密码相同
        if verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新密码不能与当前密码相同"
            )
        
        # 更新密码
        await self.user_crud.update_password(db, user=user, new_password=new_password)
        
        # 撤销用户的所有会话（强制重新登录）
        await self.session_crud.revoke_user_sessions(db, user_id=user.id)
        
        return True
    
    async def reset_user_password(
        self,
        db: AsyncSession,
        *,
        email: str,
        new_password: str,
        reset_token: str
    ) -> bool:
        """重置用户密码
        
        Args:
            db: 数据库会话
            email: 邮箱地址
            new_password: 新密码
            reset_token: 重置令牌
            
        Returns:
            bool: 是否重置成功
            
        Raises:
            HTTPException: 当重置失败时抛出异常
        """
        # TODO: 验证重置令牌
        # 这里应该验证reset_token的有效性
        
        user = await self.user_crud.get_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证新密码强度
        password_validation = validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "新密码强度不符合要求",
                    "errors": password_validation["errors"]
                }
            )
        
        # 更新密码
        await self.user_crud.update_password(db, user=user, new_password=new_password)
        
        # 撤销用户的所有会话
        await self.session_crud.revoke_user_sessions(db, user_id=user.id)
        
        return True
    
    async def get_user_list(
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
    ) -> Tuple[List[User], int]:
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
            Tuple[List[User], int]: 用户列表和总数
        """
        users = await self.user_crud.get_multi(
            db,
            skip=skip,
            limit=limit,
            search=search,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total = await self.user_crud.count(
            db,
            search=search,
            role=role,
            is_active=is_active,
            is_verified=is_verified
        )
        
        return users, total
    
    async def get_user_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """获取用户统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        return await self.user_crud.get_user_stats(db)
    
    async def verify_user_email(
        self,
        db: AsyncSession,
        *,
        verification_token: str
    ) -> User:
        """验证用户邮箱
        
        Args:
            db: 数据库会话
            verification_token: 验证令牌
            
        Returns:
            User: 验证后的用户对象
            
        Raises:
            HTTPException: 当验证失败时抛出异常
        """
        # TODO: 验证邮箱验证令牌
        # 这里应该解析验证令牌获取用户信息
        
        # 暂时返回模拟实现
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="邮箱验证功能尚未实现"
        )
    
    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """清理过期会话
        
        Args:
            db: 数据库会话
            
        Returns:
            int: 清理的会话数量
        """
        return await self.session_crud.cleanup_expired_sessions(db)


# 全局实例
user_service = UserService()

# 导出
__all__ = ["UserService", "user_service"]