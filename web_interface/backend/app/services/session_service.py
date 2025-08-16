"""
会话管理服务

提供用户会话的管理功能，包括会话创建、验证、清理和并发控制。
支持多设备登录限制和会话监控。
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import UserSession, User
from app.crud.user import user_session_crud


class SessionService:
    """会话管理服务类"""

    def __init__(self):
        self.max_sessions_per_user = getattr(settings, 'MAX_SESSIONS_PER_USER', 5)
        self.session_timeout_hours = getattr(settings, 'SESSION_TIMEOUT_HOURS', 24)

    async def create_session(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        session_token: str,
        refresh_token: str,
        ip_address: str,
        user_agent: str,
        expires_at: datetime
    ) -> UserSession:
        """创建新会话，并处理并发限制"""
        
        # 检查并清理用户的过期会话
        await self.cleanup_expired_sessions(db, user_id=user_id)
        
        # 检查用户当前活跃会话数量
        active_sessions = await self.get_active_sessions_count(db, user_id=user_id)
        
        if active_sessions >= self.max_sessions_per_user:
            # 删除最旧的会话
            await self.remove_oldest_session(db, user_id=user_id)
        
        # 创建新会话
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

    async def get_active_sessions_count(
        self,
        db: AsyncSession,
        *,
        user_id: int
    ) -> int:
        """获取用户当前活跃会话数量"""
        stmt = select(func.count(UserSession.id)).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await db.scalar(stmt)
        return result or 0

    async def get_user_sessions(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        include_inactive: bool = False
    ) -> List[UserSession]:
        """获取用户的所有会话"""
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        
        if not include_inactive:
            stmt = stmt.where(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            )
        
        stmt = stmt.order_by(UserSession.last_activity_at.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()

    async def terminate_session(
        self,
        db: AsyncSession,
        *,
        session_id: int,
        user_id: int
    ) -> bool:
        """终止指定会话"""
        stmt = update(UserSession).where(
            and_(
                UserSession.id == session_id,
                UserSession.user_id == user_id
            )
        ).values(is_active=False)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def terminate_all_sessions(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        except_session_id: Optional[int] = None
    ) -> int:
        """终止用户的所有会话（可排除当前会话）"""
        stmt = update(UserSession).where(UserSession.user_id == user_id)
        
        if except_session_id:
            stmt = stmt.where(UserSession.id != except_session_id)
        
        stmt = stmt.values(is_active=False)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def update_activity(
        self,
        db: AsyncSession,
        *,
        session_token: str
    ) -> bool:
        """更新会话活动时间"""
        stmt = update(UserSession).where(
            UserSession.session_token == session_token
        ).values(last_activity_at=datetime.utcnow())
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def cleanup_expired_sessions(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None
    ) -> int:
        """清理过期会话"""
        now = datetime.utcnow()
        
        stmt = update(UserSession).where(
            or_(
                UserSession.expires_at <= now,
                UserSession.last_activity_at <= now - timedelta(hours=self.session_timeout_hours)
            )
        )
        
        if user_id:
            stmt = stmt.where(UserSession.user_id == user_id)
        
        stmt = stmt.values(is_active=False)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def remove_oldest_session(
        self,
        db: AsyncSession,
        *,
        user_id: int
    ) -> bool:
        """删除用户最旧的活跃会话"""
        # 查找最旧的活跃会话
        stmt = select(UserSession.id).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).order_by(UserSession.last_activity_at.asc()).limit(1)
        
        result = await db.execute(stmt)
        oldest_session_id = result.scalar_one_or_none()
        
        if oldest_session_id:
            # 停用最旧的会话
            return await self.terminate_session(db, session_id=oldest_session_id, user_id=user_id)
        
        return False

    async def get_session_info(
        self,
        db: AsyncSession,
        *,
        session_token: str
    ) -> Optional[Dict[str, Any]]:
        """获取会话详细信息"""
        stmt = select(UserSession).where(UserSession.session_token == session_token)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        return {
            "id": session.id,
            "user_id": session.user_id,
            "ip_address": str(session.ip_address) if session.ip_address else None,
            "user_agent": session.user_agent,
            "is_active": session.is_active,
            "expires_at": session.expires_at,
            "last_activity_at": session.last_activity_at,
            "created_at": session.created_at,
            "is_expired": session.expires_at <= datetime.utcnow() if session.expires_at else False,
            "is_inactive": session.last_activity_at <= datetime.utcnow() - timedelta(hours=self.session_timeout_hours)
        }

    async def is_session_valid(
        self,
        db: AsyncSession,
        *,
        session_token: str
    ) -> bool:
        """检查会话是否有效"""
        session_info = await self.get_session_info(db, session_token=session_token)
        
        if not session_info:
            return False
        
        return (
            session_info["is_active"] and
            not session_info["is_expired"] and
            not session_info["is_inactive"]
        )

    async def get_concurrent_sessions_stats(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取并发会话统计"""
        base_stmt = select(UserSession).where(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        
        if user_id:
            base_stmt = base_stmt.where(UserSession.user_id == user_id)
        
        # 总活跃会话数
        total_active_stmt = select(func.count(UserSession.id)).select_from(base_stmt.subquery())
        total_active = await db.scalar(total_active_stmt) or 0
        
        # 按用户分组的会话数
        user_sessions_stmt = select(
            UserSession.user_id,
            func.count(UserSession.id).label('session_count')
        ).where(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).group_by(UserSession.user_id)
        
        if user_id:
            user_sessions_stmt = user_sessions_stmt.where(UserSession.user_id == user_id)
        
        result = await db.execute(user_sessions_stmt)
        user_sessions = [
            {"user_id": row.user_id, "session_count": row.session_count}
            for row in result
        ]
        
        # 超出限制的用户
        over_limit_users = [
            user for user in user_sessions 
            if user["session_count"] > self.max_sessions_per_user
        ]
        
        return {
            "total_active_sessions": total_active,
            "max_sessions_per_user": self.max_sessions_per_user,
            "user_sessions": user_sessions,
            "over_limit_users": over_limit_users,
            "over_limit_count": len(over_limit_users)
        }

    async def force_cleanup_user_sessions(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        keep_latest: int = 1
    ) -> int:
        """强制清理用户会话，只保留最新的N个会话"""
        # 获取用户所有活跃会话，按活动时间倒序
        stmt = select(UserSession.id).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).order_by(UserSession.last_activity_at.desc()).offset(keep_latest)
        
        result = await db.execute(stmt)
        session_ids_to_terminate = [row[0] for row in result]
        
        if not session_ids_to_terminate:
            return 0
        
        # 批量停用会话
        stmt = update(UserSession).where(
            UserSession.id.in_(session_ids_to_terminate)
        ).values(is_active=False)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount


# 创建服务实例
session_service = SessionService()