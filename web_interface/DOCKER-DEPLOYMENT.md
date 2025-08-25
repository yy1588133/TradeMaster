# TradeMaster 完整容器化部署指南

## 🚀 快速开始

### 一键启动 (推荐)
```bash
# 进入web_interface目录
cd web_interface

# 运行智能启动脚本
quick-start.bat

# 根据提示选择部署方案：
# [1] 完整容器化部署 (推荐) - 前后端+数据库全部容器化
# [2] 混合部署 - 仅数据库容器化，前后端本地运行  
# [3] Windows原生服务 - 全部使用Windows原生服务
# [A] 智能检测 - 自动选择最适合的方案
```

### 停止服务
```bash
# 停止所有服务
stop-services.bat
```

## 📋 部署方案详解

### 方案1: 完整容器化部署 🐳 (推荐)
**特点：**
- ✅ 前后端 + PostgreSQL + Redis 全部容器化
- ✅ 环境完全隔离，开发生产一致
- ✅ 一键启停，配置简单
- ✅ 数据持久化，安全可靠

**要求：** 
- Docker Desktop 已安装并运行

**访问地址：**
- 前端界面：http://localhost:3000
- 后端API：http://localhost:8000  
- API文档：http://localhost:8000/docs
- 数据库：localhost:5432
- Redis：localhost:6379

**管理命令：**
```bash
# 查看服务状态
docker compose ps

# 查看服务日志  
docker compose logs

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 完全清理（包含数据）
docker compose down -v
```

### 方案2: 混合部署 (数据库容器化)
**特点：**
- ✅ PostgreSQL + Redis 使用Docker容器
- ✅ 前后端在本地运行，便于开发调试
- ✅ 数据库环境隔离，前后端可热重载

**要求：**
- Docker Desktop 已安装并运行
- Node.js 18+，Python 3.8+

**访问地址：**
- 前端界面：http://localhost:3000 (动态检测端口)
- 后端API：http://localhost:8000 (动态检测端口)
- 数据库：localhost:15432 (避免冲突)
- Redis：localhost:16379 (避免冲突)

### 方案3: Windows原生服务
**特点：**
- ✅ 使用Windows原生PostgreSQL和Redis服务
- ✅ 系统深度集成，原生性能
- ✅ 通过Windows服务管理器管理

**要求：**
- 管理员权限
- Chocolatey 包管理器

**访问地址：**
- 前端界面：http://localhost:3000 (动态检测端口) 
- 后端API：http://localhost:8000 (动态检测端口)
- 数据库：localhost:5432
- Redis：localhost:6379

## 🔧 高级配置

### 启用管理工具 (完整容器化部署)
```bash
# 启动包含pgAdmin和Redis管理工具的完整开发环境
docker compose --profile tools up -d

# 访问管理工具：
# pgAdmin: http://localhost:5050 (admin@trademaster.local / admin123)
# Redis Commander: http://localhost:8081 (admin / admin123)
```

### 启用Nginx网关
```bash
# 启用Nginx反向代理
docker compose --profile nginx up -d

# 通过网关访问：http://localhost:8080
```

### 自定义配置
1. 复制 `.env.docker` 为 `.env`
2. 修改端口、密码等配置
3. 运行 `docker compose up -d`

## 📁 项目结构

```
web_interface/
├── quick-start.bat           # 🚀 智能启动脚本 (主入口)
├── stop-services.bat         # 🛑 服务停止脚本
├── docker-compose.yml        # 🐳 主要Docker配置
├── docker-compose.services.yml # 🗄️ 数据库服务配置
├── .env.docker              # ⚙️ Docker环境配置模板
├── .env.example             # 📋 完整配置文件示例
├── frontend/                # 🎨 React前端
├── backend/                 # ⚡ FastAPI后端  
├── docker/                  # 🐳 Docker配置文件
│   ├── backend/Dockerfile
│   ├── frontend/Dockerfile
│   └── nginx/
├── scripts/                 # 🛠️ 辅助脚本
│   ├── db-manager.bat       # 数据库管理工具
│   └── test-db-connection.py # 数据库连接测试
├── data/                    # 💾 数据持久化目录
└── logs/                    # 📝 日志文件目录
```

## 🐛 常见问题

### Q: Docker容器启动失败？
A: 
1. 检查Docker Desktop是否运行：`docker --version`
2. 检查端口占用：`netstat -ano | findstr ":3000"`  
3. 查看详细错误：`docker compose logs`
4. 重新构建：`docker compose up -d --build --force-recreate`

### Q: 前端页面无法访问？
A:
1. 等待1-2分钟，服务正在初始化
2. 检查容器状态：`docker compose ps`
3. 查看前端日志：`docker compose logs frontend`
4. 确认端口映射：访问 http://localhost:3000

### Q: 后端API返回错误？
A:
1. 检查数据库连接：`docker compose logs postgresql`
2. 检查后端日志：`docker compose logs backend`
3. 验证环境配置：检查 `.env` 文件
4. 手动数据库连接测试：`python scripts/test-db-connection.py`

### Q: 数据库连接失败？
A:
1. 等待数据库初始化完成（约30-60秒）
2. 检查数据库健康状态：`docker compose ps`
3. 手动连接测试：`docker exec -it trademaster-postgresql psql -U trademaster -d trademaster_web`
4. 检查数据目录权限：确保 `data/` 目录可写

### Q: 端口被占用怎么办？
A:
1. 脚本会自动检测并使用其他端口
2. 手动指定端口：修改 `.env` 文件中的端口配置
3. 停止占用端口的服务：`netstat -ano | findstr ":8000"`

### Q: 如何重置所有数据？
A:
```bash
# 停止服务并删除数据
docker compose down -v

# 删除数据目录
rmdir /s data

# 重新启动
quick-start.bat
```

### Q: 如何切换部署方案？
A:
1. 停止当前服务：`stop-services.bat`
2. 删除方案记录：`del .deploy-scheme`
3. 重新运行启动脚本：`quick-start.bat`

## 🔧 开发调试

### 查看实时日志
```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgresql
```

### 进入容器内部
```bash
# 进入后端容器
docker compose exec backend bash

# 进入数据库容器
docker compose exec postgresql psql -U trademaster -d trademaster_web

# 进入Redis容器
docker compose exec redis redis-cli
```

### 重新构建镜像
```bash
# 重新构建所有镜像
docker compose build --no-cache

# 重新构建特定服务
docker compose build --no-cache backend
```

## 📊 性能优化

### 生产环境配置
1. 修改 `.env` 文件：
   ```
   BUILD_ENV=production
   BUILD_TARGET=production
   DEBUG=false
   NODE_ENV=production
   ```

2. 使用生产配置启动：
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

### 资源限制调整
修改 `docker-compose.yml` 中的资源限制：
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

## 📞 技术支持

如果您在部署过程中遇到问题：

1. 首先查阅本文档的常见问题部分
2. 查看项目日志文件：`logs/` 目录
3. 运行诊断脚本：`scripts/test-db-connection.py`
4. 使用数据库管理工具：`scripts/db-manager.bat`

---

**更新时间**: 2025-08-24  
**版本**: v2.0.0  
**支持的Docker版本**: 20.10+  
**支持的系统**: Windows 10/11