"""
训练任务处理器

实现TradeMaster训练任务的异步执行、进度监控和结果处理。
集成Celery任务队列，支持实时状态更新和错误处理。
"""

import os
import sys
import asyncio
import subprocess
import json
import yaml
import signal
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from celery import Task
from loguru import logger

from app.core.celery_app import celery_app
from app.core.database import get_async_db_session
from app.models.database import StrategySession, SessionStatus, PerformanceMetric, ResourceUsage
from app.services.websocket_service import get_websocket_manager


class CallbackTask(Task):
    """带回调的任务基类"""
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        logger.info(f"训练任务成功完成: {task_id}")
        
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        logger.error(f"训练任务执行失败: {task_id}, 错误: {str(exc)}")


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
        
        if session.status != SessionStatus.PENDING:
            raise ValueError(f"会话状态错误: {session.status}")
        
        # 更新状态为运行中
        asyncio.run(_update_session_status(session_id, SessionStatus.RUNNING))
        
        # 尝试直接使用TradeMaster核心模块
        if _has_trademaster_core():
            logger.info("使用TradeMaster核心模块执行训练")
            result = _execute_with_core_module(session)
        else:
            logger.info("使用TradeMaster进程执行训练")
            result = _execute_with_process(session)
        
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


def _has_trademaster_core() -> bool:
    """检查是否有TradeMaster核心模块可用"""
    try:
        get_trademaster_core()
        return True
    except Exception:
        return False


def _execute_with_core_module(session: StrategySession) -> Dict[str, Any]:
    """使用TradeMaster核心模块执行训练"""
    try:
        core = get_trademaster_core()
        
        # 启动训练 - 添加进度回调
        def progress_callback(session_id: str, progress_data: Dict[str, Any]):
            """TradeMaster训练进度回调"""
            try:
                # 更新会话状态
                asyncio.run(_update_training_progress(
                    session.id, 
                    progress_data.get('progress', 0),
                    progress_data.get('epoch', 0),
                    progress_data.get('metrics', {})
                ))
                
                # 记录性能指标
                if 'metrics' in progress_data:
                    asyncio.run(_record_performance_metrics(
                        session.id,
                        progress_data['metrics'],
                        progress_data.get('epoch', 0)
                    ))
                    
            except Exception as e:
                logger.warning(f"Session {session.id}: 进度回调失败: {str(e)}")
        
        training_session_id = asyncio.run(
            core.start_training(session.trademaster_config, callback=progress_callback)
        )
        
        # 更新会话的TradeMaster会话ID
        asyncio.run(_update_trademaster_session_id(session.id, training_session_id))
        
        # 监控训练过程
        return _monitor_core_training(session.id, training_session_id, core)
        
    except TradeMasterCoreError as e:
        logger.error(f"TradeMaster核心模块训练失败: {str(e)}")
        return {"success": False, "error": str(e)}


def _execute_with_process(session: StrategySession) -> Dict[str, Any]:
    """使用独立进程执行TradeMaster训练"""
    try:
        # 创建配置文件
        config_path = _create_trademaster_config(session)
        
        # 启动TradeMaster进程
        process = _start_trademaster_process(config_path, session.id)
        
        # 监控训练进程
        return _monitor_training_process(process, session.id)
        
    except Exception as e:
        logger.error(f"进程训练失败: {str(e)}")
        return {"success": False, "error": str(e)}


def _monitor_core_training(
    session_id: int, 
    training_session_id: str, 
    core
) -> Dict[str, Any]:
    """监控核心模块训练过程"""
    try:
        start_time = datetime.now()
        
        while True:
            # 获取训练状态
            status = asyncio.run(core.get_training_status(training_session_id))
            
            if status.get("status") == "completed":
                # 训练完成
                final_metrics = status.get("metrics", {})
                asyncio.run(_save_final_metrics(session_id, final_metrics))
                
                return {
                    "success": True,
                    "final_metrics": final_metrics,
                    "duration": (datetime.now() - start_time).total_seconds()
                }
            elif status.get("status") == "failed":
                # 训练失败
                error_msg = status.get("error", "训练失败")
                return {"success": False, "error": error_msg}
            elif status.get("status") in ["running", "training"]:
                # 训练进行中，更新进度
                progress = status.get("progress", 0)
                current_epoch = status.get("current_epoch", 0)
                metrics = status.get("current_metrics", {})
                
                # 更新进度和指标
                asyncio.run(_update_session_progress(
                    session_id, current_epoch, progress
                ))
                
                if metrics:
                    asyncio.run(_save_performance_metrics(
                        session_id, metrics, current_epoch
                    ))
                
                # 记录资源使用
                resource_info = _collect_resource_usage()
                asyncio.run(_save_resource_usage(session_id, resource_info))
            
            # 等待5秒再检查 - 修复 asyncio.sleep 错误
            import time
            time.sleep(5)
            
    except Exception as e:
        logger.error(f"监控核心训练异常: {str(e)}")
        return {"success": False, "error": str(e)}


def _monitor_training_process(process: subprocess.Popen, session_id: int) -> Dict[str, Any]:
    """监控训练进程"""
    try:
        start_time = datetime.now()
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
                
            if output:
                # 解析训练输出
                metrics = _parse_training_output(output.strip())
                if metrics:
                    # 保存指标到数据库
                    asyncio.run(_save_performance_metrics(
                        session_id, metrics, metrics.get("epoch")
                    ))
                    
                    # 更新会话进度
                    if "epoch" in metrics:
                        progress = _calculate_progress(
                            metrics["epoch"], 
                            metrics.get("total_epochs", 100)
                        )
                        asyncio.run(_update_session_progress(
                            session_id, metrics["epoch"], progress
                        ))
                
                # 记录资源使用
                resource_info = _collect_resource_usage()
                asyncio.run(_save_resource_usage(session_id, resource_info))
        
        return_code = process.wait()
        success = return_code == 0
        
        # 收集最终结果
        final_metrics = asyncio.run(_collect_final_metrics(session_id))
        
        return {
            "success": success,
            "return_code": return_code,
            "final_metrics": final_metrics,
            "duration": (datetime.now() - start_time).total_seconds()
        }
        
    except Exception as e:
        logger.error(f"监控进程异常: {str(e)}")
        process.kill()
        return {"success": False, "error": str(e)}


def _create_trademaster_config(session: StrategySession) -> str:
    """创建TradeMaster配置文件"""
    config_dir = Path("/tmp/trademaster_configs")
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / f"session_{session.id}_config.yaml"
    
    # 写入配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(session.trademaster_config, f, default_flow_style=False)
    
    logger.info(f"创建配置文件: {config_path}")
    return str(config_path)


def _start_trademaster_process(config_path: str, session_id: int) -> subprocess.Popen:
    """启动TradeMaster训练进程"""
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
    
    # 保存进程信息
    asyncio.run(_update_session_process_info(
        session_id, 
        process.pid, 
        log_file_path
    ))
    
    logger.info(f"启动TradeMaster进程: pid={process.pid}, session_id={session_id}")
    return process


def _parse_training_output(output: str) -> Optional[Dict[str, Any]]:
    """解析训练输出日志"""
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
                part = part.strip()
                if 'Epoch:' in part:
                    metrics['epoch'] = int(part.split(':')[1].strip())
                elif 'Loss:' in part:
                    metrics['loss'] = float(part.split(':')[1].strip())
                elif 'Reward:' in part:
                    metrics['reward'] = float(part.split(':')[1].strip())
                elif 'Return:' in part:
                    metrics['return'] = float(part.split(':')[1].strip())
            
            return metrics if metrics else None
            
        return None
        
    except Exception as e:
        logger.warning(f"解析训练输出失败: {str(e)}")
        return None


def _calculate_progress(current_epoch: int, total_epochs: int) -> float:
    """计算训练进度百分比"""
    if total_epochs <= 0:
        return 0.0
    return min(100.0, (current_epoch / total_epochs) * 100.0)


def _collect_resource_usage() -> Dict[str, Any]:
    """收集当前系统资源使用情况"""
    try:
        # 获取CPU和内存使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        resource_info = {
            "cpu_percent": cpu_percent,
            "memory_mb": memory.used // (1024 * 1024),
            "memory_percent": memory.percent
        }
        
        # 尝试获取GPU信息 (需要安装nvidia-ml-py3)
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            gpu_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            resource_info.update({
                "gpu_percent": gpu_info.gpu,
                "gpu_memory_mb": gpu_memory_info.used // (1024 * 1024)
            })
        except Exception:
            # GPU信息获取失败，忽略
            pass
        
        return resource_info
        
    except Exception as e:
        logger.warning(f"收集资源使用情况失败: {str(e)}")
        return {}


# ==================== 异步数据库操作辅助函数 ====================

async def _get_session(session_id: int) -> Optional[StrategySession]:
    """获取会话信息"""
    async with get_async_db_session() as db:
        session = await db.get(StrategySession, session_id)
        return session


async def _update_session_status(
    session_id: int, 
    status: SessionStatus, 
    error_message: str = None
):
    """更新会话状态"""
    async with get_async_db_session() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.status = status
            session.updated_at = datetime.now()
            if status == SessionStatus.RUNNING and not session.started_at:
                session.started_at = datetime.now()
            if error_message:
                session.error_message = error_message
            await db.commit()


async def _update_trademaster_session_id(session_id: int, tm_session_id: str):
    """更新TradeMaster会话ID"""
    async with get_async_db_session() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.trademaster_session_id = tm_session_id
            await db.commit()


async def _update_session_process_info(
    session_id: int, 
    process_id: int, 
    log_file_path: str
):
    """更新会话进程信息"""
    async with get_async_db_session() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            # 将进程信息存储在final_metrics中
            if not session.final_metrics:
                session.final_metrics = {}
            session.final_metrics.update({
                "process_id": process_id,
                "log_file_path": log_file_path
            })
            session.log_file_path = log_file_path
            await db.commit()


async def _update_session_progress(
    session_id: int, 
    current_epoch: int, 
    progress: float
):
    """更新会话进度"""
    async with get_async_db_session() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.current_epoch = current_epoch
            session.progress = min(100.0, max(0.0, progress))
            session.updated_at = datetime.now()
            await db.commit()


async def _save_performance_metrics(
    session_id: int, 
    metrics: Dict[str, Any],
    epoch: Optional[int] = None
):
    """保存性能指标"""
    async with get_async_db_session() as db:
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)) and metric_name != "epoch":
                metric = PerformanceMetric(
                    session_id=session_id,
                    metric_name=metric_name,
                    metric_value=float(metric_value),
                    epoch=epoch,
                    step=metrics.get("step")
                )
                db.add(metric)
        await db.commit()


async def _save_resource_usage(session_id: int, resource_info: Dict[str, Any]):
    """保存资源使用记录"""
    if not resource_info:
        return
        
    async with get_async_db_session() as db:
        resource = ResourceUsage(
            session_id=session_id,
            cpu_percent=resource_info.get("cpu_percent"),
            memory_mb=resource_info.get("memory_mb"),
            gpu_percent=resource_info.get("gpu_percent"),
            gpu_memory_mb=resource_info.get("gpu_memory_mb"),
            disk_io_mb=resource_info.get("disk_io_mb"),
            network_io_mb=resource_info.get("network_io_mb")
        )
        db.add(resource)
        await db.commit()


async def _update_session_final_status(
    session_id: int, 
    status: SessionStatus, 
    result: Dict[str, Any]
):
    """更新最终状态"""
    async with get_async_db_session() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.status = status
            session.completed_at = datetime.now()
            session.final_metrics.update(result.get("final_metrics", {}))
            if not result.get("success"):
                session.error_message = result.get("error", "训练失败")
            await db.commit()


async def _save_final_metrics(session_id: int, final_metrics: Dict[str, Any]):
    """保存最终指标"""
    async with get_async_db_session() as db:
        session = await db.get(StrategySession, session_id)
        if session:
            session.final_metrics.update(final_metrics)
            await db.commit()


async def _collect_final_metrics(session_id: int) -> Dict[str, Any]:
    """收集最终指标"""
    try:
        async with get_async_db_session() as db:
            # 获取最后一轮的指标
            from sqlalchemy import select, desc
            
            query = select(PerformanceMetric).where(
                PerformanceMetric.session_id == session_id
            ).order_by(desc(PerformanceMetric.epoch), desc(PerformanceMetric.recorded_at)).limit(10)
            
            result = await db.execute(query)
            metrics = result.scalars().all()
            
            final_metrics = {}
            for metric in metrics:
                if metric.metric_name not in final_metrics:
                    final_metrics[metric.metric_name] = float(metric.metric_value)
            
            return final_metrics
            
    except Exception as e:
        logger.error(f"收集最终指标失败: {str(e)}")
        return {}


# ==================== 任务停止和清理 ====================

@celery_app.task(name="training.stop")
def stop_training_task(session_id: int):
    """停止训练任务"""
    logger.info(f"停止训练任务: session_id={session_id}")
    
    try:
        # 获取会话信息
        session = asyncio.run(_get_session(session_id))
        if not session:
            return {"success": False, "error": "会话不存在"}
        
        # 尝试停止TradeMaster会话
        if session.trademaster_session_id and _has_trademaster_core():
            try:
                core = get_trademaster_core()
                asyncio.run(core.stop_training(session.trademaster_session_id))
            except Exception as e:
                logger.warning(f"停止TradeMaster会话失败: {str(e)}")
        
        # 停止进程
        process_id = session.final_metrics.get("process_id")
        if process_id:
            try:
                process = psutil.Process(process_id)
                process.terminate()
                process.wait(timeout=10)  # 等待10秒
            except psutil.NoSuchProcess:
                pass  # 进程已经结束
            except psutil.TimeoutExpired:
                process.kill()  # 强制杀死
            except Exception as e:
                logger.warning(f"停止进程失败: {str(e)}")
        
        # 更新会话状态
        asyncio.run(_update_session_status(session_id, SessionStatus.CANCELLED))
        
        return {"success": True, "message": "训练任务已停止"}
        
    except Exception as e:
        logger.error(f"停止训练任务失败: {str(e)}")
        return {"success": False, "error": str(e)}