# TradeMaster Docker 部署最佳实践指南

<div align="center">
    <h2>🏆 生产级部署最佳实践</h2>
    <p>企业级部署标准与运维指南</p>
</div>

---

## 📋 目录

- [🏗️ 架构设计最佳实践](#架构设计最佳实践)
- [🔒 安全性最佳实践](#安全性最佳实践)
- [⚡ 性能优化最佳实践](#性能优化最佳实践)
- [📊 监控和日志最佳实践](#监控和日志最佳实践)
- [🔄 CI/CD最佳实践](#cicd最佳实践)
- [💾 数据管理最佳实践](#数据管理最佳实践)
- [🧪 测试策略最佳实践](#测试策略最佳实践)
- [🔧 运维管理最佳实践](#运维管理最佳实践)
- [📈 扩展性最佳实践](#扩展性最佳实践)
- [⚠️ 风险管理最佳实践](#风险管理最佳实践)

---

## 🏗️ 架构设计最佳实践

### 🎯 容器化设计原则

#### 1. 单一职责原则
```yaml
# 推荐: 服务分离架构
version: '3.8'
services:
  trademaster-app:
    build: .
    environment:
      - ROLE=application
    depends_on:
      - trademaster-db
      - trademaster-cache
      
  trademaster-worker:
    build: .
    environment:
      - ROLE=worker
    depends_on:
      - trademaster-db
      - trademaster-cache
      
  trademaster-db:
    image: postgres:13
    environment:
      - POSTGRES_DB=trademaster
      
  trademaster-cache:
    image: redis:alpine
```

#### 2. 配置外部化
```dockerfile
# Dockerfile最佳实践
FROM ubuntu:20.04

# 使用ARG进行构建时配置
ARG PYTHON_VERSION=3.8.10
ARG PYTORCH_VERSION=1.12.1

# 使用ENV进行运行时配置
ENV PYTHONPATH="/home/TradeMaster"
ENV WORKERS=4
ENV LOG_LEVEL=INFO

# 配置文件挂载点
VOLUME ["/app/config"]

# 使用非root用户
RUN useradd -m -u 1000 trademaster
USER trademaster

ENTRYPOINT ["/entrypoint.sh"]
```

#### 3. 多阶段构建优化
```dockerfile
# 多阶段构建示例
# 阶段1: 构建环境
FROM ubuntu:20.04 AS builder

RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    cmake

COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 阶段2: 运行环境
FROM ubuntu:20.04 AS runtime

COPY --from=builder /root/.local /root/.local
COPY . /app

# 确保用户bin在PATH中
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app
CMD ["python3", "main.py"]
```

### 🌐 网络架构设计

#### 1. 网络隔离策略
```bash
# 创建专用网络
docker network create \
  --driver bridge \
  --subnet=172.20.0.0/16 \
  --gateway=172.20.0.1 \
  trademaster-net

# 前端网络（对外暴露）
docker network create \
  --driver bridge \
  --subnet=172.21.0.0/16 \
  trademaster-frontend

# 后端网络（内部通信）
docker network create \
  --driver bridge \
  --subnet=172.22.0.0/16 \
  trademaster-backend
```

#### 2. 负载均衡配置
```nginx
# nginx.conf - 生产级配置
upstream trademaster_app {
    least_conn;
    server trademaster-app-1:8080 weight=3 max_fails=3 fail_timeout=30s;
    server trademaster-app-2:8080 weight=3 max_fails=3 fail_timeout=30s;
    server trademaster-app-3:8080 weight=2 max_fails=3 fail_timeout=30s backup;
}

server {
    listen 80;
    server_name trademaster.company.com;
    
    # 安全头设置
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # 请求限制
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://trademaster_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 健康检查端点
    location /health {
        access_log off;
        proxy_pass http://trademaster_app/health;
    }
    
    # 静态文件优化
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 💾 存储架构设计

#### 1. 数据卷管理策略
```yaml
# docker-compose.production.yml
version: '3.8'
services:
  trademaster-app:
    image: trademaster:latest
    volumes:
      # 配置只读挂载
      - ./config:/app/config:ro
      # 数据读写挂载
      - trademaster-data:/app/data
      # 日志挂载
      - trademaster-logs:/app/logs
      # 临时文件挂载
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 100M

volumes:
  trademaster-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/trademaster/data
      
  trademaster-logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/log/trademaster
```

#### 2. 备份策略设计
```bash
#!/bin/bash
# backup_strategy.sh

# 3-2-1备份策略实施
# 3个副本，2种不同媒介，1个异地备份

BACKUP_ROOT="/opt/backups/trademaster"
LOCAL_BACKUP="$BACKUP_ROOT/local"
REMOTE_BACKUP="$BACKUP_ROOT/remote"
OFFSITE_BACKUP="s3://company-backups/trademaster"

# 本地备份（每日）
create_local_backup() {
    local date=$(date +%Y%m%d)
    local backup_dir="$LOCAL_BACKUP/$date"
    
    mkdir -p "$backup_dir"
    
    # 应用数据备份
    docker exec trademaster-app tar czf - /app/data | \
        gzip > "$backup_dir/app_data.tar.gz"
    
    # 数据库备份
    docker exec trademaster-db pg_dump -U trademaster trademaster | \
        gzip > "$backup_dir/database.sql.gz"
    
    # 配置备份
    tar czf "$backup_dir/config.tar.gz" /opt/trademaster/config/
    
    # 验证备份完整性
    verify_backup "$backup_dir"
}

# 远程备份（每周）
create_remote_backup() {
    local week=$(date +%Y%U)
    local backup_dir="$REMOTE_BACKUP/$week"
    
    # 同步到远程NAS
    rsync -avz --delete "$LOCAL_BACKUP/" "$backup_dir/"
}

# 异地备份（每月）
create_offsite_backup() {
    local month=$(date +%Y%m)
    
    # 上传到云存储
    aws s3 sync "$LOCAL_BACKUP/" "$OFFSITE_BACKUP/$month/" \
        --storage-class GLACIER
}

# 备份验证
verify_backup() {
    local backup_dir="$1"
    
    # 检查文件完整性
    for file in "$backup_dir"/*.gz; do
        if ! gzip -t "$file"; then
            echo "错误: 备份文件损坏 - $file"
            return 1
        fi
    done
    
    echo "备份验证通过: $backup_dir"
}

# 备份清理策略
cleanup_old_backups() {
    # 保留本地备份30天
    find "$LOCAL_BACKUP" -type d -mtime +30 -exec rm -rf {} +
    
    # 保留远程备份12周
    find "$REMOTE_BACKUP" -type d -mtime +84 -exec rm -rf {} +
}
```

---

## 🔒 安全性最佳实践

### 🛡️ 容器安全加固

#### 1. 最小权限原则
```bash
# 安全的容器启动配置
docker run -d \
  --name trademaster-secure \
  # 非特权模式
  --user 1000:1000 \
  --security-opt no-new-privileges:true \
  # 只读根文件系统
  --read-only \
  # 临时文件系统
  --tmpfs /tmp:rw,size=100m,noexec,nosuid,nodev \
  --tmpfs /var/tmp:rw,size=50m,noexec,nosuid,nodev \
  # 能力限制
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  # 资源限制
  --memory="8g" \
  --memory-swap="8g" \
  --cpus="4" \
  --pids-limit=1000 \
  # 网络隔离
  --network trademaster-secure \
  trademaster:latest
```

#### 2. 秘密管理
```yaml
# docker-compose.secrets.yml
version: '3.8'
services:
  trademaster-app:
    image: trademaster:latest
    secrets:
      - db_password
      - api_key
      - ssl_cert
    environment:
      # 从秘密文件读取
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - API_KEY_FILE=/run/secrets/api_key
    deploy:
      replicas: 3

secrets:
  db_password:
    external: true
    name: trademaster_db_password
  api_key:
    external: true  
    name: trademaster_api_key
  ssl_cert:
    file: ./ssl/trademaster.crt
```

#### 3. 镜像安全扫描
```bash
#!/bin/bash
# security_scan.sh

echo "开始镜像安全扫描..."

# 使用Trivy扫描漏洞
trivy image --severity HIGH,CRITICAL trademaster:latest

# 使用Clair扫描
clair-scanner --ip $(hostname -I | awk '{print $1}') trademaster:latest

# 使用Docker Scout扫描
docker scout cves trademaster:latest

# 使用Snyk扫描
snyk container test trademaster:latest

echo "安全扫描完成，请查看报告"
```

### 🔐 网络安全

#### 1. TLS/SSL配置
```nginx
# SSL最佳实践配置
server {
    listen 443 ssl http2;
    server_name trademaster.company.com;
    
    # SSL证书
    ssl_certificate /etc/ssl/certs/trademaster.crt;
    ssl_certificate_key /etc/ssl/private/trademaster.key;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/certs/ca-certificates.crt;
    
    # 其他安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
}
```

#### 2. 防火墙配置
```bash
#!/bin/bash
# firewall_setup.sh

# UFW防火墙配置
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# SSH访问
ufw allow 22/tcp

# HTTP/HTTPS访问
ufw allow 80/tcp
ufw allow 443/tcp

# Docker内部通信
ufw allow from 172.20.0.0/16
ufw allow from 172.21.0.0/16
ufw allow from 172.22.0.0/16

# 监控服务
ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus
ufw allow from 10.0.0.0/8 to any port 3000  # Grafana

# 启用防火墙
ufw --force enable

echo "防火墙配置完成"
```

### 🔍 审计和合规

#### 1. 审计日志配置
```yaml
# docker-compose.audit.yml
version: '3.8'
services:
  trademaster-app:
    image: trademaster:latest
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://localhost:514"
        tag: "trademaster-app"
        syslog-format: "rfc5424micro"
    
  auditd:
    image: linuxserver/auditd
    volumes:
      - /var/log/audit:/var/log/audit
      - ./audit-rules:/etc/audit/rules.d
    privileged: true
    
  log-aggregator:
    image: fluentd:latest
    ports:
      - "24224:24224"
    volumes:
      - ./fluentd.conf:/fluentd/etc/fluent.conf
      - /var/log:/var/log
```

#### 2. 合规性检查
```python
# compliance_checker.py
import docker
import json
import sys
from datetime import datetime

class ComplianceChecker:
    def __init__(self):
        self.client = docker.from_env()
        self.violations = []
        
    def check_container_security(self, container_name):
        """检查容器安全配置"""
        try:
            container = self.client.containers.get(container_name)
            config = container.attrs
            
            # 检查特权模式
            if config['HostConfig']['Privileged']:
                self.violations.append({
                    'type': 'security',
                    'severity': 'high',
                    'message': '容器运行在特权模式',
                    'container': container_name
                })
            
            # 检查用户权限
            if config['Config']['User'] == '' or config['Config']['User'] == 'root':
                self.violations.append({
                    'type': 'security',
                    'severity': 'medium',
                    'message': '容器以root用户运行',
                    'container': container_name
                })
            
            # 检查只读根文件系统
            if not config['HostConfig']['ReadonlyRootfs']:
                self.violations.append({
                    'type': 'security',
                    'severity': 'medium',
                    'message': '根文件系统不是只读',
                    'container': container_name
                })
            
            # 检查资源限制
            if not config['HostConfig']['Memory']:
                self.violations.append({
                    'type': 'resource',
                    'severity': 'low',
                    'message': '未设置内存限制',
                    'container': container_name
                })
                
        except Exception as e:
            print(f"检查容器 {container_name} 时出错: {e}")
    
    def check_image_security(self, image_name):
        """检查镜像安全"""
        try:
            image = self.client.images.get(image_name)
            
            # 检查镜像标签
            if not image.tags or 'latest' in image.tags[0]:
                self.violations.append({
                    'type': 'security',
                    'severity': 'medium',
                    'message': '使用了latest标签或无标签镜像',
                    'image': image_name
                })
            
            # 检查镜像大小
            size_mb = image.attrs['Size'] / (1024 * 1024)
            if size_mb > 1000:  # 大于1GB
                self.violations.append({
                    'type': 'performance',
                    'severity': 'low',
                    'message': f'镜像过大: {size_mb:.1f}MB',
                    'image': image_name
                })
                
        except Exception as e:
            print(f"检查镜像 {image_name} 时出错: {e}")
    
    def generate_report(self):
        """生成合规性报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_violations': len(self.violations),
            'violations_by_severity': {
                'high': len([v for v in self.violations if v['severity'] == 'high']),
                'medium': len([v for v in self.violations if v['severity'] == 'medium']),
                'low': len([v for v in self.violations if v['severity'] == 'low'])
            },
            'violations': self.violations
        }
        
        return report
    
    def run_compliance_check(self, container_name, image_name):
        """运行完整合规性检查"""
        print("开始合规性检查...")
        
        self.check_container_security(container_name)
        self.check_image_security(image_name)
        
        report = self.generate_report()
        
        # 保存报告
        with open('/app/data/compliance_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # 打印摘要
        print(f"合规性检查完成:")
        print(f"  总违规项: {report['total_violations']}")
        print(f"  高危: {report['violations_by_severity']['high']}")
        print(f"  中危: {report['violations_by_severity']['medium']}")
        print(f"  低危: {report['violations_by_severity']['low']}")
        
        return report['violations_by_severity']['high'] == 0

if __name__ == "__main__":
    checker = ComplianceChecker()
    is_compliant = checker.run_compliance_check("trademaster-container", "trademaster:latest")
    sys.exit(0 if is_compliant else 1)
```

---

## ⚡ 性能优化最佳实践

### 🚀 容器性能优化

#### 1. 资源配置优化
```yaml
# docker-compose.performance.yml
version: '3.8'
services:
  trademaster-app:
    image: trademaster:latest
    deploy:
      resources:
        limits:
          # CPU限制 - 使用小数表示核心数
          cpus: '4.0'
          # 内存限制
          memory: 16G
          # 设备限制
          devices:
            - /dev/nvidia0:/dev/nvidia0  # GPU支持
        reservations:
          # 预留资源
          cpus: '2.0'
          memory: 8G
    
    # 系统优化
    sysctls:
      # 网络优化
      net.core.rmem_max: 134217728
      net.core.wmem_max: 134217728
      net.ipv4.tcp_rmem: "4096 87380 134217728"
      net.ipv4.tcp_wmem: "4096 65536 134217728"
      # 内存优化
      vm.swappiness: 10
      vm.dirty_ratio: 15
    
    # 环境优化
    environment:
      # Python优化
      - PYTHONOPTIMIZE=1
      - PYTHONUNBUFFERED=1
      # NumPy/SciPy优化
      - OMP_NUM_THREADS=4
      - MKL_NUM_THREADS=4
      - OPENBLAS_NUM_THREADS=4
      # PyTorch优化
      - TORCH_HOME=/app/cache/torch
```

#### 2. 镜像优化策略
```dockerfile
# 优化的Dockerfile
FROM ubuntu:20.04 as base

# 使用国内镜像源
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list

# 一次性安装，减少层数
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3=3.8.10-0ubuntu1~20.04 \
    python3-pip=20.0.2-5ubuntu1 \
    python3-dev=3.8.2-0ubuntu2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python包缓存优化
FROM base as python-deps
COPY requirements-docker.txt /tmp/
RUN pip3 install --no-cache-dir --user -r /tmp/requirements-docker.txt

# 应用层
FROM base as app
COPY --from=python-deps /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 应用代码
COPY . /app
WORKDIR /app

# 非root用户
RUN useradd -m -u 1000 trademaster && \
    chown -R trademaster:trademaster /app
USER trademaster

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
```

#### 3. 缓存策略
```python
# caching_strategy.py
import redis
import json
import hashlib
import pickle
from functools import wraps
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=False
        )
        
    def cache_result(self, ttl=3600, key_prefix="tm"):
        """结果缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(
                    func.__name__, args, kwargs, key_prefix
                )
                
                # 尝试从缓存获取
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    return pickle.loads(cached_result)
                
                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.redis_client.setex(
                    cache_key, ttl, pickle.dumps(result)
                )
                
                return result
            return wrapper
        return decorator
    
    def cache_dataframe(self, df, key, ttl=1800):
        """DataFrame缓存"""
        # 压缩存储
        compressed_df = df.to_pickle(compression='gzip')
        self.redis_client.setex(key, ttl, compressed_df)
    
    def get_cached_dataframe(self, key):
        """获取缓存的DataFrame"""
        import pandas as pd
        cached_data = self.redis_client.get(key)
        if cached_data:
            return pd.read_pickle(
                io.BytesIO(cached_data), 
                compression='gzip'
            )
        return None
    
    def _generate_cache_key(self, func_name, args, kwargs, prefix):
        """生成缓存键"""
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{func_name}:{key_hash}"
    
    def warm_up_cache(self):
        """缓存预热"""
        print("开始缓存预热...")
        
        # 预加载常用数据
        common_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        for symbol in common_symbols:
            # 预加载股票数据
            self._preload_stock_data(symbol)
        
        print("缓存预热完成")
    
    def _preload_stock_data(self, symbol):
        """预加载股票数据"""
        # 实现预加载逻辑
        pass

# 使用示例
cache_manager = CacheManager()

@cache_manager.cache_result(ttl=3600)
def expensive_calculation(param1, param2):
    """耗时计算函数"""
    import time
    time.sleep(2)  # 模拟耗时操作
    return param1 * param2

# 预热缓存
cache_manager.warm_up_cache()
```

### 💾 数据库性能优化

#### 1. PostgreSQL优化配置
```sql
-- postgresql.conf 优化配置
-- 内存配置
shared_buffers = 4GB                    -- 25% of total RAM
effective_cache_size = 12GB             -- 75% of total RAM
work_mem = 256MB                        -- For complex queries
maintenance_work_mem = 1GB              -- For maintenance operations

-- 写入优化
wal_buffers = 64MB
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min
max_wal_size = 4GB
min_wal_size = 1GB

-- 连接优化
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

-- 查询优化
random_page_cost = 1.1                  -- For SSD
effective_io_concurrency = 200          -- For SSD
```

#### 2. 数据库连接池
```python
# db_pool.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import threading
import time

class DatabaseManager:
    def __init__(self, db_url, pool_size=20, max_overflow=30):
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1小时回收连接
            echo=False
        )
        self._local = threading.local()
    
    def get_connection(self):
        """获取数据库连接"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = self.engine.connect()
        return self._local.connection
    
    def execute_query(self, query, params=None):
        """执行查询"""
        conn = self.get_connection()
        try:
            result = conn.execute(query, params or {})
            return result.fetchall()
        except Exception as e:
            conn.rollback()
            raise e
    
    def close_connection(self):
        """关闭连接"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')

# 单例模式
db_manager = None

def get_db_manager():
    global db_manager
现在创建部署最佳实践和维护指南：

<write_to_file>
<path>docs/BEST_PRACTICES_GUIDE.md</path>
<content># TradeMaster Docker 部署最佳实践指南

<div align="center">
    <h2>🏆 生产级部署最佳实践</h2>
    <p>从开发到生产的完整最佳实践指南</p>
</div>

---

## 📋 目录

- [🏗️ 架构设计最佳实践](#架构设计最佳实践)
- [🔒 安全配置最佳实践](#安全配置最佳实践)
- [⚡ 性能优化最佳实践](#性能优化最佳实践)
- [📊 监控和日志最佳实践](#监控和日志最佳实践)
- [🔄 CI/CD最佳实践](#cicd最佳实践)
- [💾 数据管理最佳实践](#数据管理最佳实践)
- [🛠️ 运维管理最佳实践](#运维管理最佳实践)
- [🌐 多环境部署最佳实践](#多环境部署最佳实践)

---

## 🏗️ 架构设计最佳实践

### 🎯 容器化架构原则

#### 单一职责原则
```yaml
# 推荐：按功能分离服务
services:
  trademaster-web:
    image: trademaster:web
    ports: ["8080:8080"]
    
  trademaster-api:
    image: trademaster:api
    ports: ["5000:5000"]
    
  trademaster-worker:
    image: trademaster:worker
    deploy:
      replicas: 3

# 避免：单容器承担所有功能
```

#### 无状态设计
```bash
# 正确：使用外部存储
docker run -d \
  --name trademaster-app \
  -v /shared/data:/app/data \
  -e DATABASE_URL=postgresql://host/db \
  -e REDIS_URL=redis://host:6379 \
  trademaster:latest

# 错误：在容器内存储状态
docker run -d \
  --name trademaster-app \
  trademaster:latest
# （数据会在容器重启时丢失）
```

### 🔧 多层架构设计

#### 三层架构实现
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # 前端层
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on: [trademaster-web]
    networks: [frontend]

  # 应用层
  trademaster-web:
    image: trademaster:latest
    deploy:
      replicas: 3
      resources:
        limits: {memory: 4G, cpus: '2'}
        reservations: {memory: 2G, cpus: '1'}
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    networks: [frontend, backend]
    depends_on: [postgres, redis]

  # 数据层
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: trademaster
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks: [backend]

  redis:
    image: redis:alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks: [backend]

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

volumes:
  postgres_data:
  redis_data:
```

### 📦 镜像构建最佳实践

#### 多阶段构建
```dockerfile
# Dockerfile.optimized
# 构建阶段
FROM python:3.8-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

COPY . .
RUN python setup.py build

# 运行阶段
FROM python:3.8-slim as runtime

# 创建非root用户
RUN groupadd -r trademaster && useradd -r -g trademaster trademaster

# 复制构建产物
COPY --from=builder /root/.local /home/trademaster/.local
COPY --from=builder /build/dist /app

# 设置权限
RUN chown -R trademaster:trademaster /app
USER trademaster

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

WORKDIR /app
CMD ["python", "-m", "trademaster.server"]
```

#### 镜像优化策略
```bash
#!/bin/bash
# image_optimization.sh

echo "Docker镜像优化脚本"

# 1. 清理未使用的镜像
docker image prune -f

# 2. 多架构构建
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag trademaster:multi-arch \
  --push .

# 3. 镜像安全扫描
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image trademaster:latest

# 4. 镜像体积分析
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest trademaster:latest
```

---

## 🔒 安全配置最佳实践

### 🛡️ 容器安全加固

#### 最小权限原则
```bash
# 生产环境安全启动
docker run -d \
  --name trademaster-secure \
  --user 1000:1000 \
  --security-opt no-new-privileges:true \
  --security-opt apparmor:docker-default \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --read-only \
  --tmpfs /tmp:rw,size=100m,noexec,nosuid,nodev \
  --tmpfs /var/tmp:rw,size=50m,noexec,nosuid,nodev \
  -p 8080:8080 \
  -v /opt/trademaster/data:/app/data:rw \
  -v /opt/trademaster/config:/app/config:ro \
  --restart unless-stopped \
  --memory="4g" \
  --cpus="2.0" \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  trademaster:latest
```

#### 网络安全配置
```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  trademaster:
    image: trademaster:latest
    networks:
      - internal
      - external
    ports:
      - "127.0.0.1:8080:8080"  # 只绑定到本地接口

  nginx:
    image: nginx:alpine
    networks:
      - external
    ports:
      - "80:80"
      - "443:443"
    configs:
      - source: nginx_config
        target: /etc/nginx/nginx.conf

networks:
  external:
    driver: bridge
  internal:
    driver: bridge
    internal: true  # 内部网络，无外网访问

configs:
  nginx_config:
    file: ./nginx/secure.conf
```

### 🔐 机密信息管理

#### Docker Secrets 配置
```yaml
# docker-compose.secrets.yml
version: '3.8'

services:
  trademaster:
    image: trademaster:latest
    secrets:
      - db_password
      - api_key
      - ssl_cert
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
      - API_KEY_FILE=/run/secrets/api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true
  ssl_cert:
    file: ./secrets/ssl_cert.pem
```

#### 环境变量最佳实践
```bash
# .env.production
# 使用强密码
DATABASE_PASSWORD=$(openssl rand -base64 32)
API_SECRET_KEY=$(openssl rand -hex 64)
JWT_SECRET=$(openssl rand -base64 32)

# 限制数据库连接
DATABASE_MAX_CONNECTIONS=20
DATABASE_CONNECTION_TIMEOUT=30

# 启用安全特性
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true

# 日志安全配置
LOG_LEVEL=INFO
LOG_SANITIZE_SECRETS=true
```

### 🔍 安全监控

#### 容器运行时安全监控
```python
# security_monitor.py
import docker
import psutil
import logging
from datetime import datetime, timedelta

class SecurityMonitor:
    def __init__(self):
        self.client = docker.from_env()
        self.logger = logging.getLogger(__name__)
        
    def monitor_container_security(self, container_name):
        """监控容器安全状态"""
        try:
            container = self.client.containers.get(container_name)
            
            # 检查容器配置
            config_issues = self.check_container_config(container)
            
            # 检查运行时状态
            runtime_issues = self.check_runtime_security(container)
            
            # 生成安全报告
            self.generate_security_report(container_name, config_issues, runtime_issues)
            
        except docker.errors.NotFound:
            self.logger.error(f"容器 {container_name} 未找到")
    
    def check_container_config(self, container):
        """检查容器配置安全性"""
        issues = []
        
        # 检查是否以root用户运行
        if container.attrs['Config']['User'] == '' or container.attrs['Config']['User'] == 'root':
            issues.append("容器以root用户运行")
        
        # 检查是否启用特权模式
        if container.attrs['HostConfig']['Privileged']:
            issues.append("容器启用了特权模式")
        
        # 检查端口绑定
        port_bindings = container.attrs['HostConfig']['PortBindings']
        for port, bindings in (port_bindings or {}).items():
            for binding in bindings:
                if binding['HostIp'] == '' or binding['HostIp'] == '0.0.0.0':
                    issues.append(f"端口 {port} 绑定到所有接口")
        
        # 检查卷挂载
        mounts = container.attrs['Mounts']
        for mount in mounts:
            if mount['Source'].startswith('/'):
                if mount['Mode'] == 'rw' and mount['Source'] in ['/etc', '/var', '/usr']:
                    issues.append(f"敏感目录 {mount['Source']} 以读写模式挂载")
        
        return issues
    
    def check_runtime_security(self, container):
        """检查运行时安全状态"""
        issues = []
        
        # 检查进程列表
        try:
            processes = container.top()['Processes']
            
            # 检查异常进程
            suspicious_processes = []
            for process in processes:
                cmd = ' '.join(process[7:]) if len(process) > 7 else ''
                
                # 检查是否有shell进程
                if any(shell in cmd.lower() for shell in ['bash', 'sh', 'zsh', 'fish']):
                    suspicious_processes.append(cmd)
                
                # 检查网络工具
                if any(tool in cmd.lower() for tool in ['nc', 'netcat', 'wget', 'curl']):
                    suspicious_processes.append(cmd)
            
            if suspicious_processes:
                issues.append(f"发现可疑进程: {suspicious_processes}")
                
        except Exception as e:
            self.logger.warning(f"无法检查进程列表: {e}")
        
        return issues
    
    def generate_security_report(self, container_name, config_issues, runtime_issues):
        """生成安全报告"""
        report = {
            'container': container_name,
            'timestamp': datetime.now().isoformat(),
            'config_issues': config_issues,
            'runtime_issues': runtime_issues,
            'risk_level': self.calculate_risk_level(config_issues, runtime_issues)
        }
        
        # 保存报告
        with open(f'/var/log/security_report_{container_name}.json', 'w') as f:
            import json
            json.dump(report, f, indent=2)
        
        # 发送告警
        if report['risk_level'] == 'HIGH':
            self.send_security_alert(report)
    
    def calculate_risk_level(self, config_issues, runtime_issues):
        """计算风险等级"""
        total_issues = len(config_issues) + len(runtime_issues)
        
        high_risk_keywords = ['root', '特权', '0.0.0.0', '/etc', 'shell']
        high_risk_count = sum(1 for issue in config_issues + runtime_issues 
                             if any(keyword in issue.lower() for keyword in high_risk_keywords))
        
        if high_risk_count > 0 or total_issues > 5:
            return 'HIGH'
        elif total_issues > 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def send_security_alert(self, report):
        """发送安全告警"""
        # 这里可以集成邮件、Slack、微信等告警渠道
        self.logger.critical(f"安全告警: 容器 {report['container']} 存在高风险安全问题")

# 使用示例
if __name__ == "__main__":
    monitor = SecurityMonitor()
    monitor.monitor_container_security('trademaster-container')
```

---

## ⚡ 性能优化最佳实践

### 🚀 容器性能优化

#### 资源配置最佳实践
```yaml
# docker-compose.performance.yml
version: '3.8'

services:
  trademaster:
    image: trademaster:latest
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'
      restart_policy:
        condition: unless-stopped
        delay: 5s
        max_attempts: 3
        window: 120s
    
    # 性能优化配置
    environment:
      - PYTHONOPTIMIZE=1
      - PYTHONUNBUFFERED=1
      - OMP_NUM_THREADS=4
      - MKL_NUM_THREADS=4
      - NUMEXPR_NUM_THREADS=4
    
    # 使用高性能存储
    volumes:
      - type: volume
        source: trademaster_data
        target: /app/data
        volume:
          driver: local
          driver_opts:
            type: tmpfs
            device: tmpfs
            o: size=2g,uid=1000
    
    # 网络优化
    networks:
      - trademaster_net
    
    # 日志优化
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "3"

networks:
  trademaster_net:
    driver: bridge
    driver_opts:
      com.docker.network.driver.mtu: 9000  # Jumbo frames

volumes:
  trademaster_data:
    driver: local
    driver_opts:
      type: none
      device: /opt/ssd/trademaster
      o: bind
```

#### CPU和内存优化
```python
# performance_optimizer.py
import os
import psutil
import torch
import numpy as np
from multiprocessing import cpu_count

class PerformanceOptimizer:
    def __init__(self):
        self.cpu_count = cpu_count()
        self.memory_total = psutil.virtual_memory().total
        
    def optimize_environment(self):
        """优化运行环境"""
        # CPU优化
        self.optimize_cpu()
        
        # 内存优化
        self.optimize_memory()
        
        # PyTorch优化
        self.optimize_pytorch()
        
        # NumPy优化
        self.optimize_numpy()
    
    def optimize_cpu(self):
        """CPU优化配置"""
        # 设置CPU亲和性
        if hasattr(os, 'sched_setaffinity'):
            # 绑定到性能核心
            performance_cpus = list(range(min(4, self.cpu_count)))
            os.sched_setaffinity(0, performance_cpus)
            print(f"CPU亲和性设置到核心: {performance_cpus}")
        
        # 设置线程数
        optimal_threads = min(4, self.cpu_count)
        os.environ['OMP_NUM_THREADS'] = str(optimal_threads)
        os.environ['MKL_NUM_THREADS'] = str(optimal_threads)
        os.environ['NUMEXPR_NUM_THREADS'] = str(optimal_threads)
        
        print(f"线程数设置为: {optimal_threads}")
    
    def optimize_memory(self):
        """内存优化配置"""
        # 设置内存映射阈值
        if self.memory_total > 8 * 1024**3:  # 8GB+
            os.environ['MALLOC_MMAP_THRESHOLD_'] = '131072'
            os.environ['MALLOC_TRIM_THRESHOLD_'] = '524288'
        
        # Python内存优化
        import gc
        gc.set_threshold(700, 10, 10)  # 调整垃圾回收阈值
        
        print("内存优化配置完成")
    
    def optimize_pytorch(self):
        """PyTorch性能优化"""
        if torch.cuda.is_available():
            # GPU优化
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.enabled = True
            
            # 设置内存池
            torch.cuda.set_per_process_memory_fraction(0.8)
            
            print("PyTorch GPU优化完成")
        else:
            # CPU优化
            torch.set_num_threads(min(4, self.cpu_count))
            torch.set_num_interop_threads(min(2, self.cpu_count // 2))
            
            print("PyTorch CPU优化完成")
    
    def optimize_numpy(self):
        """NumPy性能优化"""
        # 设置BLAS线程数
        os.environ['OPENBLAS_NUM_THREADS'] = str(min(4, self.cpu_count))
        os.environ['VECLIB_MAXIMUM_THREADS'] = str(min(4, self.cpu_count))
        
        # 启用多线程
        np.seterr(all='raise')  # 严格错误处理
        
        print("NumPy优化完成")
    
    def benchmark_performance(self):
        """性能基准测试"""
        print("开始性能基准测试...")
        
        # CPU基准测试
        cpu_score = self.cpu_benchmark()
        
        # 内存基准测试
        memory_score = self.memory_benchmark()
        
        # 深度学习基准测试
        dl_score = self.deep_learning_benchmark()
        
        # 综合评分
        overall_score = (cpu_score + memory_score + dl_score) / 3
        
        report = {
            'cpu_score': cpu_score,
            'memory_score': memory_score,
            'deep_learning_score': dl_score,
            'overall_score': overall_score,
            'performance_grade': self.get_performance_grade(overall_score)
        }
        
        return report
    
    def cpu_benchmark(self):
        """CPU基准测试"""
        import time
        
        start_time = time.time()
        
        # 矩阵乘法测试
        a = np.random.rand(1000, 1000)
        b = np.random.rand(1000, 1000)
        c = np.dot(a, b)
        
        cpu_time = time.time() - start_time
        
        # 评分（秒转换为分数，越快分数越高）
        cpu_score = max(0, 100 - cpu_time * 20)
        
        print(f"CPU基准测试: {cpu_time:.3f}秒, 评分: {cpu_score:.1f}")
        return cpu_score
    
    def memory_benchmark(self):
        """内存基准测试"""
        import time
        
        start_time = time.time()
        
        # 大数组分配和操作
        arrays = []
        for i in range(10):
            arr = np.random.rand(5000, 1000)
            arrays.append(arr * 2 + 1)
        
        # 清理
        del arrays
        import gc
        gc.collect()
        
        memory_time = time.time() - start_time
        memory_score = max(0, 100 - memory_time * 10)
        
        print(f"内存基准测试: {memory_time:.3f}秒, 评分: {memory_score:.1f}")
        return memory_score
    
    def deep_learning_benchmark(self):
        """深度学习基准测试"""
        import time
        
        start_time = time.time()
        
        # PyTorch基准测试
        if torch.cuda.is_available():
            device = torch.device('cuda')
            x = torch.randn(1000, 1000, device=device)
            y = torch.randn(1000, 1000, device=device)
            z = torch.mm(x, y)
            torch.cuda.synchronize()
        else:
            x = torch.randn(1000, 1000)
            y = torch.randn(1000, 1000)
            z = torch.mm(x, y)
        
        dl_time = time.time() - start_time
        dl_score = max(0, 100 - dl_time * 30)
        
        print(f"深度学习基准测试: {dl_time:.3f}秒, 评分: {dl_score:.1f}")
        return dl_score
    
    def get_performance_grade(self, score):
        """获取性能等级"""
        if score >= 90:
            return 'A+ (优秀)'
        elif score >= 80:
            return 'A (良好)'
        elif score >= 70:
            return 'B+ (中等偏上)'
        elif score >= 60:
            return 'B (中等)'
        elif score >= 50:
            return 'C (一般)'
        else:
            return 'D (需要优化)'

# 容器启动时自动优化
def auto_optimize():
    """自动性能优化"""
    optimizer = PerformanceOptimizer()
    optimizer.optimize_environment()
    
    # 运行基准测试
    results = optimizer.benchmark_performance()
    
    print(f"\n性能优化完成!")
    print(f"综合评分: {results['overall_score']:.1f}")
    print(f"性能等级: {results['performance_grade']}")
    
    return results

if __name__ == "__main__":
    auto_optimize()
```

### 📊 存储优化

#### 数据卷性能优化
```bash
#!/bin/bash
# storage_optimization.sh

echo "存储性能优化配置..."

# 1. 创建高性能数据卷
docker volume create \
  --driver local \
  --opt type=tmpfs \
  --opt device=tmpfs \
  --opt o=size=4g,uid=1000 \
  trademaster-cache

# 2. 使用SSD存储
docker volume create \
  --driver local \
  --opt type=none \
  --opt device=/opt/ssd/trademaster \
  --opt o=bind \
  trademaster-data

# 3. 配置I/O调度器
echo "noop" > /sys/block/sda/queue/scheduler  # SSD优化
echo "deadline" > /sys/block/sdb/queue/scheduler  # HDD优化

# 4. 优化文件系统参数
mount -o remount,noatime,nodiratime /opt/ssd

echo "存储优化完成"
```

#### 数据库连接优化
```python
# database_optimizer.py
import asyncio
import asyncpg
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class DatabaseOptimizer:
    def __init__(self):
        self.connection_pools = {}
    
    def create_optimized_engine(self, database_url):
        """创建优化的数据库引擎"""
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,                    # 连接池大小
            max_overflow=30,                 # 最大溢出连接
            pool_pre_ping=True,              # 连接预检
            pool_recycle=3600,               # 连接回收时间（秒）
            pool_timeout=30,                 # 获取连接超时
            echo=False,                      # 生产环境关闭SQL日志
            execution_options={
                'isolation_level': 'READ_COMMITTED',
                'autocommit': False
            }
        )
        
        return engine
    
    async def create_async_pool(self, database_url):
        """创建异步连接池"""
        pool = await asyncpg.create_pool(
            database_url,
            min_size=10,                     # 最小连接数
            max_size=50,                     # 最大连接数
            max_queries=50000,               # 每连接最大查询数
            max_inactive_connection_lifetime=300,  # 非活跃连接生命周期
            command_timeout=60,              # 命令超时
            server_settings={
                'jit': 'off',                # 关闭JIT编译
                'application_name': 'trademaster'
            }
        )
        
        return pool
    
    def optimize_queries(self):
        """查询优化建议"""
        optimizations = [
            "使用索引优化查询",
            "避免SELECT *，只查询需要的字段",
            "使用LIMIT限制结果集大小",
            "使用批量操作减少数据库往返",
            "实现查询结果缓存",
            "使用连接池复用连接",
            "定期分析查询执行计划"
        ]
        
        return optimizations
```

---

## 📊 监控和日志最佳实践

### 📈 全栈监控方案

#### Prometheus + Grafana 监控栈
```yaml
# monitoring-stack.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.30.0
    container_name: prometheus
    ports: ["9090:9090"]
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks: [monitoring]

  grafana:
    image: grafana/grafana:8.2.0
    container_name: grafana
    ports: ["3000:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks: [monitoring]

  alertmanager:
    image: prom/alertmanager:v0.23.0
    container_name: alertmanager
    ports: ["9093:9093"]
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    networks: [monitoring]

  node-exporter:
    image: prom/node-exporter:v1.2.0
    container_name: node-exporter
    ports: ["9100:9100"]
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    networks: [monitoring]

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.40.0
    container_name: cadvisor
    ports: ["8081:8080"]
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    networks: [monitoring]

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
```

#### 自定义监控指标
```python
# custom_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import functools
import psutil
import threading

class TradeMasterMetrics:
    def __init__(self):
        # 业务指标
        self.trade_requests = Counter('trademaster_trade_requests_total', 
                                    'Total trade requests', ['method', 'status'])
        self.trade_latency = Histogram('trademaster_trade_duration_seconds',
                                     'Trade request latency')
        self.active_positions = Gauge('trademaster_active_positions',
                                    'Number of active positions')
        self.portfolio_value = Gauge('trademaster_portfolio_value',
                                   'Current portfolio value')
        
        # 系统指标
        self.memory_usage = Gauge('trademaster_memory_usage_bytes',
                                'Memory usage in bytes')
        self.cpu_usage = Gauge('trademaster_cpu_usage_percent',
                             'CPU usage percentage')
        self.disk_usage = Gauge('trademaster_disk_usage_percent',
                              'Disk usage percentage')
        
        # 模型指标
        self.model_predictions = Counter('trademaster_model_predictions_total',
                                       'Total model predictions', ['model', 'outcome'])
        self.model_accuracy = Gauge('trademaster_model_accuracy',
                                  'Model accuracy', ['model'])
        
        self.start_system_metrics_collection()
    
    def track_trade(self, method, status='success'):
        """跟踪交易请求"""
        self.trade_requests.labels(method=method, status=status).inc()
    
    def time_trade_execution(self, func):
        """交易执行时间装饰器"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.trade_latency.time():
                return func(*args, **kwargs)
        return wrapper
    
    def update_portfolio_metrics(self, positions, total_value):
        """更新投资组合指标"""
        self.active_positions.set(len(positions))
        self.portfolio_value.set(total_value)
    
    def track_model_prediction(self, model_name, prediction, actual=None):
        """跟踪模型预测"""
        if actual is not None:
            outcome = 'correct' if prediction == actual else 'incorrect'
            self.model_predictions.labels(model=model_name, outcome=outcome).inc()
    
    def update_model_accuracy(self, model_name, accuracy):
        """更新模型准确率"""
        self.model_accuracy.labels(model=model_name).set(accuracy)
    
    def start_system_metrics_collection(self):
        """启动系统指标收集"""
        def collect_system_metrics():
            while True:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.set(cpu_percent)
                
                # 内存使用
                memory = psutil.virtual_memory()
                self.memory_usage.set(memory.used)
                
                # 磁盘使用
                disk = psutil.disk_usage('/app/data')
                self.disk_usage.set(disk.percent)
                
                time.sleep(30)  # 每30秒收集一次
        
        collector_thread = threading.Thread(target=collect_system_metrics, daemon=True)
        collector_thread.start()
    
    def start_metrics_server(self, port=8000):
        """启动指标服务器"""
        start_http_server(port)
        print(f"Prometheus指标服务器启动在端口 {port}")

# 全局指标实例
metrics = TradeMasterMetrics()

# 使用示例
@metrics.time_trade_execution
def execute_trade(symbol, quantity):
    """执行交易"""
    try:
        # 交易逻辑
        result = perform_trade(symbol, quantity)
        metrics.track_trade('buy', 'success')
        return result
    except Exception as e:
        metrics.track_trade('buy', 'failed')
        raise e

def update_portfolio_status():
    """更新投资组合状态"""
    positions = get_current_positions()
    total_value = calculate_portfolio_value(positions)
    metrics.update_portfolio_metrics(positions, total_value)

# 启动指标服务器
if __name__ == "__main__":
    metrics.start_metrics_server(8000)
```

### 📝 结构化日志

#### 日志配置最佳实践
```python
# logging_config.py
import logging
import logging.handlers
import json
import time
from datetime import datetime
import traceback
import os

class StructuredLogger:
    def __init__(self, name, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self.setup_handlers()
    
    def setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = self.ColoredFormatter()
        console_handler.setFormatter(console_formatter)
        
        # 文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            '/app/logs/trademaster.log',
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = self.JSONFormatter()
        file_handler.setFormatter(file_formatter)
        
        # 错误文件处理器
        error_handler = logging.handlers.RotatingFileHandler(
            '/app/logs/trademaster_error.log',
            maxBytes=50*1024*1024,   # 50MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    class JSONFormatter(logging.Formatter):
        """JSON格式化器"""
        def format(self, record):
            log_entry = {
                'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'process_id': os.getpid(),
                'thread_id': record.thread
            }
            
            # 添加异常信息
            if record.exc_info:
                log_entry['exception'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                    'traceback': traceback.format_exception(*record.exc_info)
                }
            
            # 添加自定义字段
            if hasattr(record, 'extra_fields'):
                log_entry.update(record.extra_fields)
            
            return json.dumps(log_entry, ensure_ascii=False)
    
    class ColoredFormatter(logging.Formatter):
        """彩色控制台格式化器"""
        COLORS = {
            'DEBUG': '\033[36m',    # 青色
            'INFO': '\033[32m',     # 绿色
            'WARNING': '\033[33m',  # 黄色
            'ERROR': '\033[31m',    # 红色
            'CRITICAL': '\033[35m', # 紫色
        }
        RESET = '\033[0m'
        
        def format(self, record):
            color = self.COLORS.get(record.levelname, self.RESET)
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            return formatter.format(record)
    
    def log_with_context(self, level, message, **context):
        """带上下文的日志记录"""
        extra = {'extra_fields': context}
        self.logger.log(level, message, extra=extra)
    
    def log_trade_event(self, event_type, symbol, quantity, price, **kwargs):
        """记录交易事件"""
        context = {
            'event_type': 'trade',
            'trade_event': event_type,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            **kwargs
        }
        self.log_with_context(logging.INFO, f"交易事件: {event_type}", **context)
    
    def log_model_event(self, model_name, event_type, **kwargs):
        """记录模型事件"""
        context = {
            'event_type': 'model',
            'model_name': model_name,
            'model_event': event_type,
            **kwargs
        }
        self.log_with_context(logging.INFO, f"模型事件: {event_type}", **context)
    
    def log_performance_metrics(self, metrics_dict):
        """记录性能指标"""
        context = {
            'event_type': 'performance',
            **metrics_dict
        }
        self.log_with_context(logging.INFO, "性能指标更新", **context)

# 全局日志实例
logger = StructuredLogger('trademaster')

# 使用示例
def example_usage():
    # 基本日志
    logger.logger.info("应用启动")
    
    # 带上下文的日志
    logger.log_with_context(
        logging.INFO, 
        "用户登录",
        user_id=12345,
        ip_address="192.168.1.100",
        user_agent="TradeMaster/1.0"
    )
    
    # 交易事件日志
    logger.log_trade_event(
        event_type="buy_order",
        symbol="AAPL",
        quantity=100,
        price=150.25,
        order_id="ORD123456",
        strategy="momentum"
    )
    
    # 模型事件日志
    logger.log_model_event(
        model_name="lstm_predictor",
        event_type="prediction",
        confidence=0.85,
        prediction="bullish",
        features_count=20
    )
    
    # 性能指标日志
    logger.log_performance_metrics({
        'cpu_usage': 45.2,
        'memory_usage': 2.1,
        'response_time': 0.123,
        'throughput': 1250
    })

if __name__ == "__main__":
    example_usage()
```

---

## 🔄 CI/CD最佳实践

### 🚀 GitHub Actions工作流

#### 完整的CI/CD管道
```yaml
# .github/workflows/docker-cicd.yml
name: TradeMaster Docker CI/CD

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 black isort
    
    - name: Code quality checks
      run: |
        # 代码格式检查
        black --check .
        isort --check-only .
        flake8 . --max-line-length=88 --extend-ignore=E203,W503
    
    - name: Run unit tests
      run: |
        pytest tests/ -v --cov=trademaster --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        platforms: linux/amd64,linux/arm64

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment..."
        # 这里添加部署到staging环境的脚本
        
  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    environment: production
    
    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production environment..."
        # 这里添加部署到生产环境的脚本

  integration-test:
    needs: build
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run integration tests
      run: |
        docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
        docker-compose -f docker-compose.test.yml down
```

#### 多环境部署配置
```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  trademaster:
    image: ghcr.io/trademaster-ntu/trademaster:develop
    environment:
      - NODE_ENV=staging
      - DATABASE_URL=${STAGING_DATABASE_URL}
      - API_BASE_URL=https://staging-api.trademaster.com
      - LOG_LEVEL=DEBUG
    deploy:
      replicas: 2
      resources:
        limits: {memory: 4G, cpus: '2'}
    networks: [staging]

networks:
  staging:
    external: true

---
# docker-compose.production.yml
version: '3.8'

services:
  trademaster:
    image: ghcr.io/trademaster-ntu/trademaster:latest
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${PRODUCTION_DATABASE_URL}
      - API_BASE_URL=https://api.trademaster.com
      - LOG_LEVEL=INFO
    deploy:
      replicas: 5
      resources:
        limits: {memory: 8G, cpus: '4'}
      update_config:
        parallelism: 2
        delay: 10s
        failure_action: rollback
        order: start-first
      rollback_config:
        parallelism: 1
        delay: 5s
    networks: [production]

networks:
  production:
    external: true
```

---

## 💾 数据管理最佳实践

### 📊 数据备份策略

#### 自动化备份系统
```bash
#!/bin/bash
# automated_backup.sh

set -euo pipefail

# 配置
BACKUP_DIR="/opt/backups/trademaster"
RETENTION_DAYS=30
S3_BUCKET="trademaster-backups"
ENCRYPTION_KEY="/etc/trademaster/backup.key"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/trademaster_backup.log
}

# 创建备份目录
mkdir -p "$BACKUP_DIR"

log "开始TradeMaster数据备份..."

# 获取当前时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

mkdir -p "$BACKUP_PATH"

# 1. 备份容器数据
log "备份容器数据卷..."
docker run --rm \
  -v trademaster_data:/data \
  -v "$BACKUP_PATH":/backup \
  alpine:latest \
  tar czf /backup/data_volume.tar.gz -C /data .

# 2. 备份数据库
log "备份PostgreSQL数据库..."
docker exec postgres-container pg_dump \
  -U trademaster \
  -d trademaster \
  --no-owner \
  --no-privileges \
  | gzip > "$BACKUP_PATH/database.sql.gz"

# 3. 备份配置文件
log "备份配置文件..."
tar czf "$BACKUP_PATH/config.tar.gz" \
  -C /opt/trademaster \
  config/ \
  docker-compose.yml \
  .env

# 4. 备份代码仓库
log "备份代码仓库..."
if [ -d "/opt/trademaster/.git" ]; then
    cd /opt/trademaster
    git bundle create "$BACKUP_PATH/repository.bundle" --all
fi

# 5. 创建备份清单
log "创建备份清单..."
cat > "$BACKUP_PATH/manifest.json" << EOF
{
  "timestamp": "$TIMESTAMP",
  "backup_type": "full",
  "components": [
    "data_volume",
    "database", 
    "config",
    "repository"
  ],
  "retention_until": "$(date -d "+$RETENTION_DAYS days" '+%Y-%m-%d')",
  "size_mb": $(du -sm "$BACKUP_PATH" | cut -f1)
}
EOF

# 6. 加密备份
if [ -f "$ENCRYPTION_KEY" ]; then
    log "加密备份文件..."
    tar czf - -C "$BACKUP_DIR" "backup_$TIMESTAMP" | \
    openssl enc -aes-256-cbc -salt -k "$(cat $ENCRYPTION_KEY)" \
    > "$BACKUP_DIR/backup_${TIMESTAMP}_encrypted.tar.gz"
    
    # 删除未加密版本
    rm -rf "$BACKUP_PATH"
    BACKUP_FILE="backup_${TIMESTAMP}_encrypted.tar.gz"
else
    # 压缩备份
    tar czf "$BACKUP_DIR/backup_${TIMESTAMP}.tar.gz" -C "$BACKUP_DIR" "backup_$TIMESTAMP"
    rm -rf "$BACKUP_PATH"
    BACKUP_FILE="backup_${TIMESTAMP}.tar.gz"
fi

# 7. 上传到云存储
if command -v aws >/dev/null 2>&1 && [ -n "${S3_BUCKET:-}" ]; then
    log "上传备份到S3..."
    aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" "s3://$S3_BUCKET/$(date +%Y/%m)/"
    
    # 验证上传
    if aws s3 ls "s3://$S3_BUCKET/$(date +%Y/%m)/$BACKUP_FILE" >/dev/null; then
        log "S3上传成功"
    else
        log "错误: S3上传失败"
        exit 1
    fi
fi

# 8. 清理旧备份
log "清理旧备份文件..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# 9. 验证备份完整性
log "验证备份完整性..."
if tar tzf "$BACKUP_DIR/$BACKUP_FILE" >/dev/null 2>&1; then
    log "备份文件完整性验证通过"
else
    log "错误: 备份文件损坏"
    exit 1
fi

# 10. 发送备份报告
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
log "备份完成! 文件大小: $BACKUP_SIZE"

# 发送通知
if command -v mail >/dev/null 2>&1; then
    echo "TradeMaster备份完成
    
时间: $TIMESTAMP
大小: $BACKUP_SIZE
位置: $BACKUP_DIR/$BACKUP_FILE" | \
    mail -s "TradeMaster备份完成" admin@example.com
fi

log "备份流程完成"
```

#### 灾难恢复测试
```bash
#!/bin/bash
# disaster_recovery_test.sh

set -euo pipefail

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log "开始灾难恢复测试..."

# 1. 创建测试环境
log "创建隔离的测试环境..."
docker network create trademaster-test 2>/dev/null || true

# 2. 选择最新备份
BACKUP_DIR="/opt/backups/trademaster"
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.tar.gz | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    log "错误: 未找到备份文件"
    exit 1
fi

log "使用备份文件: $LATEST_BACKUP"

# 3. 解压备份
TEST_DIR="/tmp/trademaster_recovery_test"
mkdir -p "$TEST_DIR"

if [[ "$LATEST_BACKUP" == *"_encrypted"* ]]; then
    # 解密备份
    openssl enc -aes-256-cbc -d -salt -k "$(cat /etc/trademaster/backup.key)" \
        -in "$LATEST_BACKUP" | tar xzf - -C "$TEST_DIR"
else
    tar xzf "$LATEST_BACKUP" -C "$TEST_DIR"
fi

# 4. 恢复数据库
log "恢复测试数据库..."
docker run -d \
    --name postgres-test \
    --network trademaster-test \
    -e POSTGRES_DB=trademaster_test \
    -e POSTGRES_USER=test \
    -e POSTGRES_PASSWORD=test123 \
    postgres:13

# 等待数据库启动
sleep 30

# 导入数据库备份
zcat "$TEST_DIR"/backup_*/database.sql.gz | \
docker exec -i postgres-test psql -U test -d trademaster_test

# 5. 恢复应用数据
log "恢复应用数据..."
docker volume create trademaster-test-data

docker run --rm \
    -v trademaster-test-data:/data \
    -v "$TEST_DIR"/backup_*:/backup \
    alpine:latest \
    tar xzf /backup/data_volume.tar.gz -C /data

# 6. 启动测试应用
log "启动测试应用..."
docker run -d \
    --name trademaster-test \
    --network trademaster-test \
    -e DATABASE_URL=postgresql://test:test123@postgres-test/trademaster_test \
    -e NODE_ENV=test \
    -v trademaster-test-data:/app/data \
    -p 18080:8080 \
    trademaster:latest

# 7. 健康检查
log "执行健康检查..."
sleep 60  # 等待应用启动

# 检查应用响应
if curl -f http://localhost:18080/health >/dev/null 2>&1; then
    log "✅ 应用健康检查通过"
else
    log "❌ 应用健康检查失败"
    RECOVERY_SUCCESS=false
fi

# 检查数据库连接
if docker exec trademaster-test python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://test:test123@postgres-test/trademaster_test')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM information_schema.tables;')
    count = cur.fetchone()[0]
    print(f'数据库表数量: {count}')
    if count > 0:
        print('✅ 数据库恢复成功')
    else:
        print('❌ 数据库恢复失败')
        exit(1)
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"; then
    log "✅ 数据库连接测试通过"
else
    log "❌ 数据库连接测试失败"
    RECOVERY_SUCCESS=false
fi

# 8. 功能测试
log "执行基础功能测试..."
if docker exec trademaster-test python3 -c "
import sys
sys.path.append('/home/TradeMaster')
try:
    import trademaster
    print('✅ TradeMaster模块导入成功')
    
    # 测试数据访问
    import os
    if os.path.exists('/app/data'):
        file_count = len(os.listdir('/app/data'))
        print(f'✅ 数据文件恢复成功，文件数量: {file_count}')
    else:
        print('❌ 数据目录不存在')
        exit(1)
        
except Exception as e:
    print(f'❌ 功能测试失败: {e}')
    exit(1)
"; then
    log "✅ 功能测试通过"
    RECOVERY_SUCCESS=true
else
    log "❌ 功能测试失败"
    RECOVERY_SUCCESS=false
fi

# 9. 清理测试环境
log "清理测试环境..."
docker rm -f trademaster-test postgres-test 2>/dev/null || true
docker volume rm trademaster-test-data 2>/dev/null || true
docker network rm trademaster-test 2>/dev/null || true
rm -rf "$TEST_DIR"

# 10. 生成测试报告
if [ "$RECOVERY_SUCCESS" = true ]; then
    log "🎉 灾难恢复测试完全成功!"
    
    # 记录成功的恢复测试
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 恢复测试成功 - 备份文件: $(basename $LATEST_BACKUP)" >> /var/log/recovery_test.log
    
    exit 0
else
    log "❌ 灾难恢复测试失败，需要检查备份流程"
    
    # 发送告警
    if command -v mail >/dev/null 2>&1; then
        echo "TradeMaster灾难恢复测试失败，请立即检查备份系统" | \
        mail -s "恢复测试失败告警" admin@example.com
    fi
    
    exit 1
fi
```

---

## 🛠️ 运维管理最佳实践

### 🔄 自动化运维流程

#### 智能运维脚本
```bash
#!/bin/bash
# intelligent_ops.sh

set -euo pipefail

# 配置
CONTAINER_NAME="trademaster-container"
LOG_FILE="/var/log/trademaster_ops.log"
ALERT_EMAIL="admin@example.com"
METRICS_API="http://localhost:9090/api/v1"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 健康检查函数
health_check() {
    local service="$1"
    local endpoint="$2"
    local timeout="${3:-10}"
    
    if curl -sf --max-time "$timeout" "$endpoint" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 资源监控函数
check_resources() {
    log "检查系统资源使用情况..."
    
    # CPU使用率
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    CPU_THRESHOLD=85.0
    
    if (( $(echo "$CPU_USAGE > $CPU_THRESHOLD" | bc -l) )); then
        log "警告: CPU使用率过高 ($CPU_USAGE%)"
        return 1
    fi
    
    # 内存使用率
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    MEM_THRESHOLD=85.0
    
    if (( $(echo "$MEM_USAGE > $MEM_THRESHOLD" | bc -l) )); then
        log "警告: 内存使用率过高 ($MEM_USAGE%)"
        return 1
    fi
    
    # 磁盘使用率
    DISK_USAGE=$(df /app/data | awk 'NR==2 {print $5}' | sed 's/%//')
    DISK_THRESHOLD=85
    
    if [ "$DISK_USAGE" -gt "$DISK_THRESHOLD" ]; then
        log "警告: 磁盘使用率过高 ($DISK_USAGE%)"
        return 1
    fi
    
    log "资源使用正常 - CPU: $CPU_USAGE%, 内存: $MEM_USAGE%, 磁盘: $DISK_USAGE%"
    return 0
}

# 性能优化函数
optimize_performance() {
    log "执行性能优化..."
    
    # 清理容器日志
    docker exec "$CONTAINER_NAME" bash -c "
        find /var/log -name '*.log' -size +100M -exec truncate -s 50M {} \;
        find /tmp -type f -mtime +1 -delete
    " 2>/dev/null || true
    
    # Python垃圾回收
    docker exec "$CONTAINER_NAME" python3 -c "
        import gc
        collected = gc.collect()
        print(f'清理了 {collected} 个对象')
    " 2>/dev/null || true
    
    # 清理Docker缓存
    docker system prune -f >/dev/null 2>&1 || true
    
    log "性能优化完成"
}

# 自动扩缩容函数
auto_scale() {
    local current_replicas=$(docker service ls --filter name=trademaster --format "{{.Replicas}}" 2>/dev/null | head -1 || echo "1")
    
    if [ -z "$current_replicas" ]; then
        log "未检测到集群模式，跳过自动扩缩容"
        return 0
    fi
    
    # 获取平均负载
    local avg_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local load_threshold=$(echo "$cpu_cores * 0.8" | bc)
    
    if (( $(echo "$avg_load > $load_threshold" | bc -l) )); then
        # 高负载，扩容
        local new_replicas=$((current_replicas + 1))
        if [ "$new_replicas" -le 5 ]; then
            log "高负载检测，扩容到 $new_replicas 个副本"
            docker service update --replicas "$new_replicas" trademaster >/dev/null 2>&1 || true
        fi
    elif (( $(echo "$avg_load < $load_threshold * 0.3" | bc -l) )); then
        # 低负载，缩容
        local new_replicas=$((current_replicas - 1))
        if [ "$new_replicas" -ge 1 ]; then
            log "低负载检测，缩容到 $new_replicas 个副本"
            docker service update --replicas "$new_replicas" trademaster >/dev/null 2>&1 || true
        fi
    fi
}

# 安全检查函数
security_check() {
    log "执行安全检查..."
    
    # 检查容器配置
    local security_issues=0
    
    # 检查是否以root运行
    if docker exec "$CONTAINER_NAME" whoami 2>/dev/null | grep -q "root"; then
        log "安全警告: 容器以root用户运行"
        ((security_issues++))
    fi
    
    # 检查端口绑定
    local open_ports=$(docker port "$CONTAINER_NAME" 2>/dev/null | grep "0.0.0.0" | wc -l)
    if [ "$open_ports" -gt 0 ]; then
        log "安全警告: 存在绑定到所有接口的端口"
        ((security_issues++))
    fi
    
    # 检查文件权限
    local world_writable=$(docker exec "$CONTAINER_NAME" find /app -type f -perm /o+w 2>/dev/null | wc -l)
    if [ "$world_writable" -gt 0 ]; then
        log "安全警告: 存在所有用户可写的文件"
        ((security_issues++))
    fi
    
    if [ "$security_issues" -eq 0 ]; then
        log "安全检查通过"
        return 0
    else
        log "发现 $security_issues 个安全问题"
        return 1
    fi
}

# 自动修复函数
auto_repair() {
    local issue="$1"
    
    log "尝试自动修复: $issue"
    
    case "$issue" in
        "container_down")
            log "重启容器..."
            docker restart "$CONTAINER_NAME"
            sleep 30
            ;;
        "high_memory")
            log "清理内存..."
            docker exec "$CONTAINER_NAME" python3 -c "
                import gc
                gc.collect()
                
                # 清理缓存
                import os
                os.system('sync && echo 3 > /proc/sys/vm/drop_caches')
            " 2>/dev/null || true
            ;;
        "disk_full")
            log "清理磁盘空间..."
            docker exec "$CONTAINER_NAME" bash -c "
                find /tmp -type f -mtime +1 -delete
                find /app/logs -name '*.log' -mtime +7 -delete
                find /app/data -name '*.tmp' -delete
            " 2>/dev/null || true
            ;;
        "service_unhealthy")
            log "重新部署服务..."
            if command -v docker-compose >/dev/null 2>&1; then
                docker-compose restart trademaster
            else
                docker restart "$CONTAINER_NAME"
            fi
            ;;
        *)
            log "未知问题，执行通用修复..."
            docker restart "$CONTAINER_NAME"
            ;;
    esac
    
    log "自动修复完成"
}

# 主监控循环
main_monitor() {
    log "开始智能运维监控..."
    
    while true; do
        # 容器状态检查
        if ! docker ps | grep -q "$CONTAINER_NAME"; then
            log "错误: 容器未运行"
            auto_repair "container_down"
            
            # 验证修复结果
            sleep 30
            if docker ps | grep -q "$CONTAINER_NAME"; then
                log "容器自动修复成功"
            else
                log "容器自动修复失败，发送告警"
                send_alert "容器启动失败" "容器 $CONTAINER_NAME 无法自动修复"
            fi
        fi
        
        # 健康检查
        if ! health_check "web" "http://localhost:8080/health"; then
            log "Web服务健康检查失败"
            auto_repair "service_unhealthy"
        fi
        
        # 资源检查
        if ! check_resources; then
            # 根据具体问题进行修复
            if [ "$?" -eq 1 ]; then
                auto_repair "high_memory"
            fi
        fi
        
        # 安全检查（每小时一次）
        if [ $(($(date +%M) % 60)) -eq 0 ]; then
            security_check || send_alert "安全检查失败" "发现安全配置问题"
        fi
        
        # 性能优化（每6小时一次）
        if [ $(($(date +%H) % 6)) -eq 0 ] && [ $(date +%M) -eq 0 ]; then
            optimize_performance
        fi
        
        # 自动扩缩容检查
        auto_scale
        
        # 等待下一次检查
        sleep 60
    done
}

# 告警发送函数
send_alert() {
    local subject="$1"
    local message="$2"
    
    log "发送告警: $subject"
    
    # 邮件告警
    if command -v mail >/dev/null 2>&1; then
        echo "$message

时间: $(date)
主机: $(hostname)
容器: $CONTAINER_NAME" | mail -s "TradeMaster运维告警: $subject" "$ALERT_EMAIL"
    fi
    
    # Slack告警（如果配置了webhook）
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"TradeMaster运维告警: $subject\n$message\"}" \
            "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
    fi
    
    # 企业微信告警（如果配置了webhook）
    if [ -n "${WECHAT_WEBHOOK:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"msgtype\":\"text\",\"text\":{\"content\":\"TradeMaster运维告警: $subject\n$message\"}}" \
            "$WECHAT_WEBHOOK" >/dev/null 2>&1 || true