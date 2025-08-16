"""
策略缓存管理模块

提供策略相关数据的缓存机制，包括策略信息、配置模板、性能数据等。
支持Redis和内存缓存，提供缓存预热、失效和刷新机制。
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib

from loguru import logger
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import Strategy, StrategyType, StrategyStatus


class CacheKey:
    """缓存键管理类"""
    
    # 策略相关缓存键
    STRATEGY_INFO = "strategy:info:{strategy_id}"
    STRATEGY_LIST = "strategy:list:{user_id}:{filters_hash}"
    STRATEGY_STATS = "strategy:stats:{user_id}"
    STRATEGY_PERFORMANCE = "strategy:performance:{strategy_id}"
    
    # 模板相关缓存键
    TEMPLATE_LIST = "template:list:{strategy_type}"
    TEMPLATE_INFO = "template:info:{template_name}"
    
    # 配置相关缓存键
    CONFIG_VALIDATION = "config:validation:{config_hash}"
    
    # 用户相关缓存键
    USER_STRATEGIES = "user:strategies:{user_id}"
    USER_QUOTA = "user:quota:{user_id}"
    
    @classmethod
    def format_key(cls, key_template: str, **kwargs) -> str:
        """格式化缓存键
        
        Args:
            key_template: 键模板
            **kwargs: 格式化参数
            
        Returns:
            str: 格式化后的键
        """
        return key_template.format(**kwargs)
    
    @classmethod
    def create_hash(cls, data: Any) -> str:
        """创建数据哈希
        
        Args:
            data: 数据对象
            
        Returns:
            str: 哈希值
        """
        if isinstance(data, dict):
            # 对字典进行排序后序列化
            sorted_data = json.dumps(data, sort_keys=True)
        else:
            sorted_data = str(data)
        
        return hashlib.md5(sorted_data.encode()).hexdigest()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self.redis_client: Optional[aioredis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
        
        # 缓存配置
        self.default_ttl = 3600  # 1小时
        self.memory_cache_size = 1000  # 内存缓存最大条目数
        
        logger.info("缓存管理器初始化完成")
    
    async def initialize(self):
        """初始化缓存连接"""
        try:
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                self.redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                # 测试连接
                await self.redis_client.ping()
                logger.info("Redis缓存连接成功")
            else:
                logger.info("未配置Redis，使用内存缓存")
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存缓存: {str(e)}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存数据或None
        """
        try:
            # 优先从Redis获取
            if self.redis_client:
                data = await self.redis_client.get(key)
                if data:
                    self.cache_stats["hits"] += 1
                    return json.loads(data)
            
            # 从内存缓存获取
            if key in self.memory_cache:
                cache_item = self.memory_cache[key]
                # 检查是否过期
                if cache_item["expires_at"] > datetime.utcnow():
                    self.cache_stats["hits"] += 1
                    return cache_item["data"]
                else:
                    # 删除过期项
                    del self.memory_cache[key]
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"缓存获取失败: {key}, {str(e)}")
            self.cache_stats["misses"] += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            
            # 设置Redis缓存
            if self.redis_client:
                await self.redis_client.setex(key, ttl, serialized_value)
            
            # 设置内存缓存
            # 如果内存缓存满了，删除最旧的项
            if len(self.memory_cache) >= self.memory_cache_size:
                oldest_key = min(
                    self.memory_cache.keys(),
                    key=lambda k: self.memory_cache[k]["created_at"]
                )
                del self.memory_cache[oldest_key]
            
            self.memory_cache[key] = {
                "data": value,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
            }
            
            self.cache_stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"缓存设置失败: {key}, {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 删除Redis缓存
            if self.redis_client:
                await self.redis_client.delete(key)
            
            # 删除内存缓存
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            self.cache_stats["deletes"] += 1
            return True
            
        except Exception as e:
            logger.error(f"缓存删除失败: {key}, {str(e)}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存
        
        Args:
            pattern: 缓存键模式
            
        Returns:
            int: 删除的键数量
        """
        deleted_count = 0
        
        try:
            # 删除Redis缓存
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
            
            # 删除内存缓存
            import fnmatch
            keys_to_delete = [
                key for key in self.memory_cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in keys_to_delete:
                del self.memory_cache[key]
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"模式删除缓存失败: {pattern}, {str(e)}")
            return deleted_count
    
    async def clear_all(self) -> bool:
        """清空所有缓存
        
        Returns:
            bool: 是否清空成功
        """
        try:
            # 清空Redis缓存
            if self.redis_client:
                await self.redis_client.flushdb()
            
            # 清空内存缓存
            self.memory_cache.clear()
            
            logger.info("所有缓存已清空")
            return True
            
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            self.cache_stats["hits"] / total_requests * 100 
            if total_requests > 0 else 0
        )
        
        return {
            **self.cache_stats,
            "hit_rate": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache),
            "redis_connected": self.redis_client is not None
        }


# 全局缓存管理器实例
_cache_manager = None

async def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例
    
    Returns:
        CacheManager: 缓存管理器实例
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.initialize()
    return _cache_manager


# 缓存装饰器
def cached(
    key_template: str,
    ttl: int = 3600,
    key_params: Optional[List[str]] = None
):
    """缓存装饰器
    
    Args:
        key_template: 缓存键模板
        ttl: 缓存时间（秒）
        key_params: 用于生成缓存键的参数名列表
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = await get_cache_manager()
            
            # 生成缓存键
            key_values = {}
            if key_params:
                # 从函数参数中提取键值
                func_args = func.__code__.co_varnames[:func.__code__.co_argcount]
                arg_dict = dict(zip(func_args, args))
                arg_dict.update(kwargs)
                
                for param in key_params:
                    if param in arg_dict:
                        key_values[param] = arg_dict[param]
            
            cache_key = CacheKey.format_key(key_template, **key_values)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# 策略缓存服务
class StrategyCacheService:
    """策略缓存服务"""
    
    def __init__(self):
        self.cache_manager: Optional[CacheManager] = None
    
    async def _get_cache_manager(self) -> CacheManager:
        """获取缓存管理器"""
        if self.cache_manager is None:
            self.cache_manager = await get_cache_manager()
        return self.cache_manager
    
    async def cache_strategy_info(
        self, 
        strategy: Strategy, 
        ttl: int = 3600
    ) -> bool:
        """缓存策略信息
        
        Args:
            strategy: 策略对象
            ttl: 缓存时间
            
        Returns:
            bool: 是否缓存成功
        """
        cache_manager = await self._get_cache_manager()
        key = CacheKey.format_key(
            CacheKey.STRATEGY_INFO,
            strategy_id=strategy.id
        )
        
        strategy_data = {
            "id": strategy.id,
            "name": strategy.name,
            "description": strategy.description,
            "strategy_type": strategy.strategy_type.value,
            "status": strategy.status.value,
            "owner_id": strategy.owner_id,
            "created_at": strategy.created_at.isoformat(),
            "updated_at": strategy.updated_at.isoformat()
        }
        
        return await cache_manager.set(key, strategy_data, ttl)
    
    async def get_cached_strategy_info(
        self, 
        strategy_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的策略信息
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            Optional[Dict[str, Any]]: 策略信息或None
        """
        cache_manager = await self._get_cache_manager()
        key = CacheKey.format_key(
            CacheKey.STRATEGY_INFO,
            strategy_id=strategy_id
        )
        
        return await cache_manager.get(key)
    
    async def invalidate_strategy_cache(self, strategy_id: int) -> int:
        """使策略相关缓存失效
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            int: 删除的缓存项数量
        """
        cache_manager = await self._get_cache_manager()
        
        # 删除策略相关的所有缓存
        patterns = [
            f"strategy:info:{strategy_id}",
            f"strategy:performance:{strategy_id}",
            f"strategy:list:*",  # 策略列表缓存需要全部清除
            f"strategy:stats:*"  # 统计缓存需要全部清除
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await cache_manager.delete_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted
    
    async def warm_up_cache(
        self, 
        strategies: List[Strategy]
    ) -> int:
        """预热策略缓存
        
        Args:
            strategies: 策略列表
            
        Returns:
            int: 缓存的策略数量
        """
        cached_count = 0
        
        for strategy in strategies:
            success = await self.cache_strategy_info(strategy)
            if success:
                cached_count += 1
        
        logger.info(f"策略缓存预热完成: {cached_count}/{len(strategies)}")
        return cached_count


# 全局策略缓存服务实例
_strategy_cache_service = None

def get_strategy_cache_service() -> StrategyCacheService:
    """获取策略缓存服务实例
    
    Returns:
        StrategyCacheService: 策略缓存服务实例
    """
    global _strategy_cache_service
    if _strategy_cache_service is None:
        _strategy_cache_service = StrategyCacheService()
    return _strategy_cache_service


# 导出主要组件
__all__ = [
    "CacheKey",
    "CacheManager",
    "get_cache_manager",
    "cached",
    "StrategyCacheService",
    "get_strategy_cache_service"
]