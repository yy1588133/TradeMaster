# TradeMaster Docker 部署完整指南

<div align="center">
    <h2>🐳 TradeMaster Docker 容器化部署</h2>
    <p>一站式量化交易平台容器化解决方案</p>
</div>

---

## 📋 目录

- [🎯 概述](#概述)
- [⚙️ 系统要求](#系统要求)
- [🚀 快速开始](#快速开始)
- [🔧 详细部署步骤](#详细部署步骤)
- [📊 容器配置详情](#容器配置详情)
- [🛠️ 管理工具](#管理工具)
- [🔍 验证测试](#验证测试)
- [⚡ 性能优化](#性能优化)
- [🆘 故障排除](#故障排除)
- [🔒 安全配置](#安全配置)
- [📈 监控维护](#监控维护)
- [❓ 常见问题](#常见问题)

---

## 🎯 概述

TradeMaster Docker 部署方案提供了一个完整的容器化环境，支持：

- **🔄 一键部署**: 自动化容器创建和配置
- **📦 环境隔离**: 独立的Python环境，避免依赖冲突
- **💾 数据持久化**: 自动挂载数据卷，确保数据安全
- **🌐 服务暴露**: 多端口映射支持Web界面、API和Jupyter
- **🛡️ 容错机制**: 自动重启和错误恢复

### 架构优势

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Host System   │    │    Docker Container  │    │   TradeMaster   │
│                 │    │                      │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────────┐ │    │ ┌─────────────┐ │
│ │   Scripts   │◄──┐  │ │   Ubuntu 20.04   │ │    │ │  Algorithms │ │
│ │  Management │   │  │ │                  │ │    │ │             │ │
│ └─────────────┘   │  │ │ ┌──────────────┐ │ │    │ │ ┌─────────┐ │ │
│                   │  │ │ │   Python     │ │ │    │ │ │  Data   │ │ │
│ ┌─────────────┐   │  │ │ │   3.8.10     │ │ │    │ │ │ Volume  │ │ │
│ │    Data     │◄──┼──┼─┤ │              │ │ │    │ │ └─────────┘ │ │
│ │   Volume    │   │  │ │ └──────────────┘ │ │    │ └─────────────┘ │
│ └─────────────┘   │  │ │                  │ │    └─────────────────┘
│                   │  │ │ ┌──────────────┐ │ │             │
│ ┌─────────────┐   │  │ │ │   PyTorch    │ │ │             │
│ │   Ports     │◄──┘  │ │ │   1.12.1     │ │ │             │
│ │ 8080|8888|  │      │ │ └──────────────┘ │ │             │
│ │    5001     │      │ └──────────────────┘ │             │
│ └─────────────┘      └──────────────────────┘             │
└─────────────────┘                                         │
        │                                                   │
        └───────────────────────────────────────────────────┘
```

---

## ⚙️ 系统要求

### 最低配置
- **操作系统**: Windows 10/11, macOS 10.14+, Linux (Ubuntu 18.04+)
- **内存**: 8GB RAM
- **存储**: 15GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: Windows 11, macOS 12+, Linux (Ubuntu 20.04+)
- **内存**: 16GB+ RAM
- **存储**: 50GB+ SSD
- **CPU**: 4核心+
- **网络**: 高速宽带连接

### 必需软件
- **Docker Desktop**: 4.0+ 
  - [Windows](https://docs.docker.com/desktop/install/windows/)
  - [macOS](https://docs.docker.com/desktop/install/mac-install/)
  - [Linux](https://docs.docker.com/desktop/install/linux-install/)

---

## 🚀 快速开始

### Windows 用户 (推荐)

```batch
# 1. 克隆项目
git clone https://github.com/TradeMaster-NTU/TradeMaster.git
cd TradeMaster

# 2. 构建镜像
docker build -t trademaster:latest .

# 3. 启动容器
start-container.bat

# 4. 进入容器
enter-container.bat
```

### Linux/macOS 用户

```bash
# 1. 克隆项目
git clone https://github.com/TradeMaster-NTU/TradeMaster.git
cd TradeMaster

# 2. 构建镜像
docker build -t trademaster:latest .

# 3. 启动容器
docker run -d \
  --name trademaster-container \
  -p 8080:8080 \
  -p 8888:8888 \
  -p 5001:5000 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd):/workspace" \
  --restart unless-stopped \
  trademaster:latest tail -f /dev/null

# 4. 进入容器
docker exec -it trademaster-container bash
```

### 验证安装
```bash
# 在容器内执行
python3 -c "import trademaster; print('✅ TradeMaster安装成功')"
python3 -c "import torch; print('✅ PyTorch版本:', torch.__version__)"
```

---

## 🔧 详细部署步骤

### 步骤 1: 环境准备

#### 1.1 检查Docker安装
```bash
docker --version
docker-compose --version
```

期望输出：
```
Docker version 20.10.17+
Docker Compose version v2.6.0+
```

#### 1.2 配置Docker (Windows)
- 启动 Docker Desktop
- 确保 "Use WSL 2 based engine" 已启用
- 分配足够的资源：
  - Memory: 8GB+
  - CPU: 4 cores+
  - Swap: 2GB+

### 步骤 2: 项目获取与配置

#### 2.1 下载源码
```bash
# 使用HTTPS (推荐)
git clone https://github.com/TradeMaster-NTU/TradeMaster.git

# 或使用SSH
git clone git@github.com:TradeMaster-NTU/TradeMaster.git

cd TradeMaster
```

#### 2.2 检查项目结构
```bash
ls -la
# 应该看到以下关键文件:
# - Dockerfile
# - requirements-docker.txt
# - start-container.bat
# - data/ 目录
```

### 步骤 3: 镜像构建

#### 3.1 标准构建
```bash
docker build -t trademaster:latest .
```

#### 3.2 加速构建 (中国用户)
```bash
# 使用阿里云镜像加速
docker build \
  --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
  --build-arg PIP_TRUSTED_HOST=mirrors.aliyun.com \
  -t trademaster:latest .
```

#### 3.3 验证镜像
```bash
docker images | grep trademaster
```

期望输出：
```
trademaster    latest    abc123def456    2 hours ago    5.47GB
```

### 步骤 4: 容器部署

#### 4.1 自动部署 (Windows)
```batch
# 使用管理脚本
manage-container.bat
# 选择 "1. 启动容器"
```

#### 4.2 手动部署
```bash
docker run -d \
  --name trademaster-container \
  -p 8080:8080 \
  -p 8888:8888 \
  -p 5001:5000 \
  -v "${PWD}/data:/app/data" \
  -v "${PWD}:/workspace" \
  --restart unless-stopped \
  --memory="8g" \
  --cpus="4" \
  trademaster:latest tail -f /dev/null
```

#### 4.3 验证部署
```bash
# 检查容器状态
docker ps | grep trademaster-container

# 检查端口映射
docker port trademaster-container

# 检查资源使用
docker stats trademaster-container
```

---

## 📊 容器配置详情

### 基础配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **基础镜像** | Ubuntu 20.04 | 稳定的Linux发行版 |
| **Python版本** | 3.8.10 | 兼容性最佳的版本 |
| **虚拟环境** | `/opt/trademaster-env` | 隔离Python环境 |
| **工作目录** | `/workspace` | 映射到项目根目录 |
| **数据目录** | `/app/data` | 数据持久化位置 |

### 端口映射

| 本地端口 | 容器端口 | 服务类型 | 用途说明 |
|----------|----------|----------|----------|
| **8080** | 8080 | HTTP | Web界面服务 |
| **8888** | 8888 | HTTP | Jupyter Notebook |
| **5001** | 5000 | HTTP | REST API服务 |

### 数据卷配置

| 本地路径 | 容器路径 | 类型 | 说明 |
|----------|----------|------|------|
| `./data` | `/app/data` | 绑定挂载 | 训练数据和模型 |
| `.` | `/workspace` | 绑定挂载 | 项目源码 |

### 环境变量

```bash
# Python环境
PYTHONPATH="/home/TradeMaster:${PYTHONPATH}"
PATH="/opt/trademaster-env/bin:$PATH"

# 系统配置
DEBIAN_FRONTEND=noninteractive
TZ=Asia/Shanghai

# 应用配置
TRADEMASTER_HOME="/home/TradeMaster"
WORKSPACE_DIR="/workspace"
DATA_DIR="/app/data"
```

---

## 🛠️ 管理工具

### Windows 批处理脚本

#### 综合管理器 - `manage-container.bat`
```batch
# 启动管理界面
manage-container.bat
```

功能菜单：
1. **启动容器** - 创建并启动新容器
2. **停止容器** - 优雅停止并删除容器
3. **进入容器** - 交互式Shell访问
4. **查看状态** - 容器运行状态和资源使用
5. **查看日志** - 实时日志监控
6. **重启容器** - 不丢失数据的重启
7. **清理数据** - 删除容器(保留挂载数据)

#### 独立脚本

**启动容器** - [`start-container.bat`](start-container.bat)
```batch
start-container.bat
```

**停止容器** - [`stop-container.bat`](stop-container.bat)
```batch
stop-container.bat
```

**进入容器** - [`enter-container.bat`](enter-container.bat)
```batch
enter-container.bat
```

### Linux/macOS 命令

#### 容器生命周期管理
```bash
# 启动
docker start trademaster-container

# 停止
docker stop trademaster-container

# 重启
docker restart trademaster-container

# 删除
docker rm -f trademaster-container
```

#### 交互和监控
```bash
# 进入容器
docker exec -it trademaster-container bash

# 实时日志
docker logs -f trademaster-container

# 资源监控
docker stats trademaster-container

# 文件复制
docker cp file.txt trademaster-container:/workspace/
docker cp trademaster-container:/workspace/output.txt ./
```

---

## 🔍 验证测试

### 基础功能测试

#### 1. Python环境验证
```bash
docker exec trademaster-container python3 -c "
import sys
print('Python版本:', sys.version)
print('Python路径:', sys.executable)
print('虚拟环境:', sys.prefix)
"
```

**期望输出**:
```
Python版本: 3.8.10 (default, Mar 18 2025, 20:04:55)
Python路径: /opt/trademaster-env/bin/python3
虚拟环境: /opt/trademaster-env
```

#### 2. 核心依赖测试
```bash
docker exec trademaster-container python3 -c "
import torch
import numpy as np
import pandas as pd
import trademaster

print('✅ PyTorch版本:', torch.__version__)
print('✅ NumPy版本:', np.__version__)
print('✅ Pandas版本:', pd.__version__)
print('✅ TradeMaster模块导入成功')
print('✅ CUDA支持:', torch.cuda.is_available())
"
```

#### 3. 数据访问测试
```bash
docker exec trademaster-container bash -c "
echo '检查数据卷挂载...'
ls -la /app/data/ | head -5
echo ''
echo '检查工作目录映射...'
ls -la /workspace/ | head -5
echo ''
echo '检查TradeMaster路径...'
ls -la /home/TradeMaster/ | head -5
"
```

### 性能基准测试

#### 1. 模型训练性能测试
```bash
docker exec trademaster-container python3 -c "
import sys
sys.path.append('/home/TradeMaster')
import time
import torch
import numpy as np

print('=== TradeMaster 性能基准测试 ===')

# 测试PyTorch基本功能
print('PyTorch版本:', torch.__version__)
print('CUDA可用:', torch.cuda.is_available())

# 创建简单的神经网络
model = torch.nn.Sequential(
    torch.nn.Linear(10, 64),
    torch.nn.ReLU(),
    torch.nn.Linear(64, 32),
    torch.nn.ReLU(),
    torch.nn.Linear(32, 1)
)

# 生成测试数据
X = torch.randn(1000, 10)
y = torch.randn(1000, 1)

criterion = torch.nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

print('开始性能测试...')
start_time = time.time()

for epoch in range(100):
    optimizer.zero_grad()
    output = model(X)
    loss = criterion(output, y)
    loss.backward()
    optimizer.step()
    
    if epoch % 20 == 0:
        print(f'Epoch {epoch}: Loss = {loss.item():.4f}')

end_time = time.time()
training_time = end_time - start_time

print(f'✅ 训练完成，总耗时: {training_time:.2f}秒')
print(f'✅ 平均每轮训练: {training_time/100*1000:.2f}ms')
print(f'✅ 最终损失: {loss.item():.4f}')

# 性能评级
if training_time < 5:
    print('🚀 性能评级: 优秀')
elif training_time < 10:
    print('⚡ 性能评级: 良好') 
elif training_time < 20:
    print('✅ 性能评级: 正常')
else:
    print('⚠️  性能评级: 需要优化')
"
```

#### 2. 数据处理性能测试
```bash
docker exec trademaster-container python3 -c "
import sys
sys.path.append('/home/TradeMaster')
import time
import pandas as pd
import numpy as np

print('=== 数据处理性能测试 ===')

# 生成大规模测试数据
print('生成测试数据...')
data_size = 100000
df = pd.DataFrame({
    'timestamp': pd.date_range('2020-01-01', periods=data_size, freq='1min'),
    'open': np.random.uniform(100, 200, data_size),
    'high': np.random.uniform(200, 300, data_size),
    'low': np.random.uniform(50, 100, data_size),
    'close': np.random.uniform(100, 200, data_size),
    'volume': np.random.randint(1000, 10000, data_size)
})

print(f'数据大小: {len(df):,} 行')
print(f'内存使用: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB')

# 测试数据处理速度
start_time = time.time()

# 计算技术指标
df['sma_20'] = df['close'].rolling(window=20).mean()
df['ema_12'] = df['close'].ewm(span=12).mean()
df['rsi'] = 100 - (100 / (1 + df['close'].pct_change().rolling(14).apply(lambda x: x[x>0].sum() / abs(x[x<0]).sum())))
df['returns'] = df['close'].pct_change()
df['volatility'] = df['returns'].rolling(window=20).std()

processing_time = time.time() - start_time

print(f'✅ 数据处理完成，耗时: {processing_time:.2f}秒')
print(f'✅ 处理速度: {data_size/processing_time:,.0f} 行/秒')

# 性能评级
if processing_time < 2:
    print('🚀 数据处理性能: 优秀')
elif processing_time < 5:
    print('⚡ 数据处理性能: 良好')
elif processing_time < 10:
    print('✅ 数据处理性能: 正常')
else:
    print('⚠️  数据处理性能: 需要优化')
"
```

### 网络服务测试

#### 1. 端口连通性测试
```bash
# 测试端口是否正常监听
docker exec trademaster-container bash -c "
echo '检查端口监听状态...'
netstat -tuln | grep -E ':(8080|8888|5000)'
echo ''
echo '测试端口连通性...'
curl -s http://localhost:8080 > /dev/null && echo '✅ 8080端口可访问' || echo '❌ 8080端口不可访问'
curl -s http://localhost:8888 > /dev/null && echo '✅ 8888端口可访问' || echo '❌ 8888端口不可访问'  
curl -s http://localhost:5000 > /dev/null && echo '✅ 5000端口可访问' || echo '❌ 5000端口不可访问'
"
```

#### 2. 服务健康检查
```bash
# 从主机测试服务访问
curl -I http://localhost:8080
curl -I http://localhost:8888
curl -I http://localhost:5001
```

### 数据持久化测试

#### 1. 创建测试数据
```bash
docker exec trademaster-container bash -c "
echo '创建持久化测试文件...'
echo 'TradeMaster 数据持久化测试 - $(date)' > /app/data/persistence_test.txt
echo '测试数据已写入工作空间' > /workspace/workspace_test.txt
ls -la /app/data/persistence_test.txt
ls -la /workspace/workspace_test.txt
"
```

#### 2. 重启后验证
```bash
# 重启容器
docker restart trademaster-container

# 等待重启完成
sleep 5

# 验证数据持久化
docker exec trademaster-container bash -c "
echo '验证数据持久化...'
if [ -f /app/data/persistence_test.txt ]; then
    echo '✅ 数据卷持久化正常'
    cat /app/data/persistence_test.txt
else
    echo '❌ 数据卷持久化失败'
fi

if [ -f /workspace/workspace_test.txt ]; then
    echo '✅ 工作目录映射正常'
    cat /workspace/workspace_test.txt
else
    echo '❌ 工作目录映射失败'
fi
"
```

---

## ⚡ 性能优化

### 系统层面优化

#### 1. Docker 资源配置
```bash
# 启动时指定资源限制
docker run -d \
  --name trademaster-container \
  --memory="16g" \
  --memory-swap="20g" \
  --cpus="8" \
  --oom-kill-disable \
  -p 8080:8080 \
  -p 8888:8888 \
  -p 5001:5000 \
  -v "${PWD}/data:/app/data" \
  -v "${PWD}:/workspace" \
  --restart unless-stopped \
  trademaster:latest tail -f /dev/null
```

#### 2. 存储优化
```bash
# 使用SSD存储挂载点
# 确保本地data目录在SSD上
du -sh ./data/

# 使用tmpfs加速临时文件
docker run -d \
  --tmpfs /tmp:rw,size=2g \
  --tmpfs /var/tmp:rw,size=1g \
  # ... 其他参数
```

#### 3. 网络优化
```bash
# 创建专用网络
docker network create trademaster-net

# 使用专用网络启动
docker run -d \
  --network trademaster-net \
  # ... 其他参数
```

### 应用层面优化

#### 1. Python 性能调优
```bash
# 在容器内执行
docker exec trademaster-container bash -c "
# 启用Python优化
export PYTHONOPTIMIZE=1

# 调整NumPy线程数
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

# 设置内存映射
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
"
```

#### 2. 数据加载优化
```python
# 在TradeMaster代码中使用
import torch.multiprocessing as mp
mp.set_start_method('spawn', force=True)

# 数据加载器配置
dataloader = torch.utils.data.DataLoader(
    dataset,
    batch_size=64,
    num_workers=4,
    pin_memory=True,
    persistent_workers=True
)
```

### 监控性能指标

#### 1. 系统资源监控
```bash
# 实时监控脚本
docker exec trademaster-container bash -c "
while true; do
    echo '=== $(date) ==='
    echo 'CPU使用率:'
    top -bn1 | grep 'Cpu(s)' 
    echo ''
    echo '内存使用情况:'
    free -h
    echo ''
    echo '磁盘I/O:'
    iostat -x 1 1 | tail -n +4
    echo ''
    echo '网络连接:'
    netstat -i
    echo '================================'
    sleep 30
done
"
```

#### 2. 应用性能监控
```python
# 性能监控代码示例
import psutil
import time
import logging

def monitor_performance():
    """监控应用性能指标"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/app/data')
    
    logging.info(f"CPU使用率: {cpu_percent}%")
    logging.info(f"内存使用率: {memory.percent}%")
    logging.info(f"磁盘使用率: {disk.percent}%")
    
    return {
        'cpu': cpu_percent,
        'memory': memory.percent,
        'disk': disk.percent
    }
```

---

## 🆘 故障排除

### 常见问题诊断

#### 1. 容器启动失败

**问题症状**:
```
Error response from daemon: driver failed programming external connectivity
```

**诊断步骤**:
```bash
# 检查端口占用
netstat -ano | findstr :8080
netstat -ano | findstr :8888
netstat -ano | findstr :5001

# 检查Docker状态
docker info
docker version
```

**解决方案**:
```bash
# 方案1: 更换端口
docker run -d \
  --name trademaster-container \
  -p 8081:8080 \
  -p 8889:8888 \
  -p 5002:5000 \
  # ... 其他参数

# 方案2: 停止占用端口的进程
# Windows
taskkill /PID <PID> /F

# Linux/macOS  
kill -9 <PID>
```

#### 2. 镜像构建失败

**问题症状**:
```
failed to solve with frontend dockerfile.v0
```

**诊断步骤**:
```bash
# 检查Docker文件
cat Dockerfile
ls -la requirements-docker.txt

# 检查磁盘空间
docker system df
df -h
```

**解决方案**:
```bash
# 清理Docker缓存
docker builder prune -f
docker system prune -f

# 重新构建
docker build --no-cache -t trademaster:latest .

# 使用国内镜像源
docker build \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/ \
  -t trademaster:latest .
```

#### 3. 模块导入失败

**问题症状**:
```python
ModuleNotFoundError: No module named 'trademaster'
```

**诊断步骤**:
```bash
docker exec trademaster-container bash -c "
echo 'Python路径:'
python3 -c 'import sys; print(\"\\n\".join(sys.path))'
echo ''
echo 'TradeMaster目录:'
ls -la /home/TradeMaster/
echo ''
echo '环境变量:'
env | grep PYTHON
"
```

**解决方案**:
```bash
# 重新设置PYTHONPATH
docker exec trademaster-container bash -c "
export PYTHONPATH='/home/TradeMaster:$PYTHONPATH'
python3 -c 'import trademaster; print(\"成功导入\")'
"

# 或进入容器手动设置
docker exec -it trademaster-container bash
cd /home/TradeMaster
export PYTHONPATH=$(pwd):$PYTHONPATH
python3 -c "import trademaster"
```

#### 4. 数据卷挂载问题

**问题症状**:
```
bind mount failed: volume specification invalid
```

**诊断步骤**:
```bash
# 检查路径存在性
ls -la ./data/
pwd

# 检查权限
ls -ld ./data/
ls -ld .
```

**解决方案**:
```bash
# 创建必要目录
mkdir -p ./data

# 使用绝对路径
docker run -d \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd):/workspace" \
  # ... 其他参数

# Windows PowerShell
docker run -d \
  -v "${PWD}/data:/app/data" \
  -v "${PWD}:/workspace" \
  # ... 其他参数
```

#### 5. 性能问题

**问题症状**:
- 训练速度异常缓慢
- 内存使用率过高
- CPU占用率不正常

**诊断步骤**:
```bash
# 监控资源使用
docker stats trademaster-container

# 检查容器资源限制
docker inspect trademaster-container | grep -A 10 "Memory"

# 查看系统负载
docker exec trademaster-container top
```

**解决方案**:
```bash
# 调整资源限制
docker update --memory="16g" --cpus="8" trademaster-container

# 重启容器应用新配置
docker restart trademaster-container

# 优化Python进程
docker exec trademaster-container bash -c "
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
python3 your_script.py
"
```

### 调试工具集

#### 1. 日志分析
```bash
# 查看容器日志
docker logs --tail 100 trademaster-container

# 实时日志监控
docker logs -f trademaster-container

# 查看系统日志
docker exec trademaster-container journalctl -f
```

#### 2. 网络诊断
```bash
# 检查网络连通性
docker exec trademaster-container ping google.com

# 检查端口监听
docker exec trademaster-container netstat -tuln

# 测试服务响应
docker exec trademaster-container curl -I http://localhost:8080
```

#### 3. 文件系统检查
```bash
# 检查磁盘使用
docker exec trademaster-container df -h

# 检查挂载点
docker exec trademaster-container mount | grep workspace

# 查找大文件
docker exec trademaster-container find /app -size +100M -type f
```

### 恢复策略

#### 1. 快速恢复
```bash
# 停止问题容器
docker stop trademaster-container

# 删除容器(保留数据)
docker rm trademaster-container

# 重新启动
start-container.bat  # Windows
# 或手动启动
```

#### 2. 完全重建
```bash
# 备份重要数据
cp -r ./data ./data_backup

# 清理所有相关资源
docker rm -f trademaster-container
docker rmi trademaster:latest

# 重新构建和部署
docker build -t trademaster:latest .
start-container.bat
```

#### 3. 数据恢复
```bash
# 恢复数据备份
docker exec trademaster-container bash -c "
if [ -d /workspace/data_backup ]; then
    cp -r /workspace/data_backup/* /app/data/
    echo '数据恢复完成'
else
    echo '未找到备份数据'
fi
"
```

---

## 🔒 安全配置

### 容器安全

#### 1. 基础安全配置
```bash
# 使用非特权用户
docker run -d \
  --user 1000:1000 \
  --security-opt no-new-privileges:true \
  --security-opt apparmor:docker-default \
  # ... 其他参数
```

#### 2. 网络安全
```bash
# 创建隔离网络
docker network create --driver bridge trademaster-net

# 限制网络访问
docker run -d \
  --network trademaster-net \
  --network-alias trademaster \
  # ... 其他参数
```

#### 3. 资源限制
```bash
# 严格的资源限制
docker run -d \
  --memory="8g" \
  --memory-swap="8g" \
  --cpus="4" \
  --pids-limit 1000 \
  --ulimit nofile=1024:1024 \
  # ... 其他参数
```

### 数据安全

#### 1. 敏感数据处理
```bash
# 使用Docker secrets
echo "your_api_key" | docker secret create api_key -

# 在运行时使用
docker run -d \
  --secret api_key \
  # ... 其他参数
```

#### 2. 备份策略
```bash
#!/bin/bash
# backup_data.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

mkdir -p $BACKUP_DIR

# 备份数据目录
tar -czf "$BACKUP_DIR/data_backup_$DATE.tar.gz" ./data/

# 备份容器配置
docker inspect trademaster-container > "$BACKUP_DIR/container_config_$DATE.json"

echo "备份完成: $BACKUP_DIR"
```

#### 3. 访问控制
```bash
# 限制文件权限
chmod 600 ./data/sensitive_config.yml
chmod 700 ./scripts/

# 设置文件所有者
chown -R $(whoami):$(whoami) ./data/
```

### 监控和审计

#### 1. 访问日志
```bash
# 启用详细日志
docker run -d \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  # ... 其他参数
```

#### 2. 安全扫描
```bash
# 扫描镜像漏洞
docker scan trademaster:latest

# 检查容器安全配置
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image trademaster:latest
```

---

## 📈 监控维护

### 监控指标

#### 1. 系统监控
```bash
# 创建监控脚本
cat > monitor.sh << 'EOF'
#!/bin/bash
LOG_FILE="monitoring.log"

while true; do
    echo "=== $(date) ===" >> $LOG_FILE
    
    # 容器状态
    docker stats --no-stream trademaster-container >> $LOG_FILE
    
    # 磁盘使用
    echo "磁盘使用情况:" >> $LOG_FILE
    df -h >> $LOG_FILE
    
    # 网络状态
    echo "网络连接:" >> $LOG_FILE
    docker exec trademaster-container netstat -i >> $LOG_FILE
    
    echo "" >> $LOG_FILE
    sleep 300  # 每5分钟记录一次
done
EOF

chmod +x monitor.sh
```

#### 2. 应用监控
```python
# 在TradeMaster中集成监控
import psutil
import time
import json

def log_performance_metrics():
    """记录性能指标"""
    metrics = {
        'timestamp': time.time(),
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/app/data').percent,
        'process_count': len(psutil.pids())
    }
    
    with open('/app/data/performance.json', 'a') as f:
        f.write(json.dumps(metrics) + '\n')
    
    return metrics
```

### 维护任务

#### 1. 定期清理
```bash
# 创建清理脚本
cat > cleanup.sh << 'EOF'
#!/bin/bash

echo "开始系统清理..."

# 清理Docker缓存
docker system prune -f

# 清理临时文件
docker exec trademaster-container bash -c "
    find /tmp -type f -atime +7 -delete
    find /var/tmp -type f -atime +7 -delete
"

# 轮转日志文件
docker exec trademaster-container bash -c "
    if [ -f /app/data/performance.json ] && [ $(wc -l < /app/data/performance.json) -gt 10000 ]; then
        tail -5000 /app/data/performance.json > /app/data/performance.json.tmp
        mv /app/data/performance.json.tmp /app/data/performance.json
    fi
"

echo "清理完成"
EOF

chmod +x cleanup.sh

# 设置定时任务 (cron)
# 0 2 * * 0 /path/to/cleanup.sh
```

#### 2. 健康检查
```bash 
# 创建健康检查脚本
cat > health_check.sh << 'EOF'
#!/bin/bash

CONTAINER_NAME="trademaster-container"
EMAIL="admin@example.com"

# 检查容器状态
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "容器未运行，尝试重启..."
    docker start $CONTAINER_NAME
    
    # 等待启动
    sleep 30
    
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo "容器重启失败，发送告警" | mail -s "TradeMaster Container Failed" $EMAIL
        exit 1
    fi
fi

# 检查服务健康
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080)
if [ "$HTTP_STATUS" != "200" ]; then
    echo "Web服务异常，状态码: $HTTP_STATUS" | mail -s "TradeMaster Service Issue" $EMAIL
fi

echo "健康检查完成 - $(date)"
EOF

chmod +x health_check.sh

# 每10分钟检查一次
# */10 * * * * /path/to/health_check.sh
```

#### 3. 自动更新
```bash
# 创建更新脚本
cat > update.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "开始更新流程..."

# 备份当前数据
echo "备份数据..."
cp -r ./data $BACKUP_DIR/
docker export trademaster-container > $BACKUP_DIR/container_backup.tar

# 拉取最新代码
echo "更新代码..."
git pull origin main

# 重新构建镜像
echo "重新构建镜像..."
docker build -t trademaster:latest .

# 停止旧容器
echo "停止旧容器..."
docker stop trademaster-container
docker rm trademaster-container

# 启动新容器
echo "启动新容器..."
./start-container.bat

# 验证更新
echo "验证更新..."
sleep 30
if docker ps | grep -q trademaster-container; then
    echo "更新成功"
else
    echo "更新失败，回滚..."
    # 回滚逻辑
    docker load < $BACKUP_DIR/container_backup.tar
    ./start-container.bat
fi

echo "更新流程完成"
EOF

chmod +x update.sh
```

---

## ❓ 常见问题

### Q1: 容器启动后立即退出怎么办？

**A**: 这通常是因为容器内的主进程退出导致的。

```bash
# 查看容器退出原因
docker logs trademaster-container

# 检查入口点脚本
docker run -it --rm trademaster:latest /bin/bash -c "cat /entrypoint.sh"

# 手动进入容器调试
docker run -it --rm trademaster:latest /bin/bash
```

### Q2: 如何在容器中使用GPU加速？

**A**: 需要安装nvidia-docker并使用GPU镜像。

```bash
# 安装nvidia-docker
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2

# 启动GPU容器
docker run -d \
  --gpus all \
  --name trademaster-container-gpu \
  # ... 其他参数
  trademaster:latest-gpu
```

### Q3: 如何备份和迁移容器数据？

**A**: 使用数据卷和容器导出功能。

```bash
# 备份数据卷
docker run --rm -v trademaster_data:/data -v $(pwd):/backup ubuntu tar czf /backup/data_backup.tar.gz -C /data .

# 导出容器
docker export trademaster-container > trademaster_backup.tar

# 在新环境恢复
docker import trademaster_backup.tar trademaster:restored
docker run --rm -v trademaster_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/data_backup.tar.gz -C /data
```

### Q4: 容器内如何访问主机文件？

**A**: 使用卷挂载或bind mount。

```bash
# 绑定挂载主机目录
docker run -d \
  -v /host/path:/container/path \
  # ... 其他参数

# 使用命名卷
docker volume create my_data
docker run -d \
  -v my_data:/container/path \
  # ... 其他参数
```

### Q5: 如何调整容器时区？

**A**: 设置时区环境变量或挂载时区文件。

```bash
# 方法1: 环境变量
docker run -d \
  -e TZ=Asia/Shanghai \
  # ... 其他参数

# 方法2: 挂载时区文件
docker run -d \
  -v /etc/localtime:/etc/localtime:ro \
  -v /etc/timezone:/etc/timezone:ro \
  # ... 其他参数

# 验证时区设置
docker exec trademaster-container date
```

### Q6: 容器网络无法访问外网怎么办？

**A**: 检查DNS和网络配置。

```bash
# 检查DNS设置
docker exec trademaster-container cat /etc/resolv.conf

# 测试网络连通性
docker exec trademaster-container ping 8.8.8.8
docker exec trademaster-container nslookup google.com

# 指定DNS服务器
docker run -d \
  --dns 8.8.8.8 \
  --dns 114.114.114.114 \
  # ... 其他参数
```

### Q7: 如何限制容器资源使用？

**A**: 使用Docker资源限制参数。

```bash
# 完整的资源限制
docker run -d \
  --name trademaster-container \
  --memory="8g" \
  --memory-swap="10g" \
  --memory-swappiness=10 \
  --cpus="4.0" \
  --cpu-shares=1024 \
  --pids-limit=1000 \
  --ulimit nofile=65536:65536 \
  # ... 其他参数

# 动态调整资源限制
docker update --memory="16g" --cpus="8" trademaster-container
```

### Q8: 如何处理权限问题？

**A**: 调整用户权限和文件所有权。

```bash
# 查看当前用户ID
id

# 使用当前用户权限运行容器
docker run -d \
  --user $(id -u):$(id -g) \
  # ... 其他参数

# 修复文件权限
sudo chown -R $(whoami):$(whoami) ./data/
chmod -R 755 ./data/
```

---

## 📚 参考资源

### 官方文档
- [TradeMaster GitHub](https://github.com/TradeMaster-NTU/TradeMaster)
- [TradeMaster 文档](https://trademaster.readthedocs.io/)
- [Docker 官方文档](https://docs.docker.com/)

### 相关链接
- [PyTorch 安装指南](https://pytorch.org/get-started/locally/)
- [CUDA 工具包](https://developer.nvidia.com/cuda-toolkit)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 社区支持
- [GitHub Issues](https://github.com/TradeMaster-NTU/TradeMaster/issues)
- [讨论区](https://github.com/TradeMaster-NTU/TradeMaster/discussions)

---

## 📄 许可证

本文档遵循 [Apache License 2.0](LICENSE) 许可证。

---

## 🤝 贡献

欢迎提交问题报告、功能请求和改进建议！

**文档维护**: TradeMaster Team  
**最后更新**: 2025年8月15日  
**版本**: v2.0.0