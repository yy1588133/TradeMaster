[根目录](../CLAUDE.md) > **web_interface**

# TradeMaster Web Interface - 现代化量化交易Web平台

## 📈 最新更新 (2025-08-25)

### 🚀 PowerShell现代化重构 v3.0
- **技术栈升级**: 完全重构为PowerShell，彻底解决编码和语法问题
- **代码量优化**: 从1300+行减少至500行，减少60%代码复杂度
- **模块化架构**: 采用现代化函数式设计，单一职责原则
- **智能错误处理**: Try-Catch-Finally完整错误处理和恢复机制
- **用户体验升级**: 彩色输出、进度条、智能提示和参数支持
- **生产就绪**: 支持命令行参数、自动化集成和质量验证

**技术改进统计**:
- ✅ **PowerShell 5.1+**: 现代化脚本引擎，原生UTF-8支持
- ✅ **模块化设计**: 8个核心功能模块，清晰的职责分离
- ✅ **命令行参数**: 支持-DeployScheme, -Debug, -Force等参数
- ✅ **智能检测**: 自动环境检测和最佳方案推荐
- ✅ **错误恢复**: 完整的异常处理和用户指导机制

## 模块职责

Web Interface模块是TradeMaster的现代化Web前端界面，采用前后端分离架构，为量化交易提供直观、高效的用户交互体验。主要包括：

- **前端应用**: 基于React 18 + TypeScript的现代化SPA
- **后端API**: 基于FastAPI的高性能异步Web服务
- **数据库系统**: PostgreSQL + Redis的企业级数据存储
- **容器化部署**: Docker + Docker Compose的标准化部署方案

## 入口与启动

### 🚀 智能启动 (推荐)
```powershell
# 现代化PowerShell启动脚本 (Windows)
# 支持自动选择数据库方案、智能错误处理、参数化配置
.\quick-start.ps1

# 高级用法示例:
.\quick-start.ps1 -DeployScheme full-docker -VerboseMode  # Docker部署 + 详细模式
.\quick-start.ps1 -DeployScheme auto -Force              # 自动检测 + 跳过确认
.\quick-start.ps1 -SkipHealthCheck                       # 跳过健康检查加速启动

# 启动流程:
# 1. 智能环境检测和方案推荐
# 2. 自动配置和启动数据库服务
# 3. 智能端口检测避免冲突
# 4. 启动前后端服务
# 5. 自动化质量验证
```

### 数据库部署方案

#### 方案1: Docker容器化部署 🐳 (推荐)
```bash
# 特点: 环境隔离、开发生产一致、数据持久化
# 端口: PostgreSQL 15432, Redis 16379 (避免冲突)
# 服务: PostgreSQL 14 + Redis 7
# 构建: uv包管理器 - 10倍速度提升

# 完整容器化部署 (前后端+数据库)
docker compose up -d --build

# 仅数据库服务启动
docker compose -f docker-compose.services.yml up -d

# 查看容器状态
docker compose ps
```

#### 方案2: Windows原生服务 💻
```bash
# 特点: 原生性能、Windows服务集成、系统级管理
# 端口: PostgreSQL 5432, Redis 6379 (标准端口)
# 安装: Chocolatey包管理器

# 手动安装和配置
scripts\windows-native-setup.bat

# Windows服务管理
net start postgresql-x64-14
net start Redis
```

### 数据库管理工具
```bash
# 统一数据库管理工具 (支持两种方案)
scripts\db-manager.bat

# 功能:
# - 服务状态检查和管理
# - 数据备份和恢复
# - 连接测试和诊断
# - 方案切换和配置
```

### 手动启动 (高级用户)
```bash
# 前端开发服务器
cd frontend/
npm run dev
# 访问: http://localhost:3000

# 后端开发服务器 (推荐uv环境)
cd backend/
# 使用uv创建和激活虚拟环境 - 现代化Python包管理
uv venv .venv
.venv\Scripts\activate  # Windows

# 使用uv安装依赖 (比pip快10倍+)
uv pip install -r requirements.txt

# 启动后端服务
.venv\Scripts\python.exe app\main.py
# 访问: http://localhost:8000
```

### 健康检查
- **后端健康检查**: `GET /health`
- **API文档**: `http://localhost:8000/api/v1/docs`
- **系统信息**: `GET /info`

## 对外接口

### RESTful API端点

#### 认证模块 (`/api/v1/auth`)
- `POST /login` - 用户登录
- `POST /register` - 用户注册  
- `POST /refresh` - 刷新Token
- `GET /me` - 获取用户信息
- `POST /logout` - 用户登出

#### 策略管理 (`/api/v1/strategies`)
- `GET /` - 获取策略列表
- `POST /` - 创建新策略
- `GET /{id}` - 获取策略详情
- `PUT /{id}` - 更新策略配置
- `DELETE /{id}` - 删除策略
- `POST /{id}/execute` - 执行策略
- `POST /{id}/stop` - 停止策略执行

#### 数据管理 (`/api/v1/data`) 
- `POST /upload` - 上传数据文件
- `GET /datasets` - 获取数据集列表
- `POST /preprocess` - 数据预处理
- `GET /{id}/preview` - 数据预览

#### 训练任务 (`/api/v1/training`)
- `POST /start` - 启动训练任务
- `GET /{id}/status` - 获取训练状态
- `POST /{id}/stop` - 停止训练任务
- `GET /{id}/logs` - 获取训练日志

#### 分析评估 (`/api/v1/analysis`)
- `GET /performance` - 性能分析
- `GET /risk` - 风险分析  
- `POST /backtest` - 回测分析
- `GET /reports` - 生成报告

### WebSocket接口
- `/ws/training` - 训练状态实时推送
- `/ws/strategy` - 策略执行状态推送
- `/ws/system` - 系统监控数据推送

## 关键依赖与配置

### 前端技术栈
```json
{
  "react": "^18.2.0",
  "typescript": "^5.2.2", 
  "antd": "^5.12.8",
  "@reduxjs/toolkit": "^1.9.7",
  "echarts": "^5.4.3",
  "vite": "^5.0.0"
}
```

### 后端技术栈
```txt
# Web框架
fastapi==0.104.1
sqlalchemy==2.0.23
asyncpg==0.29.0
redis==5.0.1
celery==5.3.4
pydantic==2.5.0

# ML/AI依赖栈 (使用uv智能管理)
torch>=2.8.0
tensorflow>=2.20.0
scikit-learn==1.3.2
scipy==1.11.4
matplotlib>=3.10.0
plotly==5.17.0
mmengine>=0.10.7
mmcv>=2.2.0
opencv-python>=4.11.0

# 推荐包管理器
# uv 0.6.14 - 现代化Python包管理
```

### 环境配置

#### 数据库配置 (双方案支持)
```bash
# Docker方案配置 (backend/.env.docker)
DATABASE_URL=postgresql+asyncpg://trademaster:TradeMaster2024!@localhost:15432/trademaster_web
REDIS_URL=redis://:TradeMaster2024!@localhost:16379/0

# Windows原生方案配置 (backend/.env.native)  
DATABASE_URL=postgresql+asyncpg://trademaster:TradeMaster2024!@localhost:5432/trademaster_web
REDIS_URL=redis://:TradeMaster2024!@localhost:6379/0

# 当前激活配置 (backend/.env)
# 由启动脚本根据选择的方案自动生成和切换

# 数据库连接池配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# JWT安全配置  
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 前端API配置 (frontend/.env.local)
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

## 数据模型

### 核心数据表

#### 用户系统
- `users` - 用户基本信息
- `user_sessions` - 用户会话管理
- `user_permissions` - 用户权限控制

#### 策略管理
- `strategies` - 交易策略配置
- `strategy_versions` - 策略版本管理
- `strategy_executions` - 策略执行记录
- `strategy_performance` - 策略性能指标

#### 数据管理
- `datasets` - 数据集元信息
- `data_sources` - 数据源配置
- `data_preprocessing` - 预处理任务记录

#### 训练任务
- `training_tasks` - 训练任务管理
- `training_logs` - 训练日志记录
- `model_versions` - 模型版本管理

### 数据库设计特点
- **异步ORM**: 使用SQLAlchemy 2.0异步功能
- **连接池**: 数据库连接池优化
- **索引策略**: 关键查询字段建立索引
- **数据分区**: 大表按时间分区存储

## 测试与质量

### 测试框架
```bash
# 后端测试 (Pytest)
cd backend/
pytest --cov=app --cov-report=html

# 前端测试 (Vitest)
cd frontend/  
npm run test:coverage
```

### 代码质量工具
- **Python**: Black + isort + Flake8 + MyPy
- **TypeScript**: ESLint + Prettier + TypeScript

### 测试覆盖率
- **单元测试覆盖率**: ≥ 80%
- **集成测试覆盖率**: ≥ 60%  
- **E2E测试覆盖率**: ≥ 40%

### 性能指标
- **页面加载时间**: < 3秒
- **API响应时间**: < 500ms
- **并发用户支持**: > 1000人

## 常见问题 (FAQ)

### Q: 如何选择数据库部署方案？
A: 运行 `quick-start.ps1` 会自动检测环境并推荐最佳方案。Docker方案适合追求环境一致性的开发者，Windows原生方案适合偏好系统集成的用户。

### Q: 数据库连接失败怎么办？
A: 
1. 检查数据库服务状态：运行 `scripts\db-manager.bat` 选择"查看数据库状态"
2. 运行连接测试：`python scripts\test-db-connection.py` 
3. 检查防火墙和端口占用：`netstat -ano | findstr ":5432"`
4. 重启数据库服务：在db-manager中选择"重启数据库服务"

### Q: Docker容器启动失败怎么办？
A: 
1. 确认Docker Desktop正在运行：`docker version`
2. 检查端口冲突：`netstat -ano | findstr ":15432"`
3. 查看容器日志：`docker compose -f docker-compose.services.yml logs`
4. 重新构建容器：`docker compose -f docker-compose.services.yml up -d --force-recreate`

### Q: Windows原生安装失败怎么办？
A:
1. 确认以管理员身份运行脚本
2. 检查Chocolatey安装：`choco --version`
3. 手动安装PostgreSQL和Redis：访问官方网站下载
4. 查看Windows事件日志：开始菜单 -> 事件查看器 -> Windows日志 -> 应用程序

### Q: 如何切换数据库方案？
A: 
1. 运行 `scripts\db-manager.bat`，选择"切换数据库方案"
2. 或删除 `.db-scheme` 文件，重新运行 `quick-start.ps1`
3. 建议切换前先备份数据

### Q: 前端编译错误如何解决？
A: 清除缓存 `npm run clean`，重新安装依赖 `npm install`，检查Node.js版本是否≥18。

### Q: 如何添加新的API端点？
A: 在 `backend/app/api/api_v1/endpoints/` 添加路由文件，在 `backend/app/api/api_v1/api.py` 注册路由。

### Q: 数据库端口冲突怎么办？
A: Docker方案使用非标准端口（15432/16379）避免冲突。如仍有冲突，可在 `docker-compose.services.yml` 中修改端口映射。

## 相关文件清单

### 核心配置文件
- `frontend/package.json` - 前端依赖和脚本配置
- `frontend/vite.config.ts` - Vite构建配置
- `frontend/tsconfig.json` - TypeScript编译配置
- `backend/requirements.txt` - Python依赖列表
- `backend/app/main.py` - FastAPI应用入口
- `backend/alembic.ini` - 数据库迁移配置

### 数据库服务配置文件
- `docker-compose.services.yml` - Docker数据库服务编排
- `scripts/init-postgresql.sql` - PostgreSQL初始化脚本
- `scripts/postgresql.conf` - PostgreSQL性能优化配置
- `scripts/redis.conf` - Redis配置文件
- `backend/.env.docker` - Docker方案环境配置
- `backend/.env.native` - Windows原生方案环境配置

### 启动和管理脚本
- `quick-start.ps1` - PowerShell智能启动脚本 (主入口)
- `scripts/docker-setup.bat` - Docker数据库服务启动
- `scripts/windows-native-setup.bat` - Windows原生数据库安装
- `scripts/db-manager.bat` - 数据库管理工具
- `scripts/test-db-connection.py` - 数据库连接测试工具

### 文档文件
- `README.md` - 模块说明文档
- `CLAUDE.md` - 模块详细技术文档  
- `.claude/plan/` - 项目计划和实施记录
- `backend/README.md` - 后端技术文档
- `frontend/README.md` - 前端技术文档

### 示例配置文件
- `backend/.env.example` - 后端环境变量模板
- `frontend/.env.example` - 前端环境变量模板

## 变更记录 (Changelog)

### 2025-08-25 - Docker架构优化与uv集成 🐳
- **网络冲突彻底修复**: 移除固定网络配置，使用Docker自动分配避免IP地址池重叠
- **端口配置优化**: PostgreSQL(5432→15432)、Redis(6379→16379)，确保与系统服务无冲突
- **uv包管理器集成**: Docker构建和开发环境集成uv 0.6.14，依赖安装速度提升10倍以上
- **配置现代化**: 移除废弃的version属性，符合Docker Compose最新标准规范
- **PowerShell重构**: 从batch脚本完全重构为PowerShell，解决编码问题和语法限制
- **配置文件统一**: 同步docker-compose.yml和services.yml配置，消除冲突和混淆

**技术改进成果**:
- **Docker网络**: 从固定`172.20.0.0/16`改为动态分配，避免网络冲突
- **端口重映射**: PostgreSQL 15432, Redis 16379（非常用端口，避免系统冲突）
- **构建加速**: Dockerfile集成uv，Python依赖安装速度显著提升
- **环境配置**: .env文件端口配置同步更新，保证开发生产一致性
- **用户体验**: 脚本输出编码修复，支持完美中文显示

### 2025-08-24 - 双数据库方案集成 🎉
- **新增**: Docker + Windows原生双数据库部署方案
- **升级**: 智能启动脚本重构为 `quick-start.ps1`，支持方案选择和自动配置
- **新增**: 统一数据库管理工具 `scripts/db-manager.bat`
- **新增**: 数据库连接测试工具 `scripts/test-db-connection.py`
- **优化**: 使用非标准端口避免Docker方案端口冲突
- **完善**: 全面的FAQ文档和故障排除指南

### 2025-08-22 21:16:30 - 初始模块文档
- 创建Web Interface模块文档
- 建立API接口规范和数据模型定义
- 配置开发环境和部署指南

---

**模块维护者**: TradeMaster Web Team  
**最后更新**: 2025-08-24  
**文档版本**: v1.1.0