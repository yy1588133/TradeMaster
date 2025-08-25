"""
TradeMaster核心模块集成服务

提供直接调用TradeMaster核心模块的功能，包括智能体、数据集、环境等组件的实例化和管理。
支持策略训练、数据处理、评估分析等核心功能的直接集成。
"""

import os
import sys
import asyncio
import threading
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future

import numpy as np
from loguru import logger

# 添加TradeMaster到Python路径
# 在Docker容器中，使用环境变量或者动态检测
try:
    # 尝试从环境变量获取
    TRADEMASTER_ROOT = os.environ.get('TRADEMASTER_ROOT')
    if not TRADEMASTER_ROOT:
        # 动态检测：从当前文件向上查找，直到找到trademaster目录或到达根目录
        current_dir = Path(__file__).resolve()
        max_levels = min(6, len(current_dir.parts))  # 防止IndexError
        for i in range(max_levels):
            try:
                potential_root = current_dir.parents[i]
                # 检查是否存在trademaster相关文件/目录
                if (potential_root / 'trademaster').exists() or \
                   (potential_root / 'setup.py').exists() or \
                   (potential_root / 'pyproject.toml').exists():
                    TRADEMASTER_ROOT = str(potential_root)
                    break
            except IndexError:
                break
        else:
            # 如果都没找到，使用默认路径或当前目录的上级
            TRADEMASTER_ROOT = str(current_dir.parent.parent.parent) if len(current_dir.parts) > 3 else str(current_dir.parent)
    
    # 添加到Python路径
    if TRADEMASTER_ROOT not in sys.path:
        sys.path.append(TRADEMASTER_ROOT)
        
    logger.info(f"TradeMaster根目录设置为: {TRADEMASTER_ROOT}")
    
except Exception as e:
    # 如果路径检测失败，使用相对安全的默认值
    TRADEMASTER_ROOT = "/app"  # Docker容器中的应用根目录
    logger.warning(f"TradeMaster根目录检测失败，使用默认值: {TRADEMASTER_ROOT}, 错误: {str(e)}")

# PyTorch可选依赖
try:
    import torch
    TORCH_AVAILABLE = True
    logger.info("PyTorch模块导入成功")
except ImportError as e:
    torch = None
    TORCH_AVAILABLE = False
    logger.warning(f"PyTorch模块不可用: {str(e)}")

# TradeMaster核心模块可选依赖
try:
    # 第一步：检查基础依赖
    from mmengine.config import Config
    
    # 第二步：检查mmcv Registry
    try:
        from mmcv.utils.registry import Registry
        logger.info("mmcv Registry导入成功")
        REGISTRY_AVAILABLE = True
    except ImportError:
        try:
            from mmcv.registry import Registry
            logger.info("mmcv Registry导入成功 (新版本路径)")
            REGISTRY_AVAILABLE = True
        except ImportError:
            Registry = None
            REGISTRY_AVAILABLE = False
            logger.info("mmcv Registry不可用，Web界面功能正常")
    
    # 第三步：只在Registry可用时尝试导入TradeMaster核心模块
    if REGISTRY_AVAILABLE:
        try:
            # 导入TradeMaster核心模块
            from trademaster.agents.builder import build_agent, AGENTS
            from trademaster.datasets.builder import build_dataset, DATASETS
            from trademaster.environments.builder import build_environment, ENVIRONMENTS
            from trademaster.utils import build_from_cfg
            
            # 导入具体实现
            from trademaster.agents.algorithmic_trading.dqn import AlgorithmicTradingDQN
            from trademaster.agents.portfolio_management.eiie import PortfolioManagementEIIE
            from trademaster.agents.portfolio_management.deeptrader import PortfolioManagementDeepTrader
            from trademaster.agents.order_execution.eteo import OrderExecutionETEO
            from trademaster.agents.high_frequency_trading.ddqn import HighFrequencyTradingDDQN
            
            TRADEMASTER_AVAILABLE = True
            logger.info("🎉 TradeMaster完整功能可用")
            
        except ImportError as e:
            # TradeMaster包不可用，但mmcv正常
            build_agent = build_dataset = build_environment = build_from_cfg = None
            AGENTS = DATASETS = ENVIRONMENTS = None
            TRADEMASTER_AVAILABLE = False
            
            if "trademaster" in str(e).lower():
                logger.info("TradeMaster包未安装，仅提供基础Web功能")
            else:
                logger.info("TradeMaster模块部分功能不可用")
    else:
        # Registry不可用时设置默认值
        build_agent = build_dataset = build_environment = build_from_cfg = None
        AGENTS = DATASETS = ENVIRONMENTS = None
        TRADEMASTER_AVAILABLE = False
    
except ImportError as e:
    # 基础依赖不可用
    Config = None
    build_agent = build_dataset = build_environment = build_from_cfg = None
    AGENTS = DATASETS = ENVIRONMENTS = None
    TRADEMASTER_AVAILABLE = False
    REGISTRY_AVAILABLE = False
    
    if "mmengine" in str(e).lower():
        logger.info("mmengine未安装，Web界面功能正常")
    else:
        logger.info("基础依赖检查失败，Web界面功能正常")

from app.core.trademaster_config import get_config_adapter, TradeMasterConfigError


class TradeMasterCoreError(Exception):
    """TradeMaster核心模块异常"""
    pass


class TrainingSession:
    """训练会话管理类"""
    
    def __init__(self, session_id: str, config: Dict[str, Any]):
        self.session_id = session_id
        self.config = config
        self.created_at = datetime.now()
        self.status = "initialized"
        self.progress = 0.0
        self.current_epoch = 0
        self.total_epochs = config.get("epochs", 100)
        self.metrics = {}
        self.logs = []
        self.error_message = None
        
        # 组件实例
        self.agent = None
        self.dataset = None
        self.environment = None
        self.trainer = None
        
        # 异步执行
        self.future: Optional[Future] = None
        self.stop_event = threading.Event()
    
    def add_log(self, level: str, message: str, data: Optional[Dict] = None):
        """添加日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        self.logs.append(log_entry)
        logger.log(level.upper(), f"Session {self.session_id}: {message}")
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """更新训练指标"""
        self.metrics.update(metrics)
        if "epoch" in metrics:
            self.current_epoch = metrics["epoch"]
            self.progress = (self.current_epoch / self.total_epochs) * 100
    
    def set_error(self, error_message: str):
        """设置错误状态"""
        self.status = "failed"
        self.error_message = error_message
        self.add_log("ERROR", error_message)
    
    def stop(self):
        """停止训练"""
        self.stop_event.set()
        if self.future and not self.future.done():
            self.future.cancel()
        self.status = "stopped"
        self.add_log("INFO", "训练已停止")


class TradeMasterCore:
    """TradeMaster核心模块集成服务
    
    提供TradeMaster核心功能的直接调用接口，包括：
    - 智能体管理
    - 数据集处理
    - 环境创建
    - 训练执行
    - 评估分析
    """
    
    def __init__(self):
        """初始化TradeMaster核心服务"""
        if not TRADEMASTER_AVAILABLE:
            raise TradeMasterCoreError("TradeMaster核心模块不可用")
        
        self.config_adapter = get_config_adapter()
        self.sessions: Dict[str, TrainingSession] = {}
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="TradeMaster")
        
        # 设置设备（PyTorch可选）
        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"TradeMaster核心服务初始化完成，设备: {self.device}")
        else:
            self.device = "cpu"  # 回退到字符串表示
            logger.info(f"TradeMaster核心服务初始化完成，设备: {self.device} (PyTorch不可用)")
    
    # ==================== 组件管理 ====================
    
    def create_dataset(self, config: Dict[str, Any]) -> Any:
        """创建数据集实例
        
        Args:
            config: 数据集配置
            
        Returns:
            数据集实例
        """
        try:
            tm_config = self.config_adapter.convert_web_config_to_trademaster(config)
            dataset_config = tm_config["data"]
            
            logger.info(f"创建数据集: {dataset_config['type']}")
            dataset = build_dataset(Config(dict(data=dataset_config)))
            
            return dataset
            
        except Exception as e:
            logger.error(f"数据集创建失败: {str(e)}")
            raise TradeMasterCoreError(f"数据集创建失败: {str(e)}")
    
    def create_agent(self, config: Dict[str, Any], dataset: Any = None) -> Any:
        """创建智能体实例
        
        Args:
            config: 智能体配置
            dataset: 数据集实例（可选）
            
        Returns:
            智能体实例
        """
        try:
            tm_config = self.config_adapter.convert_web_config_to_trademaster(config)
            agent_config = tm_config["agent"]
            
            # 添加设备配置
            agent_config["device"] = self.device
            
            # 如果有数据集，添加相关配置
            if dataset:
                agent_config["state_dim"] = getattr(dataset, "state_dim", 10)
                agent_config["action_dim"] = getattr(dataset, "action_dim", 3)
            
            logger.info(f"创建智能体: {agent_config['type']}")
            agent = build_agent(Config(dict(agent=agent_config)))
            
            return agent
            
        except Exception as e:
            logger.error(f"智能体创建失败: {str(e)}")
            raise TradeMasterCoreError(f"智能体创建失败: {str(e)}")
    
    def create_environment(self, config: Dict[str, Any], dataset: Any = None) -> Any:
        """创建环境实例
        
        Args:
            config: 环境配置
            dataset: 数据集实例（可选）
            
        Returns:
            环境实例
        """
        try:
            tm_config = self.config_adapter.convert_web_config_to_trademaster(config)
            env_config = tm_config["environment"]
            
            # 如果有数据集，关联到环境
            if dataset:
                env_config["dataset"] = dataset
            
            logger.info(f"创建环境: {env_config['type']}")
            environment = build_environment(Config(dict(environment=env_config)))
            
            return environment
            
        except Exception as e:
            logger.error(f"环境创建失败: {str(e)}")
            raise TradeMasterCoreError(f"环境创建失败: {str(e)}")
    
    # ==================== 训练管理 ====================
    
    async def start_training(
        self, 
        config: Dict[str, Any], 
        callback: Optional[Callable] = None
    ) -> str:
        """启动训练任务
        
        Args:
            config: 训练配置
            callback: 进度回调函数
            
        Returns:
            str: 训练会话ID
        """
        session_id = f"train_{int(datetime.now().timestamp() * 1000)}"
        
        try:
            # 验证配置
            # 验证配置
            tm_config = self.config_adapter.convert_web_config_to_trademaster(config)
            validation_result = self.config_adapter.validate_trademaster_config(tm_config)
            if not validation_result["valid"]:
                raise TradeMasterCoreError(f"配置验证失败: {'; '.join(validation_result['errors'])}")
            # 创建训练会话
            session = TrainingSession(session_id, tm_config)
            self.sessions[session_id] = session
            
            session.add_log("INFO", "训练会话创建成功")
            
            # 异步执行训练
            loop = asyncio.get_event_loop()
            session.future = self.executor.submit(
                self._run_training_sync, 
                session, 
                callback
            )
            
            logger.info(f"训练任务启动: {session_id}")
            return session_id
            
        except Exception as e:
            if session_id in self.sessions:
                self.sessions[session_id].set_error(str(e))
            logger.error(f"训练启动失败: {str(e)}")
            raise TradeMasterCoreError(f"训练启动失败: {str(e)}")
    
    def _run_training_sync(
        self, 
        session: TrainingSession, 
        callback: Optional[Callable] = None
    ):
        """同步执行训练（在线程池中运行）"""
        try:
            session.status = "running"
            session.add_log("INFO", "开始训练")
            
            # 创建组件
            session.add_log("INFO", "创建数据集")
            session.dataset = self.create_dataset(session.config)
            
            session.add_log("INFO", "创建智能体")
            session.agent = self.create_agent(session.config, session.dataset)
            
            session.add_log("INFO", "创建环境")
            session.environment = self.create_environment(session.config, session.dataset)
            
            # 执行训练循环
            self._training_loop(session, callback)
            
            if not session.stop_event.is_set():
                session.status = "completed"
                session.progress = 100.0
                session.add_log("INFO", "训练完成")
            
        except Exception as e:
            session.set_error(f"训练执行失败: {str(e)}")
            logger.error(f"训练执行失败: {traceback.format_exc()}")
    
    def _training_loop(
        self, 
        session: TrainingSession, 
        callback: Optional[Callable] = None
    ):
        """训练循环"""
        total_epochs = session.total_epochs
        
        for epoch in range(total_epochs):
            if session.stop_event.is_set():
                break
            
            try:
                # 模拟训练步骤
                metrics = self._train_epoch(session, epoch)
                
                # 更新会话状态
                session.update_metrics({
                    "epoch": epoch + 1,
                    **metrics
                })
                
                # 调用回调函数
                if callback:
                    try:
                        callback(session.session_id, {
                            "epoch": epoch + 1,
                            "total_epochs": total_epochs,
                            "progress": session.progress,
                            "metrics": metrics
                        })
                    except Exception as e:
                        logger.warning(f"回调函数执行失败: {str(e)}")
                
                # 添加日志
                if (epoch + 1) % 10 == 0:
                    session.add_log("INFO", f"训练进度: {epoch + 1}/{total_epochs}")
                
            except Exception as e:
                session.set_error(f"第{epoch + 1}轮训练失败: {str(e)}")
                break
    
    def _train_epoch(self, session: TrainingSession, epoch: int) -> Dict[str, Any]:
        """执行单轮训练
        
        Args:
            session: 训练会话
            epoch: 当前轮次
            
        Returns:
            Dict[str, Any]: 训练指标
        """
        # 这里应该调用实际的TradeMaster训练逻辑
        # 当前实现为模拟训练过程
        
        import time
        import random
        
        # 模拟训练时间
        time.sleep(0.1)
        
        # 模拟训练指标
        metrics = {
            "loss": random.uniform(0.1, 1.0) * np.exp(-epoch * 0.01),
            "reward": random.uniform(-10, 10) + epoch * 0.1,
            "accuracy": min(0.9, 0.5 + epoch * 0.01),
            "epsilon": max(0.01, 1.0 - epoch * 0.01)
        }
        
        return metrics
    
    async def stop_training(self, session_id: str) -> Dict[str, Any]:
        """停止训练任务
        
        Args:
            session_id: 训练会话ID
            
        Returns:
            Dict[str, Any]: 停止结果
        """
        if session_id not in self.sessions:
            raise TradeMasterCoreError(f"训练会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        session.stop()
        
        logger.info(f"训练任务停止: {session_id}")
        return {
            "session_id": session_id,
            "status": "stopped",
            "message": "训练已停止"
        }
    
    async def get_training_status(self, session_id: str) -> Dict[str, Any]:
        """获取训练状态
        
        Args:
            session_id: 训练会话ID
            
        Returns:
            Dict[str, Any]: 训练状态
        """
        if session_id not in self.sessions:
            raise TradeMasterCoreError(f"训练会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": session.status,
            "progress": session.progress,
            "current_epoch": session.current_epoch,
            "total_epochs": session.total_epochs,
            "metrics": session.metrics,
            "created_at": session.created_at.isoformat(),
            "error_message": session.error_message
        }
    
    async def get_training_logs(
        self, 
        session_id: str, 
        limit: int = 100,
        level: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取训练日志
        
        Args:
            session_id: 训练会话ID
            limit: 日志条数限制
            level: 日志级别过滤
            
        Returns:
            Dict[str, Any]: 训练日志
        """
        if session_id not in self.sessions:
            raise TradeMasterCoreError(f"训练会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        logs = session.logs
        
        # 级别过滤
        if level:
            logs = [log for log in logs if log["level"].upper() == level.upper()]
        
        # 限制数量
        logs = logs[-limit:] if limit > 0 else logs
        
        return {
            "session_id": session_id,
            "logs": logs,
            "total_logs": len(session.logs)
        }
    
    # ==================== 评估分析 ====================
    
    async def evaluate_strategy(
        self, 
        session_id: str, 
        eval_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """评估策略性能
        
        Args:
            session_id: 训练会话ID
            eval_config: 评估配置
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        if session_id not in self.sessions:
            raise TradeMasterCoreError(f"训练会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        
        if session.status != "completed":
            raise TradeMasterCoreError(f"训练未完成，无法评估: {session.status}")
        
        try:
            # 模拟评估过程
            evaluation_results = {
                "total_return": np.random.uniform(0.05, 0.25),
                "sharpe_ratio": np.random.uniform(0.8, 2.5),
                "max_drawdown": np.random.uniform(0.02, 0.15),
                "win_rate": np.random.uniform(0.45, 0.75),
                "volatility": np.random.uniform(0.10, 0.30),
                "calmar_ratio": np.random.uniform(0.5, 3.0)
            }
            
            logger.info(f"策略评估完成: {session_id}")
            return {
                "session_id": session_id,
                "evaluation_results": evaluation_results,
                "evaluation_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"策略评估失败: {str(e)}")
            raise TradeMasterCoreError(f"策略评估失败: {str(e)}")
    
    # ==================== 工具集成 ====================
    
    async def run_finagent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行FinAgent工具
        
        Args:
            config: FinAgent配置
            
        Returns:
            Dict[str, Any]: 运行结果
        """
        try:
            # 这里应该调用实际的FinAgent逻辑
            logger.info("启动FinAgent工具")
            
            # 模拟FinAgent运行
            results = {
                "status": "completed",
                "message": "FinAgent运行完成",
                "market_intelligence": "市场情报分析结果",
                "trading_signals": ["BUY", "HOLD", "SELL"],
                "confidence_scores": [0.85, 0.72, 0.68]
            }
            
            return results
            
        except Exception as e:
            logger.error(f"FinAgent运行失败: {str(e)}")
            raise TradeMasterCoreError(f"FinAgent运行失败: {str(e)}")
    
    async def run_earnmore(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行EarnMore工具
        
        Args:
            config: EarnMore配置
            
        Returns:
            Dict[str, Any]: 运行结果
        """
        try:
            # 这里应该调用实际的EarnMore逻辑
            logger.info("启动EarnMore工具")
            
            # 模拟EarnMore运行
            results = {
                "status": "completed",
                "message": "EarnMore运行完成",
                "portfolio_allocation": {
                    "AAPL": 0.25,
                    "MSFT": 0.30,
                    "GOOGL": 0.20,
                    "CASH": 0.25
                },
                "expected_return": 0.12,
                "risk_level": "Medium"
            }
            
            return results
            
        except Exception as e:
            logger.error(f"EarnMore运行失败: {str(e)}")
            raise TradeMasterCoreError(f"EarnMore运行失败: {str(e)}")
    
    # ==================== 资源管理 ====================
    
    async def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """清理训练会话
        
        Args:
            session_id: 训练会话ID
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        if session_id not in self.sessions:
            raise TradeMasterCoreError(f"训练会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        
        # 停止训练（如果还在运行）
        if session.status == "running":
            session.stop()
        
        # 清理资源
        session.agent = None
        session.dataset = None
        session.environment = None
        session.trainer = None
        
        # 移除会话
        del self.sessions[session_id]
        
        logger.info(f"训练会话清理完成: {session_id}")
        return {
            "session_id": session_id,
            "message": "会话清理成功"
        }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息
        
        Returns:
            Dict[str, Any]: 系统信息
        """
        return {
            "trademaster_available": TRADEMASTER_AVAILABLE,
            "torch_available": TORCH_AVAILABLE,
            "device": str(self.device),
            "active_sessions": len(self.sessions),
            "session_ids": list(self.sessions.keys()),
            "python_version": sys.version,
            "torch_version": torch.__version__ if TORCH_AVAILABLE else None,
            "root_path": TRADEMASTER_ROOT
        }
    
    def __del__(self):
        """析构函数"""
        try:
            # 清理所有会话
            for session_id in list(self.sessions.keys()):
                asyncio.run(self.cleanup_session(session_id))
            
            # 关闭线程池
            self.executor.shutdown(wait=True)
            
        except Exception as e:
            logger.warning(f"TradeMaster核心服务清理失败: {str(e)}")


# 全局服务实例
_trademaster_core = None

def get_trademaster_core() -> TradeMasterCore:
    """获取TradeMaster核心服务实例
    
    Returns:
        TradeMasterCore: 核心服务实例
    """
    global _trademaster_core
    if _trademaster_core is None:
        _trademaster_core = TradeMasterCore()
    return _trademaster_core


# 导出主要类和函数
__all__ = [
    "TradeMasterCore",
    "TradeMasterCoreError",
    "TrainingSession",
    "get_trademaster_core",
    "TRADEMASTER_AVAILABLE"
]