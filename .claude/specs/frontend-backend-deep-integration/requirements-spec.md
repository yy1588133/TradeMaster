# TradeMaster前后端深度集成技术规范

## 问题陈述

### 业务问题
当前TradeMaster Web界面存在以下核心问题：
- **模拟数据依赖**: 前后端大量使用硬编码模拟数据，无法提供真实的量化交易功能
- **功能缺失**: 无法实际执行TradeMaster核心算法和策略训练
- **实时监控缺失**: 缺乏训练过程的实时可视化和数据推送
- **集成不完整**: TradeMasterService框架存在但未充分利用TradeMaster核心能力

### 当前状态
- **Web界面**: React前端 + FastAPI后端架构完整，但依赖模拟数据
- **TradeMaster集成**: 基础框架已搭建(`trademaster_core.py`)，但功能不完整
- **数据库结构**: 基础用户和策略模型存在，缺少训练相关表
- **任务处理**: 无异步任务队列，无法处理长时间运行的训练任务

### 期望结果
Web界面完全集成TradeMaster核心功能，提供生产级量化交易平台：
- 所有模拟数据替换为真实TradeMaster计算结果
- 完整的策略训练、回测和实盘交易生命周期
- 实时训练监控，数据推送延迟<1秒
- 支持多用户并发，系统吞吐量>100用户

## 解决方案概述

### 解决方案策略
采用**微服务架构**和**异步任务处理**，通过以下核心组件实现深度集成：
1. **TradeMaster适配层**: 完善现有`TradeMasterService`，实现Web参数到TradeMaster配置的完整转换
2. **Celery任务队列**: 处理训练、回测等长时间运行任务
3. **WebSocket实时通信**: 提供<1秒延迟的实时数据推送
4. **扩展数据库模型**: 添加训练会话、性能指标等核心表

### 核心系统变更
- **移除所有模拟数据**: 策略API、训练API、评估API全面使用真实数据
- **完整CRUD操作**: 基于真实TradeMaster功能的策略管理
- **实时监控系统**: WebSocket + Redis的实时数据推送架构
- **生产级特性**: 多用户支持、容错恢复、安全机制

### 成功标准
- Web界面能完全操作TradeMaster所有核心功能
- 训练监控实时性<1秒，API响应<500ms
- 支持100+并发用户，系统可用性>99.5%
- 通过安全评估，支持受控的实盘交易功能

## 技术实现

### 数据库设计变更

#### 新增核心表结构

```sql
-- 策略执行会话表
CREATE TABLE strategy_sessions (
    id SERIAL PRIMARY KEY,
    uuid UUID UNIQUE DEFAULT gen_random_uuid(),
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL CHECK (session_type IN ('training', 'backtest', 'live_trading')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    
    -- TradeMaster集成
    trademaster_config JSONB NOT NULL,
    trademaster_session_id VARCHAR(100),
    celery_task_id VARCHAR(155),
    
    -- 执行信息
    progress DECIMAL(5,2) DEFAULT 0.0 CHECK (progress >= 0 AND progress <= 100),
    current_epoch INTEGER DEFAULT 0,
    total_epochs INTEGER,
    
    -- 结果数据
    final_metrics JSONB DEFAULT '{}',
    model_path TEXT,
    log_file_path TEXT,
    error_message TEXT,
    
    -- 时间戳
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 实时性能指标表
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES strategy_sessions(id) ON DELETE CASCADE,
    
    -- 指标信息
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,8) NOT NULL,
    epoch INTEGER,
    step INTEGER,
    
    -- 元数据
    metric_metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 系统资源使用记录
CREATE TABLE resource_usage (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES strategy_sessions(id) ON DELETE CASCADE,
    
    -- 资源指标
    cpu_percent DECIMAL(5,2),
    memory_mb INTEGER,
    gpu_percent DECIMAL(5,2),
    gpu_memory_mb INTEGER,
    disk_io_mb DECIMAL(10,2),
    network_io_mb DECIMAL(10,2),
    
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WebSocket连接管理表
CREATE TABLE websocket_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    connection_id VARCHAR(100) UNIQUE NOT NULL,
    session_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    
    -- 连接信息
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建优化索引
CREATE INDEX idx_strategy_sessions_strategy_id ON strategy_sessions(strategy_id);
CREATE INDEX idx_strategy_sessions_status ON strategy_sessions(status);
CREATE INDEX idx_strategy_sessions_type_status ON strategy_sessions(session_type, status);
CREATE INDEX idx_performance_metrics_session_epoch ON performance_metrics(session_id, epoch);
CREATE INDEX idx_performance_metrics_name_time ON performance_metrics(metric_name, recorded_at);
CREATE INDEX idx_resource_usage_session_time ON resource_usage(session_id, recorded_at);
CREATE INDEX idx_websocket_connections_user ON websocket_connections(user_id);
```

#### 数据库迁移脚本

```sql
-- 扩展现有strategies表
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS last_training_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS training_count INTEGER DEFAULT 0;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS best_return DECIMAL(10,4);
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS best_sharpe DECIMAL(8,4);

-- 扩展现有users表
ALTER TABLE users ADD COLUMN IF NOT EXISTS trading_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'medium' CHECK (risk_level IN ('low', 'medium', 'high'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS max_concurrent_sessions INTEGER DEFAULT 3;
```

### 代码架构变更

#### 文件结构新增

```
backend/app/
├── core/
│   ├── celery_app.py          # Celery应用配置
│   ├── websocket.py           # WebSocket管理器
│   └── task_queue.py          # 任务队列管理
├── tasks/
│   ├── __init__.py
│   ├── training_tasks.py      # 训练任务处理器
│   ├── backtest_tasks.py      # 回测任务处理器
│   └── monitoring_tasks.py    # 监控任务处理器
├── websocket/
│   ├── __init__.py
│   ├── connection_manager.py  # WebSocket连接管理
│   ├── message_handler.py     # 消息处理器
│   └── real_time_data.py      # 实时数据推送
├── models/
│   ├── session.py             # 新增会话模型
│   ├── metrics.py             # 新增指标模型
│   └── websocket_models.py    # WebSocket相关模型
└── services/
    ├── session_service.py     # 会话管理服务
    ├── real_time_service.py   # 实时数据服务
    └── resource_monitor.py    # 资源监控服务
```

#### TradeMaster集成服务完善

文件路径: `backend/app/services/trademaster_integration.py`

```python
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
from pathlib import Path
import yaml
import json
from loguru import logger

from app.core.trademaster_config import TradeMasterConfigAdapter
from app.services.trademaster_core import get_trademaster_core, TradeMasterCoreError
from app.models.session import StrategySession, SessionStatus, SessionType
from app.core.database import get_database
from app.core.celery_app import celery_app


class TradeMasterIntegrationService:
    """完整的TradeMaster集成服务
    
    负责Web界面与TradeMaster核心的完整集成，提供策略训练、
    回测、实盘交易等完整生命周期管理。
    """
    
    def __init__(self):
        self.config_adapter = TradeMasterConfigAdapter()
        self.trademaster_core = get_trademaster_core()
    
    async def create_training_session(
        self, 
        strategy_id: int, 
        user_id: int, 
        config: Dict[str, Any]
    ) -> int:
        """创建训练会话
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID  
            config: 训练配置参数
            
        Returns:
            int: 会话ID
        """
        try:
            # 1. 转换配置为TradeMaster格式
            tm_config = await self._convert_config_to_trademaster(config)
            
            # 2. 验证配置有效性
            validation_result = self.config_adapter.validate_trademaster_config(tm_config)
            if not validation_result["valid"]:
                raise ValueError(f"配置验证失败: {', '.join(validation_result['errors'])}")
            
            # 3. 创建会话记录
            async with get_database() as db:
                session = StrategySession(
                    strategy_id=strategy_id,
                    session_type=SessionType.TRAINING,
                    status=SessionStatus.PENDING,
                    trademaster_config=tm_config,
                    total_epochs=config.get("epochs", 100)
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
                
                logger.info(f"创建训练会话: {session.id}")
                return session.id
                
        except Exception as e:
            logger.error(f"创建训练会话失败: {str(e)}")
            raise TradeMasterCoreError(f"创建训练会话失败: {str(e)}")
    
    async def start_training_task(self, session_id: int) -> str:
        """启动训练任务
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: Celery任务ID
        """
        try:
            # 1. 获取会话信息
            async with get_database() as db:
                session = await db.get(StrategySession, session_id)
                if not session:
                    raise ValueError(f"会话不存在: {session_id}")
                
                if session.status != SessionStatus.PENDING:
                    raise ValueError(f"会话状态错误: {session.status}")
            
            # 2. 提交Celery任务
            from app.tasks.training_tasks import execute_training_task
            task = execute_training_task.delay(session_id)
            
            # 3. 更新会话状态
            async with get_database() as db:
                session = await db.get(StrategySession, session_id)
                session.celery_task_id = task.id
                session.status = SessionStatus.RUNNING
                session.started_at = datetime.now()
                await db.commit()
            
            logger.info(f"启动训练任务: session_id={session_id}, task_id={task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"启动训练任务失败: {str(e)}")
            raise TradeMasterCoreError(f"启动训练任务失败: {str(e)}")
    
    async def create_backtest_session(
        self,
        strategy_id: int,
        user_id: int,
        config: Dict[str, Any]
    ) -> int:
        """创建回测会话"""
        try:
            # 转换回测配置
            tm_config = await self._convert_backtest_config(config)
            
            async with get_database() as db:
                session = StrategySession(
                    strategy_id=strategy_id,
                    session_type=SessionType.BACKTEST,
                    status=SessionStatus.PENDING,
                    trademaster_config=tm_config
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
                
                logger.info(f"创建回测会话: {session.id}")
                return session.id
                
        except Exception as e:
            logger.error(f"创建回测会话失败: {str(e)}")
            raise TradeMasterCoreError(f"创建回测会话失败: {str(e)}")
    
    async def start_backtest_task(self, session_id: int) -> str:
        """启动回测任务"""
        try:
            from app.tasks.backtest_tasks import execute_backtest_task
            task = execute_backtest_task.delay(session_id)
            
            async with get_database() as db:
                session = await db.get(StrategySession, session_id)
                session.celery_task_id = task.id
                session.status = SessionStatus.RUNNING
                session.started_at = datetime.now()
                await db.commit()
            
            logger.info(f"启动回测任务: session_id={session_id}, task_id={task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"启动回测任务失败: {str(e)}")
            raise TradeMasterCoreError(f"启动回测任务失败: {str(e)}")
    
    async def stop_session(self, session_id: int, user_id: int) -> Dict[str, Any]:
        """停止会话"""
        try:
            async with get_database() as db:
                session = await db.get(StrategySession, session_id)
                if not session:
                    raise ValueError(f"会话不存在: {session_id}")
                
                # 撤销Celery任务
                if session.celery_task_id:
                    celery_app.control.revoke(session.celery_task_id, terminate=True)
                
                # 停止TradeMaster会话
                if session.trademaster_session_id:
                    await self.trademaster_core.stop_training(session.trademaster_session_id)
                
                # 更新状态
                session.status = SessionStatus.CANCELLED
                session.completed_at = datetime.now()
                await db.commit()
            
            logger.info(f"停止会话: {session_id}")
            return {"status": "stopped", "message": "会话已停止"}
            
        except Exception as e:
            logger.error(f"停止会话失败: {str(e)}")
            raise TradeMasterCoreError(f"停止会话失败: {str(e)}")
    
    async def get_session_status(self, session_id: int) -> Dict[str, Any]:
        """获取会话状态"""
        try:
            async with get_database() as db:
                session = await db.get(StrategySession, session_id)
                if not session:
                    raise ValueError(f"会话不存在: {session_id}")
                
                # 获取实时指标
                recent_metrics = await self._get_recent_metrics(session_id)
                
                return {
                    "session_id": session_id,
                    "status": session.status.value,
                    "progress": float(session.progress),
                    "current_epoch": session.current_epoch,
                    "total_epochs": session.total_epochs,
                    "recent_metrics": recent_metrics,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "error_message": session.error_message
                }
                
        except Exception as e:
            logger.error(f"获取会话状态失败: {str(e)}")
            raise TradeMasterCoreError(f"获取会话状态失败: {str(e)}")
    
    async def _convert_config_to_trademaster(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换Web配置到TradeMaster格式"""
        return self.config_adapter.convert_web_config_to_trademaster(config)
    
    async def _convert_backtest_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换回测配置"""
        tm_config = await self._convert_config_to_trademaster(config)
        
        # 添加回测特定配置
        tm_config.update({
            "mode": "backtest",
            "start_date": config.get("start_date"),
            "end_date": config.get("end_date"),
            "initial_capital": config.get("initial_capital", 100000)
        })
        
        return tm_config
    
    async def _get_recent_metrics(self, session_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的性能指标"""
        try:
            from app.models.metrics import PerformanceMetric
            async with get_database() as db:
                query = await db.execute(
                    select(PerformanceMetric)
                    .where(PerformanceMetric.session_id == session_id)
                    .order_by(PerformanceMetric.recorded_at.desc())
                    .limit(limit)
                )
                metrics = query.scalars().all()
                
                return [
                    {
                        "metric_name": m.metric_name,
                        "metric_value": float(m.metric_value),
                        "epoch": m.epoch,
                        "recorded_at": m.recorded_at.isoformat()
                    }
                    for m in metrics
                ]
                
        except Exception as e:
            logger.error(f"获取指标失败: {str(e)}")
            return []


# 全局服务实例
_integration_service = None

def get_integration_service() -> TradeMasterIntegrationService:
    """获取TradeMaster集成服务实例"""
    global _integration_service
    if _integration_service is None:
        _integration_service = TradeMasterIntegrationService()
    return _integration_service
```

#### Celery任务处理器

文件路径: `backend/app/tasks/training_tasks.py`

```python
import os
import sys
import asyncio
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from celery import Task
from loguru import logger

from app.core.celery_app import celery_app
from app.core.database import get_database
from app.models.session import StrategySession, SessionStatus
from app.models.metrics import PerformanceMetric
from app.websocket.real_time_data import RealTimeDataPusher


class CallbackTask(Task):
    """带回调的任务基类"""
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        logger.info(f"任务成功完成: {task_id}")
        
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        logger.error(f"任务执行失败: {task_id}, 错误: {str(exc)}")


@celery_app.task(bind=True, base=CallbackTask, name="training.execute")
def execute_training_task(self, session_id: int):
    """执行TradeMaster训练任务
    
    Args:
        session_id: 训练会话ID
        
    Returns:
        dict: 训练结果
    """
    logger.info(f"开始执行训练任务: session_id={session_id}")
    
    try:
        # 获取会话信息
        session = asyncio.run(_get_session(session_id))
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        # 更新状态为运行中
        asyncio.run(_update_session_status(session_id, SessionStatus.RUNNING))
        
        # 创建TradeMaster配置文件
        config_path = _create_trademaster_config(session)
        
        # 启动TradeMaster训练进程
        process = _start_trademaster_process(config_path, session_id)
        
        # 监控训练过程
        result = _monitor_training_process(process, session_id)
        
        # 更新最终状态
        final_status = SessionStatus.COMPLETED if result["success"] else SessionStatus.FAILED
        asyncio.run(_update_session_final_status(session_id, final_status, result))
        
        logger.info(f"训练任务完成: session_id={session_id}, success={result['success']}")
        return result
        
    except Exception as exc:
        logger.error(f"训练任务异常: session_id={session_id}, error={str(exc)}")
        
        # 更新为失败状态
        asyncio.run(_update_session_status(
            session_id, 
            SessionStatus.FAILED,
            error_message=str(exc)
        ))
        
        # 重新抛出异常以便Celery处理
        raise exc


def _create_trademaster_config(session: StrategySession) -> str:
    """创建TradeMaster配置文件
    
    Args:
        session: 训练会话
        
    Returns:
        str: 配置文件路径
    """
    config_dir = Path("/tmp/trademaster_configs")
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / f"session_{session.id}_config.yaml"
    
    # 写入配置文件
    with open(config_path, 'w') as f:
        yaml.dump(session.trademaster_config, f, default_flow_style=False)
    
    logger.info(f"创建配置文件: {config_path}")
    return str(config_path)


def _start_trademaster_process(config_path: str, session_id: int) -> subprocess.Popen:
    """启动TradeMaster训练进程
    
    Args:
        config_path: 配置文件路径
        session_id: 会话ID
        
    Returns:
        subprocess.Popen: 进程对象
    """
    # 设置环境变量
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": "0",  # 指定GPU
        "PYTHONPATH": "/app:${PYTHONPATH}",
        "SESSION_ID": str(session_id)
    })
    
    # 启动命令
    cmd = [
        sys.executable, "-m", "trademaster.tools.train",
        "--config", config_path,
        "--session-id", str(session_id)
    ]
    
    # 创建日志文件
    log_file_path = f"/tmp/training_logs/session_{session_id}.log"
    Path(log_file_path).parent.mkdir(exist_ok=True)
    
    # 启动进程
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # 保存进程ID和日志路径
    asyncio.run(_update_session_process_info(
        session_id, 
        process.pid, 
        log_file_path
    ))
    
    logger.info(f"启动TradeMaster进程: pid={process.pid}, session_id={session_id}")
    return process


def _monitor_training_process(process: subprocess.Popen, session_id: int) -> Dict[str, Any]:
    """监控训练进程
    
    Args:
        process: TradeMaster进程
        session_id: 会话ID
        
    Returns:
        dict: 监控结果
    """
    real_time_pusher = RealTimeDataPusher()
    
    try:
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
                
            if output:
                # 解析训练输出
                metrics = _parse_training_output(output.strip())
                if metrics:
                    # 保存指标到数据库
                    asyncio.run(_save_performance_metrics(session_id, metrics))
                    
                    # 实时推送到前端
                    asyncio.run(real_time_pusher.push_training_metrics(
                        session_id, metrics
                    ))
                    
                    # 更新会话进度
                    if "epoch" in metrics:
                        asyncio.run(_update_session_progress(
                            session_id, 
                            metrics["epoch"], 
                            metrics.get("progress", 0)
                        ))
        
        return_code = process.wait()
        success = return_code == 0
        
        # 收集最终结果
        final_metrics = asyncio.run(_collect_final_metrics(session_id))
        
        return {
            "success": success,
            "return_code": return_code,
            "final_metrics": final_metrics
        }
        
    except Exception as e:
        logger.error(f"监控进程异常: {str(e)}")
        process.kill()
        return {
            "success": False,
            "error": str(e)
        }


def _parse_training_output(output: str) -> Optional[Dict[str, Any]]:
    """解析训练输出日志
    
    Args:
        output: 日志行
        
    Returns:
        dict: 解析的指标数据，如果解析失败返回None
    """
    try:
        # 假设TradeMaster输出JSON格式的指标
        if output.startswith('[METRICS]'):
            metrics_json = output.replace('[METRICS]', '').strip()
            return json.loads(metrics_json)
        
        # 解析其他格式的日志
        if 'Epoch:' in output and 'Loss:' in output:
            # 示例: "Epoch: 10, Loss: 0.123, Reward: 15.67"
            parts = output.split(',')
            metrics = {}
            
            for part in parts:
                if 'Epoch:' in part:
                    metrics['epoch'] = int(part.split(':')[1].strip())
                elif 'Loss:' in part:
                    metrics['loss'] = float(part.split(':')[1].strip())
                elif 'Reward:' in part:
                    metrics['reward'] = float(part.split(':')[1].strip())
            
            return metrics if metrics else None
            
        return None
        
    except Exception as e:
        logger.warning(f"解析训练输出失败: {str(e)}")
        return None


# 异步数据库操作辅助函数

async def _get_session(session_id: int) -> Optional[StrategySession]:
    """获取会话信息"""
    async with get_database() as db:
        return await db.get(StrategySession, session_id)


async def _update_session_status(
    session_id: int, 
    status: SessionStatus, 
    error_message: str = None
):
    """更新会话状态"""
    async with get_database() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.status = status
            session.updated_at = datetime.now()
            if error_message:
                session.error_message = error_message
            await db.commit()


async def _update_session_process_info(
    session_id: int, 
    process_id: int, 
    log_file_path: str
):
    """更新会话进程信息"""
    async with get_database() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.process_id = process_id
            session.log_file_path = log_file_path
            await db.commit()


async def _update_session_progress(
    session_id: int, 
    current_epoch: int, 
    progress: float
):
    """更新会话进度"""
    async with get_database() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.current_epoch = current_epoch
            session.progress = progress
            session.updated_at = datetime.now()
            await db.commit()


async def _save_performance_metrics(session_id: int, metrics: Dict[str, Any]):
    """保存性能指标"""
    async with get_database() as db:
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                db.add(PerformanceMetric(
                    session_id=session_id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    epoch=metrics.get("epoch"),
                    step=metrics.get("step")
                ))
        await db.commit()


async def _update_session_final_status(
    session_id: int, 
    status: SessionStatus, 
    result: Dict[str, Any]
):
    """更新最终状态"""
    async with get_database() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.status = status
            session.completed_at = datetime.now()
            session.final_metrics = result.get("final_metrics", {})
            if not result.get("success"):
                session.error_message = result.get("error", "训练失败")
            await db.commit()


async def _collect_final_metrics(session_id: int) -> Dict[str, Any]:
    """收集最终指标"""
    try:
        from app.models.metrics import PerformanceMetric
        async with get_database() as db:
            # 获取最后一轮的指标
            query = await db.execute(
                select(PerformanceMetric)
                .where(PerformanceMetric.session_id == session_id)
                .order_by(PerformanceMetric.epoch.desc(), PerformanceMetric.recorded_at.desc())
                .limit(10)
            )
            metrics = query.scalars().all()
            
            final_metrics = {}
            for metric in metrics:
                final_metrics[metric.metric_name] = float(metric.metric_value)
            
            return final_metrics
            
    except Exception as e:
        logger.error(f"收集最终指标失败: {str(e)}")
        return {}
```

#### WebSocket实时通信服务

文件路径: `backend/app/websocket/connection_manager.py`

```python
import asyncio
import json
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.models.websocket_models import WebSocketConnection
from app.core.database import get_database


class WebSocketConnectionManager:
    """WebSocket连接管理器
    
    负责管理WebSocket连接、消息推送和连接状态维护。
    支持基于用户和会话的消息路由。
    """
    
    def __init__(self):
        # 活跃连接: connection_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 用户连接映射: user_id -> Set[connection_id]  
        self.user_connections: Dict[int, Set[str]] = {}
        
        # 会话订阅: session_id -> Set[connection_id]
        self.session_subscriptions: Dict[int, Set[str]] = {}
        
        # 连接元数据: connection_id -> metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 心跳任务: connection_id -> Task
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: int,
        client_ip: str = None,
        user_agent: str = None
    ) -> str:
        """建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
            client_ip: 客户端IP
            user_agent: 用户代理
            
        Returns:
            str: 连接ID
        """
        await websocket.accept()
        
        # 生成唯一连接ID
        connection_id = str(uuid.uuid4())
        
        # 存储连接
        self.active_connections[connection_id] = websocket
        
        # 更新用户连接映射
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # 存储连接元数据
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "client_ip": client_ip,
            "user_agent": user_agent
        }
        
        # 数据库记录连接
        await self._save_connection_to_db(
            connection_id, user_id, client_ip, user_agent
        )
        
        # 启动心跳任务
        self.heartbeat_tasks[connection_id] = asyncio.create_task(
            self._heartbeat_loop(connection_id, websocket)
        )
        
        logger.info(f"WebSocket连接建立: user_id={user_id}, connection_id={connection_id}")
        
        # 发送连接确认消息
        await self.send_personal_message(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """断开WebSocket连接
        
        Args:
            connection_id: 连接ID
        """
        if connection_id not in self.active_connections:
            return
        
        # 获取连接元数据
        metadata = self.connection_metadata.get(connection_id, {})
        user_id = metadata.get("user_id")
        
        # 移除连接
        del self.active_connections[connection_id]
        
        # 更新用户连接映射
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # 移除会话订阅
        for session_id, subscribers in self.session_subscriptions.items():
            subscribers.discard(connection_id)
        
        # 清理空的会话订阅
        self.session_subscriptions = {
            k: v for k, v in self.session_subscriptions.items() if v
        }
        
        # 取消心跳任务
        if connection_id in self.heartbeat_tasks:
            self.heartbeat_tasks[connection_id].cancel()
            del self.heartbeat_tasks[connection_id]
        
        # 清理元数据
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        # 更新数据库连接状态
        await self._update_connection_status(connection_id, False)
        
        logger.info(f"WebSocket连接断开: connection_id={connection_id}, user_id={user_id}")
    
    async def subscribe_to_session(self, connection_id: str, session_id: int):
        """订阅会话消息
        
        Args:
            connection_id: 连接ID
            session_id: 会话ID
        """
        if connection_id not in self.active_connections:
            logger.warning(f"尝试订阅不存在的连接: {connection_id}")
            return
        
        if session_id not in self.session_subscriptions:
            self.session_subscriptions[session_id] = set()
        
        self.session_subscriptions[session_id].add(connection_id)
        
        # 更新数据库订阅记录
        await self._update_session_subscriptions(connection_id, session_id, True)
        
        logger.info(f"订阅会话: connection_id={connection_id}, session_id={session_id}")
        
        # 发送订阅确认
        await self.send_personal_message(connection_id, {
            "type": "session_subscribed",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def unsubscribe_from_session(self, connection_id: str, session_id: int):
        """取消订阅会话消息
        
        Args:
            connection_id: 连接ID  
            session_id: 会话ID
        """
        if session_id in self.session_subscriptions:
            self.session_subscriptions[session_id].discard(connection_id)
            
            if not self.session_subscriptions[session_id]:
                del self.session_subscriptions[session_id]
        
        # 更新数据库订阅记录
        await self._update_session_subscriptions(connection_id, session_id, False)
        
        logger.info(f"取消订阅会话: connection_id={connection_id}, session_id={session_id}")
    
    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """发送个人消息
        
        Args:
            connection_id: 连接ID
            message: 消息内容
        """
        if connection_id not in self.active_connections:
            logger.warning(f"尝试向不存在的连接发送消息: {connection_id}")
            return
        
        websocket = self.active_connections[connection_id]
        
        try:
            await websocket.send_text(json.dumps(message))
            await self._update_last_activity(connection_id)
            
        except Exception as e:
            logger.error(f"发送个人消息失败: connection_id={connection_id}, error={str(e)}")
            await self.disconnect(connection_id)
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """发送消息给用户的所有连接
        
        Args:
            user_id: 用户ID
            message: 消息内容
        """
        if user_id not in self.user_connections:
            logger.debug(f"用户没有活跃连接: user_id={user_id}")
            return
        
        connection_ids = self.user_connections[user_id].copy()
        
        # 并发发送消息
        tasks = [
            self.send_personal_message(conn_id, message)
            for conn_id in connection_ids
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_session(self, session_id: int, message: Dict[str, Any]):
        """广播消息给会话的所有订阅者
        
        Args:
            session_id: 会话ID
            message: 消息内容
        """
        if session_id not in self.session_subscriptions:
            logger.debug(f"会话没有订阅者: session_id={session_id}")
            return
        
        connection_ids = self.session_subscriptions[session_id].copy()
        
        # 并发广播消息
        tasks = [
            self.send_personal_message(conn_id, message)
            for conn_id in connection_ids
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"广播会话消息: session_id={session_id}, 订阅者数量={len(connection_ids)}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """广播消息给所有连接
        
        Args:
            message: 消息内容
        """
        if not self.active_connections:
            return
        
        connection_ids = list(self.active_connections.keys())
        
        # 并发广播消息
        tasks = [
            self.send_personal_message(conn_id, message)
            for conn_id in connection_ids
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"全局广播消息: 连接数量={len(connection_ids)}")
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息
        
        Returns:
            dict: 连接统计
        """
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "total_sessions": len(self.session_subscriptions),
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            },
            "subscribers_by_session": {
                session_id: len(subscribers)
                for session_id, subscribers in self.session_subscriptions.items()
            }
        }
    
    async def _heartbeat_loop(self, connection_id: str, websocket: WebSocket):
        """心跳循环
        
        Args:
            connection_id: 连接ID
            websocket: WebSocket连接
        """
        try:
            while connection_id in self.active_connections:
                await asyncio.sleep(30)  # 30秒心跳间隔
                
                if connection_id not in self.active_connections:
                    break
                
                try:
                    # 发送心跳ping
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                except Exception:
                    # 连接已断开
                    await self.disconnect(connection_id)
                    break
                    
        except asyncio.CancelledError:
            pass
    
    async def _update_last_activity(self, connection_id: str):
        """更新最后活动时间"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["last_activity"] = datetime.now()
    
    async def _save_connection_to_db(
        self, 
        connection_id: str, 
        user_id: int, 
        client_ip: str = None,
        user_agent: str = None
    ):
        """保存连接到数据库"""
        try:
            async with get_database() as db:
                connection = WebSocketConnection(
                    connection_id=connection_id,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    is_active=True
                )
                db.add(connection)
                await db.commit()
                
        except Exception as e:
            logger.error(f"保存连接到数据库失败: {str(e)}")
    
    async def _update_connection_status(self, connection_id: str, is_active: bool):
        """更新连接状态"""
        try:
            async with get_database() as db:
                connection = await db.execute(
                    select(WebSocketConnection).where(
                        WebSocketConnection.connection_id == connection_id
                    )
                )
                connection = connection.scalar_one_or_none()
                
                if connection:
                    connection.is_active = is_active
                    connection.last_activity = datetime.now()
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"更新连接状态失败: {str(e)}")
    
    async def _update_session_subscriptions(
        self, 
        connection_id: str, 
        session_id: int, 
        subscribe: bool
    ):
        """更新会话订阅记录"""
        try:
            async with get_database() as db:
                connection = await db.execute(
                    select(WebSocketConnection).where(
                        WebSocketConnection.connection_id == connection_id
                    )
                )
                connection = connection.scalar_one_or_none()
                
                if connection:
                    session_ids = connection.session_ids or []
                    
                    if subscribe and session_id not in session_ids:
                        session_ids.append(session_id)
                    elif not subscribe and session_id in session_ids:
                        session_ids.remove(session_id)
                    
                    connection.session_ids = session_ids
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"更新会话订阅失败: {str(e)}")


# 全局连接管理器实例
_connection_manager = None

def get_connection_manager() -> WebSocketConnectionManager:
    """获取WebSocket连接管理器实例"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = WebSocketConnectionManager()
    return _connection_manager
```

#### API端点完全重构

文件路径: `backend/app/api/api_v1/endpoints/strategies.py` (重构现有文件)

```python
"""
策略管理API端点 - 完整TradeMaster集成版本

完全移除模拟数据，提供基于真实TradeMaster功能的策略管理。
支持策略创建、训练、回测、实时监控等完整生命周期。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.dependencies import (
    get_current_active_user, require_permission, get_pagination_params,
    CurrentUser, DatabaseSession, PaginationDeps
)
from app.core.security import Permission
from app.services.trademaster_integration import get_integration_service
from app.models.database import StrategyType, StrategyStatus
from app.models.session import SessionType
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse


router = APIRouter()


# ==================== 请求/响应模型 ====================

class TrainingRequest(BaseModel):
    """训练请求模型"""
    dataset_name: str = Field(..., description="数据集名称")
    agent_type: str = Field(..., description="智能体类型")
    epochs: int = Field(100, description="训练轮数")
    learning_rate: float = Field(0.001, description="学习率")
    batch_size: int = Field(32, description="批量大小")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="其他参数")


class BacktestRequest(BaseModel):
    """回测请求模型"""
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    initial_capital: float = Field(100000, description="初始资金")
    benchmark: Optional[str] = Field(None, description="基准指数")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="回测参数")


class SessionResponse(BaseModel):
    """会话响应模型"""
    session_id: int = Field(..., description="会话ID")
    session_type: str = Field(..., description="会话类型")
    status: str = Field(..., description="会话状态")
    progress: float = Field(..., description="进度百分比")
    current_epoch: Optional[int] = Field(None, description="当前轮次")
    total_epochs: Optional[int] = Field(None, description="总轮次")
    started_at: Optional[str] = Field(None, description="开始时间")
    error_message: Optional[str] = Field(None, description="错误信息")


class StrategyWithSessionsResponse(StrategyResponse):
    """策略及其会话响应模型"""
    active_sessions: List[SessionResponse] = Field(default_factory=list, description="活跃会话")
    total_sessions: int = Field(0, description="总会话数")
    last_training_at: Optional[str] = Field(None, description="最后训练时间")


# ==================== API端点 ====================

@router.post(
    "",
    response_model=StrategyResponse,
    summary="创建策略",
    dependencies=[Depends(require_permission(Permission.CREATE_STRATEGY))]
)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: CurrentUser,
    db: DatabaseSession
) -> StrategyResponse:
    """创建新策略
    
    基于TradeMaster核心功能创建策略，包括配置验证和模板应用。
    """
    try:
        integration_service = get_integration_service()
        
        # 验证策略配置
        config_validation = await integration_service._validate_strategy_config(
            strategy_data.config, strategy_data.strategy_type
        )
        
        if not config_validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略配置无效: {'; '.join(config_validation['errors'])}"
            )
        
        # 创建策略记录
        from app.crud.strategy import strategy_crud
        strategy = await strategy_crud.create(
            db, obj_in=strategy_data, owner_id=current_user["id"]
        )
        
        # 转换为响应格式
        return StrategyResponse.from_orm(strategy)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建策略失败: {str(e)}"
        )


@router.get("", response_model=List[StrategyWithSessionsResponse], summary="获取策略列表")
async def list_strategies(
    pagination: PaginationDeps,
    current_user: CurrentUser,
    db: DatabaseSession,
    strategy_type: Optional[StrategyType] = Query(None, description="策略类型筛选"),
    status: Optional[StrategyStatus] = Query(None, description="状态筛选")
) -> List[StrategyWithSessionsResponse]:
    """获取策略列表
    
    返回用户的所有策略及其活跃训练会话信息。
    """
    try:
        from app.crud.strategy import strategy_crud
        from app.models.session import StrategySession
        
        # 查询策略
        strategies = await strategy_crud.get_multi(
            db,
            skip=pagination.skip,
            limit=pagination.limit,
            owner_id=current_user["id"],
            strategy_type=strategy_type,
            status=status
        )
        
        # 为每个策略获取会话信息
        results = []
        for strategy in strategies:
            # 查询活跃会话
            active_sessions_query = await db.execute(
                select(StrategySession)
                .where(StrategySession.strategy_id == strategy.id)
                .where(StrategySession.status.in_(["pending", "running"]))
                .order_by(StrategySession.created_at.desc())
            )
            active_sessions = active_sessions_query.scalars().all()
            
            # 查询总会话数
            total_sessions_query = await db.execute(
                select(func.count(StrategySession.id))
                .where(StrategySession.strategy_id == strategy.id)
            )
            total_sessions = total_sessions_query.scalar()
            
            # 构建响应
            strategy_response = StrategyWithSessionsResponse(
                **StrategyResponse.from_orm(strategy).dict(),
                active_sessions=[
                    SessionResponse(
                        session_id=session.id,
                        session_type=session.session_type.value,
                        status=session.status.value,
                        progress=float(session.progress),
                        current_epoch=session.current_epoch,
                        total_epochs=session.total_epochs,
                        started_at=session.started_at.isoformat() if session.started_at else None,
                        error_message=session.error_message
                    )
                    for session in active_sessions
                ],
                total_sessions=total_sessions,
                last_training_at=strategy.last_training_at.isoformat() if strategy.last_training_at else None
            )
            
            results.append(strategy_response)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}"
        )


@router.post(
    "/{strategy_id}/train",
    response_model=SessionResponse,
    summary="启动策略训练",
    dependencies=[Depends(require_permission(Permission.EXECUTE_STRATEGY))]
)
async def start_strategy_training(
    strategy_id: int,
    training_request: TrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
) -> SessionResponse:
    """启动策略训练
    
    创建训练会话并异步启动TradeMaster训练任务。
    """
    try:
        integration_service = get_integration_service()
        
        # 验证策略所有权
        from app.crud.strategy import strategy_crud
        strategy = await strategy_crud.get(db, id=strategy_id)
        if not strategy or strategy.owner_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        # 检查用户并发限制
        current_sessions_count = await db.execute(
            select(func.count(StrategySession.id))
            .where(StrategySession.strategy_id.in_(
                select(Strategy.id).where(Strategy.owner_id == current_user["id"])
            ))
            .where(StrategySession.status.in_(["pending", "running"]))
        )
        
        max_concurrent = current_user.get("max_concurrent_sessions", 3)
        if current_sessions_count.scalar() >= max_concurrent:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"已达到最大并发训练数量限制: {max_concurrent}"
            )
        
        # 构建训练配置
        training_config = {
            "task_name": strategy.strategy_type.value,
            "dataset_name": training_request.dataset_name,
            "agent_name": training_request.agent_type,
            "epochs": training_request.epochs,
            "learning_rate": training_request.learning_rate,
            "batch_size": training_request.batch_size,
            **training_request.parameters
        }
        
        # 创建训练会话
        session_id = await integration_service.create_training_session(
            strategy_id=strategy_id,
            user_id=current_user["id"],
            config=training_config
        )
        
        # 异步启动训练任务
        task_id = await integration_service.start_training_task(session_id)
        
        # 获取会话状态
        session_status = await integration_service.get_session_status(session_id)
        
        return SessionResponse(**session_status)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动训练失败: {str(e)}"
        )


@router.post(
    "/{strategy_id}/backtest",
    response_model=SessionResponse,
    summary="启动策略回测",
    dependencies=[Depends(require_permission(Permission.EXECUTE_STRATEGY))]
)
async def start_strategy_backtest(
    strategy_id: int,
    backtest_request: BacktestRequest,
    current_user: CurrentUser,
    db: DatabaseSession
) -> SessionResponse:
    """启动策略回测
    
    基于历史数据进行策略回测分析。
    """
    try:
        integration_service = get_integration_service()
        
        # 验证策略所有权
        from app.crud.strategy import strategy_crud
        strategy = await strategy_crud.get(db, id=strategy_id)
        if not strategy or strategy.owner_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        # 构建回测配置
        backtest_config = {
            "mode": "backtest",
            "start_date": backtest_request.start_date,
            "end_date": backtest_request.end_date,
            "initial_capital": backtest_request.initial_capital,
            "benchmark": backtest_request.benchmark,
            **backtest_request.parameters
        }
        
        # 创建回测会话
        session_id = await integration_service.create_backtest_session(
            strategy_id=strategy_id,
            user_id=current_user["id"],
            config=backtest_config
        )
        
        # 启动回测任务
        task_id = await integration_service.start_backtest_task(session_id)
        
        # 获取会话状态
        session_status = await integration_service.get_session_status(session_id)
        
        return SessionResponse(**session_status)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动回测失败: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/status",
    response_model=SessionResponse,
    summary="获取会话状态"
)
async def get_session_status(
    session_id: int,
    current_user: CurrentUser,
    db: DatabaseSession
) -> SessionResponse:
    """获取会话实时状态
    
    返回训练或回测会话的当前状态和进度。
    """
    try:
        # 验证会话所有权
        session = await db.get(StrategySession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 检查策略所有权
        strategy = await db.get(Strategy, session.strategy_id)
        if not strategy or strategy.owner_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无权访问此会话"
            )
        
        integration_service = get_integration_service()
        session_status = await integration_service.get_session_status(session_id)
        
        return SessionResponse(**session_status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话状态失败: {str(e)}"
        )


@router.post(
    "/sessions/{session_id}/stop",
    summary="停止会话",
    dependencies=[Depends(require_permission(Permission.EXECUTE_STRATEGY))]
)
async def stop_session(
    session_id: int,
    current_user: CurrentUser,
    db: DatabaseSession
) -> Dict[str, Any]:
    """停止训练或回测会话
    
    立即停止正在运行的会话。
    """
    try:
        # 验证会话所有权
        session = await db.get(StrategySession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        strategy = await db.get(Strategy, session.strategy_id)
        if not strategy or strategy.owner_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无权访问此会话"
            )
        
        integration_service = get_integration_service()
        result = await integration_service.stop_session(session_id, current_user["id"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止会话失败: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/metrics",
    summary="获取会话指标"
)
async def get_session_metrics(
    session_id: int,
    current_user: CurrentUser,
    db: DatabaseSession,
    limit: int = Query(100, description="指标数量限制"),
    metric_name: Optional[str] = Query(None, description="指标名称筛选")
) -> Dict[str, Any]:
    """获取会话的性能指标数据
    
    用于前端绘制训练曲线和性能图表。
    """
    try:
        # 验证会话所有权
        session = await db.get(StrategySession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        strategy = await db.get(Strategy, session.strategy_id)
        if not strategy or strategy.owner_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无权访问此会话"
            )
        
        # 查询性能指标
        from app.models.metrics import PerformanceMetric
        
        query = select(PerformanceMetric).where(
            PerformanceMetric.session_id == session_id
        ).order_by(PerformanceMetric.recorded_at.desc())
        
        if metric_name:
            query = query.where(PerformanceMetric.metric_name == metric_name)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        # 组织数据
        metrics_data = {}
        for metric in metrics:
            if metric.metric_name not in metrics_data:
                metrics_data[metric.metric_name] = []
            
            metrics_data[metric.metric_name].append({
                "value": float(metric.metric_value),
                "epoch": metric.epoch,
                "step": metric.step,
                "timestamp": metric.recorded_at.isoformat()
            })
        
        return {
            "session_id": session_id,
            "metrics": metrics_data,
            "total_metrics": len(metrics)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话指标失败: {str(e)}"
        )
```

#### WebSocket端点

文件路径: `backend/app/api/api_v1/endpoints/websocket.py` (新文件)

```python
"""
WebSocket API端点

提供实时数据推送功能，支持训练过程监控、性能指标推送等。
"""

from typing import Any, Dict
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from loguru import logger

from app.core.dependencies import get_current_user_from_token
from app.websocket.connection_manager import get_connection_manager
from app.websocket.message_handler import WebSocketMessageHandler


router = APIRouter()


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
    client_ip: str = Query(None, description="客户端IP")
):
    """建立WebSocket连接
    
    Args:
        websocket: WebSocket连接对象
        token: JWT认证令牌
        client_ip: 客户端IP地址
    """
    connection_manager = get_connection_manager()
    message_handler = WebSocketMessageHandler()
    connection_id = None
    
    try:
        # 验证用户身份
        try:
            user = await get_current_user_from_token(token)
            if not user or not user.get("is_active"):
                await websocket.close(code=4001, reason="认证失败")
                return
        except Exception as e:
            logger.error(f"WebSocket认证失败: {str(e)}")
            await websocket.close(code=4001, reason="认证失败")
            return
        
        # 建立连接
        connection_id = await connection_manager.connect(
            websocket=websocket,
            user_id=user["id"],
            client_ip=client_ip,
            user_agent=websocket.headers.get("user-agent")
        )
        
        logger.info(f"WebSocket连接建立成功: user_id={user['id']}, connection_id={connection_id}")
        
        # 消息循环
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理消息
                await message_handler.handle_message(
                    connection_id=connection_id,
                    user_id=user["id"],
                    message=message
                )
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket正常断开: connection_id={connection_id}")
                break
                
            except json.JSONDecodeError:
                logger.warning(f"收到无效JSON消息: connection_id={connection_id}")
                await connection_manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "无效的JSON格式"
                })
                
            except Exception as e:
                logger.error(f"处理WebSocket消息异常: connection_id={connection_id}, error={str(e)}")
                await connection_manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "消息处理失败"
                })
                
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
        
    finally:
        # 清理连接
        if connection_id:
            await connection_manager.disconnect(connection_id)
            logger.info(f"WebSocket连接已清理: connection_id={connection_id}")


@router.get("/stats")
async def get_websocket_stats(
    current_user = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """获取WebSocket连接统计
    
    管理员接口，用于监控WebSocket连接状态。
    """
    if not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="权限不足")
    
    connection_manager = get_connection_manager()
    stats = await connection_manager.get_connection_stats()
    
    return {
        "status": "success",
        "data": stats
    }
```

### API配置变更

#### 新增Celery配置

文件路径: `backend/app/core/celery_app.py` (新文件)

```python
"""
Celery应用配置

配置异步任务队列，支持训练、回测等长时间运行的任务。
"""

import os
from celery import Celery
from kombu import Queue

from app.core.config import settings


# 创建Celery实例
celery_app = Celery(
    "trademaster",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.training_tasks",
        "app.tasks.backtest_tasks", 
        "app.tasks.monitoring_tasks"
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # 任务路由
    task_routes={
        "training.*": {"queue": "training"},
        "backtest.*": {"queue": "backtest"},
        "monitoring.*": {"queue": "monitoring"}
    },
    
    # 队列定义
    task_queues=(
        Queue("training", routing_key="training"),
        Queue("backtest", routing_key="backtest"),
        Queue("monitoring", routing_key="monitoring"),
        Queue("default", routing_key="default")
    ),
    
    # 任务执行配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=7200,  # 2小时任务超时
    task_soft_time_limit=6600,  # 1.8小时软超时
    
    # 结果配置
    result_expires=86400,  # 结果保存1天
    result_backend_transport_options={"master_name": "mymaster"},
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # 错误处理
    task_reject_on_worker_lost=True,
    task_ignore_result=False
)

# 配置环境变量
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10
)


if __name__ == "__main__":
    celery_app.start()
```

#### 环境变量配置扩展

文件路径: `backend/.env` (新增变量)

```bash
# TradeMaster集成配置
TRADEMASTER_ROOT=/app
TRADEMASTER_CONFIG_DIR=/app/configs
TRADEMASTER_DATA_DIR=/app/data
TRADEMASTER_LOGS_DIR=/app/logs

# Celery配置
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# WebSocket配置
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_MAX_CONNECTIONS_PER_USER=5

# 资源限制
MAX_CONCURRENT_SESSIONS_PER_USER=3
TRAINING_TIMEOUT_SECONDS=7200
BACKTEST_TIMEOUT_SECONDS=3600

# 文件存储
MODELS_STORAGE_PATH=/app/storage/models
LOGS_STORAGE_PATH=/app/storage/logs
RESULTS_STORAGE_PATH=/app/storage/results

# 监控配置  
METRICS_RETENTION_DAYS=30
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_MONITORING=true
```

### 前端集成变更

#### WebSocket集成

文件路径: `frontend/src/services/websocket.ts` (新文件)

```typescript
/**
 * WebSocket实时通信服务
 * 
 * 提供与后端的实时数据连接，支持训练监控、状态更新等功能。
 */

import { message, notification } from 'antd';
import { EventEmitter } from 'events';

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
}

export interface SessionMetricsUpdate {
  session_id: number;
  metrics: {
    [key: string]: number;
  };
  epoch: number;
  progress: number;
}

export interface SessionStatusUpdate {
  session_id: number;
  status: string;
  progress: number;
  message?: string;
}

class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private connectionId: string | null = null;
  private isConnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimeout: number = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  
  constructor() {
    super();
    this.setMaxListeners(50); // 支持更多监听器
  }
  
  /**
   * 建立WebSocket连接
   */
  async connect(token: string): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接');
      return;
    }
    
    if (this.isConnecting) {
      console.log('WebSocket正在连接中');
      return;
    }
    
    this.isConnecting = true;
    
    try {
      const wsUrl = `${this.getWebSocketUrl()}/connect?token=${encodeURIComponent(token)}`;
      console.log('连接WebSocket:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      this.isConnecting = false;
      throw error;
    }
  }
  
  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, '用户主动断开');
      this.ws = null;
    }
    
    this.connectionId = null;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    
    this.emit('disconnected');
  }
  
  /**
   * 订阅会话消息
   */
  subscribeToSession(sessionId: number): void {
    if (!this.isConnected()) {
      console.warn('WebSocket未连接，无法订阅会话');
      return;
    }
    
    this.send({
      type: 'subscribe_session',
      session_id: sessionId
    });
    
    console.log('订阅会话:', sessionId);
  }
  
  /**
   * 取消订阅会话
   */
  unsubscribeFromSession(sessionId: number): void {
    if (!this.isConnected()) {
      return;
    }
    
    this.send({
      type: 'unsubscribe_session',
      session_id: sessionId
    });
    
    console.log('取消订阅会话:', sessionId);
  }
  
  /**
   * 发送消息
   */
  private send(data: any): void {
    if (!this.isConnected()) {
      console.warn('WebSocket未连接，无法发送消息');
      return;
    }
    
    try {
      this.ws!.send(JSON.stringify(data));
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
    }
  }
  
  /**
   * 检查连接状态
   */
  private isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
  
  /**
   * 获取WebSocket URL
   */
  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NODE_ENV === 'development' 
      ? 'localhost:8000' 
      : window.location.host;
    return `${protocol}//${host}/api/v1/ws`;
  }
  
  /**
   * 处理连接打开
   */
  private handleOpen(event: Event): void {
    console.log('WebSocket连接已建立');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    
    // 启动心跳
    this.startHeartbeat();
    
    this.emit('connected');
    
    message.success('实时连接已建立');
  }
  
  /**
   * 处理消息接收
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      console.log('收到WebSocket消息:', message);
      
      switch (message.type) {
        case 'connection_established':
          this.connectionId = message.data?.connection_id;
          break;
          
        case 'session_metrics_update':
          this.handleSessionMetrics(message.data as SessionMetricsUpdate);
          break;
          
        case 'session_status_update':
          this.handleSessionStatus(message.data as SessionStatusUpdate);
          break;
          
        case 'training_completed':
          this.handleTrainingCompleted(message.data);
          break;
          
        case 'training_failed':
          this.handleTrainingFailed(message.data);
          break;
          
        case 'ping':
          // 响应心跳
          this.send({ type: 'pong' });
          break;
          
        case 'error':
          console.error('WebSocket错误消息:', message.data);
          break;
          
        default:
          console.warn('未知的WebSocket消息类型:', message.type);
      }
      
      // 触发通用消息事件
      this.emit('message', message);
      
    } catch (error) {
      console.error('解析WebSocket消息失败:', error);
    }
  }
  
  /**
   * 处理连接关闭
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket连接已关闭:', event.code, event.reason);
    
    this.isConnecting = false;
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    this.emit('disconnected');
    
    // 自动重连
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    } else if (event.code !== 1000) {
      message.error('实时连接已断开，请刷新页面重试');
    }
  }
  
  /**
   * 处理连接错误
   */
  private handleError(event: Event): void {
    console.error('WebSocket连接错误:', event);
    this.emit('error', event);
  }
  
  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
      }
    }, 30000); // 30秒心跳
  }
  
  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectTimeout * Math.pow(2, this.reconnectAttempts), 30000);
    
    console.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        const token = localStorage.getItem('access_token');
        if (token) {
          this.connect(token).catch(console.error);
        }
      }
    }, delay);
  }
  
  /**
   * 处理会话指标更新
   */
  private handleSessionMetrics(data: SessionMetricsUpdate): void {
    this.emit('sessionMetrics', data);
  }
  
  /**
   * 处理会话状态更新
   */
  private handleSessionStatus(data: SessionStatusUpdate): void {
    this.emit('sessionStatus', data);
  }
  
  /**
   * 处理训练完成
   */
  private handleTrainingCompleted(data: any): void {
    notification.success({
      message: '训练完成',
      description: `会话 ${data.session_id} 训练已成功完成`,
      duration: 5
    });
    
    this.emit('trainingCompleted', data);
  }
  
  /**
   * 处理训练失败
   */
  private handleTrainingFailed(data: any): void {
    notification.error({
      message: '训练失败',
      description: `会话 ${data.session_id} 训练失败: ${data.error_message}`,
      duration: 10
    });
    
    this.emit('trainingFailed', data);
  }
}

// 全局WebSocket服务实例
export const webSocketService = new WebSocketService();

export default webSocketService;
```

#### 实时监控组件

文件路径: `frontend/src/components/Training/RealTimeMonitor.tsx` (新文件)

```typescript
/**
 * 实时训练监控组件
 * 
 * 显示训练过程的实时指标、进度和状态更新。
 */

import React, { useEffect, useState, useRef } from 'react';
import { Card, Progress, Statistic, Row, Col, Button, Tag, Space } from 'antd';
import { Line } from '@ant-design/plots';
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined } from '@ant-design/icons';

import { webSocketService, SessionMetricsUpdate, SessionStatusUpdate } from '../../services/websocket';
import { strategyApi } from '../../services/api';

interface RealTimeMonitorProps {
  sessionId: number;
  onStop?: () => void;
  onComplete?: () => void;
}

interface MetricPoint {
  epoch: number;
  value: number;
  metric: string;
}

export const RealTimeMonitor: React.FC<RealTimeMonitorProps> = ({
  sessionId,
  onStop,
  onComplete
}) => {
  const [sessionStatus, setSessionStatus] = useState<string>('pending');
  const [progress, setProgress] = useState<number>(0);
  const [currentEpoch, setCurrentEpoch] = useState<number>(0);
  const [totalEpochs, setTotalEpochs] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // 指标数据
  const [metricsData, setMetricsData] = useState<MetricPoint[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState<Record<string, number>>({});
  
  // 控制状态
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  // 引用
  const metricsDataRef = useRef<MetricPoint[]>([]);
  
  useEffect(() => {
    // 订阅会话消息
    webSocketService.subscribeToSession(sessionId);
    
    // 监听实时指标更新
    const handleMetricsUpdate = (data: SessionMetricsUpdate) => {
      if (data.session_id === sessionId) {
        console.log('收到指标更新:', data);
        
        // 更新当前指标
        setCurrentMetrics(data.metrics);
        
        // 添加到历史数据
        const newPoints: MetricPoint[] = [];
        Object.entries(data.metrics).forEach(([metricName, value]) => {
          newPoints.push({
            epoch: data.epoch,
            value: value,
            metric: metricName
          });
        });
        
        setMetricsData(prevData => {
          const updatedData = [...prevData, ...newPoints];
          metricsDataRef.current = updatedData;
          return updatedData;
        });
        
        // 更新进度
        setProgress(data.progress);
        setCurrentEpoch(data.epoch);
      }
    };
    
    // 监听状态更新
    const handleStatusUpdate = (data: SessionStatusUpdate) => {
      if (data.session_id === sessionId) {
        console.log('收到状态更新:', data);
        
        setSessionStatus(data.status);
        setProgress(data.progress);
        
        if (data.message) {
          if (data.status === 'failed') {
            setErrorMessage(data.message);
          }
        }
        
        if (data.status === 'completed' && onComplete) {
          onComplete();
        }
      }
    };
    
    // 监听训练完成
    const handleTrainingCompleted = (data: any) => {
      if (data.session_id === sessionId) {
        setSessionStatus('completed');
        setProgress(100);
        if (onComplete) {
          onComplete();
        }
      }
    };
    
    // 监听训练失败
    const handleTrainingFailed = (data: any) => {
      if (data.session_id === sessionId) {
        setSessionStatus('failed');
        setErrorMessage(data.error_message);
      }
    };
    
    // 注册事件监听器
    webSocketService.on('sessionMetrics', handleMetricsUpdate);
    webSocketService.on('sessionStatus', handleStatusUpdate);
    webSocketService.on('trainingCompleted', handleTrainingCompleted);
    webSocketService.on('trainingFailed', handleTrainingFailed);
    
    // 初始化获取状态
    loadInitialStatus();
    
    return () => {
      // 清理事件监听器
      webSocketService.off('sessionMetrics', handleMetricsUpdate);
      webSocketService.off('sessionStatus', handleStatusUpdate);
      webSocketService.off('trainingCompleted', handleTrainingCompleted);
      webSocketService.off('trainingFailed', handleTrainingFailed);
      
      // 取消订阅
      webSocketService.unsubscribeFromSession(sessionId);
    };
  }, [sessionId]);
  
  /**
   * 加载初始状态
   */
  const loadInitialStatus = async () => {
    try {
      const response = await strategyApi.getSessionStatus(sessionId);
      
      setSessionStatus(response.status);
      setProgress(response.progress);
      setCurrentEpoch(response.current_epoch || 0);
      setTotalEpochs(response.total_epochs || 0);
      setErrorMessage(response.error_message);
      
      // 加载历史指标
      if (response.recent_metrics) {
        const points: MetricPoint[] = [];
        response.recent_metrics.forEach((metric: any) => {
          points.push({
            epoch: metric.epoch || 0,
            value: metric.value,
            metric: metric.metric_name
          });
        });
        setMetricsData(points);
      }
      
    } catch (error) {
      console.error('加载会话状态失败:', error);
    }
  };
  
  /**
   * 停止训练
   */
  const handleStop = async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    
    try {
      await strategyApi.stopSession(sessionId);
      setSessionStatus('cancelled');
      
      if (onStop) {
        onStop();
      }
      
    } catch (error) {
      console.error('停止训练失败:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  /**
   * 获取状态标签颜色
   */
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'pending': return 'blue';
      case 'running': return 'green';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };
  
  /**
   * 获取状态文本
   */
  const getStatusText = (status: string): string => {
    switch (status) {
      case 'pending': return '等待中';
      case 'running': return '训练中';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      case 'cancelled': return '已取消';
      default: return status;
    }
  };
  
  /**
   * 准备图表数据
   */
  const chartData = metricsData.map(point => ({
    epoch: point.epoch,
    value: point.value,
    metric: point.metric
  }));
  
  /**
   * 图表配置
   */
  const chartConfig = {
    data: chartData,
    xField: 'epoch',
    yField: 'value',
    seriesField: 'metric',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    slider: {
      start: Math.max(0, (chartData.length - 50) / chartData.length),
      end: 1,
    },
    tooltip: {
      title: '轮次',
      formatter: (datum: any) => {
        return {
          name: datum.metric,
          value: datum.value.toFixed(4)
        };
      }
    }
  };
  
  return (
    <div className="real-time-monitor">
      <Row gutter={[16, 16]}>
        {/* 状态卡片 */}
        <Col span={24}>
          <Card title="训练状态" size="small">
            <Space size="large" align="center">
              <Tag color={getStatusColor(sessionStatus)} style={{ fontSize: '14px', padding: '4px 8px' }}>
                {getStatusText(sessionStatus)}
              </Tag>
              
              <Statistic 
                title="进度" 
                value={progress} 
                suffix="%" 
                precision={1}
              />
              
              <Statistic 
                title="轮次" 
                value={`${currentEpoch}/${totalEpochs || '?'}`}
              />
              
              {sessionStatus === 'running' && (
                <Button 
                  type="primary" 
                  danger 
                  icon={<StopOutlined />}
                  onClick={handleStop}
                  loading={isLoading}
                >
                  停止训练
                </Button>
              )}
            </Space>
            
            {/* 进度条 */}
            <div style={{ marginTop: '16px' }}>
              <Progress 
                percent={progress} 
                status={
                  sessionStatus === 'failed' ? 'exception' : 
                  sessionStatus === 'completed' ? 'success' : 
                  'active'
                }
                showInfo={false}
              />
            </div>
            
            {/* 错误信息 */}
            {errorMessage && (
              <div style={{ marginTop: '8px', color: '#ff4d4f' }}>
                错误: {errorMessage}
              </div>
            )}
          </Card>
        </Col>
        
        {/* 当前指标 */}
        <Col span={24}>
          <Card title="当前指标" size="small">
            <Row gutter={16}>
              {Object.entries(currentMetrics).map(([metricName, value]) => (
                <Col key={metricName} xs={12} sm={8} md={6} lg={4}>
                  <Statistic 
                    title={metricName}
                    value={value}
                    precision={4}
                  />
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
        
        {/* 训练曲线 */}
        <Col span={24}>
          <Card title="训练曲线" size="small">
            {chartData.length > 0 ? (
              <Line {...chartConfig} height={300} />
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                暂无数据
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RealTimeMonitor;
```

### 配置文件变更

#### Docker Compose配置

文件路径: `web_interface/docker-compose.yml` (更新现有文件)

```yaml
version: '3.8'

services:
  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend
    networks:
      - trademaster-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://trademaster:password@postgres:5432/trademaster
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - TRADEMASTER_ROOT=/app
    depends_on:
      - postgres
      - redis
    volumes:
      - ../:/app  # 挂载TradeMaster根目录
      - trademaster_storage:/app/storage
    networks:
      - trademaster-network

  # Celery Workers
  worker-training:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.core.celery_app worker --loglevel=info --queues=training --concurrency=2
    environment:
      - DATABASE_URL=postgresql://trademaster:password@postgres:5432/trademaster
      - REDIS_URL=redis://redis:6379/0  
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - TRADEMASTER_ROOT=/app
    depends_on:
      - postgres
      - redis
    volumes:
      - ../:/app
      - trademaster_storage:/app/storage
    networks:
      - trademaster-network

  worker-backtest:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.core.celery_app worker --loglevel=info --queues=backtest --concurrency=4
    environment:
      - DATABASE_URL=postgresql://trademaster:password@postgres:5432/trademaster
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - TRADEMASTER_ROOT=/app
    depends_on:
      - postgres
      - redis
    volumes:
      - ../:/app
      - trademaster_storage:/app/storage
    networks:
      - trademaster-network

  # Celery Flower (监控)
  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.core.celery_app flower --loglevel=info
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
    networks:
      - trademaster-network

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=trademaster
      - POSTGRES_USER=trademaster
      - POSTGRES_PASSWORD=password
    ports:
      - "15432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - trademaster-network

  redis:
    image: redis:7-alpine
    ports:
      - "16379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - trademaster-network

volumes:
  postgres_data:
  redis_data:
  trademaster_storage:

networks:
  trademaster-network:
    driver: bridge
```

## 实施序列

### 阶段1: 基础集成架构 (1-2周)

#### 任务分解
1. **数据库扩展** (2天)
   - 创建新增表结构的迁移脚本
   - 执行数据库迁移和索引创建
   - 验证数据库连接和查询性能

2. **Celery集成** (3天)
   - 配置Celery和Redis
   - 实现基础任务处理框架
   - 创建任务监控和状态管理

3. **TradeMaster集成服务重构** (3天)
   - 完善`TradeMasterIntegrationService`
   - 实现配置转换和验证
   - 集成会话管理功能

4. **API端点重构** (2天)
   - 移除所有模拟数据返回
   - 实现真实的策略CRUD操作
   - 集成会话管理API

#### 验收标准
- ✅ 数据库架构完整，所有新表创建成功
- ✅ Celery任务队列正常运行，可以提交和监控任务
- ✅ 策略API返回真实数据，无任何模拟数据
- ✅ 可以创建训练会话并更新状态

### 阶段2: 核心训练功能 (2-3周)

#### 任务分解
1. **训练任务执行器** (5天)
   - 实现`execute_training_task`完整功能
   - TradeMaster进程管理和监控
   - 异常处理和重试机制

2. **WebSocket实时通信** (4天)
   - 实现WebSocket连接管理器
   - 消息处理和路由系统
   - 前端WebSocket服务集成

3. **实时监控组件** (3天)
   - React实时监控界面
   - 训练曲线可视化
   - 进度和状态显示

4. **回测功能集成** (3天)
   - 回测任务处理器
   - 历史数据处理
   - 性能指标计算

#### 验收标准
- ✅ 可以成功运行完整TradeMaster训练流程
- ✅ 前端实时显示训练进度和指标曲线
- ✅ WebSocket通信稳定，延迟<1秒
- ✅ 回测功能完整，可以生成性能报告

### 阶段3: 高级功能和优化 (2-4周)

#### 任务分解
1. **资源管理和调度** (4天)
   - 实现资源使用监控
   - 任务优先级和队列管理
   - GPU/CPU资源分配

2. **容器化训练环境** (3天)
   - Docker容器隔离训练
   - 环境一致性保证
   - 扩展性支持

3. **实盘交易集成** (7天)
   - 交易接口集成
   - 风险控制机制实现
   - 实盘监控和告警系统

4. **性能优化** (3天)
   - 数据库查询优化
   - 缓存策略实施
   - 系统性能调优

#### 验收标准
- ✅ 支持多用户并发训练，资源合理分配
- ✅ 容器化部署稳定，环境隔离可靠
- ✅ 实盘交易功能完整，风险控制到位
- ✅ 系统性能达到目标指标

### 阶段4: 监控运维和文档 (1-2周)

#### 任务分解
1. **监控系统完善** (3天)
   - Prometheus指标收集
   - Grafana可视化面板
   - 告警规则配置

2. **文档编写** (4天)
   - API文档更新
   - 用户使用手册
   - 部署运维指南

3. **测试和验收** (3天)
   - 功能测试和性能测试
   - 安全测试和压力测试
   - 用户验收测试

#### 验收标准
- ✅ 完整的监控体系和告警机制
- ✅ 详细的技术文档和用户指南
- ✅ 所有功能测试通过
- ✅ 性能指标达到预期目标

## 验证计划

### 单元测试

#### 核心服务测试
```python
# backend/tests/test_integration_service.py
import pytest
from unittest.mock import Mock, patch

from app.services.trademaster_integration import TradeMasterIntegrationService


class TestTradeMasterIntegrationService:
    
    @pytest.fixture
    def integration_service(self):
        return TradeMasterIntegrationService()
    
    async def test_create_training_session(self, integration_service):
        """测试创建训练会话"""
        config = {
            "agent_type": "dqn",
            "dataset_name": "BTC",
            "epochs": 100,
            "learning_rate": 0.001
        }
        
        session_id = await integration_service.create_training_session(
            strategy_id=1,
            user_id=1,
            config=config
        )
        
        assert isinstance(session_id, int)
        assert session_id > 0
    
    async def test_start_training_task(self, integration_service):
        """测试启动训练任务"""
        with patch('app.tasks.training_tasks.execute_training_task.delay') as mock_task:
            mock_task.return_value.id = "test-task-id"
            
            task_id = await integration_service.start_training_task(session_id=1)
            
            assert task_id == "test-task-id"
            mock_task.assert_called_once_with(1)
    
    async def test_config_validation(self, integration_service):
        """测试配置验证"""
        valid_config = {
            "agent_type": "dqn",
            "dataset_name": "BTC",
            "epochs": 100
        }
        
        invalid_config = {
            "agent_type": "invalid",
            "epochs": -1
        }
        
        # 测试有效配置
        tm_config = await integration_service._convert_config_to_trademaster(valid_config)
        assert tm_config is not None
        
        # 测试无效配置
        with pytest.raises(ValueError):
            await integration_service._convert_config_to_trademaster(invalid_config)
```

#### WebSocket连接测试
```python
# backend/tests/test_websocket.py
import pytest
from unittest.mock import Mock, AsyncMock

from app.websocket.connection_manager import WebSocketConnectionManager


class TestWebSocketConnectionManager:
    
    @pytest.fixture
    def connection_manager(self):
        return WebSocketConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        websocket = Mock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket
    
    async def test_connect_and_disconnect(self, connection_manager, mock_websocket):
        """测试WebSocket连接和断开"""
        # 测试连接
        connection_id = await connection_manager.connect(
            websocket=mock_websocket,
            user_id=1
        )
        
        assert connection_id in connection_manager.active_connections
        assert 1 in connection_manager.user_connections
        assert connection_id in connection_manager.user_connections[1]
        
        # 测试断开
        await connection_manager.disconnect(connection_id)
        
        assert connection_id not in connection_manager.active_connections
        assert 1 not in connection_manager.user_connections
    
    async def test_session_subscription(self, connection_manager, mock_websocket):
        """测试会话订阅"""
        connection_id = await connection_manager.connect(mock_websocket, user_id=1)
        
        # 测试订阅
        await connection_manager.subscribe_to_session(connection_id, session_id=100)
        
        assert 100 in connection_manager.session_subscriptions
        assert connection_id in connection_manager.session_subscriptions[100]
        
        # 测试取消订阅
        await connection_manager.unsubscribe_from_session(connection_id, session_id=100)
        
        assert 100 not in connection_manager.session_subscriptions
    
    async def test_message_broadcasting(self, connection_manager, mock_websocket):
        """测试消息广播"""
        connection_id = await connection_manager.connect(mock_websocket, user_id=1)
        await connection_manager.subscribe_to_session(connection_id, session_id=100)
        
        test_message = {"type": "test", "data": "hello"}
        
        # 测试会话广播
        await connection_manager.broadcast_to_session(100, test_message)
        
        mock_websocket.send_text.assert_called()
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert "test" in sent_data
        assert "hello" in sent_data
```

### 集成测试

#### 端到端训练流程测试
```python
# backend/tests/test_training_flow.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch

from app.main import app


class TestTrainingFlow:
    
    @pytest.fixture
    def auth_headers(self):
        # 模拟认证头
        return {"Authorization": "Bearer test-token"}
    
    async def test_complete_training_flow(self, auth_headers):
        """测试完整训练流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. 创建策略
            strategy_data = {
                "name": "测试策略",
                "description": "集成测试策略",
                "strategy_type": "algorithmic_trading",
                "config": {"agent_type": "dqn", "dataset_name": "BTC"}
            }
            
            response = await client.post(
                "/api/v1/strategies",
                json=strategy_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            strategy = response.json()
            strategy_id = strategy["id"]
            
            # 2. 启动训练
            training_request = {
                "dataset_name": "BTC",
                "agent_type": "dqn",
                "epochs": 10,
                "learning_rate": 0.001,
                "batch_size": 32
            }
            
            with patch('app.tasks.training_tasks.execute_training_task.delay') as mock_task:
                mock_task.return_value.id = "test-task-id"
                
                response = await client.post(
                    f"/api/v1/strategies/{strategy_id}/train",
                    json=training_request,
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                session = response.json()
                session_id = session["session_id"]
                
                # 验证任务已提交
                mock_task.assert_called_once()
            
            # 3. 检查会话状态
            response = await client.get(
                f"/api/v1/strategies/sessions/{session_id}/status",
                headers=auth_headers
            )
            assert response.status_code == 200
            status = response.json()
            assert status["session_id"] == session_id
            assert status["status"] in ["pending", "running"]
            
            # 4. 停止会话
            response = await client.post(
                f"/api/v1/strategies/sessions/{session_id}/stop",
                headers=auth_headers
            )
            assert response.status_code == 200
```

### 性能测试

#### 并发训练测试
```python
# backend/tests/test_performance.py
import pytest
import asyncio
from httpx import AsyncClient
from concurrent.futures import ThreadPoolExecutor

from app.main import app


class TestPerformance:
    
    async def test_concurrent_training_sessions(self):
        """测试并发训练会话"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 创建多个并发训练请求
            concurrent_requests = 10
            
            async def start_training_session(session_num):
                training_request = {
                    "dataset_name": f"TEST_{session_num}",
                    "agent_type": "dqn",
                    "epochs": 5
                }
                
                response = await client.post(
                    f"/api/v1/strategies/1/train",
                    json=training_request,
                    headers={"Authorization": "Bearer test-token"}
                )
                return response.status_code, response.json()
            
            # 执行并发请求
            tasks = [
                start_training_session(i) 
                for i in range(concurrent_requests)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证结果
            successful_requests = 0
            for result in results:
                if isinstance(result, tuple) and result[0] == 200:
                    successful_requests += 1
            
            # 至少应该有一些请求成功
            assert successful_requests > 0
            print(f"成功处理 {successful_requests}/{concurrent_requests} 个并发请求")
    
    async def test_websocket_message_throughput(self):
        """测试WebSocket消息吞吐量"""
        from app.websocket.connection_manager import get_connection_manager
        
        connection_manager = get_connection_manager()
        
        # 模拟大量消息发送
        message_count = 1000
        message = {"type": "test", "data": "performance_test"}
        
        start_time = asyncio.get_event_loop().time()
        
        # 假设有一个测试用的会话订阅
        for i in range(message_count):
            await connection_manager.broadcast_to_session(1, {
                **message, 
                "sequence": i
            })
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        throughput = message_count / duration
        print(f"WebSocket消息吞吐量: {throughput:.2f} 消息/秒")
        
        # 验证性能指标
        assert throughput > 100, "WebSocket吞吐量应该大于100消息/秒"
```

### 业务逻辑验证

#### 策略生命周期测试
```python
# backend/tests/test_strategy_lifecycle.py
import pytest
from unittest.mock import Mock, patch

from app.services.trademaster_integration import get_integration_service
from app.models.session import SessionStatus, SessionType


class TestStrategyLifecycle:
    
    @pytest.fixture
    def integration_service(self):
        return get_integration_service()
    
    async def test_training_to_backtest_flow(self, integration_service):
        """测试从训练到回测的完整流程"""
        # 1. 创建并完成训练
        training_config = {
            "agent_type": "dqn",
            "dataset_name": "BTC", 
            "epochs": 10
        }
        
        training_session_id = await integration_service.create_training_session(
            strategy_id=1,
            user_id=1,
            config=training_config
        )
        
        # 模拟训练完成
        with patch.object(integration_service, 'get_session_status') as mock_status:
            mock_status.return_value = {
                "session_id": training_session_id,
                "status": "completed",
                "progress": 100.0,
                "final_metrics": {"loss": 0.123, "reward": 15.67}
            }
            
            status = await integration_service.get_session_status(training_session_id)
            assert status["status"] == "completed"
        
        # 2. 基于训练结果创建回测
        backtest_config = {
            "mode": "backtest",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000
        }
        
        backtest_session_id = await integration_service.create_backtest_session(
            strategy_id=1,
            user_id=1,
            config=backtest_config
        )
        
        assert backtest_session_id != training_session_id
        
        # 3. 验证回测配置
        backtest_status = await integration_service.get_session_status(backtest_session_id)
        assert backtest_status["session_id"] == backtest_session_id
    
    async def test_error_handling_and_recovery(self, integration_service):
        """测试错误处理和恢复机制"""
        # 1. 测试无效配置
        invalid_config = {
            "agent_type": "nonexistent",
            "dataset_name": "",
            "epochs": -1
        }
        
        with pytest.raises(ValueError, match="配置验证失败"):
            await integration_service.create_training_session(
                strategy_id=1,
                user_id=1,
                config=invalid_config
            )
        
        # 2. 测试训练失败恢复
        valid_config = {
            "agent_type": "dqn",
            "dataset_name": "BTC",
            "epochs": 10
        }
        
        session_id = await integration_service.create_training_session(
            strategy_id=1,
            user_id=1,
            config=valid_config
        )
        
        # 模拟训练失败
        with patch.object(integration_service, 'get_session_status') as mock_status:
            mock_status.return_value = {
                "session_id": session_id,
                "status": "failed",
                "error_message": "内存不足"
            }
            
            status = await integration_service.get_session_status(session_id)
            assert status["status"] == "failed"
            assert "内存不足" in status["error_message"]
        
        # 3. 测试会话重启
        # 用相同配置重新创建会话应该成功
        new_session_id = await integration_service.create_training_session(
            strategy_id=1,
            user_id=1,
            config=valid_config
        )
        
        assert new_session_id != session_id
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"activeForm": "\u751f\u6210\u5b8c\u6574\u7684\u6280\u672f\u89c4\u8303\u6587\u6863", "content": "\u751f\u6210\u5b8c\u6574\u7684\u6280\u672f\u89c4\u8303\u6587\u6863", "status": "completed"}]