"""
策略数据库操作层 (CRUD)

提供策略相关的数据库操作接口，包括策略的创建、查询、更新、删除等操作。
支持复杂查询、分页、排序和筛选功能，与TradeMaster核心模块集成。
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from app.models.database import (
    Strategy, StrategyVersion, StrategyType, StrategyStatus,
    TrainingJob, TrainingStatus, Evaluation, User
)


class StrategyCRUD:
    """策略CRUD操作类"""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        name: str,
        description: Optional[str] = None,
        strategy_type: StrategyType,
        config: Dict[str, Any],
        parameters: Dict[str, Any],
        category: Optional[str] = None,
        tags: List[str] = None,
        owner_id: int,
        parent_strategy_id: Optional[int] = None
    ) -> Strategy:
        """创建新策略
        
        Args:
            db: 数据库会话
            name: 策略名称
            description: 策略描述
            strategy_type: 策略类型
            config: 策略配置
            parameters: 策略参数
            category: 策略分类
            tags: 标签列表
            owner_id: 所有者ID
            parent_strategy_id: 父策略ID
            
        Returns:
            Strategy: 创建的策略对象
            
        Raises:
            HTTPException: 当策略名称重复时抛出异常
        """
        # 检查同用户下策略名称是否重复
        existing_strategy = await self.get_by_name_and_owner(db, name=name, owner_id=owner_id)
        if existing_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略名称 '{name}' 已存在"
            )
        
        # 创建策略对象
        strategy = Strategy(
            name=name,
            description=description,
            strategy_type=strategy_type,
            config=config,
            parameters=parameters,
            category=category,
            tags=tags or [],
            owner_id=owner_id,
            parent_strategy_id=parent_strategy_id,
            status=StrategyStatus.DRAFT,
            version="1.0.0"
        )
        
        db.add(strategy)
        await db.commit()
        await db.refresh(strategy)
        
        return strategy
    
    async def get(
        self, 
        db: AsyncSession, 
        strategy_id: int,
        load_relations: bool = False
    ) -> Optional[Strategy]:
        """根据ID获取策略
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            load_relations: 是否加载关联对象
            
        Returns:
            Optional[Strategy]: 策略对象或None
        """
        stmt = select(Strategy).where(Strategy.id == strategy_id)
        
        if load_relations:
            stmt = stmt.options(
                selectinload(Strategy.versions),
                selectinload(Strategy.training_jobs),
                selectinload(Strategy.evaluations),
                joinedload(Strategy.owner)
            )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_uuid(
        self, 
        db: AsyncSession, 
        uuid: str,
        load_relations: bool = False
    ) -> Optional[Strategy]:
        """根据UUID获取策略
        
        Args:
            db: 数据库会话
            uuid: 策略UUID
            load_relations: 是否加载关联对象
            
        Returns:
            Optional[Strategy]: 策略对象或None
        """
        stmt = select(Strategy).where(Strategy.uuid == uuid)
        
        if load_relations:
            stmt = stmt.options(
                selectinload(Strategy.versions),
                selectinload(Strategy.training_jobs),
                selectinload(Strategy.evaluations),
                joinedload(Strategy.owner)
            )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name_and_owner(
        self,
        db: AsyncSession,
        *,
        name: str,
        owner_id: int
    ) -> Optional[Strategy]:
        """根据名称和所有者获取策略
        
        Args:
            db: 数据库会话
            name: 策略名称
            owner_id: 所有者ID
            
        Returns:
            Optional[Strategy]: 策略对象或None
        """
        stmt = select(Strategy).where(
            and_(Strategy.name == name, Strategy.owner_id == owner_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 20,
        owner_id: Optional[int] = None,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        load_relations: bool = False
    ) -> List[Strategy]:
        """获取策略列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回的记录数
            owner_id: 所有者ID筛选
            strategy_type: 策略类型筛选
            status: 状态筛选
            category: 分类筛选
            tags: 标签筛选
            search: 搜索关键词
            sort_by: 排序字段
            sort_order: 排序顺序
            load_relations: 是否加载关联对象
            
        Returns:
            List[Strategy]: 策略列表
        """
        stmt = select(Strategy)
        
        # 构建查询条件
        conditions = []
        
        if owner_id is not None:
            conditions.append(Strategy.owner_id == owner_id)
        
        if strategy_type is not None:
            conditions.append(Strategy.strategy_type == strategy_type)
        
        if status is not None:
            conditions.append(Strategy.status == status)
        
        if category is not None:
            conditions.append(Strategy.category == category)
        
        if tags:
            # 使用PostgreSQL数组操作符检查标签
            for tag in tags:
                conditions.append(Strategy.tags.any(tag))
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Strategy.name.ilike(search_term),
                    Strategy.description.ilike(search_term),
                    Strategy.category.ilike(search_term)
                )
            )
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 加载关联对象
        if load_relations:
            stmt = stmt.options(
                joinedload(Strategy.owner),
                selectinload(Strategy.versions),
                selectinload(Strategy.training_jobs),
                selectinload(Strategy.evaluations)
            )
        
        # 排序
        if hasattr(Strategy, sort_by):
            order_column = getattr(Strategy, sort_by)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(desc(order_column))
            else:
                stmt = stmt.order_by(asc(order_column))
        
        # 分页
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().unique().all()
    
    async def count(
        self,
        db: AsyncSession,
        *,
        owner_id: Optional[int] = None,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> int:
        """统计策略数量
        
        Args:
            db: 数据库会话
            owner_id: 所有者ID筛选
            strategy_type: 策略类型筛选
            status: 状态筛选
            category: 分类筛选
            tags: 标签筛选
            search: 搜索关键词
            
        Returns:
            int: 策略数量
        """
        stmt = select(func.count(Strategy.id))
        
        # 构建查询条件
        conditions = []
        
        if owner_id is not None:
            conditions.append(Strategy.owner_id == owner_id)
        
        if strategy_type is not None:
            conditions.append(Strategy.strategy_type == strategy_type)
        
        if status is not None:
            conditions.append(Strategy.status == status)
        
        if category is not None:
            conditions.append(Strategy.category == category)
        
        if tags:
            for tag in tags:
                conditions.append(Strategy.tags.any(tag))
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Strategy.name.ilike(search_term),
                    Strategy.description.ilike(search_term),
                    Strategy.category.ilike(search_term)
                )
            )
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        result = await db.execute(stmt)
        return result.scalar()
    
    async def update(
        self,
        db: AsyncSession,
        *,
        strategy: Strategy,
        update_data: Dict[str, Any]
    ) -> Strategy:
        """更新策略信息
        
        Args:
            db: 数据库会话
            strategy: 策略对象
            update_data: 更新数据字典
            
        Returns:
            Strategy: 更新后的策略对象
        """
        # 过滤允许更新的字段
        allowed_fields = {
            'name', 'description', 'category', 'tags', 
            'config', 'parameters', 'status'
        }
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(strategy, field):
                # 特殊处理需要验证唯一性的字段
                if field == 'name' and value != strategy.name:
                    existing = await self.get_by_name_and_owner(
                        db, name=value, owner_id=strategy.owner_id
                    )
                    if existing and existing.id != strategy.id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"策略名称 '{value}' 已存在"
                        )
                
                setattr(strategy, field, value)
        
        await db.commit()
        await db.refresh(strategy)
        return strategy
    
    async def update_status(
        self,
        db: AsyncSession,
        *,
        strategy: Strategy,
        new_status: StrategyStatus,
        reason: Optional[str] = None
    ) -> Strategy:
        """更新策略状态
        
        Args:
            db: 数据库会话
            strategy: 策略对象
            new_status: 新状态
            reason: 状态变更原因
            
        Returns:
            Strategy: 更新后的策略对象
        """
        strategy.status = new_status
        
        # 记录状态变更时间
        if new_status == StrategyStatus.ACTIVE:
            strategy.last_run_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(strategy)
        return strategy
    
    async def update_performance(
        self,
        db: AsyncSession,
        *,
        strategy: Strategy,
        total_return: Optional[float] = None,
        sharpe_ratio: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        win_rate: Optional[float] = None
    ) -> Strategy:
        """更新策略性能指标
        
        Args:
            db: 数据库会话
            strategy: 策略对象
            total_return: 总收益率
            sharpe_ratio: 夏普比率
            max_drawdown: 最大回撤
            win_rate: 胜率
            
        Returns:
            Strategy: 更新后的策略对象
        """
        if total_return is not None:
            strategy.total_return = total_return
        if sharpe_ratio is not None:
            strategy.sharpe_ratio = sharpe_ratio
        if max_drawdown is not None:
            strategy.max_drawdown = max_drawdown
        if win_rate is not None:
            strategy.win_rate = win_rate
        
        await db.commit()
        await db.refresh(strategy)
        return strategy
    
    async def delete(self, db: AsyncSession, *, strategy_id: int) -> bool:
        """删除策略
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            
        Returns:
            bool: 是否删除成功
        """
        stmt = delete(Strategy).where(Strategy.id == strategy_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    
    async def get_user_strategies(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[StrategyStatus] = None
    ) -> List[Strategy]:
        """获取用户的策略列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 限制返回的记录数
            status: 状态筛选
            
        Returns:
            List[Strategy]: 策略列表
        """
        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            owner_id=user_id,
            status=status,
            sort_by="updated_at",
            sort_order="desc"
        )
    
    async def get_active_strategies(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None
    ) -> List[Strategy]:
        """获取活跃策略列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID筛选
            
        Returns:
            List[Strategy]: 活跃策略列表
        """
        return await self.get_multi(
            db,
            owner_id=user_id,
            status=StrategyStatus.ACTIVE,
            sort_by="last_run_at",
            sort_order="desc"
        )
    
    async def search_strategies(
        self,
        db: AsyncSession,
        *,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Strategy]:
        """搜索策略
        
        Args:
            db: 数据库会话
            query: 搜索关键词
            user_id: 用户ID筛选
            limit: 限制返回的记录数
            
        Returns:
            List[Strategy]: 搜索结果列表
        """
        return await self.get_multi(
            db,
            owner_id=user_id,
            search=query,
            limit=limit,
            sort_by="updated_at",
            sort_order="desc"
        )
    
    async def get_strategy_stats(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取策略统计信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID筛选
            
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        base_conditions = []
        if user_id is not None:
            base_conditions.append(Strategy.owner_id == user_id)
        
        base_stmt = select(func.count(Strategy.id))
        if base_conditions:
            base_stmt = base_stmt.where(and_(*base_conditions))
        
        # 总策略数
        total_strategies = await db.scalar(base_stmt)
        
        # 按状态分布
        status_stats = {}
        for status in StrategyStatus:
            conditions = base_conditions.copy()
            conditions.append(Strategy.status == status)
            count = await db.scalar(
                select(func.count(Strategy.id)).where(and_(*conditions))
            )
            status_stats[status.value] = count
        
        # 按类型分布
        type_stats = {}
        for strategy_type in StrategyType:
            conditions = base_conditions.copy()
            conditions.append(Strategy.strategy_type == strategy_type)
            count = await db.scalar(
                select(func.count(Strategy.id)).where(and_(*conditions))
            )
            type_stats[strategy_type.value] = count
        
        # 性能统计
        performance_stmt = select(
            func.avg(Strategy.total_return),
            func.avg(Strategy.sharpe_ratio),
            func.avg(Strategy.max_drawdown),
            func.avg(Strategy.win_rate)
        )
        if base_conditions:
            performance_stmt = performance_stmt.where(and_(*base_conditions))
        
        performance_result = await db.execute(performance_stmt)
        avg_return, avg_sharpe, avg_drawdown, avg_win_rate = performance_result.first()
        
        # 最近30天创建的策略数
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_conditions = base_conditions.copy()
        recent_conditions.append(Strategy.created_at >= thirty_days_ago)
        recent_strategies = await db.scalar(
            select(func.count(Strategy.id)).where(and_(*recent_conditions))
        )
        
        return {
            "total_strategies": total_strategies,
            "active_strategies": status_stats.get("active", 0),
            "draft_strategies": status_stats.get("draft", 0),
            "status_distribution": status_stats,
            "type_distribution": type_stats,
            "avg_return": float(avg_return) if avg_return else None,
            "avg_sharpe_ratio": float(avg_sharpe) if avg_sharpe else None,
            "avg_max_drawdown": float(avg_drawdown) if avg_drawdown else None,
            "avg_win_rate": float(avg_win_rate) if avg_win_rate else None,
            "recent_strategies": recent_strategies
        }


class StrategyVersionCRUD:
    """策略版本CRUD操作类"""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        strategy_id: int,
        version: str,
        config: Dict[str, Any],
        parameters: Dict[str, Any],
        changelog: Optional[str] = None,
        is_active: bool = False,
        created_by: Optional[int] = None
    ) -> StrategyVersion:
        """创建策略版本
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            version: 版本号
            config: 版本配置
            parameters: 版本参数
            changelog: 变更日志
            is_active: 是否为活跃版本
            created_by: 创建者ID
            
        Returns:
            StrategyVersion: 创建的版本对象
        """
        # 如果设置为活跃版本，需要先停用其他版本
        if is_active:
            await db.execute(
                update(StrategyVersion)
                .where(StrategyVersion.strategy_id == strategy_id)
                .values(is_active=False)
            )
        
        strategy_version = StrategyVersion(
            strategy_id=strategy_id,
            version=version,
            config=config,
            parameters=parameters,
            changelog=changelog,
            is_active=is_active,
            created_by=created_by
        )
        
        db.add(strategy_version)
        await db.commit()
        await db.refresh(strategy_version)
        
        return strategy_version
    
    async def get_strategy_versions(
        self,
        db: AsyncSession,
        *,
        strategy_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[StrategyVersion]:
        """获取策略的版本列表
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            skip: 跳过的记录数
            limit: 限制返回的记录数
            
        Returns:
            List[StrategyVersion]: 版本列表
        """
        stmt = select(StrategyVersion).where(
            StrategyVersion.strategy_id == strategy_id
        ).order_by(desc(StrategyVersion.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_active_version(
        self,
        db: AsyncSession,
        *,
        strategy_id: int
    ) -> Optional[StrategyVersion]:
        """获取策略的活跃版本
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            
        Returns:
            Optional[StrategyVersion]: 活跃版本或None
        """
        stmt = select(StrategyVersion).where(
            and_(
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.is_active == True
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# 全局实例
strategy_crud = StrategyCRUD()
strategy_version_crud = StrategyVersionCRUD()

# 导出
__all__ = [
    "StrategyCRUD", "StrategyVersionCRUD",
    "strategy_crud", "strategy_version_crud"
]