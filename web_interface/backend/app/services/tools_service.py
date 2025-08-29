"""
工具集成服务

提供TradeMaster生态系统中各种专业工具的集成，包括FinAgent、EarnMore等。
支持工具链管理、插件系统和可扩展的工具集成架构。
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

from loguru import logger
from pydantic import BaseModel

from app.core.config import settings
from app.services.trademaster_integration import (
    get_integration_service,
    TradeMasterAPIException
)


class ToolServiceError(Exception):
    """工具服务异常"""
    pass


class ToolType(str, Enum):
    """工具类型枚举"""
    FINAGENT = "finagent"           # 多模态金融智能体
    EARNMORE = "earnmore"           # 强化学习投资组合管理
    DATA_PROCESSOR = "data_processor"  # 数据预处理工具
    MARKET_DYNAMICS = "market_dynamics"  # 市场动态建模
    CUSTOM = "custom"               # 自定义工具


class ToolStatus(str, Enum):
    """工具状态枚举"""
    AVAILABLE = "available"         # 可用
    BUSY = "busy"                  # 忙碌中
    ERROR = "error"                # 错误状态
    UNAVAILABLE = "unavailable"    # 不可用


class ToolExecutionMode(str, Enum):
    """工具执行模式"""
    SYNC = "sync"                  # 同步执行
    ASYNC = "async"                # 异步执行
    BACKGROUND = "background"      # 后台执行


class ToolConfig(BaseModel):
    """工具配置模型"""
    tool_type: ToolType
    execution_mode: ToolExecutionMode = ToolExecutionMode.ASYNC
    timeout: int = 3600  # 超时时间（秒）
    max_retries: int = 3  # 最大重试次数
    parameters: Dict[str, Any] = {}


class ToolsService:
    """工具集成服务
    
    提供统一的工具集成接口：
    - FinAgent多模态金融智能体
    - EarnMore强化学习投资组合管理
    - 数据预处理工具集
    - 市场动态建模工具
    - 自定义工具扩展
    """
    
    def __init__(self):
        """初始化工具服务"""
        self.trademaster_service = get_integration_service()
        
        # TradeMaster根路径
        self.trademaster_root = Path(__file__).resolve().parents[4]
        
        # 工具路径配置
        self.tool_paths = {
            ToolType.FINAGENT: self.trademaster_root / "tools" / "finagent",
            ToolType.EARNMORE: self.trademaster_root / "tools" / "earnmore",
            ToolType.DATA_PROCESSOR: self.trademaster_root / "tools" / "data_preprocessor",
            ToolType.MARKET_DYNAMICS: self.trademaster_root / "tools" / "market_dynamics_labeling"
        }
        
        # 工具状态缓存
        self.tool_status_cache = {}
        self.running_tasks = {}  # 正在运行的任务
        
        logger.info("工具服务初始化完成")
    
    # ==================== 工具状态管理 ====================
    
    async def get_tool_status(self, tool_type: ToolType) -> Dict[str, Any]:
        """获取工具状态
        
        Args:
            tool_type: 工具类型
            
        Returns:
            Dict[str, Any]: 工具状态信息
        """
        try:
            # 检查工具路径是否存在
            tool_path = self.tool_paths.get(tool_type)
            if not tool_path or not tool_path.exists():
                return {
                    "tool_type": tool_type.value,
                    "status": ToolStatus.UNAVAILABLE.value,
                    "message": "工具路径不存在",
                    "last_check": datetime.utcnow().isoformat()
                }
            
            # 检查工具是否忙碌
            if tool_type in self.running_tasks:
                active_tasks = [
                    task_id for task_id, task in self.running_tasks[tool_type].items()
                    if not task.done()
                ]
                if active_tasks:
                    return {
                        "tool_type": tool_type.value,
                        "status": ToolStatus.BUSY.value,
                        "message": f"工具正在执行 {len(active_tasks)} 个任务",
                        "active_tasks": active_tasks,
                        "last_check": datetime.utcnow().isoformat()
                    }
            
            # 工具可用
            return {
                "tool_type": tool_type.value,
                "status": ToolStatus.AVAILABLE.value,
                "message": "工具可用",
                "tool_path": str(tool_path),
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取工具状态失败: {tool_type}, {str(e)}")
            return {
                "tool_type": tool_type.value,
                "status": ToolStatus.ERROR.value,
                "message": f"状态检查失败: {str(e)}",
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def get_all_tools_status(self) -> Dict[str, Any]:
        """获取所有工具状态"""
        try:
            all_status = {}
            
            for tool_type in ToolType:
                status = await self.get_tool_status(tool_type)
                all_status[tool_type.value] = status
            
            # 统计信息
            available_count = sum(1 for status in all_status.values() 
                                if status["status"] == ToolStatus.AVAILABLE.value)
            busy_count = sum(1 for status in all_status.values() 
                           if status["status"] == ToolStatus.BUSY.value)
            
            return {
                "tools": all_status,
                "summary": {
                    "total_tools": len(ToolType),
                    "available": available_count,
                    "busy": busy_count,
                    "unavailable": len(ToolType) - available_count - busy_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取所有工具状态失败: {str(e)}")
            raise ToolServiceError(f"获取所有工具状态失败: {str(e)}")
    
    # ==================== FinAgent集成 ====================
    
    async def run_finagent(
        self,
        config: Dict[str, Any],
        execution_mode: ToolExecutionMode = ToolExecutionMode.ASYNC
    ) -> Dict[str, Any]:
        """运行FinAgent工具
        
        Args:
            config: FinAgent配置
            execution_mode: 执行模式
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 检查工具可用性
            tool_status = await self.get_tool_status(ToolType.FINAGENT)
            if tool_status["status"] != ToolStatus.AVAILABLE.value:
                raise ToolServiceError(f"FinAgent不可用: {tool_status['message']}")
            
            # 生成任务ID
            task_id = f"finagent_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # 构建配置
            finagent_config = await self._build_finagent_config(config)
            
            if execution_mode == ToolExecutionMode.SYNC:
                # 同步执行
                result = await self._run_finagent_sync(finagent_config)
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result,
                    "execution_mode": "sync"
                }
            else:
                # 异步执行
                task = asyncio.create_task(
                    self._run_finagent_async(task_id, finagent_config)
                )
                
                # 注册运行任务
                if ToolType.FINAGENT not in self.running_tasks:
                    self.running_tasks[ToolType.FINAGENT] = {}
                self.running_tasks[ToolType.FINAGENT][task_id] = task
                
                return {
                    "task_id": task_id,
                    "status": "started",
                    "message": "FinAgent任务已启动",
                    "execution_mode": "async",
                    "started_at": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"FinAgent执行失败: {str(e)}")
            raise ToolServiceError(f"FinAgent执行失败: {str(e)}")
    
    async def _build_finagent_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """构建FinAgent配置"""
        default_config = {
            "root": str(self.trademaster_root),
            "config": str(self.trademaster_root / "configs" / "finagent" / "exp" / "trading" / "AAPL.py"),
            "if_remove": False,
            "if_train": True,
            "if_valid": True
        }
        
        # 合并用户配置
        finagent_config = {**default_config, **config}
        
        # 验证配置
        required_fields = ["root", "config"]
        for field in required_fields:
            if field not in finagent_config:
                raise ToolServiceError(f"FinAgent配置缺少必需字段: {field}")
        
        return finagent_config
    
    async def _run_finagent_sync(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """同步运行FinAgent"""
        try:
            # 优先使用集成服务
            result = await self.trademaster_service.run_finagent(config)
            return result
            
        except TradeMasterAPIException:
            # 降级到直接调用
            return await self._run_finagent_direct(config)
    
    async def _run_finagent_async(self, task_id: str, config: Dict[str, Any]):
        """异步运行FinAgent"""
        try:
            logger.info(f"FinAgent异步任务开始: {task_id}")
            
            # 执行FinAgent
            result = await self._run_finagent_sync(config)
            
            # 缓存结果
            self.tool_status_cache[task_id] = {
                "status": "completed",
                "result": result,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"FinAgent异步任务完成: {task_id}")
            
        except Exception as e:
            self.tool_status_cache[task_id] = {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
            logger.error(f"FinAgent异步任务失败: {task_id}, {str(e)}")
        finally:
            # 清理运行任务记录
            if (ToolType.FINAGENT in self.running_tasks and 
                task_id in self.running_tasks[ToolType.FINAGENT]):
                del self.running_tasks[ToolType.FINAGENT][task_id]
    
    async def _run_finagent_direct(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """直接调用FinAgent脚本"""
        try:
            finagent_main = self.tool_paths[ToolType.FINAGENT] / "main.py"
            
            if not finagent_main.exists():
                raise ToolServiceError("FinAgent主脚本不存在")
            
            # 构建命令行参数
            cmd = [
                sys.executable,
                str(finagent_main),
                "--config", config.get("config", ""),
                "--root", config.get("root", str(self.trademaster_root))
            ]
            
            if config.get("if_remove"):
                cmd.append("--if_remove")
            if config.get("if_train"):
                cmd.append("--if_train")
            if config.get("if_valid"):
                cmd.append("--if_valid")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.trademaster_root)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "status": "completed",
                    "message": "FinAgent执行成功",
                    "output": stdout.decode('utf-8', errors='ignore'),
                    "execution_method": "direct"
                }
            else:
                raise ToolServiceError(f"FinAgent执行失败: {stderr.decode('utf-8', errors='ignore')}")
                
        except Exception as e:
            logger.error(f"FinAgent直接执行失败: {str(e)}")
            raise ToolServiceError(f"FinAgent直接执行失败: {str(e)}")
    
    # ==================== EarnMore集成 ====================
    
    async def run_earnmore(
        self,
        config: Dict[str, Any],
        execution_mode: ToolExecutionMode = ToolExecutionMode.ASYNC
    ) -> Dict[str, Any]:
        """运行EarnMore工具
        
        Args:
            config: EarnMore配置
            execution_mode: 执行模式
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 检查工具可用性
            tool_status = await self.get_tool_status(ToolType.EARNMORE)
            if tool_status["status"] != ToolStatus.AVAILABLE.value:
                raise ToolServiceError(f"EarnMore不可用: {tool_status['message']}")
            
            # 生成任务ID
            task_id = f"earnmore_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # 构建配置
            earnmore_config = await self._build_earnmore_config(config)
            
            if execution_mode == ToolExecutionMode.SYNC:
                # 同步执行
                result = await self._run_earnmore_sync(earnmore_config)
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result,
                    "execution_mode": "sync"
                }
            else:
                # 异步执行
                task = asyncio.create_task(
                    self._run_earnmore_async(task_id, earnmore_config)
                )
                
                # 注册运行任务
                if ToolType.EARNMORE not in self.running_tasks:
                    self.running_tasks[ToolType.EARNMORE] = {}
                self.running_tasks[ToolType.EARNMORE][task_id] = task
                
                return {
                    "task_id": task_id,
                    "status": "started",
                    "message": "EarnMore任务已启动",
                    "execution_mode": "async",
                    "started_at": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"EarnMore执行失败: {str(e)}")
            raise ToolServiceError(f"EarnMore执行失败: {str(e)}")
    
    async def _build_earnmore_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """构建EarnMore配置"""
        default_config = {
            "root": str(self.trademaster_root),
            "config": str(self.trademaster_root / "configs" / "earnmore" / "sac_portfolio_management.py"),
            "workdir": "workdir",
            "tag": f"earnmore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "if_remove": True
        }
        
        # 合并用户配置
        earnmore_config = {**default_config, **config}
        
        return earnmore_config
    
    async def _run_earnmore_sync(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """同步运行EarnMore"""
        try:
            # 优先使用集成服务
            result = await self.trademaster_service.run_earnmore(config)
            return result
            
        except TradeMasterAPIException:
            # 降级到直接调用
            return await self._run_earnmore_direct(config)
    
    async def _run_earnmore_async(self, task_id: str, config: Dict[str, Any]):
        """异步运行EarnMore"""
        try:
            logger.info(f"EarnMore异步任务开始: {task_id}")
            
            # 执行EarnMore
            result = await self._run_earnmore_sync(config)
            
            # 缓存结果
            self.tool_status_cache[task_id] = {
                "status": "completed",
                "result": result,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"EarnMore异步任务完成: {task_id}")
            
        except Exception as e:
            self.tool_status_cache[task_id] = {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
            logger.error(f"EarnMore异步任务失败: {task_id}, {str(e)}")
        finally:
            # 清理运行任务记录
            if (ToolType.EARNMORE in self.running_tasks and 
                task_id in self.running_tasks[ToolType.EARNMORE]):
                del self.running_tasks[ToolType.EARNMORE][task_id]
    
    async def _run_earnmore_direct(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """直接调用EarnMore脚本"""
        try:
            earnmore_train = self.tool_paths[ToolType.EARNMORE] / "train.py"
            
            if not earnmore_train.exists():
                raise ToolServiceError("EarnMore训练脚本不存在")
            
            # 构建命令行参数
            cmd = [
                sys.executable,
                str(earnmore_train),
                "--config", config.get("config", ""),
                "--root", config.get("root", str(self.trademaster_root)),
                "--workdir", config.get("workdir", "workdir"),
                "--tag", config.get("tag", "default")
            ]
            
            if config.get("if_remove"):
                cmd.append("--if_remove")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.trademaster_root)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "status": "completed",
                    "message": "EarnMore执行成功",
                    "output": stdout.decode('utf-8', errors='ignore'),
                    "execution_method": "direct"
                }
            else:
                raise ToolServiceError(f"EarnMore执行失败: {stderr.decode('utf-8', errors='ignore')}")
                
        except Exception as e:
            logger.error(f"EarnMore直接执行失败: {str(e)}")
            raise ToolServiceError(f"EarnMore直接执行失败: {str(e)}")
    
    # ==================== 数据预处理工具 ====================
    
    async def run_data_preprocessor(
        self,
        data_source: str,
        symbols: List[str],
        start_date: str,
        end_date: str,
        preprocessor_type: str = "yahoofinance"
    ) -> Dict[str, Any]:
        """运行数据预处理工具
        
        Args:
            data_source: 数据源
            symbols: 证券代码列表
            start_date: 开始日期
            end_date: 结束日期
            preprocessor_type: 预处理器类型
            
        Returns:
            Dict[str, Any]: 预处理结果
        """
        try:
            task_id = f"preprocessor_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # 构建预处理配置
            preprocessor_config = {
                "data_source": data_source,
                "symbols": symbols,
                "start_date": start_date,
                "end_date": end_date,
                "preprocessor_type": preprocessor_type
            }
            
            # 调用TradeMaster预处理API
            result = await self.trademaster_service.preprocess_data(preprocessor_config)
            
            logger.info(f"数据预处理任务启动成功: {task_id}")
            
            return {
                "task_id": task_id,
                "preprocessing_config": preprocessor_config,
                "result": result,
                "status": "started",
                "message": "数据预处理任务已启动"
            }
            
        except Exception as e:
            logger.error(f"数据预处理失败: {str(e)}")
            raise ToolServiceError(f"数据预处理失败: {str(e)}")
    
    # ==================== 市场动态建模工具 ====================
    
    async def run_market_dynamics_modeling(
        self,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行市场动态建模工具
        
        Args:
            config: 建模配置
            
        Returns:
            Dict[str, Any]: 建模结果
        """
        try:
            task_id = f"mdm_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # 构建建模配置
            modeling_config = {
                "task": "market_dynamics_modeling",
                "dataset": config.get("dataset", "BTC"),
                "start_date": config.get("start_date", "2020-01-01"),
                "end_date": config.get("end_date", "2021-12-31"),
                "model_type": config.get("model_type", "lstm"),
                **config
            }
            
            # 调用TradeMaster市场动态建模API
            result = await self.trademaster_service.start_market_dynamics_modeling(modeling_config)
            
            logger.info(f"市场动态建模任务启动成功: {task_id}")
            
            return {
                "task_id": task_id,
                "modeling_config": modeling_config,
                "result": result,
                "status": "started",
                "message": "市场动态建模任务已启动"
            }
            
        except Exception as e:
            logger.error(f"市场动态建模失败: {str(e)}")
            raise ToolServiceError(f"市场动态建模失败: {str(e)}")
    
    # ==================== 任务状态查询 ====================
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 任务状态
        """
        try:
            # 检查缓存的结果
            if task_id in self.tool_status_cache:
                cached_result = self.tool_status_cache[task_id]
                return {
                    "task_id": task_id,
                    **cached_result
                }
            
            # 检查正在运行的任务
            for tool_type, tasks in self.running_tasks.items():
                if task_id in tasks:
                    task = tasks[task_id]
                    if task.done():
                        try:
                            result = await task
                            return {
                                "task_id": task_id,
                                "status": "completed",
                                "result": result
                            }
                        except Exception as e:
                            return {
                                "task_id": task_id,
                                "status": "failed",
                                "error": str(e)
                            }
                    else:
                        return {
                            "task_id": task_id,
                            "status": "running",
                            "tool_type": tool_type.value,
                            "message": "任务正在运行中"
                        }
            
            # 任务不存在
            return {
                "task_id": task_id,
                "status": "not_found",
                "message": "任务不存在"
            }
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {task_id}, {str(e)}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
    
    async def list_active_tasks(self) -> Dict[str, Any]:
        """列出活跃任务"""
        try:
            active_tasks = []
            
            for tool_type, tasks in self.running_tasks.items():
                for task_id, task in tasks.items():
                    if not task.done():
                        active_tasks.append({
                            "task_id": task_id,
                            "tool_type": tool_type.value,
                            "status": "running"
                        })
            
            return {
                "active_tasks": active_tasks,
                "total_active": len(active_tasks),
                "by_tool": {
                    tool_type.value: len([t for t in tasks.items() if not t[1].done()])
                    for tool_type, tasks in self.running_tasks.items()
                }
            }
            
        except Exception as e:
            logger.error(f"列出活跃任务失败: {str(e)}")
            raise ToolServiceError(f"列出活跃任务失败: {str(e)}")
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 取消结果
        """
        try:
            # 查找并取消任务
            for tool_type, tasks in self.running_tasks.items():
                if task_id in tasks:
                    task = tasks[task_id]
                    if not task.done():
                        task.cancel()
                        
                        # 更新缓存状态
                        self.tool_status_cache[task_id] = {
                            "status": "cancelled",
                            "cancelled_at": datetime.utcnow().isoformat()
                        }
                        
                        logger.info(f"任务取消成功: {task_id}")
                        
                        return {
                            "task_id": task_id,
                            "status": "cancelled",
                            "message": "任务已取消"
                        }
                    else:
                        return {
                            "task_id": task_id,
                            "status": "completed",
                            "message": "任务已完成，无法取消"
                        }
            
            return {
                "task_id": task_id,
                "status": "not_found",
                "message": "任务不存在或已完成"
            }
            
        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, {str(e)}")
            raise ToolServiceError(f"取消任务失败: {str(e)}")
    
    # ==================== 工具配置管理 ====================
    
    async def get_tool_config_template(self, tool_type: ToolType) -> Dict[str, Any]:
        """获取工具配置模板
        
        Args:
            tool_type: 工具类型
            
        Returns:
            Dict[str, Any]: 配置模板
        """
        templates = {
            ToolType.FINAGENT: {
                "description": "多模态金融智能体配置",
                "parameters": {
                    "symbol": {
                        "type": "string",
                        "description": "交易标的",
                        "default": "AAPL",
                        "required": True
                    },
                    "start_date": {
                        "type": "string",
                        "description": "开始日期",
                        "default": "2020-01-01",
                        "format": "YYYY-MM-DD"
                    },
                    "end_date": {
                        "type": "string", 
                        "description": "结束日期",
                        "default": "2023-12-31",
                        "format": "YYYY-MM-DD"
                    },
                    "if_train": {
                        "type": "boolean",
                        "description": "是否训练",
                        "default": True
                    },
                    "if_valid": {
                        "type": "boolean",
                        "description": "是否验证",
                        "default": True
                    }
                }
            },
            ToolType.EARNMORE: {
                "description": "强化学习投资组合管理配置",
                "parameters": {
                    "dataset": {
                        "type": "string",
                        "description": "数据集名称",
                        "default": "dj30",
                        "required": True
                    },
                    "agent": {
                        "type": "string",
                        "description": "智能体类型",
                        "default": "sac",
                        "options": ["sac", "ppo", "ddpg"]
                    },
                    "num_episodes": {
                        "type": "integer",
                        "description": "训练轮次",
                        "default": 1000,
                        "min": 100,
                        "max": 10000
                    },
                    "learning_rate": {
                        "type": "float",
                        "description": "学习率",
                        "default": 0.001,
                        "min": 0.0001,
                        "max": 0.1
                    }
                }
            },
            ToolType.DATA_PROCESSOR: {
                "description": "数据预处理工具配置",
                "parameters": {
                    "data_source": {
                        "type": "string",
                        "description": "数据源",
                        "default": "yahoofinance",
                        "options": ["yahoofinance", "local", "api"]
                    },
                    "symbols": {
                        "type": "array",
                        "description": "证券代码列表",
                        "default": ["AAPL", "MSFT", "GOOGL"],
                        "required": True
                    },
                    "features": {
                        "type": "array",
                        "description": "特征列表",
                        "default": ["open", "high", "low", "close", "volume"]
                    }
                }
            }
        }
        
        template = templates.get(tool_type)
        if not template:
            raise ToolServiceError(f"不支持的工具类型: {tool_type}")
        
        return template
    
    # ==================== 工具健康检查 ====================
    
    async def health_check_all_tools(self) -> Dict[str, Any]:
        """检查所有工具健康状态"""
        try:
            health_results = {}
            
            for tool_type in ToolType:
                try:
                    tool_path = self.tool_paths.get(tool_type)
                    
                    if not tool_path or not tool_path.exists():
                        health_results[tool_type.value] = {
                            "healthy": False,
                            "message": "工具路径不存在"
                        }
                        continue
                    
                    # 检查主要文件是否存在
                    if tool_type == ToolType.FINAGENT:
                        main_file = tool_path / "main.py"
                    elif tool_type == ToolType.EARNMORE:
                        main_file = tool_path / "train.py"
                    else:
                        main_file = tool_path
                    
                    if main_file.exists():
                        health_results[tool_type.value] = {
                            "healthy": True,
                            "message": "工具可用",
                            "main_file": str(main_file)
                        }
                    else:
                        health_results[tool_type.value] = {
                            "healthy": False,
                            "message": "主文件不存在"
                        }
                        
                except Exception as e:
                    health_results[tool_type.value] = {
                        "healthy": False,
                        "message": f"健康检查失败: {str(e)}"
                    }
            
            # 计算总体健康状态
            healthy_count = sum(1 for result in health_results.values() if result["healthy"])
            total_count = len(health_results)
            
            return {
                "overall_health": "healthy" if healthy_count == total_count else "partial",
                "healthy_tools": healthy_count,
                "total_tools": total_count,
                "tools": health_results,
                "check_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"工具健康检查失败: {str(e)}")
            raise ToolServiceError(f"工具健康检查失败: {str(e)}")


# 全局服务实例
_tools_service = None

def get_tools_service() -> ToolsService:
    """获取工具服务实例
    
    Returns:
        ToolsService: 工具服务实例
    """
    global _tools_service
    if _tools_service is None:
        _tools_service = ToolsService()
    return _tools_service


# 导出主要类和函数
__all__ = [
    "ToolsService",
    "ToolServiceError",
    "ToolType",
    "ToolStatus",
    "ToolExecutionMode",
    "ToolConfig",
    "get_tools_service"
]