"""
性能监控系统

提供全面的系统性能监控，包括API响应时间、资源使用情况、
数据库性能、缓存命中率等关键指标的收集、分析和告警。
"""

import time
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings


class MetricType(str, Enum):
    """指标类型枚举"""
    COUNTER = "counter"           # 计数器
    GAUGE = "gauge"              # 仪表盘
    HISTOGRAM = "histogram"       # 直方图
    SUMMARY = "summary"          # 摘要


class AlertLevel(str, Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class Metric(BaseModel):
    """指标模型"""
    name: str = Field(..., description="指标名称")
    metric_type: MetricType = Field(..., description="指标类型")
    description: str = Field(..., description="指标描述")
    unit: str = Field("", description="单位")
    labels: Dict[str, str] = Field({}, description="标签")
    points: List[MetricPoint] = Field([], description="数据点")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class SystemMetrics(BaseModel):
    """系统指标模型"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")
    
    # CPU指标
    cpu_usage: float = Field(0.0, description="CPU使用率")
    cpu_count: int = Field(0, description="CPU核心数")
    load_average: List[float] = Field([], description="负载平均值")
    
    # 内存指标
    memory_total: int = Field(0, description="总内存(MB)")
    memory_used: int = Field(0, description="已用内存(MB)")
    memory_available: int = Field(0, description="可用内存(MB)")
    memory_usage_percent: float = Field(0.0, description="内存使用率")
    
    # 磁盘指标
    disk_total: int = Field(0, description="总磁盘空间(MB)")
    disk_used: int = Field(0, description="已用磁盘空间(MB)")
    disk_free: int = Field(0, description="可用磁盘空间(MB)")
    disk_usage_percent: float = Field(0.0, description="磁盘使用率")
    
    # 网络指标
    network_bytes_sent: int = Field(0, description="网络发送字节数")
    network_bytes_recv: int = Field(0, description="网络接收字节数")
    network_packets_sent: int = Field(0, description="网络发送包数")
    network_packets_recv: int = Field(0, description="网络接收包数")
    
    # 进程指标
    process_count: int = Field(0, description="进程数量")
    thread_count: int = Field(0, description="线程数量")


class APIMetrics(BaseModel):
    """API指标模型"""
    endpoint: str = Field(..., description="API端点")
    method: str = Field(..., description="HTTP方法")
    
    # 响应时间指标
    response_time_avg: float = Field(0.0, description="平均响应时间(ms)")
    response_time_p50: float = Field(0.0, description="50%分位响应时间(ms)")
    response_time_p95: float = Field(0.0, description="95%分位响应时间(ms)")
    response_time_p99: float = Field(0.0, description="99%分位响应时间(ms)")
    
    # 请求统计
    request_count: int = Field(0, description="请求总数")
    request_rate: float = Field(0.0, description="请求速率(req/s)")
    
    # 状态码统计
    status_2xx: int = Field(0, description="2xx状态码数量")
    status_4xx: int = Field(0, description="4xx状态码数量")
    status_5xx: int = Field(0, description="5xx状态码数量")
    
    # 错误率
    error_rate: float = Field(0.0, description="错误率")
    
    # 时间范围
    time_window: str = Field("1h", description="统计时间窗口")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="最后更新时间")


class Alert(BaseModel):
    """告警模型"""
    alert_id: str = Field(..., description="告警ID")
    alert_name: str = Field(..., description="告警名称")
    alert_level: AlertLevel = Field(..., description="告警级别")
    metric_name: str = Field(..., description="指标名称")
    threshold: float = Field(..., description="阈值")
    current_value: float = Field(..., description="当前值")
    message: str = Field(..., description="告警消息")
    triggered_at: datetime = Field(default_factory=datetime.utcnow, description="触发时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    is_active: bool = Field(True, description="是否活跃")
    metadata: Dict[str, Any] = Field({}, description="元数据")


class PerformanceMonitor:
    """性能监控器
    
    负责收集、存储和分析系统性能指标
    """
    
    def __init__(self):
        """初始化性能监控器"""
        self.metrics_storage: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.api_metrics: Dict[str, List[float]] = defaultdict(list)
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.active_alerts: Dict[str, Alert] = {}
        
        # 告警规则配置
        self.alert_rules = {
            "cpu_usage": {"threshold": 80.0, "level": AlertLevel.WARNING},
            "memory_usage": {"threshold": 85.0, "level": AlertLevel.WARNING},
            "disk_usage": {"threshold": 90.0, "level": AlertLevel.CRITICAL},
            "response_time_p95": {"threshold": 5000.0, "level": AlertLevel.WARNING},  # 5s
            "error_rate": {"threshold": 0.05, "level": AlertLevel.WARNING}  # 5%
        }
        
        # 启动后台监控任务
        self.monitoring_enabled = True
        self._monitoring_task = None
        
        logger.info("性能监控器初始化完成")
    
    async def start_monitoring(self):
        """启动监控"""
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("性能监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        self.monitoring_enabled = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("性能监控已停止")
    
    # ==================== 系统指标收集 ====================
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标
        
        Returns:
            SystemMetrics: 系统指标
        """
        try:
            # CPU指标
            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
            
            # 内存指标
            memory = psutil.virtual_memory()
            memory_total = round(memory.total / 1024 / 1024)  # MB
            memory_used = round(memory.used / 1024 / 1024)
            memory_available = round(memory.available / 1024 / 1024)
            memory_usage_percent = memory.percent
            
            # 磁盘指标
            disk = psutil.disk_usage('/')
            disk_total = round(disk.total / 1024 / 1024)  # MB
            disk_used = round(disk.used / 1024 / 1024)
            disk_free = round(disk.free / 1024 / 1024)
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # 网络指标
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            network_packets_sent = network.packets_sent
            network_packets_recv = network.packets_recv
            
            # 进程指标
            process_count = len(psutil.pids())
            thread_count = sum(p.num_threads() for p in psutil.process_iter(['num_threads']) 
                             if p.info['num_threads'])
            
            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                cpu_count=cpu_count,
                load_average=load_avg,
                memory_total=memory_total,
                memory_used=memory_used,
                memory_available=memory_available,
                memory_usage_percent=memory_usage_percent,
                disk_total=disk_total,
                disk_used=disk_used,
                disk_free=disk_free,
                disk_usage_percent=disk_usage_percent,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                network_packets_sent=network_packets_sent,
                network_packets_recv=network_packets_recv,
                process_count=process_count,
                thread_count=thread_count
            )
            
            # 存储历史数据
            self.system_metrics_history.append(metrics)
            
            # 检查告警条件
            await self._check_system_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {str(e)}")
            return SystemMetrics()
    
    # ==================== API指标收集 ====================
    
    async def record_api_request(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        request_size: int = 0,
        response_size: int = 0
    ):
        """记录API请求指标
        
        Args:
            endpoint: API端点
            method: HTTP方法
            response_time: 响应时间(ms)
            status_code: HTTP状态码
            request_size: 请求大小(bytes)
            response_size: 响应大小(bytes)
        """
        try:
            key = f"{method}:{endpoint}"
            
            # 记录响应时间
            self.api_metrics[f"{key}:response_time"].append(response_time)
            
            # 记录状态码
            if 200 <= status_code < 300:
                self.api_metrics[f"{key}:status_2xx"].append(1)
            elif 400 <= status_code < 500:
                self.api_metrics[f"{key}:status_4xx"].append(1)
            elif 500 <= status_code < 600:
                self.api_metrics[f"{key}:status_5xx"].append(1)
            
            # 记录请求大小
            if request_size > 0:
                self.api_metrics[f"{key}:request_size"].append(request_size)
            
            # 记录响应大小
            if response_size > 0:
                self.api_metrics[f"{key}:response_size"].append(response_size)
            
            # 记录时间戳用于计算请求速率
            self.api_metrics[f"{key}:timestamps"].append(time.time())
            
            # 限制数据点数量
            max_points = 1000
            for metric_key in self.api_metrics:
                if len(self.api_metrics[metric_key]) > max_points:
                    self.api_metrics[metric_key] = self.api_metrics[metric_key][-max_points:]
            
        except Exception as e:
            logger.error(f"记录API请求指标失败: {str(e)}")
    
    async def get_api_metrics(
        self,
        endpoint: Optional[str] = None,
        time_window: str = "1h"
    ) -> List[APIMetrics]:
        """获取API指标
        
        Args:
            endpoint: 指定端点（可选）
            time_window: 时间窗口
            
        Returns:
            List[APIMetrics]: API指标列表
        """
        try:
            metrics_list = []
            time_delta = self._parse_time_window(time_window)
            cutoff_time = time.time() - time_delta.total_seconds()
            
            # 获取所有端点
            endpoints = set()
            for key in self.api_metrics.keys():
                if ":response_time" in key:
                    endpoint_key = key.replace(":response_time", "")
                    endpoints.add(endpoint_key)
            
            # 筛选指定端点
            if endpoint:
                endpoints = {ep for ep in endpoints if endpoint in ep}
            
            for endpoint_key in endpoints:
                method, ep = endpoint_key.split(":", 1)
                
                # 获取时间窗口内的数据
                timestamps = self.api_metrics.get(f"{endpoint_key}:timestamps", [])
                recent_indices = [i for i, ts in enumerate(timestamps) if ts >= cutoff_time]
                
                if not recent_indices:
                    continue
                
                # 响应时间指标
                response_times = self.api_metrics.get(f"{endpoint_key}:response_time", [])
                recent_response_times = [response_times[i] for i in recent_indices if i < len(response_times)]
                
                if recent_response_times:
                    response_times_sorted = sorted(recent_response_times)
                    n = len(response_times_sorted)
                    
                    response_time_avg = sum(recent_response_times) / n
                    response_time_p50 = response_times_sorted[int(n * 0.5)]
                    response_time_p95 = response_times_sorted[int(n * 0.95)]
                    response_time_p99 = response_times_sorted[int(n * 0.99)]
                else:
                    response_time_avg = response_time_p50 = response_time_p95 = response_time_p99 = 0.0
                
                # 请求统计
                request_count = len(recent_indices)
                request_rate = request_count / time_delta.total_seconds() if time_delta.total_seconds() > 0 else 0
                
                # 状态码统计
                status_2xx = len([i for i in recent_indices 
                                if i < len(self.api_metrics.get(f"{endpoint_key}:status_2xx", []))])
                status_4xx = len([i for i in recent_indices 
                                if i < len(self.api_metrics.get(f"{endpoint_key}:status_4xx", []))])
                status_5xx = len([i for i in recent_indices 
                                if i < len(self.api_metrics.get(f"{endpoint_key}:status_5xx", []))])
                
                # 错误率
                error_count = status_4xx + status_5xx
                error_rate = error_count / request_count if request_count > 0 else 0.0
                
                api_metrics = APIMetrics(
                    endpoint=ep,
                    method=method,
                    response_time_avg=response_time_avg,
                    response_time_p50=response_time_p50,
                    response_time_p95=response_time_p95,
                    response_time_p99=response_time_p99,
                    request_count=request_count,
                    request_rate=request_rate,
                    status_2xx=status_2xx,
                    status_4xx=status_4xx,
                    status_5xx=status_5xx,
                    error_rate=error_rate,
                    time_window=time_window
                )
                
                metrics_list.append(api_metrics)
                
                # 检查API告警条件
现在创建性能监控系统：

<write_to_file>
<path>web_interface/backend/app/core/monitoring.py</path>
<content>
"""
性能监控和指标收集系统

提供API性能监控、系统资源监控、业务指标收集和实时监控面板。
集成Prometheus指标格式，支持自定义监控规则和告警。
"""

import time
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass, asdict
import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings


class MetricType(str, Enum):
    """指标类型枚举"""
    COUNTER = "counter"           # 计数器（只增不减）
    GAUGE = "gauge"              # 仪表盘（可增可减）
    HISTOGRAM = "histogram"       # 直方图（分布统计）
    SUMMARY = "summary"          # 摘要（分位数统计）


class MonitoringLevel(str, Enum):
    """监控级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: float
    value: float
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class Metric(BaseModel):
    """指标模型"""
    name: str = Field(..., description="指标名称")
    metric_type: MetricType = Field(..., description="指标类型")
    description: str = Field("", description="指标描述")
    unit: str = Field("", description="单位")
    labels: Dict[str, str] = Field({}, description="标签")
    
    # 数据存储
    data_points: List[MetricPoint] = Field([], description="数据点")
    max_points: int = Field(1000, description="最大数据点数")
    
    # 统计信息
    current_value: float = Field(0.0, description="当前值")
    min_value: float = Field(0.0, description="最小值")
    max_value: float = Field(0.0, description="最大值")
    avg_value: float = Field(0.0, description="平均值")
    total_value: float = Field(0.0, description="总值")
    sample_count: int = Field(0, description="样本数")
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_point(self, value: float, labels: Optional[Dict[str, str]] = None, timestamp: Optional[float] = None):
        """添加数据点"""
        if timestamp is None:
            timestamp = time.time()
        
        point = MetricPoint(
            timestamp=timestamp,
            value=value,
            labels=labels or {}
        )
        
        self.data_points.append(point)
        
        # 限制数据点数量
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        
        # 更新统计信息
        self._update_statistics()
    
    def _update_statistics(self):
        """更新统计信息"""
        if not self.data_points:
            return
        
        values = [p.value for p in self.data_points]
        
        self.current_value = values[-1]
        self.min_value = min(values)
        self.max_value = max(values)
        self.avg_value = sum(values) / len(values)
        self.sample_count = len(values)
        
        if self.metric_type == MetricType.COUNTER:
            self.total_value = self.current_value
        else:
            self.total_value = sum(values)


class SystemMetrics(BaseModel):
    """系统指标模型"""
    # CPU指标
    cpu_usage_percent: float = Field(0.0, description="CPU使用率")
    cpu_cores: int = Field(0, description="CPU核心数")
    load_average: List[float] = Field([], description="负载平均值")
    
    # 内存指标
    memory_total: int = Field(0, description="总内存")
    memory_used: int = Field(0, description="已用内存")
    memory_percent: float = Field(0.0, description="内存使用率")
    
    # 磁盘指标
    disk_total: int = Field(0, description="总磁盘空间")
    disk_used: int = Field(0, description="已用磁盘空间")
    disk_percent: float = Field(0.0, description="磁盘使用率")
    
    # 网络指标
    network_bytes_sent: int = Field(0, description="网络发送字节数")
    network_bytes_recv: int = Field(0, description="网络接收字节数")
    
    # 进程指标
    process_count: int = Field(0, description="进程数")
    thread_count: int = Field(0, description="线程数")
    
    # 时间戳
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="采集时间")


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    # 请求指标
    request_count: int = Field(0, description="请求总数")
    request_rate: float = Field(0.0, description="请求速率（RPS）")
    active_requests: int = Field(0, description="活跃请求数")
    
    # 响应时间指标
    avg_response_time: float = Field(0.0, description="平均响应时间")
    p50_response_time: float = Field(0.0, description="50%分位响应时间")
    p90_response_time: float = Field(0.0, description="90%分位响应时间")
    p95_response_time: float = Field(0.0, description="95%分位响应时间")
    p99_response_time: float = Field(0.0, description="99%分位响应时间")
    
    # 状态码统计
    status_2xx: int = Field(0, description="2xx状态码数量")
    status_3xx: int = Field(0, description="3xx状态码数量")
    status_4xx: int = Field(0, description="4xx状态码数量")
    status_5xx: int = Field(0, description="5xx状态码数量")
    
    # 错误率
    error_rate: float = Field(0.0, description="错误率")
    
    # 时间戳
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="统计时间")


class BusinessMetrics(BaseModel):
    """业务指标模型"""
    # 策略相关指标
    total_strategies: int = Field(0, description="策略总数")
    active_strategies: int = Field(0, description="活跃策略数")
    running_trainings: int = Field(0, description="运行中的训练任务")
    completed_trainings: int = Field(0, description="已完成的训练任务")
    
    # 数据相关指标
    total_datasets: int = Field(0, description="数据集总数")
    data_upload_count: int = Field(0, description="数据上传次数")
    data_processing_jobs: int = Field(0, description="数据处理任务数")
    
    # 分析相关指标
    backtest_count: int = Field(0, description="回测次数")
    analysis_jobs: int = Field(0, description="分析任务数")
    
    # 用户相关指标
    active_users: int = Field(0, description="活跃用户数")
    user_sessions: int = Field(0, description="用户会话数")
    
    # 时间戳
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="统计时间")


class MonitoringService:
    """监控服务
    
    提供全方位的系统监控，包括：
    - 系统资源监控
    - API性能监控  
    - 业务指标收集
    - 自定义指标管理
    - 实时告警
    """
    
    def __init__(self):
        """初始化监控服务"""
        # 指标存储
        self.metrics: Dict[str, Metric] = {}
        self.system_metrics_history = deque(maxlen=1440)  # 24小时数据
        self.performance_metrics_history = deque(maxlen=1440)
        self.business_metrics_history = deque(maxlen=1440)
        
        # 监控配置
        self.monitoring_enabled = True
        self.collection_interval = 60  # 秒
        self.retention_days = 7
        
        # 告警配置
        self.alert_rules = []
        self.alert_callbacks: List[Callable] = []
        
        # 性能追踪
        self.request_times = deque(maxlen=10000)
        self.request_counts = defaultdict(int)
        self.status_codes = defaultdict(int)
        self.active_requests = 0
        
        # 初始化内置指标
        self._initialize_builtin_metrics()
        
        # 启动监控任务
        self._start_monitoring_tasks()
        
        logger.info("监控服务初始化完成")
    
    # ==================== 指标管理 ====================
    
    def create_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str = "",
        unit: str = "",
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """创建自定义指标
        
        Args:
            name: 指标名称
            metric_type: 指标类型
            description: 指标描述
            unit: 单位
            labels: 标签
            
        Returns:
            Metric: 指标对象
        """
        if name in self.metrics:
            logger.warning(f"指标已存在，将被覆盖: {name}")
        
        metric = Metric(
            name=name,
            metric_type=metric_type,
            description=description,
            unit=unit,
            labels=labels or {}
        )
        
        self.metrics[name] = metric
        logger.info(f"创建指标: {name} ({metric_type.value})")
        
        return metric
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """递增计数器指标"""
        metric = self.metrics.get(name)
        if not metric:
            metric = self.create_metric(name, MetricType.COUNTER)
        
        if metric.metric_type != MetricType.COUNTER:
            logger.warning(f"指标类型不匹配: {name} 不是计数器类型")
            return
        
        new_value = metric.current_value + value
        metric.add_point(new_value, labels)
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """设置仪表盘指标值"""
        metric = self.metrics.get(name)
        if not metric:
            metric = self.create_metric(name, MetricType.GAUGE)
        
        if metric.metric_type != MetricType.GAUGE:
            logger.warning(f"指标类型不匹配: {name} 不是仪表盘类型")
            return
        
        metric.add_point(value, labels)
    
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """观察直方图指标"""
        metric = self.metrics.get(name)
        if not metric:
            metric = self.create_metric(name, MetricType.HISTOGRAM)
        
        if metric.metric_type != MetricType.HISTOGRAM:
            logger.warning(f"指标类型不匹配: {name} 不是直方图类型")
            return
        
        metric.add_point(value, labels)
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """获取指标"""
        return self.metrics.get(name)
    
    def list_metrics(self) -> List[str]:
        """列出所有指标名称"""
        return list(self.metrics.keys())
    
    # ==================== 系统监控 ====================
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_cores = psutil.cpu_count()
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                # Windows系统不支持getloadavg
                load_avg = [0.0, 0.0, 0.0]
            
            # 内存指标
            memory = psutil.virtual_memory()
            
            # 磁盘指标
            disk = psutil.disk_usage('/')
            
            # 网络指标
            network = psutil.net_io_counters()
            
            # 进程指标
            process_count = len(psutil.pids())
            thread_count = sum(p.num_threads() for p in psutil.process_iter(['num_threads']) if p.info['num_threads'])
            
            metrics = SystemMetrics(
                cpu_usage_percent=cpu_percent,
                cpu_cores=cpu_cores,
                load_average=load_avg,
                memory_total=memory.total,
                memory_used=memory.used,
                memory_percent=memory.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_percent=(disk.used / disk.total) * 100,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                process_count=process_count,
                thread_count=thread_count
            )
            
            # 存储历史数据
            self.system_metrics_history.append(metrics)
            
            # 更新内置指标
            self.set_gauge("system_cpu_usage_percent", cpu_percent)
            self.set_gauge("system_memory_usage_percent", memory.percent)
            self.set_gauge("system_disk_usage_percent", metrics.disk_percent)
            self.set_gauge("system_active_processes", process_count)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {str(e)}")
            return SystemMetrics()
    
    async def collect_performance_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        try:
            current_time = time.time()
            one_minute_ago = current_time - 60
            
            # 过滤最近一分钟的请求
            recent_requests = [
                rt for rt in self.request_times 
                if rt['timestamp'] > one_minute_ago
            ]
            
            if not recent_requests:
                return PerformanceMetrics()
            
            # 计算响应时间统计
            response_times = [rt['duration'] for rt in recent_requests]
            response_times.sort()
            
            count = len(response_times)
            avg_response_time = sum(response_times) / count
            p50_response_time = response_times[int(count * 0.5)]
            p90_response_time = response_times[int(count * 0.9)]
            p95_response_time = response_times[int(count * 0.95)]
            p99_response_time = response_times[int(count * 0.99)]
            
            # 统计状态码
            status_2xx = sum(1 for rt in recent_requests if 200 <= rt['status_code'] < 300)
            status_3xx = sum(1 for rt in recent_requests if 300 <= rt['status_code'] < 400)
            status_4xx = sum(1 for rt in recent_requests if 400 <= rt['status_code'] < 500)
            status_5xx = sum(1 for rt in recent_requests if 500 <= rt['status_code'] < 600)
            
            # 计算错误率
            error_requests = status_4xx + status_5xx
            error_rate = (error_requests / count) * 100 if count > 0 else 0
            
            metrics = PerformanceMetrics(
                request_count=count,
                request_rate=count / 60.0,  # RPS
                active_requests=self.active_requests,
                avg_response_time=avg_response_time,
                p50_response_time=p50_response_time,
                p90_response_time=p90_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                status_2xx=status_2xx,
                status_3xx=status_3xx,
                status_4xx=status_4xx,
                status_5xx=status_5xx,
                error_rate=error_rate
            )
            
            # 存储历史数据
            self.performance_metrics_history.append(metrics)
            
            # 更新内置指标
            self.set_gauge("http_requests_per_second", metrics.request_rate)
            self.set_gauge("http_response_time_avg", avg_response_time)
            self.set_gauge("http_error_rate", error_rate)
            self.set_gauge("http_active_requests", self.active_requests)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集性能指标失败: {str(e)}")
            return PerformanceMetrics()
    
    async def collect_business_metrics(self) -> BusinessMetrics:
        """收集业务指标"""
        try:
            # 这里需要从数据库或缓存中获取业务数据
            # 暂时返回模拟数据
            metrics = BusinessMetrics(
                total_strategies=100,
                active_strategies=25,
                running_trainings=5,
                completed_trainings=150,
                total_datasets=80,
                data_upload_count=200,
                data_processing_jobs=15,
                backtest_count=300,
                analysis_jobs=10,
                active_users=20,
                user_sessions=35
            )
            
            # 存储历史数据
            self.business_metrics_history.append(metrics)
            
            # 更新内置指标
            self.set_gauge("business_total_strategies", metrics.total_strategies)
            self.set_gauge("business_active_strategies", metrics.active_strategies)
            self.set_gauge("business_running_trainings", metrics.running_trainings)
            self.set_gauge("business_active_users", metrics.active_users)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集业务指标失败: {str(e)}")
            return BusinessMetrics()
    
    # ==================== 性能追踪 ====================
    
    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: Optional[str] = None
    ):
        """记录请求信息"""
        request_info = {
            'timestamp': time.time(),
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration': duration,
            'user_id': user_id
        }
        
        self.request_times.append(request_info)
        
        # 更新计数器
        self.increment_counter("http_requests_total", labels={
            'method': method,
            'status': str(status_code)
        })
        
        # 记录响应时间
        self.observe_histogram("http_request_duration_seconds", duration, labels={
            'method': method,
            'path': path
        })
    
    def start_request(self):
        """开始请求追踪"""
        self.active_requests += 1
    
    def end_request(self):
        """结束请求追踪"""
        self.active_requests = max(0, self.active_requests - 1)
    
    # ==================== 告警系统 ====================
    
    def add_alert_rule(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        level: MonitoringLevel = MonitoringLevel.WARNING,
        message: str = ""
    ):
        """添加告警规则
        
        Args:
            name: 规则名称
            condition: 告警条件函数
            level: 告警级别
            message: 告警消息
        """
        rule = {
            'name': name,
            'condition': condition,
            'level': level,
            'message': message,
            'last_triggered': None
        }
        
        self.alert_rules.append(rule)
        logger.info(f"添加告警规则: {name}")
    
    def register_alert_callback(self, callback: Callable):
        """注册告警回调函数"""
        self.alert_callbacks.append(callback)
    
    async def check_alerts(self, metrics_data: Dict[str, Any]):
        """检查告警条件"""
        for rule in self.alert_rules:
            try:
                if rule['condition'](metrics_data):
                    await self._trigger_alert(rule, metrics_data)
            except Exception as e:
                logger.error(f"告警规则检查失败: {rule['name']}, {str(e)}")
    
    async def _trigger_alert(self, rule: Dict[str, Any], metrics_data: Dict[str, Any]):
        """触发告警"""
        current_time = datetime.utcnow()
        
        # 防止重复告警（1分钟内不重复）
        if (rule['last_triggered'] and 
            current_time - rule['last_triggered'] < timedelta(minutes=1)):
            return
        
        rule['last_triggered'] = current_time
        
        alert_info = {
            'rule_name': rule['name'],
            'level': rule['level'],
            'message': rule['message'],
            'timestamp': current_time,
            'metrics_data': metrics_data
        }
        
        logger.warning(f"[ALERT] {rule['name']}: {rule['message']}")
        
        # 调用注册的回调函数
        for callback in self.alert_callbacks:
            try:
                await callback(alert_info)
            except Exception as e:
                logger.error(f"告警回调执行失败: {str(e)}")
    
    # ==================== 数据导出 ====================
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}
        
        for name, metric in self.metrics.items():
            summary[name] = {
                'type': metric.metric_type.value,
                'description': metric.description,
                'current_value': metric.current_value,
                'min_value': metric.min_value,
                'max_value': metric.max_value,
                'avg_value': metric.avg_value,
                'sample_count': metric.sample_count,
                'unit': metric.unit,
                'labels': metric.labels
            }
        
        return summary
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        if not self.system_metrics_history:
            return {"status": "no_data"}
        
        latest_metrics = self.system_metrics_history[-1]
        
        # 判断系统健康状态
        health_score = 100
        issues = []
        
        if latest_metrics.cpu_usage_percent > 80:
            health_score -= 20
            issues.append("CPU使用率过高")
        
        if latest_metrics.memory_percent > 85:
            health_score -= 20
            issues.append("内存使用率过高")
        
        if latest_metrics.disk_percent > 90:
            health_score -= 15
            issues.append("磁盘空间不足")
        
        # 确定健康状态
        if health_score >= 90:
            health_status = "healthy"
        elif health_score >= 70:
            health_status = "warning"
        else:
            health_status = "critical"
        
        return {
            "health_status": health_status,
            "health_score": health_score,
            "issues": issues,
            "metrics": latest_metrics.dict(),
            "last_updated": latest_metrics.timestamp.isoformat()
        }
    
    def export_prometheus_metrics(self) -> str:
        """导出Prometheus格式的指标"""
        lines = []
        
        for name, metric in self.metrics.items():
            # 添加HELP注释
            if metric.description:
                lines.append(f"# HELP {name} {metric.description}")
            
            # 添加TYPE注释
            lines.append(f"# TYPE {name} {metric.metric_type.value}")
            
            # 添加指标数据
            if metric.data_points:
                latest_point = metric.data_points[-1]
                labels_str = ""
                if latest_point.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in latest_point.labels.items()]
                    labels_str = "{" + ",".join(label_pairs) + "}"
                
                lines.append(f"{name}{labels_str} {latest_point.value} {int(latest_point.timestamp * 1000)}")
        
        return "\n".join(lines)
    
    # ==================== 私有方法 ====================
    
    def _initialize_builtin_metrics(self):
        """初始化内置指标"""
        # 系统指标
        self.create_metric("system_cpu_usage_percent", MetricType.GAUGE, "CPU使用率", "%")
        self.create_metric("system_memory_usage_percent", MetricType.GAUGE, "内存使用率", "%")
        self.create_metric("system_disk_usage_percent", MetricType.GAUGE, "磁盘使用率", "%")
        self.create_metric("system_active_processes", MetricType.GAUGE, "活跃进程数", "count")
        
        # HTTP指标
        self.create_metric("http_requests_total", MetricType.COUNTER, "HTTP请求总数", "count")
        self.create_metric("http_requests_per_second", MetricType.GAUGE, "HTTP请求速率", "rps")
        self.create_metric("http_request_duration_seconds", MetricType.HISTOGRAM, "HTTP请求响应时间", "seconds")
        self.create_metric("http_response_time_avg", MetricType.GAUGE, "平均响应时间", "seconds")
        self.create_metric("http_error_rate", MetricType.GAUGE, "HTTP错误率", "%")
        self.create_metric("http_active_requests", MetricType.GAUGE, "活跃HTTP请求数", "count")
        
        # 业务指标
        self.create_metric("business_total_strategies", MetricType.GAUGE, "策略总数", "count")
        self.create_metric("business_active_strategies", MetricType.GAUGE, "活跃策略数", "count")
        self.create_metric("business_running_trainings", MetricType.GAUGE, "运行中训练任务", "count")
        self.create_metric("business_active_users", MetricType.GAUGE, "活跃用户数", "count")
    
    def _start_monitoring_tasks(self):
        """启动监控任务"""
        if not self.monitoring_enabled:
            return
        
        # 这里应该启动后台任务定期收集指标
        # 在实际应用中，可以使用asyncio.create_task或其他调度器
        logger.info("监控任务已启动")


class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件"""
    
    def __init__(self, app, monitoring_service: MonitoringService):
        super().__init__(app)
        self.monitoring_service = monitoring_service
    
    async def dispatch(self, request: Request, call_next):
        # 开始请求追踪
        self.monitoring_service.start_request()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # 记录成功请求
            duration = time.time() - start_time
            self.monitoring_service.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                user_id=getattr(request.state, 'user_id', None)
            )
            
            return response
            
        except Exception as e:
            # 记录异常请求
            duration = time.time() - start_time
            self.monitoring_service.record_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration=duration,
                user_id=getattr(request.state, 'user_id', None)
            )
            
            raise e
        
        finally:
            # 结束请求追踪
            self.monitoring_service.end_request()


# 全局监控服务实例
_monitoring_service = None

def get_monitoring_service() -> MonitoringService:
    """获取监控服务实例
    
    Returns:
        MonitoringService: 监控服务实例
    """
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


# 导出主要类和函数
__all__ = [
    "MonitoringService",
    "MonitoringMiddleware",
    "Metric",
    "SystemMetrics",
    "PerformanceMetrics",
    "BusinessMetrics",
    "MetricType",
    "MonitoringLevel",
    "get_monitoring_service"
]