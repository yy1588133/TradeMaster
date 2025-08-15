# TradeMaster Docker 故障排除指南

<div align="center">
    <h2>🔧 系统性故障诊断与解决方案</h2>
    <p>快速定位问题，高效解决故障</p>
</div>

---

## 📋 目录

- [🚨 紧急故障快速处理](#紧急故障快速处理)
- [🔍 系统性故障诊断](#系统性故障诊断)
- [⚡ 性能问题分析](#性能问题分析)
- [🐛 常见错误解决方案](#常见错误解决方案)
- [📊 监控和日志分析](#监控和日志分析)
- [🛠️ 调试工具箱](#调试工具箱)
- [🔄 恢复和修复流程](#恢复和修复流程)

---

## 🚨 紧急故障快速处理

### ⚠️ 生产环境紧急恢复

当生产环境出现严重故障时，请按以下优先级处理：

#### 🔥 P0级故障 (服务完全不可用)

**1分钟内快速诊断**:
```bash
# 检查容器状态
docker ps -a | grep trademaster

# 检查系统资源
df -h && free -h && top -n1

# 检查网络连通性
curl -I http://localhost:8080/health
```

**5分钟内紧急恢复**:
```bash
# 方案1: 快速重启
docker restart trademaster-container

# 方案2: 回滚到备份
docker stop trademaster-container
docker run -d --name trademaster-container-backup \
  # ... 使用上一个稳定版本的镜像

# 方案3: 启用备用实例
docker start trademaster-container-standby
# 切换负载均衡到备用实例
```

#### 🟡 P1级故障 (部分功能不可用)

**快速诊断脚本**:
```bash
#!/bin/bash
# emergency_diagnosis.sh

echo "=== 紧急诊断报告 $(date) ==="

echo "1. 容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "2. 资源使用:"
docker stats --no-stream trademaster-container

echo "3. 最近错误日志:"
docker logs --tail 50 trademaster-container | grep -i error

echo "4. 网络连通性:"
for port in 8080 8888 5001; do
    echo "Port $port: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port || echo "FAILED")"
done

echo "5. 磁盘空间:"
df -h | grep -E "(/$|/var|/opt)"

echo "6. 进程状态:"
docker exec trademaster-container ps aux | head -10

echo "=== 诊断完成 ==="
```

### 🔄 自动恢复机制

#### 健康检查脚本
```bash
#!/bin/bash
# health_check.sh

CONTAINER_NAME="trademaster-container"
MAX_RETRIES=3
RETRY_COUNT=0

check_health() {
    # 检查容器是否运行
    if ! docker ps | grep -q $CONTAINER_NAME; then
        return 1
    fi
    
    # 检查HTTP服务
    if ! curl -sf http://localhost:8080/health > /dev/null; then
        return 1
    fi
    
    # 检查关键进程
    if ! docker exec $CONTAINER_NAME pgrep python > /dev/null; then
        return 1
    fi
    
    return 0
}

restart_service() {
    echo "$(date): 尝试重启服务... (重试次数: $RETRY_COUNT/$MAX_RETRIES)"
    
    docker restart $CONTAINER_NAME
    sleep 30
    
    if check_health; then
        echo "$(date): 服务重启成功"
        # 发送恢复通知
        curl -X POST https://hooks.slack.com/your-webhook \
            -H 'Content-type: application/json' \
            --data '{"text":"TradeMaster服务已自动恢复"}'
        exit 0
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
            echo "$(date): 自动恢复失败，需要人工介入"
            # 发送告警
            curl -X POST https://hooks.slack.com/your-webhook \
                -H 'Content-type: application/json' \
                --data '{"text":"TradeMaster服务自动恢复失败，需要人工介入"}'
            exit 1
        fi
    fi
}

# 主逻辑
if ! check_health; then
    restart_service
else
    echo "$(date): 服务运行正常"
fi
```

---

## 🔍 系统性故障诊断

### 🏗️ 诊断决策树

```
故障报告
    ├─ 无法访问服务
    │   ├─ 容器未运行 → [容器启动故障]
    │   ├─ 端口无响应 → [网络配置问题]
    │   └─ 服务异常 → [应用层故障]
    │
    ├─ 性能缓慢
    │   ├─ CPU高占用 → [计算资源问题]
    │   ├─ 内存不足 → [内存资源问题]
    │   └─ I/O阻塞 → [存储性能问题]
    │
    └─ 功能异常
        ├─ 模块导入失败 → [环境配置问题]
        ├─ 数据访问错误 → [数据卷问题]
        └─ 计算结果异常 → [业务逻辑问题]
```

### 🔍 分层诊断方法

#### 1. 基础设施层诊断

**Docker环境检查**:
```bash
# Docker状态检查脚本
#!/bin/bash
# docker_diagnosis.sh

echo "=== Docker环境诊断 ==="

echo "1. Docker版本信息:"
docker version

echo "2. Docker系统信息:"
docker system df
docker system info | grep -E "(Storage Driver|Logging Driver|Cgroup Driver)"

echo "3. 网络配置:"
docker network ls
docker network inspect bridge | jq '.[0].IPAM'

echo "4. 存储使用:"
docker system df -v

echo "5. 正在运行的容器:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo "6. 资源限制:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

**系统资源检查**:
```bash
#!/bin/bash
# system_diagnosis.sh

echo "=== 系统资源诊断 ==="

echo "1. CPU信息:"
lscpu | grep -E "(Model name|CPU\(s\)|Thread)"
top -bn1 | grep "Cpu(s)"

echo "2. 内存信息:"
free -h
cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable|Cached)"

echo "3. 磁盘信息:"
df -h
lsblk
iostat -x 1 1

echo "4. 网络信息:"
netstat -tuln | grep -E "(8080|8888|5001)"
ss -tuln | grep -E "(8080|8888|5001)"

echo "5. 进程信息:"
ps aux | grep -E "(docker|python)" | head -10
```

#### 2. 容器层诊断

**容器内部检查**:
```bash
#!/bin/bash
# container_diagnosis.sh

CONTAINER_NAME="trademaster-container"

echo "=== 容器内部诊断 ==="

echo "1. 容器配置信息:"
docker inspect $CONTAINER_NAME | jq '.[] | {
    Image: .Config.Image,
    Env: .Config.Env,
    Cmd: .Config.Cmd,
    Mounts: .Mounts,
    NetworkSettings: .NetworkSettings.Ports
}'

echo "2. 容器资源使用:"
docker exec $CONTAINER_NAME bash -c "
echo 'CPU核心数: $(nproc)'
echo '内存信息:'
free -h
echo '磁盘使用:'
df -h
echo '进程列表:'
ps aux | head -10
"

echo "3. Python环境检查:"
docker exec $CONTAINER_NAME bash -c "
echo 'Python版本:'
python3 --version
echo 'pip版本:'
pip --version
echo '虚拟环境:'
echo \$VIRTUAL_ENV
echo 'Python路径:'
python3 -c 'import sys; print(\"\\n\".join(sys.path))'
"

echo "4. 关键服务状态:"
docker exec $CONTAINER_NAME bash -c "
echo '端口监听:'
netstat -tuln | grep -E ':(8080|8888|5000)'
echo 'Python进程:'
pgrep -fl python
"
```

#### 3. 应用层诊断

**TradeMaster环境检查**:
```bash
#!/bin/bash
# app_diagnosis.sh

CONTAINER_NAME="trademaster-container"

echo "=== 应用层诊断 ==="

echo "1. TradeMaster模块检查:"
docker exec $CONTAINER_NAME python3 -c "
try:
    import trademaster
    print('✅ TradeMaster模块导入成功')
    print('版本信息:', getattr(trademaster, '__version__', '未知'))
except Exception as e:
    print('❌ TradeMaster模块导入失败:', str(e))
    import traceback
    traceback.print_exc()
"

echo "2. 核心依赖检查:"
docker exec $CONTAINER_NAME python3 -c "
dependencies = [
    'torch', 'numpy', 'pandas', 'sklearn', 
    'matplotlib', 'seaborn', 'plotly'
]

for dep in dependencies:
    try:
        module = __import__(dep)
        version = getattr(module, '__version__', '未知')
        print(f'✅ {dep}: {version}')
    except ImportError as e:
        print(f'❌ {dep}: 导入失败')
"

echo "3. 数据目录检查:"
docker exec $CONTAINER_NAME bash -c "
echo '工作目录内容:'
ls -la /workspace/ | head -10
echo ''
echo '数据目录内容:'
ls -la /app/data/ | head -10
echo ''
echo 'TradeMaster目录:'
ls -la /home/TradeMaster/ | head -10
"

echo "4. 配置文件检查:"
docker exec $CONTAINER_NAME bash -c "
echo '环境变量:'
env | grep -E '(PYTHON|PATH|TRADE)' | sort
echo ''
echo '权限检查:'
whoami
id
ls -la /app/data/ | head -3
"
```

---

## ⚡ 性能问题分析

### 📊 性能监控脚本

#### 综合性能监控
```bash
#!/bin/bash
# performance_monitor.sh

CONTAINER_NAME="trademaster-container"
LOG_FILE="performance_$(date +%Y%m%d_%H%M%S).log"

echo "开始性能监控，日志文件: $LOG_FILE"

{
    echo "=== 性能监控报告 $(date) ==="
    
    echo "1. 系统负载:"
    uptime
    
    echo "2. CPU使用情况:"
    top -bn1 | head -20
    
    echo "3. 内存使用详情:"
    free -h
    docker exec $CONTAINER_NAME cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable|Cached|Buffers)"
    
    echo "4. 磁盘I/O统计:"
    iostat -x 1 1
    
    echo "5. 网络统计:"
    netstat -i
    
    echo "6. 容器资源使用:"
    docker stats --no-stream $CONTAINER_NAME
    
    echo "7. 进程树:"
    docker exec $CONTAINER_NAME pstree -p 1
    
    echo "8. 文件句柄使用:"
    docker exec $CONTAINER_NAME bash -c "
        echo '总限制: '$(ulimit -n)
        echo '当前使用: '$(lsof | wc -l)
        echo '按进程统计:'
        lsof | awk '{print \$2}' | sort | uniq -c | sort -nr | head -5
    "
    
    echo "=== 监控完成 ==="
    
} | tee -a $LOG_FILE
```

#### Python应用性能分析
```python
# performance_profiler.py
import psutil
import time
import threading
import json
from datetime import datetime

class PerformanceProfiler:
    def __init__(self, interval=5):
        self.interval = interval
        self.running = False
        self.data = []
        
    def collect_metrics(self):
        """收集性能指标"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            'memory': {
                'virtual': psutil.virtual_memory()._asdict(),
                'swap': psutil.swap_memory()._asdict()
            },
            'disk': {
                'usage': psutil.disk_usage('/app/data')._asdict(),
                'io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
            },
            'network': psutil.net_io_counters()._asdict(),
            'processes': len(psutil.pids()),
            'connections': len(psutil.net_connections())
        }
    
    def monitor_process(self, pid):
        """监控特定进程"""
        try:
            process = psutil.Process(pid)
            return {
                'pid': pid,
                'name': process.name(),
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info()._asdict(),
                'num_threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
        except psutil.NoSuchProcess:
            return None
    
    def start_monitoring(self):
        """开始监控"""
        self.running = True
        
        def monitor_loop():
            while self.running:
                metrics = self.collect_metrics()
                
                # 监控Python进程
                python_processes = []
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'python' in proc.info['name'].lower():
                        proc_metrics = self.monitor_process(proc.info['pid'])
                        if proc_metrics:
                            python_processes.append(proc_metrics)
                
                metrics['python_processes'] = python_processes
                self.data.append(metrics)
                
                # 保存到文件
                with open('/app/data/performance_metrics.json', 'w') as f:
                    json.dump(self.data[-100:], f, indent=2)  # 只保留最近100条记录
                
                time.sleep(self.interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
    
    def get_performance_summary(self):
        """获取性能摘要"""
        if not self.data:
            return "暂无性能数据"
        
        latest = self.data[-1]
        
        # 计算平均值（最近10个数据点）
        recent_data = self.data[-10:]
        avg_cpu = sum(d['cpu']['percent'] for d in recent_data) / len(recent_data)
        avg_memory = sum(d['memory']['virtual']['percent'] for d in recent_data) / len(recent_data)
        
        summary = f"""
性能摘要 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):
==========================================
CPU使用率: {latest['cpu']['percent']:.1f}% (平均: {avg_cpu:.1f}%)
内存使用率: {latest['memory']['virtual']['percent']:.1f}% (平均: {avg_memory:.1f}%)
可用内存: {latest['memory']['virtual']['available'] / 1024**3:.1f}GB
磁盘使用率: {latest['disk']['usage']['percent']:.1f}%
活跃进程数: {latest['processes']}
网络连接数: {latest['connections']}
Python进程数: {len(latest['python_processes'])}

Python进程详情:
"""
        
        for proc in latest['python_processes']:
            summary += f"  PID {proc['pid']}: CPU {proc['cpu_percent']:.1f}%, 内存 {proc['memory_info']['rss']/1024**2:.1f}MB\n"
        
        return summary

# 使用示例
if __name__ == "__main__":
    profiler = PerformanceProfiler(interval=10)
    profiler.start_monitoring()
    
    try:
        while True:
            time.sleep(60)
            print(profiler.get_performance_summary())
    except KeyboardInterrupt:
        profiler.stop_monitoring()
        print("性能监控已停止")
```

### 🚀 性能优化策略

#### 内存优化
```python
# memory_optimizer.py
import gc
import psutil
import torch
import numpy as np

class MemoryOptimizer:
    def __init__(self):
        self.initial_memory = self.get_memory_usage()
        
    def get_memory_usage(self):
        """获取当前内存使用情况"""
        process = psutil.Process()
        return {
            'rss': process.memory_info().rss / 1024**2,  # MB
            'vms': process.memory_info().vms / 1024**2,  # MB
            'percent': process.memory_percent()
        }
    
    def optimize_memory(self):
        """执行内存优化"""
        print("开始内存优化...")
        
        # 强制垃圾回收
        collected = gc.collect()
        print(f"垃圾回收清理了 {collected} 个对象")
        
        # PyTorch缓存清理
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("清理了CUDA缓存")
        
        # 清理NumPy缓存
        if hasattr(np, 'clear_cache'):
            np.clear_cache()
        
        # 获取优化后的内存使用
        current_memory = self.get_memory_usage()
        saved_memory = self.initial_memory['rss'] - current_memory['rss']
        
        print(f"内存优化完成，节省了 {saved_memory:.1f}MB")
        return saved_memory
    
    def set_memory_limits(self):
        """设置内存使用限制"""
        # 设置PyTorch内存增长策略
        if torch.cuda.is_available():
            torch.cuda.set_per_process_memory_fraction(0.8)
        
        # 设置NumPy线程数
        import os
        os.environ['OMP_NUM_THREADS'] = '4'
        os.environ['MKL_NUM_THREADS'] = '4'
        
        print("内存限制设置完成")
    
    def monitor_memory_usage(self, threshold=80):
        """监控内存使用，超过阈值时优化"""
        current = self.get_memory_usage()
        
        if current['percent'] > threshold:
            print(f"内存使用率 {current['percent']:.1f}% 超过阈值 {threshold}%，开始优化...")
            self.optimize_memory()
            return True
        
        return False

# 在TradeMaster中集成内存优化
def setup_memory_optimization():
    """设置内存优化"""
    optimizer = MemoryOptimizer()
    optimizer.set_memory_limits()
    
    # 定期检查内存使用
    import threading
    import time
    
    def memory_monitor():
        while True:
            optimizer.monitor_memory_usage(threshold=80)
            time.sleep(300)  # 每5分钟检查一次
    
    monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
    monitor_thread.start()
    
    return optimizer
```

#### CPU优化配置
```bash
#!/bin/bash
# cpu_optimization.sh

CONTAINER_NAME="trademaster-container"

echo "开始CPU优化配置..."

# 设置CPU亲和性
docker exec $CONTAINER_NAME bash -c "
# 设置Python进程CPU亲和性
python_pids=\$(pgrep python)
for pid in \$python_pids; do
    taskset -cp 0-3 \$pid 2>/dev/null || true
done

# 设置环境变量优化多线程性能
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export NUMEXPR_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4

# 优化系统调度
echo 'performance' > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || true
"

# 更新容器CPU配置
docker update --cpus="4.0" --cpu-shares=1024 $CONTAINER_NAME

echo "CPU优化配置完成"
```

---

## 🐛 常见错误解决方案

### 🔴 启动错误

#### 错误1: 容器启动后立即退出

**错误信息**:
```
trademaster-container exited with code 0
```

**诊断步骤**:
```bash
# 查看容器日志
docker logs trademaster-container

# 检查启动命令
docker inspect trademaster-container | jq '.[0].Config.Cmd'

# 手动运行调试
docker run -it --rm trademaster:latest /bin/bash
```

**解决方案**:
```bash
# 方案1: 修改启动命令，保持容器运行
docker run -d \
  --name trademaster-container \
  # ... 其他参数
  trademaster:latest tail -f /dev/null

# 方案2: 使用正确的入口点
docker run -d \
  --name trademaster-container \
  # ... 其他参数
  trademaster:latest /entrypoint.sh bash

# 方案3: 交互式启动调试
docker run -it \
  --name trademaster-container \
  # ... 其他参数
  trademaster:latest /bin/bash
```

#### 错误2: 端口绑定失败

**错误信息**:
```
Error starting userland proxy: listen tcp 0.0.0.0:8080: bind: address already in use
```

**诊断步骤**:
```bash
# 检查端口占用
netstat -tuln | grep 8080
ss -tuln | grep 8080

# Windows系统
netstat -ano | findstr :8080

# 查找占用进程
lsof -i :8080  # Linux/Mac
```

**解决方案**:
```bash
# 方案1: 停止占用端口的进程
kill -9 $(lsof -ti:8080)  # Linux/Mac
taskkill /PID <PID> /F    # Windows

# 方案2: 使用不同端口
docker run -d \
  --name trademaster-container \
  -p 8081:8080 \  # 修改本地端口
  -p 8889:8888 \
  -p 5002:5000 \
  # ... 其他参数
  trademaster:latest

# 方案3: 使用主机网络模式
docker run -d \
  --name trademaster-container \
  --network host \
  # ... 其他参数
  trademaster:latest
```

### 🟡 运行时错误

#### 错误3: 模块导入失败

**错误信息**:
```python
ModuleNotFoundError: No module named 'trademaster'
```

**诊断步骤**:
```bash
# 检查Python路径
docker exec trademaster-container python3 -c "
import sys
print('Python版本:', sys.version)
print('Python路径:')
for path in sys.path:
    print('  ', path)
"

# 检查TradeMaster目录
docker exec trademaster-container ls -la /home/TradeMaster/

# 检查环境变量
docker exec trademaster-container env | grep PYTHON
```

**解决方案**:
```bash
# 方案1: 设置PYTHONPATH环境变量
docker exec trademaster-container bash -c "
export PYTHONPATH='/home/TradeMaster:\$PYTHONPATH'
python3 -c 'import trademaster; print(\"成功\")'
"

# 方案2: 在容器启动时设置环境变量
docker run -d \
  --name trademaster-container \
  -e PYTHONPATH="/home/TradeMaster" \
  # ... 其他参数
  trademaster:latest

# 方案3: 创建符号链接
docker exec trademaster-container bash -c "
ln -sf /home/TradeMaster/trademaster /opt/trademaster-env/lib/python3.8/site-packages/
"
```

#### 错误4: 权限被拒绝

**错误信息**:
```
PermissionError: [Errno 13] Permission denied: '/app/data/model.pkl'
```

**诊断步骤**:
```bash
# 检查文件权限
docker exec trademaster-container ls -la /app/data/

# 检查用户身份
docker exec trademaster-container whoami
docker exec trademaster-container id

# 检查挂载点权限
ls -la ./data/
```

**解决方案**:
```bash
# 方案1: 修改本地文件权限
sudo chown -R $(whoami):$(whoami) ./data/
chmod -R 755 ./data/

# 方案2: 在容器内修改权限
docker exec trademaster-container bash -c "
chown -R \$(whoami):\$(whoami) /app/data/
chmod -R 755 /app/data/
"

# 方案3: 使用正确的用户权限启动容器
docker run -d \
  --name trademaster-container \
  --user $(id -u):$(id -g) \
  # ... 其他参数
  trademaster:latest
```

#### 错误5: 内存不足

**错误信息**:
```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

**诊断步骤**:
```bash
# 检查容器内存限制
docker stats trademaster-container

# 检查GPU内存使用
docker exec trademaster-container nvidia-smi

# 检查系统内存
free -h
```

**解决方案**:
```bash
# 方案1: 增加容器内存限制
docker update --memory="16g" --memory-swap="20g" trademaster-container
docker restart trademaster-container

# 方案2: 在Python中设置内存管理
docker exec trademaster-container python3 -c "
import torch
if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.7)
    torch.cuda.empty_cache()
    print('GPU内存设置完成')
"

# 方案3: 使用内存映射模式
docker exec trademaster-container python3 -c "
import torch
# 启用内存映射
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.enabled = True
"
```

### 🔵 网络问题

#### 错误6: 网络连接失败

**错误信息**:
```
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='api.example.com', port=443)
```

**诊断步骤**:
```bash
# 检查容器网络配置
docker inspect trademaster-container | jq '.[0].NetworkSettings'

# 测试网络连通性
docker exec trademaster-container ping google.com
docker exec trademaster-container nslookup google.com

# 检查DNS配置
docker exec trademaster-container cat /etc/resolv.conf
```

**解决方案**:
```bash
# 方案1: 设置DNS服务器
docker run -d \
  --name trademaster-container \
  --dns 8.8.8.8 \
  --dns 114.114.114.114 \
  # ... 其他参数
  trademaster:latest

# 方案2: 使用主机网络
docker run -d \
  --name trademaster-container \
  --network host \
  # ... 其他参数
  trademaster:latest

# 方案3: 配置代理
docker run -d \
  --name trademaster-container \
  -e HTTP_PROXY=http://proxy.company.com:8080 \
  -e HTTPS_PROXY=http://proxy.company.com:8080 \
  # ... 其他参数
  trademaster:latest
```

---

## 📊 监控和日志分析

### 📝 日志收集与分析

#### 集中日志收集
```bash
#!/bin/bash
# log_collector.sh

LOG_DIR="/opt/trademaster/logs"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $LOG_DIR

echo "开始收集日志 - $DATE"

# 收集容器日志
docker logs trademaster-container > "$LOG_DIR/container_$DATE.log" 2>&1

# 收集系统日志
journalctl -u docker.service --since "1 hour ago" > "$LOG_DIR/docker_system_$DATE.log"

# 收集应用日志
docker exec trademaster-container bash -c "
find /app/logs -name '*.log' -mtime -1 -exec cp {} /tmp/ \;
tar czf /tmp/app_logs_$DATE.tar.gz /tmp/*.log 2>/dev/null || true
" 

docker cp trademaster-container:/tmp/app_logs_$DATE.tar.gz "$LOG_DIR/"

# 收集性能数据
docker exec trademaster-container bash -c "
if [ -f /app/data/performance_metrics.json ]; then
    cp /app/data/performance_metrics.json /tmp/performance_$DATE.json
fi
"

docker cp trademaster-container:/tmp/performance_$DATE.json "$LOG_DIR/" 2>/dev/null || true

echo "日志收集完成，存储位置: $LOG_DIR"
```

#### 日志分析脚本
```python
# log_analyzer.py
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class LogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.error_patterns = [
            r'ERROR:.*',
            r'Exception:.*',
            r'Traceback.*',
            r'FATAL:.*',
            r'CRITICAL:.*'
        ]
        
    def parse_container_logs(self):
        """解析容器日志"""
        errors = []
        warnings = []
        info_messages = []
        
        with open(self.log_file, 'r') as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                
                # 提取时间戳
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', line)
                timestamp = timestamp_match.group(1) if timestamp_match else None
                
                # 分类日志级别
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.error_patterns):
                    errors.append({
                        'line_no': line_no,
                        'timestamp': timestamp,
                        'message': line
                    })
                elif 'WARNING' in line.upper() or 'WARN' in line.upper():
                    warnings.append({
                        'line_no': line_no,
                        'timestamp': timestamp,
                        'message': line
                    })
                elif 'INFO' in line.upper():
                    info_messages.append({
                        'line_no': line_no,
                        'timestamp': timestamp,
                        'message': line
                    })
        
        return {
            'errors': errors,
            'warnings': warnings,
            'info': info_messages
        }
    
    def analyze_error_patterns(self, logs):
        """分析错误模式"""
        error_types = Counter()
        error_modules = Counter()
        
        for error in logs['errors']:
            message = error['message']
            
            # 提取错误类型
            error_type_match = re.search(r'(\w+Error|\w+Exception)', message)
            if error_type_match:
                error_types[error_type_match.group(1)] += 1
            
            # 提取模块名
            module_match = re.search(r'File ".*?/([^/]+\.py)"', message)
            if module_match:
                error_modules[module_match.group(1)] += 1
        
        return {
            'error_types': dict(error_types.most_common(10)),
            'error_modules': dict(error_modules.most_common(10))
        }
    
    def generate_report(self):
        """生成分析报告"""
        logs = self.parse_container_logs()
        patterns = self.analyze_error_patterns(logs)
        
        report = f"""
日志分析报告
=============
文件: {self.log_file}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

统计信息:
- 错误数量: {len(logs['errors'])}
- 警告数量: {len(logs['warnings'])}
- 信息数量: {len(logs['info'])}

最常见错误类型:
"""
        
        for error_type, count in patterns['error_types'].items():
            report += f"- {error_type}: {count}次\n"
        
        report += "\n最常出错模块:\n"
        for module, count in patterns['error_modules'].items():
            report += f"- {module}: {count}次\n"
        
        report += "\n最近10个错误:\n"
        for error in logs['errors'][-10:]:
            report += f"[行{error['line_no']}] {error['timestamp']}: {error['message'][:100]}...\n"
        
        return report
    
    def export_json(self, output_file):
        """导出JSON格式的分析结果"""
        logs = self.parse_container_logs()
        patterns = self.analyze_error_patterns(logs)
        
        result = {
            'analysis_time': datetime.now().isoformat(),
            'log_file': self.log_file,
            'summary': {
                'error_count': len(logs['errors']),
                'warning_count': len(logs['warnings']),
                'info_count': len(logs['info'])
            },
            'patterns': patterns,
            'recent_errors': logs['errors'][-20:]  # 最近20个错误
        }
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result

# 使用示例
if __name__ == "__main__":
    analyzer = LogAnalyzer('/opt/trademaster/logs/container_latest.log')
    report = analyzer.generate_report()
    print(report)
    
    # 导出详细分析
    analyzer.export_json('/opt/trademaster/logs/analysis_report.json')
```

### 📈 性能趋势分析

#### 性能数据分析
```python
# performance_analyzer.py
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

class PerformanceAnalyzer:
    def __init__(self, metrics_file):
        self.metrics_file = metrics_file
        self.data = self.load_data()
        
    def load_data(self):
        """加载性能数据"""
        try:
            with open(self.metrics_file, 'r') as f:
                data = json.load(f)
            
            # 转换为DataFrame
            df = pd.json_normalize(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df.sort_values('timestamp')
            
        except Exception as e:
            print(f"加载数据失败: {e}")
            return pd.DataFrame()
    
    def analyze_cpu_usage(self):
        """分析CPU使用情况"""
        if self.data.empty:
            return None
            
        cpu_stats = {
            'mean': self.data['cpu.percent'].mean(),
            'max': self.data['cpu.percent'].max(),
            'min': self.data['cpu.percent'].min(),
            'std': self.data['cpu.percent'].std(),
            'p95': self.data['cpu.percent'].quantile(0.95),
            'p99': self.data['cpu.percent'].quantile(0.99)
        }
        
        # 检测CPU异常
        threshold = cpu_stats['mean'] + 2 * cpu_stats['std']
        high_cpu_periods = self.data[self.data['cpu.percent'] > threshold]
        
        return {
            'statistics': cpu_stats,
            'high_usage_periods': len(high_cpu_periods),
            'recommendations': self.get_cpu_recommendations(cpu_stats)
        }
    
    def analyze_memory_usage(self):
        """分析内存使用情况"""
        if self.data.empty:
            return None
            
        memory_stats = {
            'mean_percent': self.data['memory.virtual.percent'].mean(),
            'max_percent': self.data['memory.virtual.percent'].max(),
            'mean_available_gb': self.data['memory.virtual.available'].mean() / 1024**3,
            'min_available_gb': self.data['memory.virtual.available'].min() / 1024**3
        }
        
        # 内存泄漏检测
        if len(self.data) > 10:
            recent_trend = self.data['memory.virtual.percent'].tail(10).mean()
            earlier_trend = self.data['memory.virtual.percent'].head(10).mean()
            memory_growth = recent_trend - earlier_trend
        else:
            memory_growth = 0
        
        return {
            'statistics': memory_stats,
            'memory_growth': memory_growth,
            'recommendations': self.get_memory_recommendations(memory_stats, memory_growth)
        }
    
    def analyze_disk_usage(self):
        """分析磁盘使用情况"""
        if self.data.empty:
            return None
            
        disk_stats = {
            'usage_percent': self.data['disk.usage.percent'].iloc[-1],
            'free_gb': self.data['disk.usage.free'].iloc[-1] / 1024**3,
            'total_gb': self.data['disk.usage.total'].iloc[-1] / 1024**3
        }
        
        return {
            'statistics': disk_stats,
            'recommendations': self.get_disk_recommendations(disk_stats)
        }
    
    def get_cpu_recommendations(self, stats):
        """CPU优化建议"""
        recommendations = []
        
        if stats['mean'] > 80:
            recommendations.append("CPU使用率过高，建议增加CPU核心数或优化算法")
        elif stats['mean'] < 20:
            recommendations.append("CPU使用率较低，可以考虑减少分配的CPU资源")
        
        if stats['max'] > 95:
            recommendations.append("检测到CPU峰值过高，可能存在计算密集型任务")
        
        if stats['std'] > 30:
            recommendations.append("CPU使用率波动较大，建议优化任务调度")
        
        return recommendations
    
    def get_memory_recommendations(self, stats, growth):
        """内存优化建议"""
        recommendations = []
        
        if stats['mean_percent'] > 85:
            recommendations.append("内存使用率过高，建议增加内存或优化内存使用")
        
        if stats['min_available_gb'] < 1:
            recommendations.append("可用内存过低，存在OOM风险")
        
        if growth > 10:
            recommendations.append("检测到内存增长趋势，可能存在内存泄漏")
        
        return recommendations
    
    def get_disk_recommendations(self, stats):
        """磁盘优化建议"""
        recommendations = []
        
        if stats['usage_percent'] > 85:
            recommendations.append("磁盘使用率过高，建议清理数据或扩容")
        
        if stats['free_gb'] < 5:
            recommendations.append("磁盘剩余空间不足，需要立即处理")
        
        return recommendations
    
    def generate_performance_report(self):
        """生成性能报告"""
        cpu_analysis = self.analyze_cpu_usage()
        memory_analysis = self.analyze_memory_usage()
        disk_analysis = self.analyze_disk_usage()
        
        report = f"""
性能分析报告
============
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
数据点数量: {len(self.data)}
分析时间范围: {self.data['timestamp'].min()} 到 {self.data['timestamp'].max()}

CPU分析:
"""
        if cpu_analysis:
            report += f"""
- 平均使用率: {cpu_analysis['statistics']['mean']:.1f}%
- 最高使用率: {cpu_analysis['statistics']['max']:.1f}%
- P95使用率: {cpu_analysis['statistics']['p95']:.1f}%
- 高负载时段: {cpu_analysis['high_usage_periods']}次

CPU优化建议:
"""
            for rec in cpu_analysis['recommendations']:
                report += f"- {rec}\n"
        
        report += "\n内存分析:\n"
        if memory_analysis:
            report += f"""
- 平均使用率: {memory_analysis['statistics']['mean_percent']:.1f}%
- 最高使用率: {memory_analysis['statistics']['max_percent']:.1f}%
- 平均可用内存: {memory_analysis['statistics']['mean_available_gb']:.1f}GB
- 内存增长趋势: {memory_analysis['memory_growth']:.1f}%

内存优化建议:
"""
            for rec in memory_analysis['recommendations']:
                report += f"- {rec}\n"
        
        report += "\n磁盘分析:\n"
        if disk_analysis:
            report += f"""
- 当前使用率: {disk_analysis['statistics']['usage_percent']:.1f}%
- 剩余空间: {disk_analysis['statistics']['free_gb']:.1f}GB
- 总容量: {disk_analysis['statistics']['total_gb']:.1f}GB

磁盘优化建议:
"""
            for rec in disk_analysis['recommendations']:
                report += f"- {rec}\n"
        
        return report
    
    def plot_performance_trends(self, output_dir='/app/data'):
        """绘制性能趋势图"""
        if self.data.empty:
            print("无数据可绘制")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('TradeMaster 性能趋势分析', fontsize=16)
        
        # CPU使用率趋势
        axes[0, 0].plot(self.data['timestamp'], self.data['cpu.percent'])
        axes[0, 0].set_title('CPU使用率趋势')
        axes[0, 0].set_ylabel('CPU %')
        axes[0, 0].grid(True)
        
        # 内存使用率趋势
        axes[0, 1].plot(self.data['timestamp'], self.data['memory.virtual.percent'])
        axes[0, 1].set_title('内存使用率趋势')
        axes[0, 1].set_ylabel('内存 %')
        axes[0, 1].grid(True)
        
        # 磁盘使用率趋势
        axes[1, 0].plot(self.data['timestamp'], self.data['disk.usage.percent'])
        axes[1, 0].set_title('磁盘使用率趋势')
        axes[1, 0].set_ylabel('磁盘 %')
        axes[1, 0].grid(True)
        
        # 进程数量趋势
        axes[1, 1].plot(self.data['timestamp'], self.data['processes'])
        axes[1, 1].set_title('进程数量趋势')
        axes[1, 1].set_ylabel('进程数')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/performance_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"性能趋势图已保存到: {output_dir}/performance_trends.png")

# 使用示例
if __name__ == "__main__":
    analyzer = PerformanceAnalyzer('/app/data/performance_metrics.json')
    report = analyzer.generate_performance_report()
    print(report)
    analyzer.plot_performance_trends()
```

---

## 🛠️ 调试工具箱

### 🔍 交互式调试环境

#### 远程调试配置
```python
# remote_debugger.py
import pdb
import sys
import threading
import socket
from contextlib import contextmanager

class RemoteDebugger:
    def __init__(self, host='0.0.0.0', port=5678):
        self.host = host
        self.port = port
        self.debugger_active = False
        
    def start_remote_debugger(self):
        """启动远程调试服务"""
        try:
            import ptvsd
            ptvsd.enable_attach(address=(self.host, self.port), redirect_output=True)
            print(f"远程调试器已启动，连接地址: {self.host}:{self.port}")
            self.debugger_active = True
        except ImportError:
            print("ptvsd未安装，使用标准pdb调试器")
            self.start_pdb_server()
    
    def start_pdb_server(self):
        """启动PDB服务器"""
        def pdb_server():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(1)
            
            print(f"PDB调试服务器启动: {self.host}:{self.port}")
            
            while True:
                try:
                    client, addr = server.accept()
                    print(f"调试客户端连接: {addr}")
                    
                    # 重定向stdin/stdout到客户端
                    sys.stdin = client.makefile('r')
                    sys.stdout = client.makefile('w')
                    
                    pdb.set_trace()
                    
                except Exception as e:
                    print(f"调试服务器错误: {e}")
                finally:
                    client.close()
        
        debug_thread = threading.Thread(target=pdb_server, daemon=True)
        debug_thread.start()
        self.debugger_active = True
    
    @contextmanager
    def debug_context(self, condition=True):
        """调试上下文管理器"""
        if condition and self.debugger_active:
            try:
                import ptvsd
                ptvsd.break_into_debugger()
            except ImportError:
                pdb.set_trace()
        yield
    
    def log_debug_info(self, obj, name="debug_object"):
        """记录调试信息"""
        debug_info = {
            'name': name,
            'type': type(obj).__name__,
            'value': str(obj)[:1000],  # 限制长度
            'attributes': [attr for attr in dir(obj) if not attr.startswith('_')]
        }
        
        with open('/app/data/debug_log.json', 'a') as f:
            import json
            f.write(json.dumps(debug_info) + '\n')
        
        print(f"调试信息已记录: {name}")

# 在TradeMaster中集成调试器
def setup_debugging():
    """设置调试环境"""
    debugger = RemoteDebugger()
    
    # 在开发环境中启动远程调试
    import os
    if os.getenv('DEBUG', '').lower() == 'true':
        debugger.start_remote_debugger()
    
    return debugger
```

#### 性能分析工具
```python
# profiling_tools.py
import cProfile
import pstats
import functools
import time
import traceback
from contextlib import contextmanager
import psutil
import threading

class ProfilerManager:
    def __init__(self):
        self.profiles = {}
        self.active_profilers = {}
        
    def profile_function(self, func_name=None):
        """函数性能分析装饰器"""
        def decorator(func):
            name = func_name or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                profiler = cProfile.Profile()
                profiler.enable()
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    profiler.disable()
                    end_time = time.time()
                    
                    # 保存性能数据
                    stats = pstats.Stats(profiler)
                    self.profiles[name] = {
                        'stats': stats,
                        'execution_time': end_time - start_time,
                        'timestamp': time.time()
                    }
                    
                    # 输出性能报告
                    self.save_profile_report(name)
            
            return wrapper
        return decorator
    
    @contextmanager
    def profile_context(self, name="context_profile"):
        """上下文性能分析"""
        profiler = cProfile.Profile()
        profiler.enable()
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            profiler.disable()
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            stats = pstats.Stats(profiler)
            self.profiles[name] = {
                'stats': stats,
                'execution_time': end_time - start_time,
                'memory_delta': end_memory - start_memory,
                'timestamp': time.time()
            }
            
            self.save_profile_report(name)
    
    def save_profile_report(self, name):
        """保存性能报告"""
        if name not in self.profiles:
            return
        
        profile_data = self.profiles[name]
        
        # 生成文本报告
        with open(f'/app/data/profile_{name}.txt', 'w') as f:
            f.write(f"性能分析报告: {name}\n")
            f.write(f"执行时间: {profile_data['execution_time']:.4f}秒\n")
            if 'memory_delta' in profile_data:
                f.write(f"内存变化: {profile_data['memory_delta'] / 1024**2:.2f}MB\n")
            f.write(f"分析时间: {time.ctime(profile_data['timestamp'])}\n")
            f.write("\n" + "="*50 + "\n")
            
            # 输出详细统计
            stats = profile_data['stats']
            stats.sort_stats('cumulative')
            stats.print_stats(20, file=f)
        
        print(f"性能报告已保存: /app/data/profile_{name}.txt")
    
    def start_continuous_profiling(self, duration=300):
        """启动持续性能分析"""
        def continuous_profile():
            profiler = cProfile.Profile()
            profiler.enable()
            
            start_time = time.time()
            
            # 等待指定时间
            time.sleep(duration)
            
            profiler.disable()
            end_time = time.time()
            
            # 保存结果
            stats = pstats.Stats(profiler)
            self.profiles['continuous'] = {
                'stats': stats,
                'execution_time': end_time - start_time,
                'timestamp': time.time()
            }
            
            self.save_profile_report('continuous')
            print(f"持续性能分析完成，时长: {duration}秒")
        
        profile_thread = threading.Thread(target=continuous_profile, daemon=True)
        profile_thread.start()
        
        print(f"开始持续性能分析，时长: {duration}秒")
    
    def memory_profiler(self, func):
        """内存使用分析装饰器"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import tracemalloc
            
            # 开始内存跟踪
            tracemalloc.start()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # 获取内存快照
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                end_memory = psutil.Process().memory_info().rss
                
                # 记录内存使用情况
                memory_report = {
                    'function': func.__name__,
                    'current_traced': current / 1024**2,  # MB
                    'peak_traced': peak / 1024**2,        # MB
                    'rss_delta': (end_memory - start_memory) / 1024**2,  # MB
                    'timestamp': time.time()
                }
                
                with open('/app/data/memory_profile.json', 'a') as f:
                    import json
                    f.write(json.dumps(memory_report) + '\n')
                
                print(f"内存分析完成: {func.__name__}")
                print(f"  当前内存: {current / 1024**2:.2f}MB")
                print(f"  峰值内存: {peak / 1024**2:.2f}MB")
                print(f"  RSS变化: {(end_memory - start_memory) / 1024**2:.2f}MB")
        
        return wrapper

# 使用示例
profiler_manager = ProfilerManager()

# 装饰器使用
@profiler_manager.profile_function("model_training")
def train_model():
    # 模型训练代码
    pass

@profiler_manager.memory_profiler
def load_large_dataset():
    # 数据加载代码
    pass

# 上下文管理器使用
def some_function():
    with profiler_manager.profile_context("data_processing"):
        # 数据处理代码
        pass
```

### 🧪 测试和验证工具

#### 集成测试套件
```bash
#!/bin/bash
# integration_test.sh

CONTAINER_NAME="trademaster-container"
TEST_RESULTS_DIR="/tmp/test_results"

mkdir -p $TEST_RESULTS_DIR

echo "开始集成测试..."

# 测试1: 基础环境测试
echo "1. 基础环境测试..."
docker exec $CONTAINER_NAME python3 -c "
import sys
import os
import subprocess

print('Python版本:', sys.version)
print('当前用户:', os.getenv('USER', 'unknown'))
print('工作目录:', os.getcwd())
print('PYTHONPATH:', sys.path[:3])

# 测试基础命令
try:
    result = subprocess.run(['which', 'python3'], capture_output=True, text=True)
    print('Python路径:', result.stdout.strip())
except Exception as e:
    print('命令测试失败:', e)
" > "$TEST_RESULTS_DIR/basic_env_test.txt"

# 测试2: 模块导入测试
echo "2. 模块导入测试..."
docker exec $CONTAINER_NAME python3 -c "
import importlib
import traceback

modules_to_test = [
    'trademaster',
    'torch',
    'numpy',
    'pandas',
    'sklearn',
    'matplotlib',
    'plotly',
    'yfinance'
]

results = {}
for module in modules_to_test:
    try:
        imported_module = importlib.import_module(module)
        version = getattr(imported_module, '__version__', 'unknown')
        results[module] = {'status': 'success', 'version': version}
        print(f'✅ {module}: {version}')
    except Exception as e:
        results[module] = {'status': 'failed', 'error': str(e)}
        print(f'❌ {module}: {str(e)}')

print('\n模块导入测试完成')
print('成功:', sum(1 for r in results.values() if r['status'] == 'success'))
print('失败:', sum(1 for r in results.values() if r['status'] == 'failed'))
" > "$TEST_RESULTS_DIR/module_import_test.txt"

# 测试3: 数据访问测试
echo "3. 数据访问测试..."
docker exec $CONTAINER_NAME bash -c "
echo '测试数据目录访问...'
echo '工作目录内容:'
ls -la /workspace/ | head -5
echo ''
echo '数据目录内容:'
ls -la /app/data/ | head -5
echo ''
echo 'TradeMaster目录内容:'
ls -la /home/TradeMaster/ | head -5

echo ''
echo '权限测试:'
echo '创建测试文件...'
echo 'test data' > /app/data/test_file.txt
if [ -f /app/data/test_file.txt ]; then
    echo '✅ 数据目录写入权限正常'
    rm /app/data/test_file.txt
else
    echo '❌ 数据目录写入权限异常'
fi
" > "$TEST_RESULTS_DIR/data_access_test.txt"

# 测试4: 网络连接测试
echo "4. 网络连接测试..."
docker exec $CONTAINER_NAME bash -c "
echo '网络连通性测试...'

# 测试DNS解析
if nslookup google.com >/dev/null 2>&1; then
    echo '✅ DNS解析正常'
else
    echo '❌ DNS解析失败'
fi

# 测试HTTP连接
if curl -s --connect-timeout 10 http://www.google.com >/dev/null; then
    echo '✅ HTTP连接正常'
else
    echo '❌ HTTP连接失败'
fi

# 测试HTTPS连接
if curl -s --connect-timeout 10 https://pypi.org >/dev/null; then
    echo '✅ HTTPS连接正常'
else
    echo '❌ HTTPS连接失败'
fi

echo ''
echo '端口监听测试:'
netstat -tuln | grep -E ':(8080|8888|5000)' || echo '端口未监听'
" > "$TEST_RESULTS_DIR/network_test.txt"

# 测试5: 性能基准测试
echo "5. 性能基准测试..."
docker exec $CONTAINER_NAME python3 -c "
import time
import numpy as np
import torch

print('开始性能基准测试...')

# CPU计算性能测试
print('1. CPU计算性能测试:')
start_time = time.time()
a = np.random.rand(1000, 1000)
b = np.random.rand(1000, 1000)
c = np.dot(a, b)
cpu_time = time.time() - start_time
print(f'   矩阵乘法 (1000x1000): {cpu_time:.3f}秒')

# PyTorch性能测试
print('2. PyTorch性能测试:')
start_time = time.time()
x = torch.randn(1000, 1000)
y = torch.randn(1000, 1000)
z = torch.mm(x, y)
torch_time = time.time() - start_time
print(f'   PyTorch矩阵乘法: {torch_time:.3f}秒')

# 内存分配测试
print('3. 内存性能测试:')
start_time = time.time()
large_array = np.zeros((10000, 1000))
memory_time = time.time() - start_time
print(f'   大数组分配: {memory_time:.3f}秒')

# 性能评级
total_time = cpu_time + torch_time + memory_time
if total_time < 5:
    print('性能评级: 优秀')
elif total_time < 10:
    print('性能评级: 良好')
elif total_time < 20:
    print('性能评级: 正常')
else:
    print('性能评级: 需要优化')

print(f'总计用时: {total_time:.3f}秒')
" > "$TEST_RESULTS_DIR/performance_test.txt"

# 生成测试报告
echo "生成测试报告..."
{
    echo "TradeMaster Docker 集成测试报告"
    echo "=================================="
    echo "测试时间: $(date)"
    echo "容器名称: $CONTAINER_NAME"
    echo ""
    
    echo "测试结果概述:"
    echo "============="
    
    for test_file in "$TEST_RESULTS_DIR"/*.txt; do
        test_name=$(basename "$test_file" .txt)
        echo "- $test_name:"
        
        if grep -q "✅" "$test_file"; then
            success_count=$(grep -c "✅" "$test_file")
            echo "  成功项: $success_count"
        fi
        
        if grep -q "❌" "$test_file"; then
            failure_count=$(grep -c "❌" "$test_file")
            echo "  失败项: $failure_count"
        fi
        
        echo ""
    done
    
    echo "详细结果:"
    echo "========="
    
    for test_file in "$TEST_RESULTS_DIR"/*.txt; do
        echo ""
        echo "$(basename "$test_file" .txt):"
        echo "$(head -c 80 < /dev/zero | tr '\0' '-')"
        cat "$test_file"
        echo ""
    done
    
} > "$TEST_RESULTS_DIR/integration_test_report.txt"

echo "集成测试完成!"
echo "测试报告位置: $TEST_RESULTS_DIR/integration_test_report.txt"
echo ""
echo "快速查看结果:"
grep -E "(✅|❌|性能评级)" "$TEST_RESULTS_DIR"/*.txt
```

---

## 🔄 恢复和修复流程

### 🚨 灾难恢复流程

#### 完整系统恢复
```bash
#!/bin/bash
# disaster_recovery.sh

set -euo pipefail

BACKUP_DIR="/opt/backups"
RECOVERY_LOG="/var/log/trademaster_recovery.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$RECOVERY_LOG"
}

log "开始灾难恢复流程..."

# 步骤1: 评估损坏情况
log "评估系统状态..."
CONTAINER_EXISTS=$(docker ps -a | grep trademaster-container | wc -l)
IMAGE_EXISTS=$(docker images | grep trademaster | wc -l)

log "容器存在: $CONTAINER_EXISTS, 镜像存在: $IMAGE_EXISTS"

# 步骤2: 停止所有相关服务
log "停止所有TradeMaster相关服务..."
docker stop trademaster-container 2>/dev/null || true
docker rm trademaster-container 2>/dev/null || true

# 步骤3: 查找最新备份
log "查找最新备份..."
LATEST_BACKUP=$(find "$BACKUP_DIR" -type d -name "*" | sort | tail -1)
log "最新备份: $LATEST_BACKUP"

if [ -z "$LATEST_BACKUP" ] || [ ! -d "$LATEST_BACKUP" ]; then
    log "错误: 未找到有效备份"
    exit 1
fi

# 步骤4: 恢复镜像
log "恢复Docker镜像..."
if [ -f "$LATEST_BACKUP/trademaster_image.tar" ]; then
    docker load < "$LATEST_BACKUP/trademaster_image.tar"
    log "镜像恢复完成"
else
    log "警告: 未找到镜像备份，尝试重新构建..."
    if [ -f "./Dockerfile" ]; then
        docker build -t trademaster:latest .
        log "镜像重新构建完成"
    else
        log "错误: 无法构建镜像"
        exit 1
    fi
fi

# 步骤5: 恢复数据
log "恢复应用数据..."
if [ -f "$LATEST_BACKUP/app_data.tar.gz" ]; then
    mkdir -p ./data_recovery
    tar -xzf "$LATEST_BACKUP/app_data.tar.gz" -C ./data_recovery
    
    # 备份当前数据（如果存在）
    if [ -d "./data" ]; then
        mv ./data "./data_backup_$(date +%Y%m%d_%H%M%S)"
    fi
    
    mv ./data_recovery ./data
    log "数据恢复完成"
else
    log "警告: 未找到数据备份"
fi

# 步骤6: 恢复配置
log "恢复配置文件..."
if [ -d "$LATEST_BACKUP/config" ]; then
    cp -r "$LATEST_BACKUP/config"/* ./
    log "配置恢复完成"
fi

# 步骤7: 启动服务
log "启动恢复后的服务..."
if [ -f "./start-container.bat" ] && command -v cmd.exe >/dev/null 2>&1; then
    # Windows环境
    cmd.exe /c start-container.bat
elif [ -f "./start-container.sh" ]; then
    # Linux环境
    ./start-container.sh
else
    # 手动启动
    docker run -d \
        --name trademaster-container \
        -p 8080:8080 \
        -p 8888:8888 \
        -p 5001:5000 \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd):/workspace" \
        --restart unless-stopped \
        trademaster:latest tail -f /dev/null
fi

# 步骤8: 验证恢复
log "验证服务恢复..."
sleep 30

if docker ps | grep -q trademaster-container; then
    log "✅ 容器启动成功"
else
    log "❌ 容器启动失败"
    exit 1
fi

# 健康检查
if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
    log "✅ 服务健康检查通过"
else
    log "⚠️ 服务健康检查失败，但容器正在运行"
fi

# 步骤9: 数据完整性检查
log "数据完整性检查..."
docker exec trademaster-container python3 -c "
import os
import sys
sys.path.append('/home/TradeMaster')

try:
    import trademaster
    print('✅ TradeMaster模块可用')
    
    # 检查关键数据文件
    data_files = [
        '/app/data/portfolio_management',
        '/app/data/algorithmic_trading'
    ]
    
    for path in data_files:
        if os.path.exists(path):
            file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
            print(f'✅ {path}: {file_count} 个文件')
        else:
            print(f'⚠️ {path}: 目录不存在')
            
except Exception as e:
    print(f'❌ 数据检查失败: {e}')
    sys.exit(1)
" 2>&1 | tee -a "$RECOVERY_LOG"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log "✅ 数据完整性检查通过"
else
    log "❌ 数据完整性检查失败"
fi

log "灾难恢复流程完成!"
log "请检查应用功能是否正常"

# 发送恢复通知
if command -v mail >/dev/null 2>&1; then
    echo "TradeMaster系统已完成灾难恢复，请检查功能" | mail -s "系统恢复完成" admin@example.com
fi
```

#### 逐步恢复检查清单
```bash
#!/bin/bash
# recovery_checklist.sh

echo "TradeMaster 恢复检查清单"
echo "========================"

checks=0
passed=0

run_check() {
    local description="$1"
    local command="$2"
    
    checks=$((checks + 1))
    echo -n "[$checks] $description ... "
    
    if eval "$command" >/dev/null 2>&1; then
        echo "✅ 通过"
        passed=$((passed + 1))
        return 0
    else
        echo "❌ 失败"
        return 1
    fi
}

echo "基础设施检查:"
echo "============"

run_check "Docker服务运行" "docker info"
run_check "容器正在运行" "docker ps | grep -q trademaster-container"
run_check "镜像存在" "docker images | grep -q trademaster"

echo ""
echo "网络连接检查:"
echo "============"

run_check "端口8080可访问" "curl -sf http://localhost:8080"
run_check "端口8888可访问" "curl -sf http://localhost:8888"
run_check "端口5001可访问" "curl -sf http://localhost:5001"

echo ""
echo "应用功能检查:"
echo "============"

run_check "Python环境正常" "docker exec trademaster-container python3 --version"
run_check "TradeMaster模块可导入" "docker exec trademaster-container python3 -c 'import trademaster'"
run_check "数据目录可访问" "docker exec trademaster-container ls /app/data"
run_check "工作目录映射正常" "docker exec trademaster-container ls /workspace"

echo ""
echo "数据完整性检查:"
echo "=============="

run_check "配置文件存在" "docker exec trademaster-container ls /workspace/configs"
run_check "训练数据存在" "docker exec trademaster-container ls /app/data/portfolio_management"
run_check "模型目录存在" "docker exec trademaster-container ls /home/TradeMaster/trademaster"

echo ""
echo "性能检查:"
echo "========"

run_check "CPU使用率正常" "[ \$(docker stats --no-stream --format '{{.CPUPerc}}' trademaster-container | sed 's/%//') -lt 90 ]"
run_check "内存使用率正常" "[ \$(docker stats --no-stream --format '{{.MemPerc}}' trademaster-container | sed 's/%//') -lt 90 ]"

echo ""
echo "检查结果总结:"
echo "============"
echo "总检查项: $checks"
echo "通过项: $passed"
echo "失败项: $((checks - passed))"

if [ $passed -eq $checks ]; then
    echo "🎉 所有检查项都通过，系统恢复成功！"
    exit 0
elif [ $passed -gt $((checks / 2)) ]; then
    echo "⚠️ 大部分检查项通过，但仍有问题需要解决"
    exit 1
else
    echo "❌ 多项检查失败，需要进一步排查问题"
    exit 2
fi
```

---

## 📞 获取支持

### 🆘 技术支持渠道

- **GitHub Issues**: https://github.com/TradeMaster-NTU/TradeMaster/issues
- **邮件支持**: TradeMaster.NTU@gmail.com  
- **社区讨论**: https://github.com/TradeMaster-NTU/TradeMaster/discussions

### 📋 问题报告模板

提交问题时，请包含以下信息：

```
**环境信息**:
- 操作系统: [Windows/Linux/macOS]
- Docker版本: [docker --version]
- TradeMaster版本: [镜像标签]

**问题描述**:
[详细描述遇到的问题]

**重现步骤**:
1. [步骤1]
2. [步骤2]
3. [步骤3]

**期望行为**:
[描述期望的正常行为]

**错误日志**:
```
[粘贴相关错误日志]
```

**诊断信息**:
[运行诊断脚本的输出结果]
```

---

## 📄 版本信息

**文档版本**: v2.0.0  
**最后更新**: 2025年8月15日  
**适用于**: TradeMaster Docker v1.0+  
**维护团队**: TradeMaster Development Team