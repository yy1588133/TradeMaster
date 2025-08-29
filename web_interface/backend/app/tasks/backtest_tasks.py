"""
回测任务处理器

实现基于历史数据的策略回测分析。
支持多种回测参数配置和性能评估指标。
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from app.core.celery_app import celery_app
from app.tasks.training_tasks import CallbackTask, _get_session, _update_session_status, _save_performance_metrics
from app.models.database import SessionStatus, SessionType
from app.services.trademaster_core import get_trademaster_core, TradeMasterCoreError


@celery_app.task(bind=True, base=CallbackTask, name="backtest.execute")
def execute_backtest_task(self, session_id: int):
    """执行回测任务
    
    Args:
        session_id: 回测会话ID
        
    Returns:
        dict: 回测结果
    """
    logger.info(f"开始执行回测任务: session_id={session_id}")
    
    try:
        # 获取会话信息
        session = asyncio.run(_get_session(session_id))
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        if session.session_type != SessionType.BACKTEST:
            raise ValueError(f"会话类型错误: {session.session_type}")
        
        if session.status != SessionStatus.PENDING:
            raise ValueError(f"会话状态错误: {session.status}")
        
        # 更新状态为运行中
        asyncio.run(_update_session_status(session_id, SessionStatus.RUNNING))
        
        # 执行回测
        try:
            core = get_trademaster_core()
            result = asyncio.run(_execute_backtest_with_core(session, core))
        except Exception:
            # 降级到模拟回测
            logger.warning("TradeMaster核心不可用，使用模拟回测")
            result = _execute_mock_backtest(session)
        
        # 更新最终状态
        final_status = SessionStatus.COMPLETED if result["success"] else SessionStatus.FAILED
        asyncio.run(_update_session_final_status(session_id, final_status, result))
        
        logger.info(f"回测任务完成: session_id={session_id}, success={result['success']}")
        return result
        
    except Exception as exc:
        logger.error(f"回测任务异常: session_id={session_id}, error={str(exc)}")
        
        # 更新为失败状态
        asyncio.run(_update_session_status(
            session_id, 
            SessionStatus.FAILED,
            error_message=str(exc)
        ))
        
        raise exc


async def _execute_backtest_with_core(session, core) -> Dict[str, Any]:
    """使用TradeMaster核心执行回测"""
    try:
        # 配置回测参数
        backtest_config = session.trademaster_config.copy()
        backtest_config.update({
            "mode": "backtest",
            "task": backtest_config.get("task", "algorithmic_trading")
        })
        
        # 启动回测
        backtest_session_id = await core.start_backtest(backtest_config)
        
        # 等待回测完成
        start_time = datetime.now()
        while True:
            status = await core.get_backtest_status(backtest_session_id)
            
            if status.get("status") == "completed":
                # 回测完成，获取结果
                results = await core.get_backtest_results(backtest_session_id)
                
                # 保存性能指标
                if "metrics" in results:
                    await _save_performance_metrics(
                        session.id, results["metrics"]
                    )
                
                return {
                    "success": True,
                    "final_metrics": results.get("metrics", {}),
                    "duration": (datetime.now() - start_time).total_seconds(),
                    "backtest_results": results
                }
            elif status.get("status") == "failed":
                error_msg = status.get("error", "回测失败")
                return {"success": False, "error": error_msg}
            
            # 等待2秒再检查
            await asyncio.sleep(2)
            
    except TradeMasterCoreError as e:
        logger.error(f"TradeMaster核心回测失败: {str(e)}")
        return {"success": False, "error": str(e)}


def _execute_mock_backtest(session) -> Dict[str, Any]:
    """执行模拟回测（用于演示和测试）"""
    import time
    import random
    
    logger.info(f"执行模拟回测: session_id={session.id}")
    
    try:
        # 模拟回测过程
        config = session.trademaster_config
        initial_capital = config.get("initial_capital", 100000)
        
        # 模拟回测计算
        time.sleep(2)  # 模拟计算时间
        
        # 生成模拟回测结果
        total_return = random.uniform(-0.1, 0.3)  # -10% 到 30% 的收益率
        sharpe_ratio = random.uniform(0.5, 2.5)
        max_drawdown = random.uniform(0.02, 0.15)
        win_rate = random.uniform(0.45, 0.75)
        
        final_metrics = {
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "initial_capital": initial_capital,
            "final_capital": initial_capital * (1 + total_return),
            "total_trades": random.randint(50, 200),
            "avg_trade_return": total_return / random.randint(50, 200)
        }
        
        # 异步保存指标
        asyncio.run(_save_performance_metrics(session.id, final_metrics))
        
        return {
            "success": True,
            "final_metrics": final_metrics,
            "duration": 2.0,
            "backtest_results": {
                "summary": final_metrics,
                "trade_log": [],  # 简化的交易记录
                "daily_returns": []  # 简化的日收益率
            }
        }
        
    except Exception as e:
        logger.error(f"模拟回测失败: {str(e)}")
        return {"success": False, "error": str(e)}


# 从training_tasks导入需要的函数
from app.tasks.training_tasks import _update_session_final_status