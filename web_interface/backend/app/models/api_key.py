"""
API密钥数据模型

用于管理用户API密钥，支持密钥生成、权限控制、使用追踪等功能。
"""

from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import hashlib

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class APIKey(Base):
    """API密钥模型"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    
    # 密钥信息
    name = Column(String(100), nullable=False, comment="密钥名称")
    key_hash = Column(String(64), unique=True, nullable=False, comment="密钥哈希值")
    key_prefix = Column(String(10), nullable=False, comment="密钥前缀（用于显示）")
    
    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 权限设置
    permissions = Column(Text, comment="权限列表（JSON格式）")
    ip_whitelist = Column(Text, comment="IP白名单（JSON格式）")
    
    # 使用限制
    rate_limit = Column(Integer, default=1000, comment="每小时请求限制")
    usage_count = Column(Integer, default=0, comment="总使用次数")
    last_used_at = Column(DateTime, comment="最后使用时间")
    
    # 状态管理
    is_active = Column(Boolean, default=True, comment="是否激活")
    expires_at = Column(DateTime, comment="过期时间")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="api_keys")
    
    # 索引
    __table_args__ = (
        Index('idx_api_keys_user_id', 'user_id'),
        Index('idx_api_keys_key_hash', 'key_hash'),
        Index('idx_api_keys_active', 'is_active'),
        Index('idx_api_keys_expires', 'expires_at'),
    )
    
    @classmethod
    def generate_key(cls) -> tuple[str, str]:
        """生成新的API密钥
        
        Returns:
            tuple: (完整密钥, 密钥哈希)
        """
        # 生成32字节随机密钥
        key = secrets.token_urlsafe(32)
        
        # 生成哈希值用于存储
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        return key, key_hash
    
    @classmethod
    def hash_key(cls, key: str) -> str:
        """对密钥进行哈希处理"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def is_expired(self) -> bool:
        """检查密钥是否过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """检查密钥是否有效"""
        return self.is_active and not self.is_expired()
    
    def get_display_key(self) -> str:
        """获取用于显示的密钥（隐藏大部分内容）"""
        return f"{self.key_prefix}...{self.key_hash[-8:]}"
    
    def record_usage(self):
        """记录使用情况"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class APIKeyUsageLog(Base):
    """API密钥使用日志模型"""
    __tablename__ = "api_key_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 关联信息
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, comment="API密钥ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 请求信息
    endpoint = Column(String(200), comment="请求端点")
    method = Column(String(10), comment="请求方法")
    ip_address = Column(String(45), comment="客户端IP地址")
    user_agent = Column(Text, comment="用户代理")
    
    # 响应信息
    status_code = Column(Integer, comment="响应状态码")
    response_time = Column(Integer, comment="响应时间（毫秒）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    api_key = relationship("APIKey")
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('idx_api_key_logs_key_id', 'api_key_id'),
        Index('idx_api_key_logs_user_id', 'user_id'),
        Index('idx_api_key_logs_created_at', 'created_at'),
        Index('idx_api_key_logs_endpoint', 'endpoint'),
    )
    
    def __repr__(self):
        return f"<APIKeyUsageLog(id={self.id}, api_key_id={self.api_key_id}, endpoint='{self.endpoint}')>"