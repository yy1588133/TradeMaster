# TradeMaster Web Interface Docker 部署指南

## 📋 目录

- [概述](#概述)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [部署模式](#部署模式)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [监控和维护](#监控和维护)
- [故障排除](#故障排除)

## 🎯 概述

TradeMaster Web Interface 提供了完整的Docker容器化解决方案，支持：

- **🔧 开发环境**: 支持热重载和调试工具
- **🚀 生产环境**: 高性能、高可用的生产部署
- **🔗 集成模式**: 与现有TradeMaster核心无缝集成

### 架构组件

```
┌─────────────────────────────────────────────────────────────┐
│                    TradeMaster 生态系统                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   统一网关       │   Web界面        │   TradeMaster核心        │
│   (Nginx)       │   (React+FastAPI)│   (Python)              │
├─────────────────┼─────────────────┼─────────────────────────┤
│   负载均衡       │   - 前端应用     │   - 算法交易             │
│   SSL终端       │   - 后端API      │   - 数据处理             │
│   静态资源       │   - WebSocket    │   - 模型训练             │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 📋 系统要求

### 最低要求
- **操作系统**: Linux, macOS, Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 8GB RAM
- **磁盘**: 20GB 可用空间

### 推荐配置
- **CPU**: 4核心以上
- **内存**: 16GB RAM
- **磁盘**: 50GB SSD
- **网络**: 稳定的互联网连接

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/TradeMaster-NTU/TradeMaster.git
cd TradeMaster
```

### 2. 选择部署模式

#### 🔧 开发环境 (推荐新手)

```bash
cd web_interface

# 复制配置文件
cp .env.dev.template .env.dev

# 一键部署
chmod +x scripts/deploy.sh
./scripts/deploy.sh dev

# 或使用Docker Compose
docker-compose -f docker-compose.dev.yml up -d
```

**访问地址**:
- Web界面: http://localhost:3000
- API文档: http://localhost:8000/docs
- 数据库管理: http://localhost:5050

#### 🚀 生产环境

```bash
cd web_interface

# 配置生产环境
cp .env.prod.template .env.prod
# 编辑 .env.prod 填入实际配置

# 部署
./scripts/deploy.sh prod --backup

# 或使用Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

**访问地址**:
- Web界面: http://localhost
- TradeMaster API: http://localhost:8080

#### 🔗 集成模式 (完整生态系统)

```bash
# 在项目根目录
cp .env.integrated.template .env
# 编辑 .env 填入配置

# 部署完整系统
./web_interface/scripts/deploy.sh integrated

# 或使用Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.extended.yml up -d
```

**访问地址**:
- 统一入口: http://localhost (包含Web界面和API)
- TradeMaster API: http://localhost:8080

## 🔧 部署模式详解

### 开发环境 (Development)

**特点**:
- ✅ 支持热重载
- ✅ 包含调试工具
- ✅ 详细错误信息
- ✅ 开发工具集成

**服务组件**:
- PostgreSQL (端口 5432)
- Redis (端口 6379)  
- 后端API (端口 8000)
- 前端开发服务器 (端口 3000)
- Nginx代理 (端口 80)
- pgAdmin (端口 5050)
- Redis Commander (端口 8081)
- MailHog (端口 8025)

**启动命令**:
```bash
# 基础启动
docker-compose -f docker-compose.dev.yml up -d

# 包含开发工具
docker-compose -f docker-compose.dev.yml --profile tools up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 生产环境 (Production)

**特点**:
- 🔒 安全加固
- ⚡ 性能优化
- 📊 监控集成
- 🔄 自动备份

**服务组件**:
- PostgreSQL (内部)
- Redis (内部)
- 后端API (多实例)
- 前端服务 (多实例)
- Nginx负载均衡器 (端口 80/443)
- Prometheus监控 (端口 9090)
- Grafana仪表板 (端口 3001)

**启动命令**:
```bash
# 生产部署
docker-compose -f docker-compose.prod.yml up -d

# 包含监控
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# 扩展后端实例
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### 集成模式 (Integrated)

**特点**:
- 🔗 完整TradeMaster生态系统
- 🌐 统一访问入口
- 📊 数据共享
- 🔄 无缝集成

**服务架构**:
```
统一网关 (localhost)
├── /              → Web界面
├── /api/v1/       → Web界面API
├── /trademaster/  → TradeMaster核心API
└── /ws/           → WebSocket连接
```

## ⚙️ 配置说明

### 环境变量配置

#### 开发环境 (.env.dev)
```bash
# 基础配置
PROJECT_NAME=TradeMaster Web Interface (Dev)
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库配置
POSTGRES_PASSWORD=dev_password_123
REDIS_PASSWORD=

# 安全配置 (开发环境使用弱密钥)
SECRET_KEY=dev-secret-key-123456789
```

#### 生产环境 (.env.prod)
```bash
# 基础配置
PROJECT_NAME=TradeMaster Web Interface
DEBUG=false
LOG_LEVEL=INFO

# 数据库配置 - 必须修改
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD_123!@#
REDIS_PASSWORD=CHANGE_THIS_REDIS_PASSWORD_456!@#

# 安全配置 - 必须修改
SECRET_KEY=CHANGE_THIS_TO_A_VERY_STRONG_RANDOM_SECRET_KEY

# 域名配置
BACKEND_CORS_ORIGINS=https://your-domain.com
REACT_APP_API_BASE_URL=https://your-domain.com/api/v1
```

### Docker Compose 文件说明

| 文件 | 用途 | 环境 |
|------|------|------|
| `docker-compose.dev.yml` | 开发环境 | 本地开发 |
| `docker-compose.prod.yml` | 生产环境 | 生产部署 |
| `docker-compose.extended.yml` | 集成模式 | 完整系统 |

### 数据持久化

**数据卷配置**:
```yaml
volumes:
  postgres_data:     # 数据库数据
  redis_data:        # 缓存数据  
  backend_logs:      # 后端日志
  backend_uploads:   # 上传文件
  nginx_cache:       # 静态资源缓存
```

**备份位置**:
- 开发环境: `./docker/volumes/`
- 生产环境: `/opt/trademaster/`

## 📊 监控和维护

### 健康检查

**检查服务状态**:
```bash
# 查看容器状态
docker-compose ps

# 查看健康检查
docker-compose ps | grep healthy

# 手动健康检查
curl http://localhost/health
curl http://localhost:8000/api/v1/health
```

### 日志管理

**查看日志**:
```bash
# 所有服务日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# 实时日志
docker-compose logs -f --tail=100
```

**日志配置**:
- 自动轮转
- 压缩存储
- 大小限制: 50MB/文件
- 保留数量: 10个文件

### 监控仪表板

**Grafana仪表板** (生产环境):
- URL: http://localhost:3001
- 默认用户: admin
- 密码: 在环境变量中配置

**监控指标**:
- 系统资源使用率
- API响应时间
- 数据库性能
- 错误率统计

### 数据备份

**自动备份**:
```bash
# 启用备份服务
docker-compose -f docker-compose.prod.yml --profile backup up -d

# 手动备份
./scripts/deploy.sh prod --backup
```

**备份内容**:
- PostgreSQL数据库
- 上传文件
- 配置文件
- 日志文件

## 🔧 常用管理命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 查看资源使用
docker stats
```

### 数据库管理

```bash
# 连接数据库
docker-compose exec postgres psql -U trademaster -d trademaster_web

# 数据库备份
docker-compose exec postgres pg_dump -U trademaster trademaster_web > backup.sql

# 数据库恢复
docker-compose exec -T postgres psql -U trademaster -d trademaster_web < backup.sql

# 运行迁移
docker-compose exec backend alembic upgrade head
```

### 镜像管理

```bash
# 构建镜像
docker-compose build

# 强制重建
docker-compose build --no-cache

# 清理旧镜像
docker system prune -a

# 查看镜像大小
docker images | grep trademaster
```

## 🚨 故障排除

### 常见问题

#### 1. 端口冲突
**现象**: 容器启动失败，提示端口被占用
```bash
# 检查端口占用
lsof -i :80
lsof -i :8000

# 解决方案
# 修改 docker-compose.yml 中的端口映射
ports:
  - "8080:80"  # 改为其他端口
```

#### 2. 数据库连接失败
**现象**: 后端无法连接数据库
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

#### 3. 前端无法加载
**现象**: 访问前端显示空白页面
```bash
# 检查前端构建
docker-compose logs frontend

# 重新构建前端
docker-compose build frontend --no-cache

# 检查nginx配置
docker-compose exec nginx nginx -t
```

#### 4. API请求失败
**现象**: 前端无法调用后端API
```bash
# 检查CORS配置
# 确保 BACKEND_CORS_ORIGINS 包含前端域名

# 检查API健康状态
curl http://localhost:8000/api/v1/health

# 查看后端日志
docker-compose logs backend | grep ERROR
```

### 性能优化

#### 1. 数据库优化
```bash
# 调整数据库连接池
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=50

# 优化数据库配置
POSTGRES_SHARED_BUFFERS=512MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

#### 2. 缓存优化
```bash
# Redis内存配置
REDIS_MAXMEMORY=1gb
REDIS_MAXMEMORY_POLICY=allkeys-lru

# Nginx缓存
proxy_cache_valid 200 1d;
```

#### 3. 资源限制
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

### 安全加固

#### 1. 密码安全
```bash
# 生成强密码
openssl rand -base64 32

# 检查密码强度
grep "CHANGE_THIS" .env.prod  # 不应有输出
```

#### 2. SSL证书配置
```bash
# 生成自签名证书（开发环境）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/nginx/ssl/key.pem \
    -out docker/nginx/ssl/cert.pem

# 配置Let's Encrypt（生产环境）
# 使用 certbot 获取免费SSL证书
```

#### 3. 防火墙配置
```bash
# 开放必要端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp

# 限制数据库端口（仅内部访问）
ufw deny 5432/tcp
ufw deny 6379/tcp
```

## 📚 进阶主题

### 集群部署

使用Docker Swarm进行集群部署:

```bash
# 初始化Swarm
docker swarm init

# 部署Stack
docker stack deploy -c docker-compose.prod.yml trademaster

# 扩展服务
docker service scale trademaster_backend=3
```

### CI/CD集成

GitHub Actions示例:

```yaml
name: Deploy TradeMaster Web Interface

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to production
        run: |
          cd web_interface
          ./scripts/deploy.sh prod --backup
```

### 自定义开发

**添加新服务**:
1. 在`docker-compose.dev.yml`中添加服务定义
2. 配置网络和数据卷
3. 更新健康检查和监控

**修改构建配置**:
1. 编辑对应的`Dockerfile`
2. 调整构建参数
3. 重新构建镜像

## 📞 获取帮助

- **文档**: [TradeMaster文档](https://trademaster.readthedocs.io/)
- **问题报告**: [GitHub Issues](https://github.com/TradeMaster-NTU/TradeMaster/issues)
- **社区讨论**: [TradeMaster社区](https://github.com/TradeMaster-NTU/TradeMaster/discussions)

---

## 📄 许可证

本项目基于 MIT 许可证开源。详情请参阅 [LICENSE](../LICENSE) 文件。

**最后更新**: 2025年8月15日  
**版本**: 1.0.0  
**维护团队**: TradeMaster Development Team