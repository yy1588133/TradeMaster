# TradeMaster Docker 配置参数指南

<div align="center">
    <h2>⚙️ 全面的配置参数说明</h2>
    <p>从基础配置到高级调优的完整指南</p>
</div>

---

## 📋 目录

- [🐳 Docker容器配置](#docker容器配置)
- [🌐 环境变量配置](#环境变量配置)
- [📊 数据卷配置](#数据卷配置)
- [🔌 网络配置](#网络配置)
- [⚡ 性能调优参数](#性能调优参数)
- [🔒 安全配置参数](#安全配置参数)
- [📝 日志配置](#日志配置)
- [📈 监控配置](#监控配置)
- [🔄 集群配置](#集群配置)
- [🧪 开发调试配置](#开发调试配置)

---

## 🐳 Docker容器配置

### 基础容器参数

#### 资源限制配置
```bash
docker run -d \
  --name trademaster-container \
  
  # CPU配置
  --cpus="4.0"                    # CPU核心数限制
  --cpu-shares=1024               # CPU权重 (默认1024)
  --cpuset-cpus="0-3"            # 绑定到特定CPU核心
  
  # 内存配置
  --memory="8g"                   # 内存限制
  --memory-swap="10g"             # 内存+交换分区总限制
  --memory-swappiness=10          # 交换分区使用倾向 (0-100)
  --oom-kill-disable             # 禁用OOM killer
  
  # 进程限制
  --pids-limit=1000              # 最大进程数
  --ulimit nofile=65536:65536    # 文件句柄数限制
  --ulimit nproc=4096:4096       # 进程数限制
  
  trademaster:latest
```

#### 存储配置
```bash
docker run -d \
  --name trademaster-container \
  
  # 数据卷挂载
  -v "/opt/data:/app/data:rw"           # 读写数据卷
  -v "/opt/config:/app/config:ro"      # 只读配置卷
  -v "/var/log/tm:/app/logs:rw"        # 日志卷
  
  # 临时文件系统
  --tmpfs /tmp:rw,size=2g,noexec       # 临时目录
  --tmpfs /var/tmp:rw,size=1g          # 变量临时目录
  
  # 只读根文件系统
  --read-only                          # 根文件系统只读
  
  trademaster:latest
```

#### 网络配置
```bash
docker run -d \
  --name trademaster-container \
  
  # 端口映射
  -p "127.0.0.1:8080:8080"      # 绑定到本地接口
  -p "8888:8888"                # Jupyter端口
  -p "5001:5000"                # API端口
  
  # 网络模式
  --network="trademaster-net"   # 自定义网络
  --hostname="trademaster-01"   # 主机名
  --dns="8.8.8.8"              # DNS服务器
  --dns-search="company.com"    # DNS搜索域
  
  trademaster:latest
```

### Docker Compose 配置

#### 生产环境配置模板
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  trademaster:
    image: trademaster:${VERSION:-latest}
    container_name: trademaster-${ENVIRONMENT:-prod}
    hostname: trademaster-${HOSTNAME_SUFFIX:-01}
    
    # 重启策略
    restart: unless-stopped
    
    # 资源配置
    deploy:
      resources:
        limits:
          cpus: '${CPU_LIMIT:-4.0}'
          memory: ${MEMORY_LIMIT:-8G}
        reservations:
          cpus: '${CPU_RESERVATION:-2.0}'
          memory: ${MEMORY_RESERVATION:-4G}
      
      # 更新配置
      update_config:
        parallelism: ${UPDATE_PARALLELISM:-2}
        delay: ${UPDATE_DELAY:-10s}
        failure_action: rollback
        order: start-first
      
      # 回滚配置
      rollback_config:
        parallelism: 1
        delay: 5s
        failure_action: pause
    
    # 环境变量
    environment:
      # 应用配置
      - NODE_ENV=${NODE_ENV:-production}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DEBUG=${DEBUG:-false}
      
      # 数据库配置
      - DATABASE_URL=${DATABASE_URL}
      - DATABASE_POOL_SIZE=${DB_POOL_SIZE:-20}
      - DATABASE_TIMEOUT=${DB_TIMEOUT:-30}
      
      # 缓存配置
      - REDIS_URL=${REDIS_URL}
      - CACHE_TTL=${CACHE_TTL:-3600}
      
      # 性能配置
      - WORKERS=${WORKERS:-4}
      - WORKER_CONNECTIONS=${WORKER_CONNECTIONS:-1000}
      - PYTHONOPTIMIZE=${PYTHON_OPTIMIZE:-1}
      
      # 安全配置
      - SECRET_KEY_FILE=/run/secrets/secret_key
      - SSL_CERT_PATH=/run/secrets/ssl_cert
    
    # 数据卷
    volumes:
      - type: volume
        source: trademaster_data
        target: /app/data
        volume:
          driver: ${VOLUME_DRIVER:-local}
          driver_opts:
            type: ${VOLUME_TYPE:-none}
            device: ${VOLUME_DEVICE:-/opt/trademaster/data}
            o: ${VOLUME_OPTIONS:-bind}
      
      - type: bind
        source: ${CONFIG_PATH:-./config}
        target: /app/config
        read_only: true
      
      - type: volume
        source: trademaster_logs
        target: /app/logs
    
    # 网络配置
    networks:
      - trademaster_frontend
      - trademaster_backend
    
    # 端口配置
    ports:
      - "${WEB_PORT:-8080}:8080"
      - "${JUPYTER_PORT:-8888}:8888"
      - "${API_PORT:-5001}:5000"
    
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: ${HEALTH_INTERVAL:-30s}
      timeout: ${HEALTH_TIMEOUT:-10s}
      retries: ${HEALTH_RETRIES:-3}
      start_period: ${HEALTH_START_PERIOD:-60s}
    
    # 日志配置
    logging:
      driver: ${LOG_DRIVER:-json-file}
      options:
        max-size: ${LOG_MAX_SIZE:-50m}
        max-file: ${LOG_MAX_FILES:-5}
        compress: "${LOG_COMPRESS:-true}"
    
    # 安全配置
    security_opt:
      - no-new-privileges:true
      - apparmor:docker-default
    
    # 能力配置
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
      - CHOWN
      - SETUID
      - SETGID
    
    # 用户配置
    user: "${RUN_USER:-1000:1000}"
    
    # 依赖关系
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    
    # 秘密配置
    secrets:
      - secret_key
      - ssl_cert
      - db_password

# 网络配置
networks:
  trademaster_frontend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: tm-frontend
      com.docker.network.driver.mtu: ${NETWORK_MTU:-1500}
  
  trademaster_backend:
    driver: bridge
    internal: true
    driver_opts:
      com.docker.network.bridge.name: tm-backend

# 数据卷配置
volumes:
  trademaster_data:
    driver: ${VOLUME_DRIVER:-local}
    driver_opts:
      type: ${DATA_VOLUME_TYPE:-none}
      device: ${DATA_VOLUME_PATH:-/opt/trademaster/data}
      o: bind
  
  trademaster_logs:
    driver: local
    driver_opts:
      type: none
      device: ${LOG_VOLUME_PATH:-/var/log/trademaster}
      o: bind

# 秘密配置
secrets:
  secret_key:
    file: ${SECRET_KEY_FILE:-./secrets/secret_key.txt}
  ssl_cert:
    file: ${SSL_CERT_FILE:-./secrets/ssl_cert.pem}
  db_password:
    external: true
    name: trademaster_db_password
```

---

## 🌐 环境变量配置

### 应用核心配置

#### 基础应用设置
```bash
# .env.production

# 应用环境
NODE_ENV=production                    # 运行环境: development/staging/production
APP_NAME=TradeMaster                   # 应用名称
APP_VERSION=1.0.0                      # 应用版本
DEBUG=false                            # 调试模式

# 服务配置
HOST=0.0.0.0                          # 监听地址
PORT=8080                              # Web端口
API_PORT=5000                          # API端口
JUPYTER_PORT=8888                      # Jupyter端口

# 工作进程配置
WORKERS=4                              # 工作进程数
WORKER_CONNECTIONS=1000                # 每个工作进程的连接数
WORKER_TIMEOUT=30                      # 工作进程超时时间
WORKER_MAX_REQUESTS=1000               # 每个工作进程最大请求数
WORKER_MAX_REQUESTS_JITTER=100         # 请求数随机抖动
```

#### 数据库配置
```bash
# 数据库连接
DATABASE_URL=postgresql://user:pass@host:5432/trademaster
DATABASE_HOST=postgres                 # 数据库主机
DATABASE_PORT=5432                     # 数据库端口
DATABASE_NAME=trademaster              # 数据库名称
DATABASE_USER=trademaster              # 数据库用户
DATABASE_PASSWORD_FILE=/run/secrets/db_password  # 密码文件路径

# 连接池配置
DATABASE_POOL_SIZE=20                  # 连接池大小
DATABASE_MAX_OVERFLOW=30               # 最大溢出连接
DATABASE_POOL_TIMEOUT=30               # 获取连接超时
DATABASE_POOL_RECYCLE=3600             # 连接回收时间
DATABASE_POOL_PRE_PING=true            # 连接预检

# 查询配置
DATABASE_QUERY_TIMEOUT=60              # 查询超时时间
DATABASE_STATEMENT_TIMEOUT=300         # 语句超时时间
DATABASE_ECHO=false                    # SQL日志输出
```

#### 缓存配置
```bash
# Redis配置
REDIS_URL=redis://redis:6379/0         # Redis连接URL
REDIS_HOST=redis                       # Redis主机
REDIS_PORT=6379                        # Redis端口
REDIS_DB=0                             # Redis数据库
REDIS_PASSWORD=                        # Redis密码
REDIS_MAX_CONNECTIONS=50               # 最大连接数

# 缓存策略
CACHE_TTL=3600                         # 默认缓存时间 (秒)
CACHE_KEY_PREFIX=tm:                   # 缓存键前缀
CACHE_COMPRESSION=true                 # 启用压缩
CACHE_SERIALIZER=pickle                # 序列化方式: json/pickle

# 会话配置
SESSION_TIMEOUT=1800                   # 会话超时时间
SESSION_REFRESH=true                   # 自动刷新会话
SESSION_COOKIE_SECURE=true             # 安全Cookie
SESSION_COOKIE_HTTPONLY=true           # HttpOnly Cookie
```

### 性能调优配置

#### Python优化设置
```bash
# Python解释器优化
PYTHONOPTIMIZE=1                       # 启用字节码优化
PYTHONUNBUFFERED=1                     # 禁用输出缓冲
PYTHONDONTWRITEBYTECODE=1              # 不生成.pyc文件
PYTHONHASHSEED=random                  # 随机哈希种子

# 内存管理
MALLOC_ARENA_MAX=4                     # malloc区域数量
MALLOC_MMAP_THRESHOLD_=131072          # mmap阈值
MALLOC_TRIM_THRESHOLD_=524288          # trim阈值

# 垃圾回收
GC_GENERATION0_THRESHOLD=700           # 0代垃圾回收阈值
GC_GENERATION1_THRESHOLD=10            # 1代垃圾回收阈值
GC_GENERATION2_THRESHOLD=10            # 2代垃圾回收阈值
```

#### 多线程优化
```bash
# OpenMP配置
OMP_NUM_THREADS=4                      # OpenMP线程数
OMP_SCHEDULE=static                    # 调度策略
OMP_PROC_BIND=true                     # 线程绑定

# BLAS库配置
MKL_NUM_THREADS=4                      # Intel MKL线程数
OPENBLAS_NUM_THREADS=4                 # OpenBLAS线程数
VECLIB_MAXIMUM_THREADS=4               # vecLib线程数
NUMEXPR_NUM_THREADS=4                  # NumExpr线程数

# PyTorch配置
TORCH_NUM_THREADS=4                    # PyTorch CPU线程数
TORCH_NUM_INTEROP_THREADS=2            # PyTorch互操作线程数
```

#### GPU配置 (如果适用)
```bash
# CUDA配置
CUDA_VISIBLE_DEVICES=0,1               # 可见GPU设备
CUDA_DEVICE_ORDER=PCI_BUS_ID           # 设备排序
CUDA_CACHE_PATH=/app/cache/cuda        # CUDA缓存路径

# PyTorch GPU配置
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # 内存分配配置
TORCH_CUDNN_V8_API_ENABLED=1           # 启用cuDNN v8 API
```

---

## 📊 数据卷配置

### 数据卷类型和配置

#### 本地绑定挂载
```yaml
# 高性能本地存储
volumes:
  # 应用数据 - SSD存储
  - type: bind
    source: /opt/ssd/trademaster/data
    target: /app/data
    bind:
      propagation: rprivate
      create_host_path: true
  
  # 配置文件 - 只读挂载
  - type: bind
    source: /opt/trademaster/config
    target: /app/config
    read_only: true
    bind:
      propagation: rprivate
  
  # 日志目录 - 可写挂载
  - type: bind
    source: /var/log/trademaster
    target: /app/logs
    bind:
      propagation: rshared
```

#### 命名卷配置
```yaml
# 使用Docker命名卷
volumes:
  trademaster_data:
    driver: local
    driver_opts:
      type: ext4
      device: /dev/sdb1
      o: defaults,noatime
  
  trademaster_cache:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
      o: size=4g,uid=1000,gid=1000
```

#### NFS网络存储
```yaml
# 网络存储配置
volumes:
  trademaster_shared:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs.company.com,rw,sync
      device: ":/volume1/trademaster"
```

### 存储性能优化

#### 文件系统优化参数
```bash
# 在主机上优化挂载选项
mount -o remount,noatime,nodiratime,data=writeback /opt/trademaster/data

# 对于高I/O负载，可以使用以下选项：
# noatime: 不更新访问时间
# nodiratime: 不更新目录访问时间
# data=writeback: 写回模式（性能最佳，但可能丢失数据）
# barrier=0: 禁用写屏障（提高性能，但降低安全性）
```

#### 容器内优化配置
```dockerfile
# Dockerfile中的存储优化
FROM ubuntu:20.04

# 创建优化的挂载点
RUN mkdir -p /app/data /app/logs /app/cache && \
    chmod 755 /app/data /app/logs /app/cache

# 设置临时文件系统
VOLUME ["/tmp", "/var/tmp"]

# 优化数据目录权限
RUN chown -R 1000:1000 /app/data /app/logs
```

---

## 🔌 网络配置

### 容器网络配置

#### 自定义网络创建
```bash
# 创建前端网络（对外）
docker network create \
  --driver bridge \
  --subnet=172.20.0.0/16 \
  --gateway=172.20.0.1 \
  --ip-range=172.20.1.0/24 \
  --opt com.docker.network.bridge.name=tm-frontend \
  --opt com.docker.network.driver.mtu=9000 \
  trademaster-frontend

# 创建后端网络（内部）
docker network create \
  --driver bridge \
  --subnet=172.21.0.0/16 \
  --gateway=172.21.0.1 \
  --internal \
  --opt com.docker.network.bridge.name=tm-backend \
  trademaster-backend

# 创建数据库网络（隔离）
docker network create \
  --driver bridge \
  --subnet=172.22.0.0/16 \
  --internal \
  --opt com.docker.network.bridge.enable_icc=false \
  trademaster-database
```

#### 网络安全配置
```yaml
# docker-compose网络配置
networks:
  frontend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: tm-frontend
      com.docker.network.driver.mtu: "1500"
      com.docker.network.bridge.enable_icc: "true"
      com.docker.network.bridge.enable_ip_masquerade: "true"
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
          ip_range: 172.20.1.0/24
    
  backend:
    driver: bridge
    internal: true
    driver_opts:
      com.docker.network.bridge.name: tm-backend
      com.docker.network.bridge.enable_icc: "true"
    ipam:
      driver: default
      config:
        - subnet: 172.21.0.0/16
          gateway: 172.21.0.1
```

### 端口映射配置

#### 安全端口绑定
```bash
# 只绑定到本地接口（最安全）
docker run -p 127.0.0.1:8080:8080 trademaster:latest

# 绑定到特定接口
docker run -p 192.168.1.100:8080:8080 trademaster:latest

# 使用随机端口
docker run -p 8080 trademaster:latest
```

#### 高级端口配置
```yaml
# docker-compose端口配置
services:
  trademaster:
    ports:
      # 标准格式：HOST:CONTAINER
      - "8080:8080"
      
      # 绑定到特定接口
      - "127.0.0.1:8888:8888"
      
      # 协议指定
      - "5001:5000/tcp"
      - "53:53/udp"
      
      # 端口范围
      - "7000-7010:7000-7010"
      
      # 长格式配置
      - target: 5000
        published: 5001
        protocol: tcp
        mode: host
```

---

## ⚡ 性能调优参数

### 系统级优化

#### 内核参数调优
```bash
# 在主机上执行系统调优
cat > /etc/sysctl.d/99-trademaster.conf << EOF
# 网络优化
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_congestion_control = bbr

# 文件系统优化
fs.file-max = 2097152
fs.nr_open = 1048576
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 进程优化
kernel.pid_max = 4194304
kernel.threads-max = 1048576
EOF

# 应用配置
sysctl -p /etc/sysctl.d/99-trademaster.conf
```

#### 容器系统调优
```yaml
# docker-compose系统调优
services:
  trademaster:
    sysctls:
      # 网络缓冲区大小
      net.core.rmem_max: 134217728
      net.core.wmem_max: 134217728
      net.ipv4.tcp_rmem: "4096 87380 134217728"
      net.ipv4.tcp_wmem: "4096 65536 134217728"
      
      # 连接跟踪
      net.netfilter.nf_conntrack_max: 1048576
      net.netfilter.nf_conntrack_tcp_timeout_established: 600
      
      # 内存管理
      vm.swappiness: 10
      vm.dirty_ratio: 15
      vm.overcommit_memory: 1
```

### 应用级优化

#### TradeMaster性能参数
```bash
# 模型训练优化
MODEL_BATCH_SIZE=64                    # 批处理大小
MODEL_NUM_WORKERS=4                    # 数据加载器工作进程
MODEL_PIN_MEMORY=true                  # 内存固定
MODEL_PERSISTENT_WORKERS=true          # 持久化工作进程

# 数据处理优化
DATA_CHUNK_SIZE=10000                  # 数据块大小
DATA_CACHE_SIZE=1000000                # 数据缓存大小
DATA_PREFETCH_FACTOR=2                 # 预取因子
DATA_PARALLEL_WORKERS=8                # 并行工作进程

# 策略执行优化
STRATEGY_UPDATE_INTERVAL=60            # 策略更新间隔（秒）
STRATEGY_BATCH_ORDERS=true             # 批量下单
STRATEGY_MAX_POSITIONS=100             # 最大持仓数
STRATEGY_RISK_CHECK_INTERVAL=5         # 风险检查间隔（秒）

# 实时数据优化
REALTIME_BUFFER_SIZE=1000              # 实时数据缓冲区大小
REALTIME_BATCH_SIZE=50                 # 实时数据批处理大小
REALTIME_FLUSH_INTERVAL=1              # 数据刷新间隔（秒）
```

#### 数据库查询优化
```bash
# 查询优化参数
DB_QUERY_CACHE_SIZE=64                 # 查询缓存大小(MB)
DB_CONNECTION_POOL_SIZE=20             # 连接池大小
DB_STATEMENT_CACHE_SIZE=100            # 语句缓存大小
DB_BULK_INSERT_SIZE=1000               # 批量插入大小

# 索引优化
DB_INDEX_SCAN_THRESHOLD=0.1            # 索引扫描阈值
DB_PARALLEL_QUERY_WORKERS=4            # 并行查询工作进程
DB_WORK_MEM=256                        # 工作内存(MB)
DB_MAINTENANCE_WORK_MEM=512            # 维护工作内存(MB)
```

---

## 🔒 安全配置参数

### 容器安全设置

#### 安全选项配置
```bash
docker run -d \
  --name trademaster-secure \
  
  # 安全选项
  --security-opt no-new-privileges:true      # 禁止获取新权限
  --security-opt apparmor:docker-default     # AppArmor配置
  --security-opt seccomp:default             # Seccomp配置
  
  # 能力控制
  --cap-drop ALL                             # 删除所有能力
  --cap-add NET_BIND_SERVICE                 # 添加端口绑定能力
  --cap-add CHOWN                            # 添加文件所有权能力
  --cap-add SETUID                           # 添加设置UID能力
  --cap-add SETGID                           # 添加设置GID能力
  
  # 用户配置
  --user 1000:1000                          # 非root用户运行
  
  # 文件系统安全
  --read-only                                # 只读根文件系统
  --tmpfs /tmp:rw,size=100m,noexec,nosuid    # 安全临时文件系统
  
  trademaster:latest
```

#### 网络安全配置
```yaml
# 网络安全设置
services:
  trademaster:
    networks:
      - trademaster_internal
    ports:
      # 只绑定到本地接口
      - "127.0.0.1:8080:8080"
    
    # 环境变量安全
    environment:
      # 使用秘密文件而不是环境变量
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
      - API_KEY_FILE=/run/secrets/api_key
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
    
    # 秘密管理
    secrets:
      - db_password
      - api_key
      - jwt_secret

networks:
  trademaster_internal:
    internal: true  # 内部网络，无外网访问

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true
    name: trademaster_api_key
  jwt_secret:
    external: true
    name: trademaster_jwt_secret
```

### 应用安全参数

#### 认证和授权
```bash
# JWT配置
JWT_ALGORITHM=HS256                    # JWT算法
JWT_ACCESS_TOKEN_EXPIRE=900            # 访问令牌过期时间（秒）
JWT_REFRESH_TOKEN_EXPIRE=86400         # 刷新令牌过期时间（秒）
JWT_ISSUER=TradeMaster                 # 令牌发行者

# 密码策略
PASSWORD_MIN_LENGTH=12                 # 最小密码长度
PASSWORD_REQUIRE_UPPERCASE=true        # 要求大写字母
PASSWORD_REQUIRE_LOWERCASE=true        # 要求小写字母
PASSWORD_REQUIRE_NUMBERS=true          # 要求数字
PASSWORD_REQUIRE_SYMBOLS=true          # 要求特殊字符
PASSWORD_MAX_AGE=90                    # 密码最大使用天数

# 会话安全
SESSION_SECURE=true                    # 安全会话Cookie
SESSION_HTTPONLY=true                  # HttpOnly会话Cookie
SESSION_SAMESITE=Strict                # SameSite策略
CSRF_PROTECTION=true                   # CSRF保护
```

#### 数据加密
```bash
# 数据库加密
DB_ENCRYPTION_AT_REST=true             # 静态数据加密
DB_ENCRYPTION_IN_TRANSIT=true          # 传输数据加密
DB_SSL_MODE=require                    # SSL模式
DB_SSL_CERT_PATH=/app/certs/client.crt # SSL证书路径
DB_SSL_KEY_PATH=/app/certs/client.key  # SSL私钥路径

# API加密
API_TLS_VERSION=1.3                    # TLS版本
API_CIPHER_SUITE=ECDHE-ECDSA-AES256-GCM-SHA384  # 加密套件
API_HSTS_MAX_AGE=31536000             # HSTS最大年龄

# 文件加密
FILE_ENCRYPTION_ALGORITHM=AES-256-GCM  # 文件加密算法
FILE_ENCRYPTION_KEY_PATH=/run/secrets/encryption_key  # 加密密钥路径
```

---

## 📝 日志配置

### 日志驱动配置

#### JSON文件日志驱动
```yaml
# 标准JSON文件日志
services:
  trademaster:
    logging:
      driver: json-file
      options:
        max-size: "50m"              # 单个日志文件最大大小
        max-file: "5"                # 最大日志文件数
        compress: "true"             # 压缩旧日志文件
        labels: "service,version"    # 包含的标签
        env: "NODE_ENV,LOG_LEVEL"    # 包含的环境变量
```

#### Syslog日志驱动
```yaml
# Syslog日志配置
services:
  trademaster:
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://log-server:514"  # Syslog服务器地址
        syslog-facility: "daemon"               # Syslog设施
        syslog-format: "rfc5424micro"           # Syslog格式
        tag: "trademaster-{{.Name}}"            # 日志标签
        env: "NODE_ENV,SERVICE_NAME"            # 环境变量
```

#### Fluentd日志驱动
```yaml
# Fluentd日志配置
services:
  trademaster:
    logging:
      driver: fluentd
      options:
        fluentd-address: "fluentd:24224"        # Fluentd地址
        fluentd-async-connect: "true"           # 异步连接
        fluentd-buffer-limit: "4mb"             # 缓冲区限制
        fluentd-retry-wait: "1s"                # 重试等待时间
        fluentd-max-retries: "3"                # 最大重试次数
        tag: "docker.trademaster.{{.Name}}"     # 标签模板
```

### 应用日志配置

#### Python日志配置
```python
# logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': '/app/logs/trademaster.log',
            'maxBytes': 100 * 1024 * 1024,  # 100MB
            'backupCount': 10,
            'encoding': 'utf-8'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filename': '/app/logs/error.log',
            'maxBytes': 50 * 1024 * 1024,   # 50MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'trademaster': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'uvicorn': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}
```

#### 日志环境变量
```bash
# 日志级别配置
LOG_LEVEL=INFO                         # 全局日志级别
TRADEMASTER_LOG_LEVEL=DEBUG            # TradeMaster模块日志级别
SQLALCHEMY_LOG_LEVEL=WARNING           # SQLAlchemy日志级别
REQUESTS_LOG_LEVEL=WARNING             # Requests库日志级别

# 日志输出配置
LOG_FORMAT=json                        # 日志格式: json/text
LOG_TIMESTAMP_FORMAT=iso               # 时间戳格式: iso/unix
LOG_INCLUDE_CALLER=true                # 包含调用者信息
LOG_INCLUDE_STACK_TRACE=true           # 包含堆栈跟踪

# 日志文件配置
LOG_FILE_PATH=/app/logs                # 日志文件路径
LOG_FILE_MAX_SIZE=100MB                # 单个日志文件最大大小
LOG_FILE_MAX_COUNT=10                  # 最大日志文件数
LOG_FILE_ROTATION=daily                # 日志轮转: daily/weekly/monthly

# 日志过滤配置
LOG_FILTER_SENSITIVE=true              # 过滤敏感信息
LOG_SANITIZE_PATTERNS="password,token,key,secret"  # 敏感字段模式
```

---

## 📈 监控配置

### Prometheus监控配置

#### 指标收集配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'trademaster-production'
    environment: 'production'

rule_files:
  - "rules/*.yml"

scrape_configs:
  # TradeMaster应用指标
  - job_name: 'trademaster'
    static_configs:
      - targets: ['trademaster:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s
    honor_labels: true
    
  # 容器指标
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  # 系统指标
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  # 数据库指标
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    metrics_path: '/metrics'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

#### 告警规则配置
```yaml
# alerts/trademaster.yml
groups:
  - name: trademaster.alerts
    rules:
      # 应用可用性告警
      - alert: TradeMasterDown
        expr: up{job="trademaster"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "TradeMaster服务不可用"
          description: "TradeMaster服务已经宕机超过1分钟"
      
      # 高内存使用告警
      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes{name="trademaster-container"} / container_spec_memory_limit_bytes{name="trademaster-container"}) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率已超过85%，当前为{{ $value }}%"
      
      # 高CPU使用告警
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total{name="trademaster-container"}[5m]) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率已超过80%，当前为{{ $value }}%"
      
      # 磁盘空间告警
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/app/data"} / node_filesystem_size_bytes{mountpoint="/app/data"}) * 100 < 15
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足"
          description: "数据目录剩余空间少于15%，当前为{{ $value }}%"
      
      # 响应时间告警
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "响应时间过长"
          description: "95%分位数响应时间超过2秒，当前为{{ $value }}秒"
```

### 应用监控配置

#### 自定义指标配置
```bash
# 业务监控配置
METRICS_ENABLED=true                   # 启用指标收集
METRICS_PORT=8000                      # 指标端口
METRICS_PATH=/metrics                  # 指标路径
METRICS_NAMESPACE=trademaster          # 指标命名空间

# 业务指标配置
BUSINESS_METRICS_ENABLED=true          # 启用业务指标
TRADE_METRICS_ENABLED=true             # 启用交易指标
PORTFOLIO_METRICS_ENABLED=true         # 启用投资组合指标
RISK_METRICS_ENABLED=true              # 启用风险指标

# 性能指标配置
PERFORMANCE_METRICS_INTERVAL=60        # 性能指标收集间隔（秒）
SYSTEM_METRICS_INTERVAL=30             # 系统指标收集间隔（秒）
BUSINESS_METRICS_INTERVAL=10           # 业务指标收集间隔（秒）

# 指标保留配置
METRICS_RETENTION_DAYS=30              # 指标保留天数
METRICS_AGGREGATION_INTERVAL=300       # 指标聚合间隔（秒）
```

---

## 🔄 集群配置

### Docker Swarm配置

#### Swarm初始化配置
```bash
# 初始化Swarm集群
docker swarm init \
  --advertise-addr 192.168.1.100 \
  --listen-addr 0.0.0.0:2377 \
  --data-path-addr 192.168.1.100

# 创建overlay网络
docker network create \
  --driver overlay \
  --subnet=10.0.0.0/16 \
  --attachable \
  trademaster-overlay
```

#### 服务部署配置
```yaml
# docker-compose.swarm.yml
version: '3.8'

services:
  trademaster:
    image: trademaster:latest
    
    # 服务部署配置
    deploy:
      mode: replicated
      replicas: 3
      
      # 资源约束
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      
      # 更新配置
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        monitor: 60s
        order: start-first
      
      # 重启策略
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
      
      # 放置约束
      placement:
        constraints:
          - node.role == worker
          - node.labels.storage == ssd
        preferences:
          - spread: node.labels.zone
    
    # 网络配置
    networks:
      - trademaster-overlay
    
    # 端口配置
    ports:
      - target: 8080
        published: 8080
        protocol: tcp
        mode: ingress
    
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

networks:
  trademaster-overlay:
    external: true
```

### Kubernetes配置

#### 基础部署配置
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trademaster
  namespace: trademaster
  labels:
    app: trademaster
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: trademaster
  template:
    metadata:
      labels:
        app: trademaster
        version: v1.0.0
    spec:
      # 安全上下文
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      
      # 容器配置
      containers:
      - name: trademaster
        image: trademaster:latest
        imagePullPolicy: Always
        
        # 端口配置
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        - containerPort: 8000
          name: metrics
          protocol: TCP
        
        # 环境变量
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trademaster-secrets
              key: database-url
        
        # 资源配置
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        
        # 健康检查
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # 数据卷挂载
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: config-volume
          mountPath: /app/config
          readOnly: true
        - name: logs-volume
          mountPath: /app/logs
      
      # 数据卷
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: trademaster-data-pvc
      - name: config-volume
        configMap:
          name: trademaster-config
      - name: logs-volume
        emptyDir: {}
      
      # 节点选择
      nodeSelector:
        kubernetes.io/os: linux
        node-type: compute
      
      # 容忍度
      tolerations:
      - key: "dedicated"
        operator: "Equal"
        value: "trademaster"
        effect: "NoSchedule"
      
      # 亲和性
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - trademaster
              topologyKey: kubernetes.io/hostname
```

---

## 🧪 开发调试配置

### 开发环境配置

#### 开发模式环境变量
```bash
# .env.development

# 开发环境标识
NODE_ENV=development
DEBUG=true
DEVELOPMENT_MODE=true

# 调试配置
DEBUG_LEVEL=DEBUG
FLASK_DEBUG=1
DJANGO_DEBUG=True
FASTAPI_DEBUG=True

# 热重载配置
AUTO_RELOAD=true
RELOAD_DIRS=/app/src,/app/config
RELOAD_INCLUDES=*.py,*.yml,*.yaml
RELOAD_EXCLUDES=*.pyc,__pycache__

# 开发服务器配置
DEV_SERVER_HOST=0.0.0.0
DEV_SERVER_PORT=8080
DEV_SERVER_WORKERS=1

# 开发数据库配置
DATABASE_URL=postgresql://dev:dev@localhost:5432/trademaster_dev
DATABASE_ECHO=true
DATABASE_POOL_SIZE=5

# 开发缓存配置
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=60

# 调试工具配置
ENABLE_PROFILER=true
ENABLE_DEBUGGER=true
ENABLE_INTERACTIVE_DEBUGGER=true

# 测试配置
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/trademaster_test
RUN_TESTS_ON_START=false
```

#### 调试容器配置
```yaml
# docker-compose.debug.yml
version: '3.8'

services:
  trademaster-debug:
    build:
      context: .
      target: development
    
    # 调试端口
    ports:
      - "8080:8080"    # 应用端口
      - "5678:5678"    # 调试端口
      - "8888:8888"    # Jupyter端口
    
    # 环境变量
    environment:
      - NODE_ENV=development
      - DEBUG=true
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    
    # 代码挂载（实时更新）
    volumes:
      - ./src:/app/src
      - ./config:/app/config
      - ./tests:/app/tests
      - /app/node_modules  # 避免覆盖node_modules
    
    # 命令覆盖
    command: ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "-m", "trademaster.main"]
    
    # 开发工具
    depends_on:
      - postgres-dev
      - redis-dev
      - mailhog  # 邮件测试工具

  # 开发数据库
  postgres-dev:
    image: postgres:13
    environment:
      POSTGRES_DB: trademaster_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  # 开发缓存
  redis-dev:
    image: redis:alpine
    ports:
      - "6379:6379"

  # 邮件测试工具
  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP端口
      - "8025:8025"  # Web界面

volumes:
  postgres_dev_data:
```

### 调试工具配置

#### VS Code调试配置
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: TradeMaster",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/main.py",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src",
                "NODE_ENV": "development",
                "DEBUG": "true"
            },
            "args": [],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "envFile": "${workspaceFolder}/.env.development"
        },
        {
            "name": "Python: Remote Attach",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ]
        },
        {
            "name": "Docker: Attach to Python",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ],
            "justMyCode": false
        }
    ]
}
```

#### PyCharm远程调试配置
```python
# remote_debug.py
import pydevd_pycharm

# 连接到PyCharm调试服务器
pydevd_pycharm.settrace(
    host='host.docker.internal',  # Docker Desktop
    port=12345,
    stdoutToServer=True,
    stderrToServer=True,
    suspend=False
)
```

---

## 📚 配置文件模板

### 完整环境配置模板

#### 生产环境配置 (.env.production)
```bash
# ===========================================
# TradeMaster 生产环境配置
# ===========================================

# 基础配置
NODE_ENV=production
APP_NAME=TradeMaster
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# 服务配置
HOST=0.0.0.0
PORT=8080
API_PORT=5000
WORKERS=4
WORKER_TIMEOUT=30

# 数据库配置
DATABASE_URL=postgresql://trademaster:${DB_PASSWORD}@postgres:5432/trademaster
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30

# 缓存配置
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600
CACHE_KEY_PREFIX=tm:

# 安全配置
SECRET_KEY_FILE=/run/secrets/secret_key
JWT_SECRET_FILE=/run/secrets/jwt_secret
SSL_CERT_PATH=/run/secrets/ssl_cert
SESSION_COOKIE_SECURE=true
CSRF_PROTECTION=true

# 性能配置
PYTHONOPTIMIZE=1
OMP_NUM_THREADS=4
MKL_NUM_THREADS=4

# 监控配置
METRICS_ENABLED=true
METRICS_PORT=8000
HEALTH_CHECK_ENABLED=true

# 业务配置
MODEL_BATCH_SIZE=64
STRATEGY_UPDATE_INTERVAL=60
REALTIME_BUFFER_SIZE=1000

# 文件路径
DATA_PATH=/app/data
CONFIG_PATH=/app/config
LOG_PATH=/app/logs
CACHE_PATH=/app/cache
```

#### Docker Compose生产配置模板
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  trademaster:
    image: ${REGISTRY}/trademaster:${VERSION}
    container_name: trademaster-${ENVIRONMENT}
    hostname: trademaster-${HOSTNAME_SUFFIX}
    
    restart: unless-stopped
    
    deploy:
      resources:
        limits:
          cpus: '${CPU_LIMIT}'
          memory: ${MEMORY_LIMIT}
        reservations:
          cpus: '${CPU_RESERVATION}'
          memory: ${MEMORY_RESERVATION}
    
    environment:
      - NODE_ENV=${NODE_ENV}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - LOG_LEVEL=${LOG_LEVEL}
      - WORKERS=${WORKERS}
    
    volumes:
      - type: bind
        source: ${DATA_PATH}
        target: /app/data
      - type: bind
        source: ${CONFIG_PATH}
        target: /app/config
        read_only: true
      - type: bind
        source: ${LOG_PATH}
        target: /app/logs
    
    networks:
      - trademaster_frontend
      - trademaster_backend
    
    ports:
      - "${WEB_PORT}:8080"
      - "${API_PORT}:5000"
      - "${METRICS_PORT}:8000"
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
        compress: "true"
    
    security_opt:
      - no-new-privileges:true
    
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:${POSTGRES_VERSION}
    container_name: postgres-${ENVIRONMENT}
    
    restart: unless-stopped
    
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d
    
    networks:
      - trademaster_backend
    
    ports:
      - "${POSTGRES_PORT}:5432"
    
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:${REDIS_VERSION}
    container_name: redis-${ENVIRONMENT}
    
    restart: unless-stopped
    
    command: redis-server --appendonly yes --maxmemory ${REDIS_MAX_MEMORY} --maxmemory-policy allkeys-lru
    
    volumes:
      - redis_data:/data
    
    networks:
      - trademaster_backend
    
    ports:
      - "${REDIS_PORT}:6379"
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

networks:
  trademaster_frontend:
    driver: bridge
  trademaster_backend:
    driver: bridge
    internal: true

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: ${POSTGRES_DATA_PATH}
      o: bind
  
  redis_data:
    driver: local
    driver_opts:
      type: none
      device: ${REDIS_DATA_PATH}
      o: bind
```

---

## 📄 配置验证和测试

### 配置验证脚本
```bash
#!/bin/bash
# config_validator.sh

set -euo pipefail

echo "TradeMaster配置验证工具"
echo "======================"

# 配置文件检查
check_config_files() {
    echo "检查配置文件..."
    
    required_files=(
        ".env"
        "docker-compose.yml"
        "Dockerfile"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo "✅ $file 存在"
        else
            echo "❌ $file 缺失"
            return 1
        fi
    done
}

# 环境变量检查
check_environment_variables() {
    echo "检查环境变量..."
    
    required_vars=(
        "NODE_ENV"
        "DATABASE_URL"
        "REDIS_URL"
        "LOG_LEVEL"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -n "${!var:-}" ]; then
            echo "✅ $var 已设置"
        else
            echo "❌ $var 未设置"
            return 1
        fi
    done
}

# 数据库连接测试
test_database_connection() {
    echo "测试数据库连接..."
    
    if docker exec trademaster-container python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    print('✅ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
    "; then
        echo "数据库连接验证通过"
    else
        echo "数据库连接验证失败"
        return 1
    fi
}

# 缓存连接测试
test_cache_connection() {
    echo "测试缓存连接..."
    
    if docker exec trademaster-container python3 -c "
import redis
import os
try:
    r = redis.from_url(os.environ['REDIS_URL'])
    r.ping()
    print('✅ Redis连接成功')
except Exception as e:
    print(f'❌ Redis连接失败: {e}')
    exit(1)
    "; then
        echo "缓存连接验证通过"
    else
        echo "缓存连接验证失败"
        return 1
    fi
}

# 运行所有检查
main() {
    check_config_files || exit 1
    check_environment_variables || exit 1
    test_database_connection || exit 1
    test_cache_connection || exit 1
    
    echo ""
    echo "🎉 所有配置验证通过！"
}

main "$@"
```

---

## 📞 技术支持

如需配置帮助，请联系：
- **GitHub Issues**: https://github.com/TradeMaster-NTU/TradeMaster/issues
- **邮件支持**: TradeMaster.NTU@gmail.com
- **文档问题**: 请在相应文档页面反馈

---

## 📄 版本信息

**文档版本**: v2.0.0  
**最后更新**: 2025年8月15日  
**适用版本**: TradeMaster Docker v1.0+  
**维护团队**: TradeMaster Development Team