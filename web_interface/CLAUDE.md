[根目录](../CLAUDE.md) > **web_interface**

# TradeMaster Web Interface - 现代化量化交易Web平台

## 模块职责

Web Interface模块是TradeMaster的现代化Web前端界面，采用前后端分离架构，为量化交易提供直观、高效的用户交互体验。主要包括：

- **前端应用**: 基于React 18 + TypeScript的现代化SPA
- **后端API**: 基于FastAPI的高性能异步Web服务
- **数据库系统**: PostgreSQL + Redis的企业级数据存储
- **容器化部署**: Docker + Docker Compose的标准化部署方案

## 入口与启动

### 开发环境启动
```bash
# 前端开发服务器
cd frontend/
npm run dev
# 访问: http://localhost:3000

# 后端开发服务器 (推荐uv环境)
cd backend/
# 使用uv创建和激活虚拟环境
uv venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# 使用uv安装依赖 (快速、智能解析)
uv pip install -r requirements.txt

# 启动后端服务
.venv\Scripts\python.exe app\main.py
# 或使用uvicorn启动
# .venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
# 访问: http://localhost:8000
```

### 生产环境启动
```bash
# Docker一键启动
docker-compose -f docker-compose.prod.yml up -d

# 手动启动脚本
./start-dev.sh  # 开发环境
./quick-start.bat  # Windows快速启动
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
```bash
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trademaster
POSTGRES_DB=trademaster

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT配置  
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API配置
VITE_API_BASE_URL=http://localhost:8000
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

### Q: 如何配置开发环境？
A: 运行 `./scripts/dev-setup.sh` 自动配置开发环境，或按照 `docs/DEVELOPMENT_GUIDE.md` 手动配置。

### Q: 数据库连接失败怎么办？
A: 检查PostgreSQL服务状态和 `.env` 配置文件中的数据库连接参数。

### Q: 前端编译错误如何解决？
A: 清除缓存 `npm run clean`，重新安装依赖 `npm install`，检查Node.js版本是否≥18。

### Q: 如何添加新的API端点？
A: 在 `backend/app/api/api_v1/endpoints/` 添加路由文件，在 `backend/app/api/api_v1/api.py` 注册路由。

### Q: 如何自定义前端主题？
A: 修改 `frontend/src/main.tsx` 中的 Ant Design ConfigProvider theme配置。

### Q: Docker部署时端口冲突怎么办？
A: 修改 `docker-compose.yml` 中的端口映射，或使用环境变量覆盖默认端口。

## 相关文件清单

### 核心配置文件
- `frontend/package.json` - 前端依赖和脚本配置
- `frontend/vite.config.ts` - Vite构建配置
- `frontend/tsconfig.json` - TypeScript编译配置
- `backend/requirements.txt` - Python依赖列表
- `backend/app/main.py` - FastAPI应用入口
- `backend/alembic.ini` - 数据库迁移配置

### 部署配置文件
- `docker-compose.dev.yml` - 开发环境容器编排
- `docker-compose.prod.yml` - 生产环境容器编排
- `start-dev.sh` / `start-dev.bat` - 开发启动脚本
- `quick-start.bat` - Windows快速启动脚本

### 文档文件
- `README.md` - 模块说明文档
- `ARCHITECTURE.md` - 架构设计文档
- `docs/` - 详细技术文档目录
- `backend/README.md` - 后端技术文档
- `frontend/README.md` - 前端技术文档

### 示例配置文件
- `.env.example` / `backend/.env.example` - 环境变量模板
- `frontend/.env.example` - 前端环境变量模板

## 变更记录 (Changelog)

### 2025-08-22 21:16:30 - 初始模块文档
- 创建Web Interface模块文档
- 建立API接口规范和数据模型定义
- 配置开发环境和部署指南

---

**模块维护者**: TradeMaster Web Team  
**最后更新**: 2025-08-22 21:16:30  
**文档版本**: v1.0.0