"""
TradeMaster系统集成服务

提供与现有TradeMaster Flask API的无缝集成，封装所有的API调用。
同时支持直接调用TradeMaster核心模块，提供更高性能的集成方案。
支持策略训练、测试、数据处理、市场动态建模等核心功能。
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

import httpx
from loguru import logger

from app.core.config import settings
from app.services.trademaster_core import (
    get_trademaster_core,
    TradeMasterCore,
    TradeMasterCoreError,
    TRADEMASTER_AVAILABLE
)


class IntegrationMode(str, Enum):
    """集成模式枚举"""
    API_ONLY = "api_only"           # 仅使用Flask API
    CORE_ONLY = "core_only"         # 仅使用核心模块
    HYBRID = "hybrid"               # 混合模式，优先核心模块
    AUTO = "auto"                   # 自动选择最佳模式


class TradeMasterAPIException(Exception):
    """TradeMaster API异常"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class TradeMasterService:
    """TradeMaster集成服务
    
    提供统一的TradeMaster服务接口，支持多种集成模式：
    - Flask API模式：使用现有的Flask API接口
    - 核心模块模式：直接调用TradeMaster核心模块
    - 混合模式：智能选择最佳集成方式
    
    实现错误处理、重试机制、响应缓存等功能。
    """
    
    def __init__(self, integration_mode: IntegrationMode = IntegrationMode.AUTO):
        """初始化TradeMaster服务
        
        Args:
            integration_mode: 集成模式
        """
        self.integration_mode = integration_mode
        
        # Flask API配置
        self.base_url = settings.TRADEMASTER_API_URL.rstrip("/")
        self.timeout = settings.TRADEMASTER_API_TIMEOUT
        self.max_retries = settings.TRADEMASTER_API_RETRY_ATTEMPTS
        self.retry_delay = settings.TRADEMASTER_API_RETRY_DELAY
        
        # 创建HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50)
        )
        
        # TradeMaster核心模块
        self.core_service = None
        if TRADEMASTER_AVAILABLE and integration_mode != IntegrationMode.API_ONLY:
            try:
                self.core_service = get_trademaster_core()
                logger.info("TradeMaster核心模块加载成功")
            except Exception as e:
                logger.warning(f"TradeMaster核心模块加载失败: {str(e)}")
                if integration_mode == IntegrationMode.CORE_ONLY:
                    raise TradeMasterAPIException(f"核心模块加载失败: {str(e)}")
        
        # 确定最终集成模式
        self._determine_integration_mode()
        
        logger.info(f"TradeMaster服务初始化完成: {self.base_url}, 集成模式: {self.integration_mode}")
    
    def _determine_integration_mode(self):
        """确定最终集成模式"""
        if self.integration_mode == IntegrationMode.AUTO:
            if self.core_service:
                self.integration_mode = IntegrationMode.HYBRID
                logger.info("自动选择混合集成模式")
            else:
                self.integration_mode = IntegrationMode.API_ONLY
                logger.info("自动选择API集成模式")
        
        if self.integration_mode == IntegrationMode.CORE_ONLY and not self.core_service:
            raise TradeMasterAPIException("核心模块不可用，无法使用CORE_ONLY模式")
    
    def _should_use_core(self, operation: str = None) -> bool:
        """判断是否应该使用核心模块
        
        Args:
            operation: 操作类型
            
        Returns:
            bool: 是否使用核心模块
        """
        if self.integration_mode == IntegrationMode.API_ONLY:
            return False
        elif self.integration_mode == IntegrationMode.CORE_ONLY:
            return True
        elif self.integration_mode == IntegrationMode.HYBRID:
            # 混合模式下，优先使用核心模块处理训练和评估任务
            core_preferred_operations = [
                "train", "evaluate", "analyze", "create_dataset",
                "create_agent", "create_environment"
            ]
            return self.core_service and (not operation or operation in core_preferred_operations)
        
        return False
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """发送HTTP请求到TradeMaster API
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            params: 查询参数
            retry_count: 重试次数
            
        Returns:
            Dict[str, Any]: API响应数据
            
        Raises:
            TradeMasterAPIException: 当API调用失败时抛出异常
        """
        url = f"{self.base_url}/api/TradeMaster/{endpoint}"
        
        # 记录请求日志
        logger.info(f"TradeMaster API请求: {method} {url}")
        if data:
            logger.debug(f"请求数据: {json.dumps(data, indent=2)}")
        
        try:
            # 发送请求
            if method.upper() == "GET":
                response = await self.client.get(url, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, params=params)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, params=params)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, params=params)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应数据
            try:
                response_data = response.json()
                logger.info(f"TradeMaster API响应成功: {response.status_code}")
                logger.debug(f"响应数据: {json.dumps(response_data, indent=2)}")
                return response_data
            except json.JSONDecodeError:
                # 如果响应不是JSON格式，返回文本内容
                return {"message": response.text, "status": "success"}
                
        except httpx.TimeoutException as e:
            error_msg = f"TradeMaster API请求超时: {url}"
            logger.error(error_msg)
            
            # 重试逻辑
            if retry_count < self.max_retries:
                logger.info(f"重试请求 ({retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(self.retry_delay)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            raise TradeMasterAPIException(error_msg, status_code=408)
            
        except httpx.HTTPStatusError as e:
            error_msg = f"TradeMaster API错误: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            
            try:
                error_data = e.response.json()
            except:
                error_data = {"error": e.response.text}
            
            raise TradeMasterAPIException(
                error_msg, 
                status_code=e.response.status_code,
                response_data=error_data
            )
            
        except httpx.RequestError as e:
            error_msg = f"TradeMaster API连接错误: {str(e)}"
            logger.error(error_msg)
            
            # 重试逻辑
            if retry_count < self.max_retries:
                logger.info(f"重试请求 ({retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(self.retry_delay)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            raise TradeMasterAPIException(error_msg)
    
    # ==================== 基础API方法 ====================
    
    async def get_parameters(self) -> Dict[str, Any]:
        """获取训练参数
        
        Returns:
            Dict[str, Any]: 可用的训练参数配置
        """
        return await self._make_request("GET", "getParameters")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 服务健康状态
        """
        try:
            response = await self._make_request("GET", "health", retry_count=0)
            return {
                "status": "healthy",
                "service": "TradeMaster",
                "timestamp": datetime.utcnow().isoformat(),
                "response": response
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "TradeMaster", 
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    # ==================== 策略训练相关 ====================
    
    async def train_strategy(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """训练策略
        
        Args:
            config: 策略训练配置
            
        Returns:
            Dict[str, Any]: 训练任务信息，包含session_id
        """
        logger.info("开始策略训练")
        
        # 验证必要的配置参数
        required_fields = ["task", "dataset", "agent"]
        for field in required_fields:
            if field not in config:
                raise TradeMasterAPIException(f"缺少必要的配置参数: {field}")
        
        # 设置默认值
        default_config = {
            "task": "algorithmic_trading",
            "dataset": "BTC",
            "agent": "dqn",
            "train_start_date": "2020-01-01",
            "train_end_date": "2021-12-31",
            "test_start_date": "2022-01-01", 
            "test_end_date": "2022-12-31",
            "initial_capital": 100000,
            "if_remove": True,
            "if_store": True
        }
        
        # 合并配置
        final_config = {**default_config, **config}
        
        # 根据集成模式选择实现方式
        if self._should_use_core("train"):
            try:
                logger.info("使用核心模块进行策略训练")
                session_id = await self.core_service.start_training(final_config)
                return {
                    "session_id": session_id,
                    "status": "started",
                    "message": "训练任务已启动（核心模块）",
                    "integration_mode": "core"
                }
            except TradeMasterCoreError as e:
                logger.warning(f"核心模块训练失败，降级到API模式: {str(e)}")
                if self.integration_mode == IntegrationMode.CORE_ONLY:
                    raise TradeMasterAPIException(f"核心模块训练失败: {str(e)}")
                # 降级到API模式
                
        # 使用Flask API模式
        logger.info("使用Flask API进行策略训练")
        result = await self._make_request("POST", "train", final_config)
        result["integration_mode"] = "api"
        return result
    
    async def get_train_status(self, session_id: str) -> Dict[str, Any]:
        """获取训练状态
        
        Args:
            session_id: 训练会话ID
            
        Returns:
            Dict[str, Any]: 训练状态信息
        """
        # 优先使用核心模块
        if self.core_service:
            try:
                return await self.core_service.get_training_status(session_id)
            except TradeMasterCoreError:
                if self.integration_mode == IntegrationMode.CORE_ONLY:
                    raise
                # 降级到API模式
        
        return await self._make_request("POST", "train_status", {"session_id": session_id})
    
    async def stop_training(self, session_id: str) -> Dict[str, Any]:
        """停止训练
        
        Args:
            session_id: 训练会话ID
            
        Returns:
            Dict[str, Any]: 停止操作结果
        """
        # 优先使用核心模块
        if self.core_service:
            try:
                return await self.core_service.stop_training(session_id)
            except TradeMasterCoreError:
                if self.integration_mode == IntegrationMode.CORE_ONLY:
                    raise
                # 降级到API模式
        
        return await self._make_request("POST", "stop_train", {"session_id": session_id})
    
    # ==================== 策略测试相关 ====================
    
    async def test_strategy(self, session_id: str, test_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """测试策略
        
        Args:
            session_id: 训练会话ID
            test_config: 测试配置参数
            
        Returns:
            Dict[str, Any]: 测试任务信息
        """
        data = {"session_id": session_id}
        if test_config:
            data.update(test_config)
        
        return await self._make_request("POST", "test", data)
    
    async def get_test_status(self, session_id: str) -> Dict[str, Any]:
        """获取测试状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 测试状态信息
        """
        return await self._make_request("POST", "test_status", {"session_id": session_id})
    
    # ==================== 数据管理相关 ====================
    
    async def upload_data(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """上传数据文件
        
        Args:
            file_data: 文件数据和元信息
            
        Returns:
            Dict[str, Any]: 上传结果
        """
        logger.info("开始上传数据文件")
        
        required_fields = ["filename", "data_type"]
        for field in required_fields:
            if field not in file_data:
                raise TradeMasterAPIException(f"缺少必要的文件信息: {field}")
        
        return await self._make_request("POST", "upload_csv", file_data)
    
    async def get_available_datasets(self) -> Dict[str, Any]:
        """获取可用数据集列表
        
        Returns:
            Dict[str, Any]: 数据集列表
        """
        return await self._make_request("GET", "datasets")
    
    async def preprocess_data(self, preprocess_config: Dict[str, Any]) -> Dict[str, Any]:
        """数据预处理
        
        Args:
            preprocess_config: 预处理配置
            
        Returns:
            Dict[str, Any]: 预处理任务信息
        """
        return await self._make_request("POST", "preprocess", preprocess_config)
    
    # ==================== 市场动态建模相关 ====================
    
    async def start_market_dynamics_modeling(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """启动市场动态建模
        
        Args:
            config: 建模配置
            
        Returns:
            Dict[str, Any]: 建模任务信息
        """
        logger.info("开始市场动态建模")
        
        # 设置默认配置
        default_config = {
            "task": "market_dynamics_modeling",
            "dataset": "BTC",
            "start_date": "2020-01-01",
            "end_date": "2021-12-31",
            "model_type": "lstm"
        }
        
        final_config = {**default_config, **config}
        
        return await self._make_request("POST", "start_market_dynamics_labeling", final_config)
    
    async def get_mdm_status(self, session_id: str) -> Dict[str, Any]:
        """获取市场动态建模状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 建模状态信息
        """
        return await self._make_request("POST", "MDM_status", {"session_id": session_id})
    
    # ==================== 结果分析相关 ====================
    
    async def get_training_results(self, session_id: str) -> Dict[str, Any]:
        """获取训练结果
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 训练结果数据
        """
        return await self._make_request("POST", "get_results", {"session_id": session_id})
    
    async def get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """获取性能指标
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 性能指标数据
        """
        return await self._make_request("POST", "get_metrics", {"session_id": session_id})
    
    async def generate_report(self, session_id: str, report_type: str = "full") -> Dict[str, Any]:
        """生成分析报告
        
        Args:
            session_id: 会话ID
            report_type: 报告类型
            
        Returns:
            Dict[str, Any]: 报告数据
        """
        return await self._make_request(
            "POST", 
            "generate_report", 
            {"session_id": session_id, "report_type": report_type}
        )
    
    # ==================== 高级功能 ====================
    
    async def batch_train_strategies(self, strategies_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量训练策略
        
        Args:
            strategies_config: 策略配置列表
            
        Returns:
            Dict[str, Any]: 批量训练任务信息
        """
        logger.info(f"开始批量训练 {len(strategies_config)} 个策略")
        
        results = []
        for i, config in enumerate(strategies_config):
            try:
                result = await self.train_strategy(config)
                results.append({
                    "index": i,
                    "status": "success",
                    "result": result
                })
                logger.info(f"策略 {i+1} 训练启动成功")
            except Exception as e:
                results.append({
                    "index": i,
                    "status": "failed",
                    "error": str(e)
                })
                logger.error(f"策略 {i+1} 训练启动失败: {str(e)}")
        
        return {
            "batch_id": f"batch_{int(time.time())}",
            "total_strategies": len(strategies_config),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def compare_strategies(self, session_ids: List[str]) -> Dict[str, Any]:
        """比较多个策略的性能
        
        Args:
            session_ids: 会话ID列表
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        logger.info(f"开始比较 {len(session_ids)} 个策略")
        
        strategy_results = []
        for session_id in session_ids:
            try:
                # 获取每个策略的性能指标
                metrics = await self.get_performance_metrics(session_id)
                strategy_results.append({
                    "session_id": session_id,
                    "status": "success",
                    "metrics": metrics
                })
            except Exception as e:
                strategy_results.append({
                    "session_id": session_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "comparison_id": f"comp_{int(time.time())}",
            "strategies": strategy_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_session_logs(self, session_id: str, limit: int = 100) -> Dict[str, Any]:
        """获取会话日志
        
        Args:
            session_id: 会话ID
            limit: 日志条数限制
            
        Returns:
            Dict[str, Any]: 日志数据
        """
        return await self._make_request(
            "POST", 
            "get_logs", 
            {"session_id": session_id, "limit": limit}
        )
    
    # ==================== 资源管理 ====================
    
    async def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """清理会话资源
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        return await self._make_request("POST", "cleanup", {"session_id": session_id})
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态
        
        Returns:
            Dict[str, Any]: 系统状态信息
        """
        # 合并核心模块和API状态
        api_status = None
        core_status = None
        
        try:
            api_status = await self._make_request("GET", "system_status")
        except Exception as e:
            api_status = {"error": str(e), "available": False}
        
        if self.core_service:
            try:
                core_status = await self.core_service.get_system_info()
                core_status["available"] = True
            except Exception as e:
                core_status = {"error": str(e), "available": False}
        
        return {
            "integration_mode": self.integration_mode.value,
            "api_status": api_status,
            "core_status": core_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ==================== 核心模块专用方法 ====================
    
    async def create_dataset(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建数据集（核心模块专用）
        
        Args:
            config: 数据集配置
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        if not self.core_service:
            raise TradeMasterAPIException("核心模块不可用")
        
        try:
            dataset = self.core_service.create_dataset(config)
            return {
                "status": "success",
                "message": "数据集创建成功",
                "dataset_info": {
                    "type": type(dataset).__name__,
                    "config": config
                }
            }
        except Exception as e:
            raise TradeMasterAPIException(f"数据集创建失败: {str(e)}")
    
    async def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建智能体（核心模块专用）
        
        Args:
            config: 智能体配置
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        if not self.core_service:
            raise TradeMasterAPIException("核心模块不可用")
        
        try:
            agent = self.core_service.create_agent(config)
            return {
                "status": "success",
                "message": "智能体创建成功",
                "agent_info": {
                    "type": type(agent).__name__,
                    "config": config
                }
            }
        except Exception as e:
            raise TradeMasterAPIException(f"智能体创建失败: {str(e)}")
    
    async def create_environment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建环境（核心模块专用）
        
        Args:
            config: 环境配置
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        if not self.core_service:
            raise TradeMasterAPIException("核心模块不可用")
        
        try:
            environment = self.core_service.create_environment(config)
            return {
                "status": "success",
                "message": "环境创建成功",
                "environment_info": {
                    "type": type(environment).__name__,
                    "config": config
                }
            }
        except Exception as e:
            raise TradeMasterAPIException(f"环境创建失败: {str(e)}")
    
    async def evaluate_strategy(self, session_id: str, eval_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """评估策略性能
        
        Args:
            session_id: 训练会话ID
            eval_config: 评估配置
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        # 优先使用核心模块
        if self.core_service:
            try:
                return await self.core_service.evaluate_strategy(session_id, eval_config)
            except TradeMasterCoreError:
                if self.integration_mode == IntegrationMode.CORE_ONLY:
                    raise
                # 降级到API模式
        
        # API模式的评估实现
        data = {"session_id": session_id}
        if eval_config:
            data.update(eval_config)
        
        return await self._make_request("POST", "evaluate", data)
    
    async def run_finagent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行FinAgent工具
        
        Args:
            config: FinAgent配置
            
        Returns:
            Dict[str, Any]: 运行结果
        """
        # 优先使用核心模块
        if self.core_service:
            try:
                return await self.core_service.run_finagent(config)
            except TradeMasterCoreError:
                if self.integration_mode == IntegrationMode.CORE_ONLY:
                    raise
                # 降级到API模式
        
        # API模式的FinAgent实现
        return await self._make_request("POST", "finagent", config)
    
    async def run_earnmore(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行EarnMore工具
        
        Args:
            config: EarnMore配置
            
        Returns:
            Dict[str, Any]: 运行结果
        """
        # 优先使用核心模块
        if self.core_service:
            try:
                return await self.core_service.run_earnmore(config)
            except TradeMasterCoreError:
                if self.integration_mode == IntegrationMode.CORE_ONLY:
                    raise
                # 降级到API模式
        
        # API模式的EarnMore实现
        return await self._make_request("POST", "earnmore", config)
    
    async def get_training_logs(self, session_id: str, limit: int = 100, level: Optional[str] = None) -> Dict[str, Any]:
        """获取训练日志
        
        Args:
            session_id: 训练会话ID
            limit: 日志条数限制
            level: 日志级别过滤
            
        Returns:
            Dict[str, Any]: 训练日志
        """
        # 优先使用核心模块
        if self.core_service:
            try:
                return await self.core_service.get_training_logs(session_id, limit, level)
            except TradeMasterCoreError:
                if self.integration_mode == IntegrationMode.CORE_ONLY:
                    raise
                # 降级到API模式
        
        # API模式日志获取
        return await self.get_session_logs(session_id, limit)
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
        logger.info("TradeMaster服务连接已关闭")
    
    def __del__(self):
        """析构函数"""
        try:
            asyncio.get_event_loop().run_until_complete(self.close())
        except:
            pass


# 全局服务实例（单例模式）
_trademaster_service = None

def get_trademaster_service() -> TradeMasterService:
    """获取TradeMaster服务实例
    
    Returns:
        TradeMasterService: 服务实例
    """
    global _trademaster_service
    if _trademaster_service is None:
        _trademaster_service = TradeMasterService()
    return _trademaster_service


# 导出主要类和函数
__all__ = [
    "TradeMasterService",
    "TradeMasterAPIException",
    "IntegrationMode",
    "get_trademaster_service"
]