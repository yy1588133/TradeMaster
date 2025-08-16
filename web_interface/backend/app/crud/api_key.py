"""
API密钥CRUD操作

提供API密钥的数据库操作接口，包括创建、查询、更新、删除等功能。
支持密钥管理、使用统计和安全控制。
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.api_key import APIKey, APIKeyUsageLog
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate


class APIKeyCRUD:
    """API密钥CRUD操作类"""

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        obj_in: APIKeyCreate,
        user_id: int
    ) -> APIKey:
        """创建新的API密钥"""
        # 生成密钥和哈希
        key, key_hash = APIKey.generate_key()
        key_prefix = key[:8]  # 取前8位作为前缀
        
        # 处理权限和IP白名单
        permissions = json.dumps(obj_in.permissions) if obj_in.permissions else None
        ip_whitelist = json.dumps(obj_in.ip_whitelist) if obj_in.ip_whitelist else None
        
        # 创建数据库对象
        db_obj = APIKey(
            name=obj_in.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            user_id=user_id,
            permissions=permissions,
            ip_whitelist=ip_whitelist,
            rate_limit=obj_in.rate_limit,
            expires_at=obj_in.expires_at,
            is_active=True
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # 返回完整密钥（仅此次返回）
        db_obj.full_key = key  # 临时属性，用于返回
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, *, id: int) -> Optional[APIKey]:
        """根据ID获取API密钥"""
        stmt = select(APIKey).where(APIKey.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_key_hash(db: AsyncSession, *, key_hash: str) -> Optional[APIKey]:
        """根据密钥哈希获取API密钥"""
        stmt = select(APIKey).where(APIKey.key_hash == key_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_id(
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[APIKey]:
        """获取用户的API密钥列表"""
        stmt = select(APIKey).where(APIKey.user_id == user_id)
        
        if active_only:
            stmt = stmt.where(APIKey.is_active == True)
        
        stmt = stmt.offset(skip).limit(limit).order_by(APIKey.created_at.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        db_obj: APIKey,
        obj_in: APIKeyUpdate
    ) -> APIKey:
        """更新API密钥"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # 处理权限和IP白名单
        if 'permissions' in update_data:
            update_data['permissions'] = json.dumps(update_data['permissions']) if update_data['permissions'] else None
        
        if 'ip_whitelist' in update_data:
            update_data['ip_whitelist'] = json.dumps(update_data['ip_whitelist']) if update_data['ip_whitelist'] else None
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def delete(db: AsyncSession, *, id: int, user_id: int) -> bool:
        """删除API密钥"""
        stmt = delete(APIKey).where(
            and_(APIKey.id == id, APIKey.user_id == user_id)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def deactivate(db: AsyncSession, *, id: int, user_id: int) -> bool:
        """停用API密钥"""
        stmt = update(APIKey).where(
            and_(APIKey.id == id, APIKey.user_id == user_id)
        ).values(is_active=False)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def activate(db: AsyncSession, *, id: int, user_id: int) -> bool:
        """激活API密钥"""
        stmt = update(APIKey).where(
            and_(APIKey.id == id, APIKey.user_id == user_id)
        ).values(is_active=True)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def record_usage(
        db: AsyncSession,
        *,
        api_key: APIKey,
        endpoint: str,
        method: str,
        ip_address: str,
        user_agent: str,
        status_code: int,
        response_time: int
    ) -> APIKeyUsageLog:
        """记录API密钥使用"""
        # 更新密钥使用统计
        api_key.record_usage()
        
        # 创建使用日志
        usage_log = APIKeyUsageLog(
            api_key_id=api_key.id,
            user_id=api_key.user_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            response_time=response_time
        )
        
        db.add(usage_log)
        await db.commit()
        await db.refresh(usage_log)
        return usage_log

    @staticmethod
    async def get_usage_stats(
        db: AsyncSession,
        *,
        api_key_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取API密钥使用统计"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 总请求数
        total_requests_stmt = select(func.count(APIKeyUsageLog.id)).where(
            and_(
                APIKeyUsageLog.api_key_id == api_key_id,
                APIKeyUsageLog.created_at >= start_date
            )
        )
        total_requests = await db.scalar(total_requests_stmt)
        
        # 成功请求数
        success_requests_stmt = select(func.count(APIKeyUsageLog.id)).where(
            and_(
                APIKeyUsageLog.api_key_id == api_key_id,
                APIKeyUsageLog.created_at >= start_date,
                APIKeyUsageLog.status_code.between(200, 299)
            )
        )
        success_requests = await db.scalar(success_requests_stmt)
        
        # 平均响应时间
        avg_response_time_stmt = select(func.avg(APIKeyUsageLog.response_time)).where(
            and_(
                APIKeyUsageLog.api_key_id == api_key_id,
                APIKeyUsageLog.created_at >= start_date
            )
        )
        avg_response_time = await db.scalar(avg_response_time_stmt)
        
        # 按日统计
        daily_stats_stmt = select(
            func.date(APIKeyUsageLog.created_at).label('date'),
            func.count(APIKeyUsageLog.id).label('count')
        ).where(
            and_(
                APIKeyUsageLog.api_key_id == api_key_id,
                APIKeyUsageLog.created_at >= start_date
            )
        ).group_by(func.date(APIKeyUsageLog.created_at)).order_by('date')
        
        daily_stats_result = await db.execute(daily_stats_stmt)
        daily_stats = [
            {"date": row.date.isoformat(), "count": row.count}
            for row in daily_stats_result
        ]
        
        # 按端点统计
        endpoint_stats_stmt = select(
            APIKeyUsageLog.endpoint,
            func.count(APIKeyUsageLog.id).label('count')
        ).where(
            and_(
                APIKeyUsageLog.api_key_id == api_key_id,
                APIKeyUsageLog.created_at >= start_date
            )
        ).group_by(APIKeyUsageLog.endpoint).order_by(func.count(APIKeyUsageLog.id).desc()).limit(10)
        
        endpoint_stats_result = await db.execute(endpoint_stats_stmt)
        endpoint_stats = [
            {"endpoint": row.endpoint, "count": row.count}
            for row in endpoint_stats_result
        ]
        
        return {
            "total_requests": total_requests or 0,
            "success_requests": success_requests or 0,
            "error_requests": (total_requests or 0) - (success_requests or 0),
            "success_rate": (success_requests / total_requests * 100) if total_requests else 0,
            "avg_response_time": float(avg_response_time) if avg_response_time else 0,
            "daily_stats": daily_stats,
            "endpoint_stats": endpoint_stats
        }

    @staticmethod
    async def get_usage_logs(
        db: AsyncSession,
        *,
        api_key_id: int,
        skip: int = 0,
        limit: int = 100,
        days: int = 7
    ) -> List[APIKeyUsageLog]:
        """获取API密钥使用日志"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(APIKeyUsageLog).where(
            and_(
                APIKeyUsageLog.api_key_id == api_key_id,
                APIKeyUsageLog.created_at >= start_date
            )
        ).offset(skip).limit(limit).order_by(APIKeyUsageLog.created_at.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def check_rate_limit(
        db: AsyncSession,
        *,
        api_key: APIKey,
        window_hours: int = 1
    ) -> Dict[str, Any]:
        """检查速率限制"""
        start_time = datetime.utcnow() - timedelta(hours=window_hours)
        
        # 统计时间窗口内的请求数
        current_usage_stmt = select(func.count(APIKeyUsageLog.id)).where(
            and_(
                APIKeyUsageLog.api_key_id == api_key.id,
                APIKeyUsageLog.created_at >= start_time
            )
        )
        current_usage = await db.scalar(current_usage_stmt) or 0
        
        # 计算剩余配额
        remaining = max(0, api_key.rate_limit - current_usage)
        
        return {
            "limit": api_key.rate_limit,
            "current_usage": current_usage,
            "remaining": remaining,
            "reset_time": start_time + timedelta(hours=window_hours),
            "is_exceeded": current_usage >= api_key.rate_limit
        }

    @staticmethod
    async def cleanup_expired_keys(db: AsyncSession) -> int:
        """清理过期的API密钥"""
        now = datetime.utcnow()
        
        stmt = update(APIKey).where(
            and_(
                APIKey.expires_at.isnot(None),
                APIKey.expires_at <= now,
                APIKey.is_active == True
            )
        ).values(is_active=False)
        
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    @staticmethod
    async def get_user_key_count(db: AsyncSession, *, user_id: int) -> int:
        """获取用户活跃API密钥数量"""
        stmt = select(func.count(APIKey.id)).where(
            and_(APIKey.user_id == user_id, APIKey.is_active == True)
        )
        result = await db.scalar(stmt)
        return result or 0


# 导出CRUD实例
api_key_crud = APIKeyCRUD()