# TradeMaster Docker 快速启动指南

<div align="center">
    <h2>🚀 5分钟快速上手</h2>
    <p>面向不同技术水平用户的分层指导</p>
</div>

---

## 🎯 选择您的角色

<table align="center">
    <tr>
        <td align="center" width="200">
            <h3>🌟 新手用户</h3>
            <p>初次接触Docker<br/>想要快速体验</p>
            <a href="#新手用户">👉 点击开始</a>
        </td>
        <td align="center" width="200">
            <h3>⚡ 开发者</h3>
            <p>有开发经验<br/>需要定制配置</p>
            <a href="#开发者">👉 点击开始</a>
        </td>
        <td align="center" width="200">
            <h3>🔧 运维人员</h3>
            <p>负责生产部署<br/>关注稳定性</p>
            <a href="#运维人员">👉 点击开始</a>
        </td>
    </tr>
</table>

---

## 🌟 新手用户

### 🎯 目标
- 5分钟内启动TradeMaster容器
- 体验基本功能
- 了解基础操作

### 📋 前置条件检查

#### ✅ 检查清单
- [ ] 已安装Docker Desktop
- [ ] 电脑有8GB以上内存
- [ ] 有15GB以上磁盘空间
- [ ] 网络连接正常

#### 🔧 快速安装Docker Desktop

**Windows用户**:
1. 下载: [Docker Desktop for Windows](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe)
2. 双击安装，重启电脑
3. 启动Docker Desktop

**Mac用户**:
1. 下载: [Docker Desktop for Mac](https://desktop.docker.com/mac/main/amd64/Docker.dmg)
2. 拖拽到Applications文件夹
3. 启动Docker Desktop

#### ✨ 验证安装
```bash
# 打开命令行，输入以下命令
docker --version
```
**应该看到**: `Docker version 20.10.17+`

### 🚀 一键启动

#### Windows用户 (推荐)
```batch
# 1. 下载项目 (复制粘贴到命令行)
git clone https://github.com/TradeMaster-NTU/TradeMaster.git
cd TradeMaster

# 2. 构建镜像 (需要等待5-10分钟)
docker build -t trademaster:latest .

# 3. 启动服务 (双击即可)
start-container.bat
```

#### Mac/Linux用户
```bash
# 1. 下载项目
git clone https://github.com/TradeMaster-NTU/TradeMaster.git
cd TradeMaster

# 2. 构建镜像 
docker build -t trademaster:latest .

# 3. 启动服务
chmod +x *.sh
./start-container.sh
```

### 🎉 成功验证

#### 检查服务状态
```bash
docker ps
```
**应该看到**: `trademaster-container` 在运行

#### 访问Web界面
- 打开浏览器访问: http://localhost:8080
- Jupyter Notebook: http://localhost:8888

#### 测试基本功能
```bash
# Windows
enter-container.bat

# Mac/Linux  
docker exec -it trademaster-container bash

# 在容器内测试
python3 -c "import trademaster; print('✅ 成功!')"
```

### 🆘 遇到问题？

#### 常见问题解决

**问题1**: `docker: command not found`
```bash
# 解决: 重新安装Docker Desktop，确保添加到PATH
```

**问题2**: `port already in use`
```bash
# 解决: 修改端口
# 编辑 start-container.bat，将 8080 改为 8081
```

**问题3**: 容器启动失败
```bash
# 解决: 检查资源
docker system df
docker system prune  # 清理空间
```

### 📚 下一步学习

- [📖 详细部署指南](DOCKER_DEPLOYMENT_GUIDE.md)
- [🔧 管理工具使用](CONTAINER_MANAGEMENT.md)
- [📊 监控和优化](PERFORMANCE_GUIDE.md)

---

## ⚡ 开发者

### 🎯 目标
- 快速搭建开发环境
- 自定义配置选项
- 集成开发工具

### 🔧 高级安装选项

#### 自定义构建参数
```bash
# 使用国内镜像源加速
docker build \
  --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
  --build-arg CUDA_VERSION=11.8 \
  -t trademaster:dev .

# 开发模式构建 (包含更多工具)
docker build \
  --target development \  
  -t trademaster:dev .
```

#### 开发环境配置
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  trademaster:
    build: 
      context: .
      target: development
    container_name: trademaster-dev
    ports:
      - "8080:8080"
      - "8888:8888"
      - "5001:5000"
      - "3000:3000"    # React dev server
      - "5432:5432"    # PostgreSQL
    volumes:
      - .:/workspace
      - ./data:/app/data
      - node_modules:/workspace/node_modules
    environment:
      - NODE_ENV=development
      - PYTHONPATH=/workspace
      - DEBUG=true
    networks:
      - trademaster-net

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: trademaster
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - trademaster-net

networks:
  trademaster-net:
    driver: bridge

volumes:
  node_modules:
  postgres_data:
```

#### 启动开发环境
```bash
# 使用docker-compose启动完整开发栈
docker-compose -f docker-compose.dev.yml up -d

# 或者自定义启动
docker run -d \
  --name trademaster-dev \
  -p 8080:8080 -p 8888:8888 -p 5001:5000 \
  -v "$(pwd):/workspace" \
  -v "$(pwd)/data:/app/data" \
  -v trademaster_node_modules:/workspace/node_modules \
  -e NODE_ENV=development \
  -e DEBUG=true \
  --restart unless-stopped \
  trademaster:dev
```

### 🛠️ 开发工具集成

#### VS Code 远程开发
```json
// .vscode/settings.json
{
  "remote.containers.defaultExtensions": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-toolsai.jupyter"
  ],
  "python.defaultInterpreterPath": "/opt/trademaster-env/bin/python",
  "python.terminal.activateEnvironment": true
}
```

#### JetBrains PyCharm配置
```bash
# 配置远程解释器
# Host: localhost
# Port: 2222 (需要开放SSH端口)
# Username: developer
# Python路径: /opt/trademaster-env/bin/python
```

#### Jupyter Lab高级配置
```bash
# 进入容器
docker exec -it trademaster-dev bash

# 生成Jupyter配置
jupyter lab --generate-config

# 编辑配置文件
vim ~/.jupyter/jupyter_lab_config.py
```

### 📊 性能开发配置

#### GPU支持
```bash
# 构建GPU版本
docker build \
  --build-arg CUDA_VERSION=11.8 \
  --build-arg PYTORCH_VERSION=1.12.1+cu116 \
  -t trademaster:gpu .

# 启动GPU容器
docker run -d \
  --gpus all \
  --name trademaster-gpu \
  -p 8080:8080 -p 8888:8888 -p 5001:5000 \
  -v "$(pwd):/workspace" \
  -v "$(pwd)/data:/app/data" \
  trademaster:gpu
```

#### 多容器架构
```yaml
# docker-compose.cluster.yml
version: '3.8'
services:
  trademaster-training:
    build: .
    deploy:
      replicas: 3
    environment:
      - ROLE=training
      - WORKER_ID=${WORKER_ID}
    
  trademaster-inference:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ROLE=inference
    depends_on:
      - redis
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 🔍 调试和测试

#### 单元测试环境
```bash
# 运行测试容器
docker run --rm \
  -v "$(pwd):/workspace" \
  trademaster:dev \
  python -m pytest tests/ -v

# 覆盖率测试
docker run --rm \
  -v "$(pwd):/workspace" \
  trademaster:dev \
  coverage run -m pytest && coverage report
```

#### 性能分析
```python
# 在容器内使用性能分析工具
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 你的代码
your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### 🚀 持续集成

#### GitHub Actions配置
```yaml
# .github/workflows/docker.yml
name: Docker Build and Test

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: docker build -t trademaster:test .
      
    - name: Run tests
      run: |
        docker run --rm trademaster:test python -m pytest
        
    - name: Security scan
      run: |
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
          aquasec/trivy image trademaster:test
```

### 📚 开发资源

- [🔧 API文档](API_DOCUMENTATION.md)
- [🏗️ 架构设计](ARCHITECTURE.md)
- [🧪 测试指南](TESTING_GUIDE.md)

---

## 🔧 运维人员

### 🎯 目标
- 生产级部署配置
- 监控和告警设置
- 自动化运维流程

### 🏭 生产环境部署

#### 安全加固配置
```bash
# 创建专用用户
sudo useradd -r -s /bin/false trademaster
sudo mkdir -p /opt/trademaster/{data,logs,config}
sudo chown -R trademaster:trademaster /opt/trademaster

# 生产环境启动
docker run -d \
  --name trademaster-prod \
  --user trademaster:trademaster \
  --security-opt no-new-privileges:true \
  --security-opt apparmor:docker-default \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --read-only \
  --tmpfs /tmp:rw,size=100m \
  --tmpfs /var/tmp:rw,size=50m \
  -p 8080:8080 \
  -v /opt/trademaster/data:/app/data:rw \
  -v /opt/trademaster/config:/app/config:ro \
  -v /opt/trademaster/logs:/app/logs:rw \
  --memory="16g" \
  --memory-swap="16g" \
  --cpus="8" \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=5 \
  trademaster:latest
```

#### 负载均衡配置
```nginx
# nginx.conf
upstream trademaster_backend {
    least_conn;
    server 127.0.0.1:8080 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8081 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8082 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name trademaster.yourdomain.com;
    
    location / {
        proxy_pass http://trademaster_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # 健康检查
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
    }
    
    # 健康检查端点
    location /health {
        access_log off;
        proxy_pass http://trademaster_backend;
    }
}
```

#### SSL/TLS配置
```bash
# 使用Let's Encrypt
sudo certbot --nginx -d trademaster.yourdomain.com

# 手动证书配置
server {
    listen 443 ssl http2;
    server_name trademaster.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/trademaster.crt;
    ssl_certificate_key /etc/ssl/private/trademaster.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
}
```

### 📊 监控系统

#### Prometheus + Grafana配置
```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:v2.30.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:8.2.0
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123

  node-exporter:
    image: prom/node-exporter:v1.2.0
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'

volumes:
  prometheus_data:
  grafana_data:
```

#### 自定义监控指标
```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# 业务指标
TRADE_REQUESTS = Counter('trademaster_trade_requests_total', 
                        'Total trade requests', ['method', 'endpoint'])
TRADE_LATENCY = Histogram('trademaster_trade_duration_seconds',
                         'Trade request latency')
ACTIVE_POSITIONS = Gauge('trademaster_active_positions',
                        'Number of active positions')

# 系统指标
CONTAINER_MEMORY = Gauge('trademaster_container_memory_bytes',
                        'Container memory usage')
CONTAINER_CPU = Gauge('trademaster_container_cpu_percent',
                     'Container CPU usage percentage')

class MetricsCollector:
    def collect_system_metrics(self):
        """收集系统指标"""
        import psutil
        
        # CPU使用率
        CONTAINER_CPU.set(psutil.cpu_percent())
        
        # 内存使用
        memory = psutil.virtual_memory()
        CONTAINER_MEMORY.set(memory.used)
        
    def track_trade_request(self, method, endpoint):
        """跟踪交易请求"""
        TRADE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
        
    @TRADE_LATENCY.time()
    def execute_trade(self):
        """执行交易并记录延迟"""
        # 交易逻辑
        pass
```

### 🚨 告警配置

#### AlertManager配置
```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourdomain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@yourdomain.com'
    subject: 'TradeMaster Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
```

#### 告警规则
```yaml
# alert.rules.yml
groups:
- name: trademaster
  rules:
  - alert: ContainerDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "TradeMaster container is down"
      description: "Container {{ $labels.instance }} has been down for more than 1 minute."

  - alert: HighMemoryUsage
    expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100 > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
      description: "Memory usage is above 85% for 5 minutes."

  - alert: HighCPUUsage
    expr: rate(container_cpu_usage_seconds_total[5m]) * 100 > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
      description: "CPU usage is above 80% for 5 minutes."
```

### 🔄 自动化运维

#### 备份脚本
```bash
#!/bin/bash
# backup_production.sh

set -euo pipefail

BACKUP_DIR="/opt/backups/trademaster"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "开始生产环境备份 - $DATE"

# 创建备份目录
mkdir -p "$BACKUP_DIR/$DATE"

# 备份应用数据
echo "备份应用数据..."
docker exec trademaster-prod tar czf /tmp/app_data.tar.gz -C /app/data .
docker cp trademaster-prod:/tmp/app_data.tar.gz "$BACKUP_DIR/$DATE/"

# 备份数据库
echo "备份数据库..."
docker exec postgres-prod pg_dump -U trademaster trademaster | gzip > "$BACKUP_DIR/$DATE/database.sql.gz"

# 备份配置文件
echo "备份配置..."
cp -r /opt/trademaster/config "$BACKUP_DIR/$DATE/"

# 导出容器配置
echo "备份容器配置..."
docker inspect trademaster-prod > "$BACKUP_DIR/$DATE/container_config.json"

# 上传到远程存储 (可选)
if [ -n "${AWS_S3_BUCKET:-}" ]; then
    echo "上传到S3..."
    aws s3 sync "$BACKUP_DIR/$DATE" "s3://$AWS_S3_BUCKET/trademaster/backups/$DATE/"
fi

# 清理旧备份
echo "清理旧备份..."
find "$BACKUP_DIR" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} +

echo "备份完成 - $DATE"
```

#### 自动更新脚本
```bash
#!/bin/bash
# auto_update.sh

set -euo pipefail

CONTAINER_NAME="trademaster-prod"
IMAGE_NAME="trademaster:latest"
BACKUP_DIR="/opt/backups/updates"

echo "开始自动更新流程..."

# 预检查
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "错误: 容器未运行"
    exit 1
fi

# 健康检查
if ! curl -f http://localhost:8080/health; then
    echo "错误: 服务不健康"
    exit 1
fi

# 创建更新前备份
echo "创建更新前备份..."
./backup_production.sh

# 拉取新镜像
echo "拉取新镜像..."
docker pull $IMAGE_NAME

# 滚动更新
echo "执行滚动更新..."
for port in 8081 8082; do
    # 启动新实例
    docker run -d \
        --name ${CONTAINER_NAME}-new-$port \
        -p $port:8080 \
        # ... 其他配置
        $IMAGE_NAME
    
    # 等待健康检查通过
    sleep 30
    if curl -f http://localhost:$port/health; then
        echo "新实例 $port 启动成功"
    else
        echo "新实例 $port 启动失败，回滚"
        docker rm -f ${CONTAINER_NAME}-new-$port
        exit 1
    fi
done

# 停止旧实例
echo "停止旧实例..."
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME

# 重命名新实例
docker rename ${CONTAINER_NAME}-new-8081 $CONTAINER_NAME

# 清理临时实例
docker rm -f ${CONTAINER_NAME}-new-8082

echo "更新完成"
```

#### 定时任务配置
```bash
# crontab -e
# 每天凌晨2点备份
0 2 * * * /opt/scripts/backup_production.sh >> /var/log/trademaster_backup.log 2>&1

# 每周日凌晨3点自动更新
0 3 * * 0 /opt/scripts/auto_update.sh >> /var/log/trademaster_update.log 2>&1

# 每小时健康检查
0 * * * * /opt/scripts/health_check.sh >> /var/log/trademaster_health.log 2>&1

# 每天清理日志
0 1 * * * find /var/log -name "*.log" -mtime +7 -delete
```

### 🔒 安全最佳实践

#### 容器安全检查
```bash
# security_check.sh
#!/bin/bash

echo "执行安全检查..."

# 检查容器权限
docker inspect trademaster-prod | jq '.[] | .HostConfig | {Privileged, ReadonlyRootfs, CapAdd, CapDrop}'

# 漏洞扫描
trivy image trademaster:latest

# 网络安全检查
nmap -sT localhost -p 8080,8888,5001

# 文件权限检查
docker exec trademaster-prod find /app -perm /o+w -type f

echo "安全检查完成"
```

### 📚 运维资源

- [🔒 安全配置指南](SECURITY_GUIDE.md)
- [📊 监控配置详解](MONITORING_SETUP.md)
- [🚨 故障应急手册](INCIDENT_RESPONSE.md)

---

## 📞 技术支持

### 🆘 获取帮助

**问题报告**:
- [GitHub Issues](https://github.com/TradeMaster-NTU/TradeMaster/issues)
- 邮件: TradeMaster.NTU@gmail.com

**文档反馈**:
- 发现错误或需要改进的地方
- 提供使用建议和最佳实践

**社区讨论**:
- [GitHub Discussions](https://github.com/TradeMaster-NTU/TradeMaster/discussions)
- 技术交流和经验分享

---

## 📄 版本信息

**文档版本**: v2.0.0  
**最后更新**: 2025年8月15日  
**适用版本**: TradeMaster Docker v1.0+  
**维护团队**: TradeMaster Development Team