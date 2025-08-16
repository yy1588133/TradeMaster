# Docker 部署配置指南

## 🐳 Docker 架构设计

### 容器化架构图

```mermaid
graph TB
    subgraph "Docker Network: trademaster-net"
        subgraph "Load Balancer"
            A[Nginx]
        end
        
        subgraph "Frontend"
            B[React App]
        end
        
        subgraph "Backend Services"
            C[FastAPI App]
            D[Celery Worker]
            E[Celery Beat]
            F[Flower Monitor]
        end
        
        subgraph "Data Layer"
            G[(PostgreSQL)]
            H[(Redis)]
        end
        
        subgraph "TradeMaster Integration"
            I[Flask API :8080]
            J[TradeMaster Core]
        end
        
        subgraph "Monitoring"
            K[Prometheus]
            L[Grafana]
        end
    end
    
    A --> B
    A --> C
    C --> G
    C --> H
    D --> G
    D --> H
    D --> I
    I --> J
    K --> C
    K --> G
    K --> H
    L --> K
```

## 📋 Docker Compose 配置

### 生产环境配置

```yaml
# docker/docker-compose.yml
version: '3.8'

networks:
  trademaster-net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  app_uploads:
  nginx_logs:
  app_logs:

services:
  # 数据库服务
  postgres:
    image: postgres:15-alpine
    container_name: trademaster-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-trademaster}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_HOST_AUTH_METHOD: trust
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    ports:
      - "5432:5432"
    networks:
      - trademaster-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-trademaster}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Redis服务
  redis:
    image: redis:7-alpine
    container_name: trademaster-redis
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    ports:
      - "6379:6379"
    networks:
      - trademaster-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 后端API服务
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
      args:
        - BUILD_ENV=production
    container_name: trademaster-backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-trademaster}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - TRADEMASTER_API_URL=http://trademaster-flask:8080
    volumes:
      - app_uploads:/app/uploads
      - app_logs:/app/logs
    ports:
      - "8000:8000"
    networks:
      - trademaster-net
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Celery Worker
  celery-worker:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
      args:
        - BUILD_ENV=production
    container_name: trademaster-celery-worker
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-trademaster}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - TRADEMASTER_API_URL=http://trademaster-flask:8080
    volumes:
      - app_uploads:/app/uploads
      - app_logs:/app/logs
    networks:
      - trademaster-net
    depends_on:
      - postgres
      - redis
      - backend
    restart: unless-stopped
    deploy:
      replicas: 2

  # Celery Beat (定时任务)
  celery-beat:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
      args:
        - BUILD_ENV=production
    container_name: trademaster-celery-beat
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-trademaster}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - app_logs:/app/logs
    networks:
      - trademaster-net
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # Flower (Celery监控)
  flower:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
      args:
        - BUILD_ENV=production
    container_name: trademaster-flower
    command: celery -A app.core.celery_app flower --port=5555
    environment:
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "5555:5555"
    networks:
      - trademaster-net
    depends_on:
      - redis
    restart: unless-stopped

  # 前端服务
  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
      args:
        - BUILD_ENV=production
        - VITE_API_URL=http://localhost/api
    container_name: trademaster-frontend
    ports:
      - "3000:80"
    networks:
      - trademaster-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx反向代理
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: trademaster-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    networks:
      - trademaster-net
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  # TradeMaster Flask API (现有服务)
  trademaster-flask:
    image: trademaster:latest
    container_name: trademaster-flask
    command: python deploy/backend_service.py
    environment:
      - PYTHONPATH=/home/TradeMaster
    volumes:
      - ${TRADEMASTER_DATA_PATH:-../data}:/home/TradeMaster/data
      - ${TRADEMASTER_WORK_DIR:-../work_dir}:/home/TradeMaster/work_dir
    ports:
      - "8080:8080"
    networks:
      - trademaster-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/TradeMaster/healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 监控服务
  prometheus:
    image: prom/prometheus:latest
    container_name: trademaster-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - trademaster-net
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: trademaster-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    ports:
      - "3001:3000"
    networks:
      - trademaster-net
    depends_on:
      - prometheus
    restart: unless-stopped
```

### 开发环境配置

```yaml
# docker/docker-compose.dev.yml
version: '3.8'

networks:
  trademaster-dev:
    driver: bridge

volumes:
  postgres_data_dev:
  redis_data_dev:

services:
  postgres-dev:
    image: postgres:15-alpine
    container_name: trademaster-postgres-dev
    environment:
      POSTGRES_DB: trademaster_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    networks:
      - trademaster-dev

  redis-dev:
    image: redis:7-alpine
    container_name: trademaster-redis-dev
    ports:
      - "6380:6379"
    networks:
      - trademaster-dev

  backend-dev:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
      target: development
    container_name: trademaster-backend-dev
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres-dev:5432/trademaster_dev
      - REDIS_URL=redis://redis-dev:6379/0
      - SECRET_KEY=dev-secret-key
      - DEBUG=true
      - RELOAD=true
    volumes:
      - ../backend:/app
      - /app/__pycache__
      - /app/.pytest_cache
    ports:
      - "8001:8000"
    networks:
      - trademaster-dev
    depends_on:
      - postgres-dev
      - redis-dev
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker-dev:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
      target: development
    container_name: trademaster-celery-dev
    command: celery -A app.core.celery_app worker --loglevel=debug --reload
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres-dev:5432/trademaster_dev
      - REDIS_URL=redis://redis-dev:6379/0
      - SECRET_KEY=dev-secret-key
    volumes:
      - ../backend:/app
    networks:
      - trademaster-dev
    depends_on:
      - postgres-dev
      - redis-dev

  frontend-dev:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
      target: development
    container_name: trademaster-frontend-dev
    environment:
      - VITE_API_URL=http://localhost:8001/api
      - VITE_WS_URL=ws://localhost:8001/ws
    volumes:
      - ../frontend:/app
      - /app/node_modules
    ports:
      - "3001:3000"
    networks:
      - trademaster-dev
    command: npm run dev
```

## 🏗️ Dockerfile 配置

### 后端 Dockerfile

```dockerfile
# docker/Dockerfile.backend
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 安装Python依赖
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# 开发阶段
FROM base as development
RUN pip install --no-cache-dir -r requirements/dev.txt
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 生产阶段
FROM base as production
RUN pip install --no-cache-dir -r requirements/prod.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/uploads /app/logs && \
    chown -R appuser:appuser /app

# 切换到应用用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "app.main:app"]
```

### 前端 Dockerfile

```dockerfile
# docker/Dockerfile.frontend
FROM node:18-alpine as base

# 安装pnpm
RUN npm install -g pnpm

WORKDIR /app

# 复制package文件
COPY package*.json pnpm-lock.yaml ./

# 开发阶段
FROM base as development
RUN pnpm install
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev", "--host", "0.0.0.0"]

# 构建阶段
FROM base as build
RUN pnpm install --frozen-lockfile
COPY . .
ARG BUILD_ENV=production
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN pnpm build

# 生产阶段
FROM nginx:alpine as production
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Dockerfile

```dockerfile
# docker/nginx/Dockerfile
FROM nginx:alpine

# 安装curl用于健康检查
RUN apk --no-cache add curl

# 复制配置文件
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# 创建日志目录
RUN mkdir -p /var/log/nginx

# 暴露端口
EXPOSE 80 443

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

## ⚙️ Nginx 配置

### 主配置文件

```nginx
# docker/nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # 基础配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate no_last_modified no_etag auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # 包含站点配置
    include /etc/nginx/conf.d/*.conf;
}
```

### 站点配置

```nginx
# docker/nginx/conf.d/default.conf
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

upstream frontend {
    server frontend:80;
}

# HTTP重定向到HTTPS (生产环境)
server {
    listen 80;
    server_name _;
    return 301 https://$server_name$request_uri;
}

# 主服务器配置
server {
    listen 443 ssl http2;
    server_name _;

    # SSL配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # 前端静态文件
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API代理
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # WebSocket代理
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # 登录限流
    location /api/v1/auth/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}

# 开发环境配置 (无SSL)
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 📊 监控配置

### Prometheus 配置

```yaml
# docker/monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'trademaster-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']

  - job_name: 'celery'
    static_configs:
      - targets: ['flower:5555']
    metrics_path: '/api/workers'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## 🚀 部署脚本

### 生产部署脚本

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="trademaster-web"

echo "🚀 Starting deployment for $ENVIRONMENT environment..."

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

# 设置环境变量
if [ "$ENVIRONMENT" = "production" ]; then
    ENV_FILE=".env.prod"
    COMPOSE_FILE="docker/docker-compose.yml"
else
    ENV_FILE=".env.dev"
    COMPOSE_FILE="docker/docker-compose.dev.yml"
fi

# 检查环境文件
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found"
    exit 1
fi

# 备份数据库 (生产环境)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "📦 Creating database backup..."
    ./scripts/backup.sh
fi

# 构建镜像
echo "🏗️ Building Docker images..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE build --no-cache

# 停止现有容器
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE down

# 启动服务
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d

# 等待服务启动
echo "⏳ Waiting for services to start..."
sleep 30

# 运行数据库迁移
echo "🗃️ Running database migrations..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec backend alembic upgrade head

# 健康检查
echo "🔍 Performing health checks..."
./scripts/health-check.sh

echo "✅ Deployment completed successfully!"

# 显示服务状态
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps
```

### 健康检查脚本

```bash
#!/bin/bash
# scripts/health-check.sh

set -e

TIMEOUT=60
INTERVAL=5

check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo "Checking $service_name..."
    
    for i in $(seq 1 $((TIMEOUT / INTERVAL))); do
        if curl -f -s -w "HTTP %{http_code}\n" "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        fi
        echo "⏳ Waiting for $service_name... (attempt $i)"
        sleep $INTERVAL
    done
    
    echo "❌ $service_name health check failed"
    return 1
}

# 检查各个服务
check_service "Frontend" "http://localhost:3000"
check_service "Backend API" "http://localhost:8000/health"
check_service "TradeMaster Flask API" "http://localhost:8080/api/TradeMaster/healthcheck"
check_service "Flower" "http://localhost:5555"

echo "🎉 All services are healthy!"
```

### 备份脚本

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
POSTGRES_CONTAINER="trademaster-postgres"
POSTGRES_DB="trademaster"
POSTGRES_USER="postgres"

mkdir -p "$BACKUP_DIR"

echo "📦 Creating database backup..."

# 备份PostgreSQL
docker exec $POSTGRES_CONTAINER pg_dump -U $POSTGRES_USER -d $POSTGRES_DB > "$BACKUP_DIR/postgres_backup.sql"

# 备份上传文件
if [ -d "uploads" ]; then
    tar -czf "$BACKUP_DIR/uploads_backup.tar.gz" uploads/
fi

# 备份日志
if [ -d "logs" ]; then
    tar -czf "$BACKUP_DIR/logs_backup.tar.gz" logs/
fi

echo "✅ Backup completed: $BACKUP_DIR"

# 清理旧备份 (保留最近7天)
find backups/ -type d -mtime +7 -exec rm -rf {} +
```

## 🔧 环境变量配置

### 生产环境变量

```bash
# .env.prod
# 基础配置
PROJECT_NAME=TradeMaster Web Interface
VERSION=1.0.0
DEBUG=false
SECRET_KEY=your-super-secret-key-here

# 数据库配置
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=trademaster
POSTGRES_PORT=5432

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# TradeMaster集成
TRADEMASTER_API_URL=http://trademaster-flask:8080
TRADEMASTER_DATA_PATH=./data
TRADEMASTER_WORK_DIR=./work_dir

# SSL配置
SSL_CERT_PATH=./ssl/cert.pem
SSL_KEY_PATH=./ssl/key.pem

# 监控配置
GRAFANA_PASSWORD=your-grafana-password
SENTRY_DSN=https://your-sentry-dsn

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-email-password
EMAILS_FROM_EMAIL=noreply@trademaster.com
EMAILS_FROM_NAME=TradeMaster
```

### 开发环境变量

```bash
# .env.dev
PROJECT_NAME=TradeMaster Web Interface (Dev)
VERSION=1.0.0-dev
DEBUG=true
SECRET_KEY=dev-secret-key

POSTGRES_SERVER=postgres-dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=trademaster_dev
POSTGRES_PORT=5432

REDIS_HOST=redis-dev
REDIS_PORT=6379
REDIS_DB=0

TRADEMASTER_API_URL=http://localhost:8080
```

这个Docker部署配置确保了：

- **容器化架构**：完整的微服务容器化部署
- **环境隔离**：开发、测试、生产环境分离
- **服务编排**：Docker Compose自动化服务管理
- **负载均衡**：Nginx反向代理和负载均衡
- **监控系统**：Prometheus + Grafana监控栈
- **安全配置**：SSL/TLS加密和安全头设置
- **健康检查**：自动化服务健康监控
- **数据持久化**：数据卷管理和备份策略
- **自动化部署**：完整的部署和运维脚本