"""
安全中间件

提供API安全增强功能，包括请求限流、IP白名单、攻击检测等。
实现多层安全防护，保护应用免受常见攻击。
"""

import time
import hashlib
import json
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis.asyncio as redis

from app.core.config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件类"""
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client
        
        # 内存存储（Redis不可用时的备选方案）
        self.rate_limit_cache: Dict[str, deque] = defaultdict(deque)
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.blocked_ips: Set[str] = set()
        
        # 安全配置
        self.max_requests_per_minute = settings.RATE_LIMIT_PER_MINUTE
        self.max_failed_attempts = 5
        self.block_duration_minutes = 15
        self.suspicious_patterns = [
            r"union\s+select",
            r"drop\s+table",
            r"<script",
            r"javascript:",
            r"onload\s*=",
            r"eval\s*\(",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """处理HTTP请求"""
        start_time = time.time()
        
        try:
            # 获取客户端IP
            client_ip = self.get_client_ip(request)
            
            # 1. IP黑名单检查
            if await self.is_ip_blocked(client_ip):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "IP地址已被暂时封锁",
                        "retry_after": self.block_duration_minutes * 60
                    }
                )
            
            # 2. 请求频率限制
            if not await self.check_rate_limit(client_ip):
                await self.record_failed_attempt(client_ip)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "请求过于频繁，请稍后重试",
                        "retry_after": 60
                    }
                )
            
            # 3. 可疑请求检测
            if await self.detect_suspicious_request(request):
                await self.record_failed_attempt(client_ip, severity="high")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "请求被安全策略拒绝"}
                )
            
            # 4. 请求大小限制
            if not await self.check_request_size(request):
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "请求数据过大"}
                )
            
            # 处理请求
            response = await call_next(request)
            
            # 5. 记录成功请求
            await self.record_successful_request(client_ip)
            
            # 6. 添加安全响应头
            self.add_security_headers(response)
            
            return response
            
        except Exception as e:
            # 记录异常
            await self.record_failed_attempt(client_ip, error=str(e))
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 优先从X-Forwarded-For头获取
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # 从X-Real-IP头获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 从客户端地址获取
        return request.client.host if request.client else "unknown"
    
    async def check_rate_limit(self, client_ip: str) -> bool:
        """检查请求频率限制"""
        now = time.time()
        window_start = now - 60  # 1分钟窗口
        
        if self.redis_client:
            # 使用Redis滑动窗口限流
            try:
                key = f"rate_limit:{client_ip}"
                pipe = self.redis_client.pipeline()
                
                # 删除过期记录
                pipe.zremrangebyscore(key, 0, window_start)
                # 添加当前请求
                pipe.zadd(key, {str(now): now})
                # 设置过期时间
                pipe.expire(key, 60)
                # 获取当前窗口内的请求数
                pipe.zcard(key)
                
                results = await pipe.execute()
                current_requests = results[-1]
                
                return current_requests <= self.max_requests_per_minute
                
            except Exception:
                # Redis失败时使用内存存储
                pass
        
        # 使用内存存储的简单限流
        requests = self.rate_limit_cache[client_ip]
        
        # 清理过期请求
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # 检查限制
        if len(requests) >= self.max_requests_per_minute:
            return False
        
        # 记录当前请求
        requests.append(now)
        return True
    
    async def detect_suspicious_request(self, request: Request) -> bool:
        """检测可疑请求"""
        import re
        
        # 检查URL路径
        url_path = str(request.url.path).lower()
        
        # 检查查询参数
        query_string = str(request.url.query).lower()
        
        # 读取请求体（仅对POST/PUT请求）
        body_content = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_content = body.decode('utf-8', errors='ignore').lower()
            except Exception:
                pass
        
        # 检查所有内容
        content_to_check = f"{url_path} {query_string} {body_content}"
        
        # 使用正则表达式检查可疑模式
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content_to_check, re.IGNORECASE):
                return True
        
        # 检查过长的参数值（可能的缓冲区溢出攻击）
        for key, value in request.query_params.items():
            if len(str(value)) > 1000:  # 参数值过长
                return True
        
        return False
    
    async def check_request_size(self, request: Request) -> bool:
        """检查请求大小限制"""
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                # 限制请求大小为10MB（除了文件上传）
                max_size = settings.MAX_UPLOAD_SIZE if "/upload" in str(request.url) else 10 * 1024 * 1024
                return size <= max_size
            except ValueError:
                return False
        
        return True
    
    async def is_ip_blocked(self, client_ip: str) -> bool:
        """检查IP是否被封锁"""
        if self.redis_client:
            try:
                blocked_until = await self.redis_client.get(f"blocked_ip:{client_ip}")
                if blocked_until:
                    return float(blocked_until) > time.time()
            except Exception:
                pass
        
        # 检查内存中的封锁列表
        return client_ip in self.blocked_ips
    
    async def record_failed_attempt(
        self, 
        client_ip: str, 
        severity: str = "low",
        error: str = ""
    ):
        """记录失败尝试"""
        now = datetime.utcnow()
        
        if self.redis_client:
            try:
                key = f"failed_attempts:{client_ip}"
                # 记录失败尝试
                await self.redis_client.lpush(key, json.dumps({
                    "timestamp": now.isoformat(),
                    "severity": severity,
                    "error": error
                }))
                await self.redis_client.expire(key, self.block_duration_minutes * 60)
                
                # 检查是否需要封锁IP
                attempts_count = await self.redis_client.llen(key)
                if attempts_count >= self.max_failed_attempts:
                    block_until = time.time() + (self.block_duration_minutes * 60)
                    await self.redis_client.set(
                        f"blocked_ip:{client_ip}", 
                        block_until,
                        ex=self.block_duration_minutes * 60
                    )
                
                return
            except Exception:
                pass
        
        # 使用内存存储
        attempts = self.failed_attempts[client_ip]
        
        # 清理过期记录
        cutoff_time = now - timedelta(minutes=self.block_duration_minutes)
        attempts[:] = [attempt for attempt in attempts if attempt > cutoff_time]
        
        # 添加新记录
        attempts.append(now)
        
        # 检查是否需要封锁
        if len(attempts) >= self.max_failed_attempts:
            self.blocked_ips.add(client_ip)
            
            # 设置自动解封（简单实现）
            asyncio.create_task(self.auto_unblock_ip(client_ip))
    
    async def record_successful_request(self, client_ip: str):
        """记录成功请求"""
        # 成功请求时，可以考虑减少失败计数或清理记录
        if self.redis_client:
            try:
                # 清理部分失败记录（奖励机制）
                key = f"failed_attempts:{client_ip}"
                await self.redis_client.ltrim(key, 0, -2)  # 保留最新的记录
            except Exception:
                pass
    
    async def auto_unblock_ip(self, client_ip: str):
        """自动解封IP地址"""
        await asyncio.sleep(self.block_duration_minutes * 60)
        self.blocked_ips.discard(client_ip)
        
        # 清理失败记录
        if client_ip in self.failed_attempts:
            del self.failed_attempts[client_ip]
    
    def add_security_headers(self, response: Response):
        """添加安全响应头"""
        # 基本安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"  
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # CSP头（内容安全策略）
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "font-src 'self'",
            "object-src 'none'",
            "media-src 'self'",
            "frame-src 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # HSTS头（仅在生产环境和HTTPS下）
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # 防止MIME类型嗅探
        response.headers["X-Download-Options"] = "noopen"


class LoginAttemptTracker:
    """登录尝试追踪器"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.memory_store: Dict[str, List[datetime]] = defaultdict(list)
        
        # 配置
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        self.attempt_window = timedelta(minutes=5)
    
    async def record_failed_login(self, identifier: str, ip_address: str) -> bool:
        """记录失败的登录尝试
        
        Args:
            identifier: 用户标识（用户名或邮箱）
            ip_address: IP地址
            
        Returns:
            bool: 是否应该锁定账户
        """
        now = datetime.utcnow()
        
        # 同时追踪用户和IP
        keys = [f"failed_login_user:{identifier}", f"failed_login_ip:{ip_address}"]
        
        should_lock = False
        
        for key in keys:
            if self.redis_client:
                try:
                    # 使用Redis存储
                    await self.redis_client.lpush(key, now.isoformat())
                    await self.redis_client.expire(key, int(self.lockout_duration.total_seconds()))
                    
                    # 检查尝试次数
                    attempts = await self.redis_client.llen(key)
                    if attempts >= self.max_attempts:
                        should_lock = True
                        
                except Exception:
                    # Redis失败时使用内存存储
                    pass
            
            if not self.redis_client or key not in self.memory_store:
                # 使用内存存储
                attempts = self.memory_store[key]
                
                # 清理过期记录
                cutoff = now - self.lockout_duration
                attempts[:] = [attempt for attempt in attempts if attempt > cutoff]
                
                # 添加新记录
                attempts.append(now)
                
                # 检查是否需要锁定
                if len(attempts) >= self.max_attempts:
                    should_lock = True
        
        return should_lock
    
    async def is_locked(self, identifier: str, ip_address: str) -> bool:
        """检查账户或IP是否被锁定"""
        keys = [f"failed_login_user:{identifier}", f"failed_login_ip:{ip_address}"]
        
        for key in keys:
            if self.redis_client:
                try:
                    attempts = await self.redis_client.llen(key)
                    if attempts >= self.max_attempts:
                        return True
                except Exception:
                    pass
            
            # 检查内存存储
            if key in self.memory_store:
                now = datetime.utcnow()
                cutoff = now - self.lockout_duration
                
                # 清理过期记录
                attempts = self.memory_store[key]
                attempts[:] = [attempt for attempt in attempts if attempt > cutoff]
                
                if len(attempts) >= self.max_attempts:
                    return True
        
        return False
    
    async def record_successful_login(self, identifier: str, ip_address: str):
        """记录成功的登录尝试"""
        # 清理失败记录
        keys = [f"failed_login_user:{identifier}", f"failed_login_ip:{ip_address}"]
        
        for key in keys:
            if self.redis_client:
                try:
                    await self.redis_client.delete(key)
                except Exception:
                    pass
            
            if key in self.memory_store:
                del self.memory_store[key]


class APIKeySecurityManager:
    """API密钥安全管理器"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.api_key_usage: Dict[str, deque] = defaultdict(deque)
    
    async def validate_api_key_usage(self, api_key_hash: str, ip_address: str) -> bool:
        """验证API密钥使用情况"""
        now = time.time()
        window_start = now - 3600  # 1小时窗口
        
        key = f"api_usage:{api_key_hash}:{ip_address}"
        
        if self.redis_client:
            try:
                # 使用Redis记录使用情况
                await self.redis_client.lpush(key, now)
                await self.redis_client.expire(key, 3600)
                
                # 检查使用频率
                usage_count = await self.redis_client.llen(key)
                return usage_count <= 1000  # 每小时最多1000次
                
            except Exception:
                pass
        
        # 使用内存存储
        usage = self.api_key_usage[key]
        
        # 清理过期记录
        while usage and usage[0] < window_start:
            usage.popleft()
        
        # 检查限制
        if len(usage) >= 1000:
            return False
        
        # 记录使用
        usage.append(now)
        return True
    
    def generate_api_key_hash(self, api_key: str) -> str:
        """生成API密钥哈希"""
        return hashlib.sha256(api_key.encode()).hexdigest()


# 全局实例
login_tracker = LoginAttemptTracker()
api_key_manager = APIKeySecurityManager()

# 导出
__all__ = [
    "SecurityMiddleware",
    "LoginAttemptTracker", 
    "APIKeySecurityManager",
    "login_tracker",
    "api_key_manager"
]