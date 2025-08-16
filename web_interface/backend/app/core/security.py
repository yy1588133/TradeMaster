"""
安全认证系统

提供JWT令牌生成和验证、密码加密和验证、权限管理等安全功能。
实现现代化的安全机制，包括访问令牌、刷新令牌、密码策略等。
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict, List
from enum import Enum

from jose import jwt, JWTError
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import HTTPException, status

from app.core.config import settings


# 密码上下文配置
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12  # 增加加密轮数提高安全性
)


class TokenType(str, Enum):
    """Token类型枚举"""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    ANALYST = "analyst"


class Permission(str, Enum):
    """权限枚举"""
    # 策略相关权限
    CREATE_STRATEGY = "create_strategy"
    READ_STRATEGY = "read_strategy"
    UPDATE_STRATEGY = "update_strategy"
    DELETE_STRATEGY = "delete_strategy"
    EXECUTE_STRATEGY = "execute_strategy"
    
    # 数据相关权限
    UPLOAD_DATA = "upload_data"
    READ_DATA = "read_data" 
    DELETE_DATA = "delete_data"
    PROCESS_DATA = "process_data"
    
    # 训练相关权限
    CREATE_TRAINING = "create_training"
    READ_TRAINING = "read_training"
    STOP_TRAINING = "stop_training"
    DELETE_TRAINING = "delete_training"
    
    # 分析相关权限
    READ_ANALYSIS = "read_analysis"
    CREATE_ANALYSIS = "create_analysis"
    EXPORT_ANALYSIS = "export_analysis"
    
    # 系统管理权限
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"


# 角色权限映射
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [p for p in Permission],  # 管理员拥有所有权限
    UserRole.USER: [
        Permission.CREATE_STRATEGY, Permission.READ_STRATEGY, 
        Permission.UPDATE_STRATEGY, Permission.DELETE_STRATEGY, 
        Permission.EXECUTE_STRATEGY,
        Permission.UPLOAD_DATA, Permission.READ_DATA, Permission.PROCESS_DATA,
        Permission.CREATE_TRAINING, Permission.READ_TRAINING, Permission.STOP_TRAINING,
        Permission.READ_ANALYSIS, Permission.CREATE_ANALYSIS, Permission.EXPORT_ANALYSIS,
    ],
    UserRole.ANALYST: [
        Permission.READ_STRATEGY, Permission.READ_DATA,
        Permission.READ_TRAINING, Permission.READ_ANALYSIS, 
        Permission.CREATE_ANALYSIS, Permission.EXPORT_ANALYSIS,
    ],
    UserRole.VIEWER: [
        Permission.READ_STRATEGY, Permission.READ_DATA,
        Permission.READ_TRAINING, Permission.READ_ANALYSIS,
    ],
}


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """创建访问令牌
    
    Args:
        subject: 令牌主体（通常是用户ID）
        expires_delta: 过期时间间隔
        additional_claims: 额外的声明信息
        
    Returns:
        JWT访问令牌字符串
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": TokenType.ACCESS.value,
        "iat": datetime.utcnow(),
        "jti": generate_token_id()  # JWT ID for token revocation
    }
    
    # 添加额外声明
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """创建刷新令牌
    
    Args:
        subject: 令牌主体（通常是用户ID）
        additional_claims: 额外的声明信息
        
    Returns:
        JWT刷新令牌字符串
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": TokenType.REFRESH.value,
        "iat": datetime.utcnow(),
        "jti": generate_token_id()
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_password_reset_token(email: str) -> str:
    """创建密码重置令牌
    
    Args:
        email: 用户邮箱
        
    Returns:
        密码重置令牌字符串
    """
    expire = datetime.utcnow() + timedelta(hours=1)  # 1小时有效期
    
    to_encode = {
        "exp": expire,
        "sub": email,
        "type": TokenType.RESET_PASSWORD.value,
        "iat": datetime.utcnow(),
        "jti": generate_token_id()
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_email_verification_token(email: str) -> str:
    """创建邮箱验证令牌
    
    Args:
        email: 用户邮箱
        
    Returns:
        邮箱验证令牌字符串
    """
    expire = datetime.utcnow() + timedelta(days=1)  # 24小时有效期
    
    to_encode = {
        "exp": expire,
        "sub": email,
        "type": TokenType.EMAIL_VERIFICATION.value,
        "iat": datetime.utcnow(),
        "jti": generate_token_id()
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(
    token: str, 
    expected_type: Optional[TokenType] = None
) -> Dict[str, Any]:
    """验证JWT令牌
    
    Args:
        token: JWT令牌字符串
        expected_type: 期望的令牌类型
        
    Returns:
        令牌载荷字典
        
    Raises:
        HTTPException: 当令牌无效时抛出异常
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # 检查令牌类型
        if expected_type and payload.get("type") != expected_type.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌类型不匹配",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"令牌验证失败: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_subject_from_token(token: str) -> str:
    """从令牌中获取主体信息
    
    Args:
        token: JWT令牌字符串
        
    Returns:
        令牌主体字符串
    """
    payload = verify_token(token)
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌缺少主体信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return subject


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        密码是否匹配
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        哈希密码字符串
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """验证密码强度
    
    Args:
        password: 待验证的密码
        
    Returns:
        验证结果字典，包含是否有效和错误信息
    """
    errors = []
    
    # 检查最小长度
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        errors.append(f"密码长度至少需要{settings.MIN_PASSWORD_LENGTH}个字符")
    
    # 检查字符类型
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_upper:
        errors.append("密码必须包含至少一个大写字母")
    if not has_lower:
        errors.append("密码必须包含至少一个小写字母")
    if not has_digit:
        errors.append("密码必须包含至少一个数字")
    
    if settings.REQUIRE_SPECIAL_CHARS and not has_special:
        errors.append("密码必须包含至少一个特殊字符")
    
    # 检查常见弱密码
    weak_passwords = [
        "password", "123456", "123456789", "qwerty", 
        "abc123", "password123", "admin", "root"
    ]
    if password.lower() in weak_passwords:
        errors.append("不能使用常见的弱密码")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "strength_score": calculate_password_strength_score(password)
    }


def calculate_password_strength_score(password: str) -> int:
    """计算密码强度分数（0-100）
    
    Args:
        password: 密码字符串
        
    Returns:
        强度分数（0-100）
    """
    score = 0
    
    # 长度加分
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    if len(password) >= 16:
        score += 10
    
    # 字符类型加分
    if any(c.isupper() for c in password):
        score += 15
    if any(c.islower() for c in password):
        score += 15
    if any(c.isdigit() for c in password):
        score += 15
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 15
    
    return min(score, 100)


def generate_token_id() -> str:
    """生成随机令牌ID
    
    Returns:
        随机令牌ID字符串
    """
    return secrets.token_urlsafe(16)


def generate_random_password(length: int = 12) -> str:
    """生成随机密码
    
    Args:
        length: 密码长度
        
    Returns:
        随机密码字符串
    """
    # 确保包含各种字符类型
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # 至少包含一个大写字母、小写字母、数字和特殊字符
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*")
    ]
    
    # 填充剩余长度
    for _ in range(length - 4):
        password.append(secrets.choice(chars))
    
    # 打乱顺序
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def check_user_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """检查用户权限
    
    Args:
        user_role: 用户角色
        required_permission: 需要的权限
        
    Returns:
        是否有权限
    """
    user_permissions = ROLE_PERMISSIONS.get(user_role, [])
    return required_permission in user_permissions


def get_user_permissions(user_role: UserRole) -> List[Permission]:
    """获取用户的所有权限
    
    Args:
        user_role: 用户角色
        
    Returns:
        权限列表
    """
    return ROLE_PERMISSIONS.get(user_role, [])


def create_api_key(user_id: str, name: str, expires_days: int = 365) -> str:
    """创建API密钥
    
    Args:
        user_id: 用户ID
        name: API密钥名称
        expires_days: 过期天数
        
    Returns:
        API密钥字符串
    """
    expire = datetime.utcnow() + timedelta(days=expires_days)
    
    to_encode = {
        "exp": expire,
        "sub": user_id,
        "type": "api_key",
        "name": name,
        "iat": datetime.utcnow(),
        "jti": generate_token_id()
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_api_key(api_key: str) -> Dict[str, Any]:
    """验证API密钥
    
    Args:
        api_key: API密钥字符串
        
    Returns:
        API密钥信息字典
        
    Raises:
        HTTPException: 当API密钥无效时抛出异常
    """
    try:
        payload = jwt.decode(
            api_key, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "api_key":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的API密钥类型"
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥"
        )


# 导出主要功能
__all__ = [
    "create_access_token",
    "create_refresh_token", 
    "create_password_reset_token",
    "create_email_verification_token",
    "verify_token",
    "get_subject_from_token",
    "verify_password",
    "get_password_hash",
    "validate_password_strength",
    "generate_random_password",
    "check_user_permission",
    "get_user_permissions",
    "create_api_key",
    "verify_api_key",
    "TokenType",
    "UserRole", 
    "Permission",
    "ROLE_PERMISSIONS"
]