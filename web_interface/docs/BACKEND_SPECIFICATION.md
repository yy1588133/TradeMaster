# 后端技术规范与架构设计

## 🎯 技术栈选型

### 核心框架
- **FastAPI 0.95+**: 现代高性能Web框架，自动API文档生成
- **Python 3.8+**: 稳定版本，支持类型注解
- **Uvicorn**: ASGI服务器，支持异步处理

### 数据库与存储
- **PostgreSQL 13+**: 主数据库，ACID事务支持
- **Redis 6+**: 缓存和会话存储
- **SQLAlchemy 2.0**: ORM框架，支持异步操作
- **Alembic**: 数据库迁移工具

### 异步任务处理
- **Celery 5.3+**: 分布式任务队列
- **RabbitMQ/Redis**: 消息代理
- **Flower**: Celery监控工具

### 认证与安全
- **PyJWT**: JWT token处理  
- **Passlib**: 密码哈希
- **python-multipart**: 文件上传支持
- **cryptography**: 加密解密

### 数据验证与序列化
- **Pydantic 2.0+**: 数据验证和序列化
- **email-validator**: 邮箱验证
- **python-decouple**: 环境变量管理

### 开发工具
- **Black**: 代码格式化
- **isort**: 导入排序
- **Flake8**: 代码检查
- **MyPy**: 类型检查
- **Pytest**: 测试框架

## 📋 Requirements.txt 配置

```text
# requirements/base.txt - 基础依赖
fastapi==0.95.1
uvicorn[standard]==0.21.1
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-decouple==3.8
pydantic==2.0.2
pydantic-settings==2.0.1
email-validator==2.0.0

# 数据库
sqlalchemy==2.0.13
asyncpg==0.27.0
alembic==1.10.3
psycopg2-binary==2.9.6

# Redis
redis==4.5.4
aioredis==2.0.1

# 异步任务
celery==5.3.0
flower==2.0.1

# HTTP客户端
httpx==0.24.1
aiofiles==23.1.0

# 工具
loguru==0.7.0
structlog==23.1.0
click==8.1.3
typer==0.9.0
rich==13.3.5

# 监控
prometheus-client==0.16.0
sentry-sdk[fastapi]==1.21.1

# requirements/dev.txt - 开发依赖
-r base.txt
pytest==7.3.1
pytest-asyncio==0.21.0
pytest-cov==4.0.0
pytest-mock==3.10.0
httpx==0.24.1
black==23.3.0
isort==5.12.0
flake8==6.0.0
mypy==1.3.0
pre-commit==3.3.2
factory-boy==3.2.1

# requirements/prod.txt - 生产依赖
-r base.txt
gunicorn==20.1.0
```

## ⚙️ FastAPI 应用配置

### 应用入口文件

```python
# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
import time
import uuid

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing import TimingMiddleware

# 设置日志
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TradeMaster Web Interface API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# 中间件配置
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TimingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error"
            },
            "request_id": request.state.request_id,
            "timestamp": int(time.time())
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "type": "validation_error",
                "details": exc.errors()
            },
            "request_id": request.state.request_id,
            "timestamp": int(time.time())
        }
    )

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": settings.VERSION
    }

# API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # 使用自定义日志配置
    )
```

### 核心配置

```python
# app/core/config.py
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, PostgresDsn, validator, HttpUrl
from pydantic.networks import AnyHttpUrl

class Settings(BaseSettings):
    # 基础配置
    PROJECT_NAME: str = "TradeMaster Web Interface"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # 安全配置
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # 服务器配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 数据库配置
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # Celery配置
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    
    # TradeMaster集成配置
    TRADEMASTER_API_URL: str = "http://localhost:8080"
    TRADEMASTER_API_TIMEOUT: int = 300
    
    # 文件存储配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".json", ".xlsx"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # 监控配置
    SENTRY_DSN: Optional[HttpUrl] = None
    ENABLE_METRICS: bool = True
    
    # 邮件配置
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## 🏗️ 数据库模型设计

### 基础模型

```python
# app/models/base.py
from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    id: Any
    __name__: str
    
    # 自动生成表名
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # 公共字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
```

### 用户模型

```python
# app/models/user.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    settings = Column(JSON, default=dict)
    
    # 关系
    strategies = relationship("Strategy", back_populates="owner")
    training_jobs = relationship("TrainingJob", back_populates="user")
```

### 策略模型

```python
# app/models/strategy.py
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class StrategyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class StrategyType(str, enum.Enum):
    ALGORITHMIC_TRADING = "algorithmic_trading"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    ORDER_EXECUTION = "order_execution"
    HIGH_FREQUENCY_TRADING = "high_frequency_trading"

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(Enum(StrategyType), nullable=False)
    status = Column(Enum(StrategyStatus), default=StrategyStatus.DRAFT)
    config = Column(JSON, default=dict)
    parameters = Column(JSON, default=dict)
    
    # 外键
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # 关系
    owner = relationship("User", back_populates="strategies")
    training_jobs = relationship("TrainingJob", back_populates="strategy")
    evaluations = relationship("Evaluation", back_populates="strategy")
```

### 训练任务模型

```python
# app/models/training.py
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class TrainingStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TrainingJob(Base):
    __tablename__ = "training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    status = Column(Enum(TrainingStatus), default=TrainingStatus.PENDING)
    progress = Column(Float, default=0.0)
    logs = Column(Text, nullable=True)
    config = Column(JSON, default=dict)
    metrics = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    
    # TradeMaster集成字段
    trademaster_session_id = Column(String(100), nullable=True)
    
    # 外键
    user_id = Column(Integer, ForeignKey("users.id"))
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    
    # 关系
    user = relationship("User", back_populates="training_jobs")
    strategy = relationship("Strategy", back_populates="training_jobs")
```

## 🔧 服务层架构

### 基础服务类

```python
# app/services/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, crud: CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
        self.crud = crud
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        return await self.crud.get(db, id=id)
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        return await self.crud.get_multi(db, skip=skip, limit=limit)
    
    async def create(
        self, 
        db: AsyncSession, 
        obj_in: CreateSchemaType
    ) -> ModelType:
        return await self.crud.create(db, obj_in=obj_in)
    
    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        return await self.crud.update(db, db_obj=db_obj, obj_in=obj_in)
    
    async def remove(self, db: AsyncSession, id: Any) -> ModelType:
        return await self.crud.remove(db, id=id)
```

### 策略服务

```python
# app/services/strategy_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.base import BaseService
from app.crud.strategy import strategy_crud
from app.models.strategy import Strategy, StrategyStatus, StrategyType
from app.schemas.strategy import StrategyCreate, StrategyUpdate
from app.services.trademaster_service import TradeMasterService

class StrategyService(BaseService[Strategy, StrategyCreate, StrategyUpdate]):
    def __init__(self):
        super().__init__(strategy_crud)
        self.trademaster_service = TradeMasterService()
    
    async def get_by_owner(
        self, 
        db: AsyncSession, 
        owner_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Strategy]:
        """获取用户的策略列表"""
        result = await db.execute(
            select(Strategy)
            .where(Strategy.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_status(
        self,
        db: AsyncSession,
        status: StrategyStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Strategy]:
        """根据状态获取策略"""
        result = await db.execute(
            select(Strategy)
            .where(Strategy.status == status)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_type(
        self,
        db: AsyncSession,
        strategy_type: StrategyType,
        skip: int = 0,
        limit: int = 100
    ) -> List[Strategy]:
        """根据类型获取策略"""
        result = await db.execute(
            select(Strategy)
            .where(Strategy.strategy_type == strategy_type)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def start_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int
    ) -> dict:
        """启动策略"""
        strategy = await self.get(db, strategy_id)
        if not strategy or strategy.owner_id != user_id:
            raise ValueError("Strategy not found or access denied")
        
        # 调用TradeMaster API
        result = await self.trademaster_service.train_strategy(strategy.config)
        
        # 更新策略状态
        await self.update(
            db, 
            strategy, 
            {"status": StrategyStatus.ACTIVE}
        )
        
        return result
    
    async def stop_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int
    ) -> dict:
        """停止策略"""
        strategy = await self.get(db, strategy_id)
        if not strategy or strategy.owner_id != user_id:
            raise ValueError("Strategy not found or access denied")
        
        # 更新策略状态
        await self.update(
            db, 
            strategy, 
            {"status": StrategyStatus.STOPPED}
        )
        
        return {"message": "Strategy stopped successfully"}

strategy_service = StrategyService()
```

### TradeMaster集成服务

```python
# app/services/trademaster_service.py
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from loguru import logger

class TradeMasterService:
    def __init__(self):
        self.base_url = settings.TRADEMASTER_API_URL
        self.timeout = settings.TRADEMASTER_API_TIMEOUT
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """发送HTTP请求到TradeMaster API"""
        url = f"{self.base_url}/api/TradeMaster/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url)
                else:
                    response = await client.post(url, json=data)
                
                response.raise_for_status()
                return response.json()
                
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise Exception(f"Failed to connect to TradeMaster API: {str(e)}")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e}")
                raise Exception(f"TradeMaster API error: {e.response.status_code}")
    
    async def get_parameters(self) -> Dict[str, Any]:
        """获取训练参数"""
        return await self._make_request("GET", "getParameters")
    
    async def train_strategy(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """训练策略"""
        return await self._make_request("POST", "train", config)
    
    async def get_train_status(self, session_id: str) -> Dict[str, Any]:
        """获取训练状态"""
        return await self._make_request("POST", "train_status", {"session_id": session_id})
    
    async def test_strategy(self, session_id: str) -> Dict[str, Any]:
        """测试策略"""
        return await self._make_request("POST", "test", {"session_id": session_id})
    
    async def get_test_status(self, session_id: str) -> Dict[str, Any]:
        """获取测试状态"""
        return await self._make_request("POST", "test_status", {"session_id": session_id})
    
    async def upload_data(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """上传数据"""
        return await self._make_request("POST", "upload_csv", file_data)
    
    async def start_market_dynamics_modeling(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """启动市场动态建模"""
        return await self._make_request("POST", "start_market_dynamics_labeling", config)
    
    async def get_mdm_status(self, session_id: str) -> Dict[str, Any]:
        """获取市场动态建模状态"""
        return await self._make_request("POST", "MDM_status", {"session_id": session_id})

trademaster_service = TradeMasterService()
```

## 🔄 异步任务设计

### Celery配置

```python
# app/core/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "trademaster_web",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks.training_tasks', 'app.tasks.evaluation_tasks']
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟
    task_soft_time_limit=25 * 60,  # 25分钟
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 任务路由
celery_app.conf.task_routes = {
    'app.tasks.training_tasks.*': {'queue': 'training'},
    'app.tasks.evaluation_tasks.*': {'queue': 'evaluation'},
    'app.tasks.data_tasks.*': {'queue': 'data'},
}
```

### 训练任务

```python
# app/tasks/training_tasks.py
from celery import current_task
from app.core.celery_app import celery_app
from app.services.trademaster_service import trademaster_service
from app.core.database import get_db
from app.models.training import TrainingJob, TrainingStatus
from loguru import logger
import asyncio

@celery_app.task(bind=True)
def start_training_task(self, training_job_id: int, config: dict):
    """启动训练任务"""
    try:
        # 更新任务状态
        self.update_state(state='PROGRESS', meta={'progress': 0})
        
        # 异步执行训练
        result = asyncio.run(execute_training(training_job_id, config))
        
        return {
            'status': 'completed',
            'result': result,
            'progress': 100
        }
        
    except Exception as e:
        logger.error(f"Training task failed: {str(e)}")
        asyncio.run(update_training_status(training_job_id, TrainingStatus.FAILED, str(e)))
        raise self.retry(exc=e, countdown=60, max_retries=3)

async def execute_training(training_job_id: int, config: dict):
    """执行训练逻辑"""
    async with get_db() as db:
        # 获取训练任务
        training_job = await db.get(TrainingJob, training_job_id)
        if not training_job:
            raise ValueError("Training job not found")
        
        # 更新状态为运行中
        training_job.status = TrainingStatus.RUNNING
        await db.commit()
        
        try:
            # 调用TradeMaster API
            result = await trademaster_service.train_strategy(config)
            session_id = result.get('session_id')
            
            if session_id:
                training_job.trademaster_session_id = session_id
                await db.commit()
                
                # 轮询训练状态
                await poll_training_status(training_job_id, session_id)
            
            return result
            
        except Exception as e:
            training_job.status = TrainingStatus.FAILED
            training_job.error_message = str(e)
            await db.commit()
            raise

async def poll_training_status(training_job_id: int, session_id: str):
    """轮询训练状态"""
    async with get_db() as db:
        training_job = await db.get(TrainingJob, training_job_id)
        
        while True:
            try:
                status_result = await trademaster_service.get_train_status(session_id)
                
                # 更新进度和日志
                if 'train_end' in status_result and status_result['train_end']:
                    training_job.status = TrainingStatus.COMPLETED
                    training_job.progress = 100.0
                    break
                
                # 更新日志
                if 'info' in status_result:
                    training_job.logs = status_result['info']
                
                await db.commit()
                await asyncio.sleep(10)  # 10秒检查一次
                
            except Exception as e:
                logger.error(f"Error polling training status: {str(e)}")
                training_job.status = TrainingStatus.FAILED
                training_job.error_message = str(e)
                await db.commit()
                break

async def update_training_status(training_job_id: int, status: TrainingStatus, error_msg: str = None):
    """更新训练状态"""
    async with get_db() as db:
        training_job = await db.get(TrainingJob, training_job_id)
        if training_job:
            training_job.status = status
            if error_msg:
                training_job.error_message = error_msg
            await db.commit()
```

## 🔒 安全设计

### JWT认证

```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Union[str, None]:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

## 📊 API设计规范

### 统一响应格式

```python
# app/schemas/response.py
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool = True
    data: Optional[T] = None
    message: str = "Success"
    code: int = 200
    timestamp: int
    request_id: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = False
    error: Dict[str, Any]
    message: str
    code: int
    timestamp: int
    request_id: Optional[str] = None
```

### API路由示例

```python
# app/api/v1/strategy.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.strategy import Strategy
from app.schemas.strategy import (
    StrategyCreate, 
    StrategyUpdate, 
    StrategyResponse,
    StrategyListResponse
)
from app.schemas.response import ApiResponse, PaginatedResponse
from app.services.strategy_service import strategy_service

router = APIRouter()

@router.get("", response_model=ApiResponse[PaginatedResponse[StrategyResponse]])
async def list_strategies(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取策略列表"""
    strategies = await strategy_service.get_by_owner(
        db, 
        owner_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    total = len(strategies)  # 实际应该查询总数
    
    return ApiResponse(
        data=PaginatedResponse(
            items=strategies,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    )

@router.post("", response_model=ApiResponse[StrategyResponse])
async def create_strategy(
    strategy_in: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建策略"""
    strategy = await strategy_service.create(
        db, 
        obj_in=strategy_in,
        owner_id=current_user.id
    )
    return ApiResponse(data=strategy)

@router.get("/{strategy_id}", response_model=ApiResponse[StrategyResponse])
async def get_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取策略详情"""
    strategy = await strategy_service.get(db, id=strategy_id)
    if not strategy or strategy.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    return ApiResponse(data=strategy)

@router.post("/{strategy_id}/start", response_model=ApiResponse[dict])
async def start_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动策略"""
    result = await strategy_service.start_strategy(
        db, 
        strategy_id, 
        current_user.id
    )
    return ApiResponse(data=result, message="Strategy started successfully")
```

这个后端规范确保了：

- **现代化架构**：基于FastAPI的异步Web框架
- **数据库设计**：完整的ORM模型和关系设计
- **服务层抽象**：清晰的业务逻辑分离
- **异步任务**：Celery分布式任务处理
- **安全认证**：JWT token和密码加密
- **API规范**：统一的响应格式和错误处理
- **TradeMaster集成**：无缝对接现有Flask API
- **可维护性**：模块化设计和类型提示