# TradeMaster Web Interface

## 🎯 项目概述

TradeMaster Web Interface 是一个现代化的量化交易平台Web界面，为[TradeMaster](https://github.com/TradeMaster-NTU/TradeMaster)量化交易框架提供完整的Web端操作界面。该项目采用前后端分离架构，支持策略管理、数据处理、模型训练、回测分析等完整的量化交易工作流程。

### ✨ 主要特性

#### 🔐 **用户认证与权限管理**
- **多角色权限系统**：Admin、User、Analyst、Viewer四种角色
- **JWT令牌认证**：访问令牌和刷新令牌机制
- **API密钥管理**：支持创建和管理API密钥
- **会话管理**：多设备登录控制和会话监控
- **安全增强**：IP白名单、请求限流、登录追踪

#### 📈 **策略管理系统**
- **策略创建与编辑**：可视化策略配置界面
- **多策略类型支持**：算法交易、高频交易、投资组合管理、订单执行
- **策略模板系统**：预定义策略模板，快速创建策略
- **策略版本控制**：支持策略版本管理和回滚
- **实时监控**：策略运行状态实时监控

#### 📊 **数据管理与处理**
- **多数据源支持**：支持CSV、Excel、API等多种数据导入方式
- **数据预处理**：数据清洗、特征工程、缺失值处理
- **数据可视化**：交互式图表展示市场数据和指标
- **数据质量检查**：自动检测数据质量问题

#### 🤖 **模型训练与优化**
- **异步训练任务**：支持长时间运行的训练任务
- **训练进度监控**：实时显示训练进度和性能指标
- **超参数优化**：自动化超参数调优
- **分布式训练支持**：支持多GPU和分布式训练

#### 📋 **回测与分析**
- **回测引擎**：高性能回测系统
- **性能分析**：夏普比率、最大回撤、收益率等指标
- **风险分析**：VaR、CVaR、风险敞口分析
- **对比分析**：多策略性能对比
- **报告生成**：自动生成详细的分析报告

#### 🛠️ **工具集成**
- **FinAgent集成**：智能金融代理支持
- **EarnMore集成**：收益优化工具
- **外部工具接口**：支持第三方工具集成
- **插件系统**：可扩展的插件架构

#### 📱 **现代化用户体验**
- **响应式设计**：支持桌面和移动设备
- **实时通信**：WebSocket实时数据推送
- **国际化支持**：多语言界面支持
- **主题定制**：亮色/暗色主题切换
- **快捷操作**：键盘快捷键支持

## 🏗️ 技术架构

### 前端技术栈
- **框架**：React 18 + TypeScript
- **状态管理**：Redux Toolkit + RTK Query
- **UI组件库**：Ant Design + Ant Design Charts
- **构建工具**：Vite
- **样式方案**：CSS Modules + Styled Components
- **图表库**：ECharts + D3.js
- **HTTP客户端**：Axios
- **路由管理**：React Router v6

### 后端技术栈
- **框架**：FastAPI (Python 3.8+)
- **数据库**：PostgreSQL 13+ + SQLAlchemy 2.0
- **缓存**：Redis 6+
- **任务队列**：Celery + Redis
- **认证**：JWT + Passlib
- **API文档**：OpenAPI/Swagger
- **数据验证**：Pydantic v2
- **异步支持**：全面使用async/await

### 基础设施
- **容器化**：Docker + Docker Compose
- **Web服务器**：Nginx
- **数据库迁移**：Alembic
- **监控**：Prometheus + Grafana
- **日志**：ELK Stack
- **部署**：CI/CD Pipeline

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                       用户访问层                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Web浏览器      │   移动应用        │   API客户端              │
│   (React SPA)   │   (React Native) │   (Python/JavaScript)   │
└─────────────────┴─────────────────┴─────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                       网关层                                │
│   Nginx (负载均衡 + SSL终止 + 静态资源服务)                    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                       应用层                                │
├─────────────────┬─────────────────┬─────────────────────────┤
│   前端服务        │   后端API服务     │   WebSocket服务          │
│   (React Build)  │   (FastAPI)     │   (Socket.IO)           │
└─────────────────┴─────────────────┴─────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     业务服务层                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│   认证服务        │   策略服务        │   数据服务               │
│   用户管理        │   训练服务        │   分析服务               │
└─────────────────┴─────────────────┴─────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      TradeMaster集成层                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   TradeMaster   │   FinAgent      │   EarnMore              │
│   核心系统       │   智能代理       │   收益优化               │
└─────────────────┴─────────────────┴─────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                       数据层                                │
├─────────────────┬─────────────────┬─────────────────────────┤
│   PostgreSQL    │   Redis         │   文件存储               │
│   (主数据库)      │   (缓存/会话)     │   (模型/数据文件)         │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 📦 项目结构

```
TradeMaster/
├── web_interface/                    # Web界面项目根目录
│   ├── README.md                    # 项目主文档
│   ├── docker-compose.dev.yml       # 开发环境Docker编排
│   ├── docker-compose.prod.yml      # 生产环境Docker编排
│   ├── .env.dev                     # 开发环境配置
│   ├── .env.prod.template           # 生产环境配置模板
│   │
│   ├── frontend/                    # 前端应用
│   │   ├── src/
│   │   │   ├── components/          # React组件
│   │   │   ├── pages/              # 页面组件
│   │   │   ├── store/              # Redux状态管理
│   │   │   ├── services/           # API服务
│   │   │   ├── hooks/              # 自定义Hooks
│   │   │   ├── utils/              # 工具函数
│   │   │   └── types/              # TypeScript类型
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   ├── backend/                     # 后端应用
│   │   ├── app/
│   │   │   ├── api/                # API路由
│   │   │   ├── core/               # 核心配置
│   │   │   ├── models/             # 数据模型
│   │   │   ├── schemas/            # 数据验证
│   │   │   ├── services/           # 业务服务
│   │   │   └── main.py            # 应用入口
│   │   ├── alembic/                # 数据库迁移
│   │   ├── requirements.txt
│   │   └── .env.example
│   │
│   ├── docs/                        # 项目文档
│   │   ├── user-guide/             # 用户指南
│   │   ├── development/            # 开发文档
│   │   ├── deployment/             # 部署文档
│   │   ├── project/                # 项目管理
│   │   └── support/                # 帮助支持
│   │
│   ├── docker/                      # Docker配置
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── nginx/
│   │
│   └── scripts/                     # 脚本工具
│       ├── deploy.sh               # 部署脚本
│       ├── backup.sh               # 备份脚本
│       └── dev-setup.sh            # 开发环境搭建
│
└── ... (TradeMaster核心模块)
```

## 🚀 快速开始

### 环境要求

**最低要求**：
- Node.js 16+
- Python 3.8+
- Docker 20.10+
- Docker Compose 2.0+

**推荐配置**：
- 16GB RAM
- 4核CPU
- 50GB 可用磁盘空间

### 1. 克隆项目

```bash
git clone https://github.com/TradeMaster-NTU/TradeMaster.git
cd TradeMaster/web_interface
```

### 2. 一键部署 (推荐)

#### 开发环境部署

```bash
# 复制环境配置
cp .env.dev.template .env.dev

# 一键启动开发环境
chmod +x scripts/deploy.sh
./scripts/deploy.sh dev

# 等待服务启动完成...
```

**访问地址**：
- 🌐 **Web界面**: http://localhost:3000
- 📚 **API文档**: http://localhost:8000/docs
- 🗄️ **数据库管理**: http://localhost:5050 (pgAdmin)
- 🔍 **Redis管理**: http://localhost:8081 (Redis Commander)

#### 生产环境部署

```bash
# 配置生产环境
cp .env.prod.template .env.prod
# 编辑 .env.prod 填入实际配置

# 部署生产环境
./scripts/deploy.sh prod

# 或使用Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 手动部署

#### 前端开发环境

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 后端开发环境

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 初始化数据

```bash
# 创建管理员用户
docker-compose exec backend python app/scripts/init_database.py

# 或手动创建
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "AdminPass123!",
    "role": "admin"
  }'
```

## 🎯 核心功能使用

### 用户认证

```bash
# 用户登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "AdminPass123!"
  }'

# 获取用户信息
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 策略管理

```bash
# 创建策略
curl -X POST "http://localhost:8000/api/v1/strategies" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sample Strategy",
    "strategy_type": "algorithmic_trading",
    "config": {
      "symbol": "BTC-USDT",
      "timeframe": "1d"
    }
  }'

# 启动策略训练
curl -X POST "http://localhost:8000/api/v1/strategies/{id}/train" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 数据管理

```bash
# 上传数据文件
curl -X POST "http://localhost:8000/api/v1/data/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@data.csv" \
  -F "dataset_name=sample_data"
```

## 📚 详细文档

| 文档类型 | 链接 | 描述 |
|---------|------|------|
| 🔰 **用户指南** | [docs/user-guide/](docs/user-guide/) | 面向最终用户的使用指南 |
| 👨‍💻 **开发文档** | [docs/development/](docs/development/) | 开发者技术文档 |
| 🚀 **部署指南** | [docs/deployment/](docs/deployment/) | 部署和运维文档 |
| 📋 **API文档** | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | 完整的API接口文档 |
| 🏗️ **架构文档** | [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构设计文档 |
| 🐳 **Docker部署** | [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md) | Docker部署详细指南 |
| 🆘 **帮助支持** | [docs/support/](docs/support/) | 常见问题和技术支持 |

## 🔧 配置说明

### 环境变量配置

#### 开发环境 (.env.dev)
```bash
# 项目配置
PROJECT_NAME=TradeMaster Web Interface (Dev)
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库配置
POSTGRES_USER=trademaster
POSTGRES_PASSWORD=dev_password_123
POSTGRES_DB=trademaster_web

# 认证配置
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# TradeMaster集成
TRADEMASTER_API_URL=http://localhost:8080
```

#### 生产环境 (.env.prod)
```bash
# 项目配置
PROJECT_NAME=TradeMaster Web Interface
DEBUG=false
LOG_LEVEL=INFO

# 数据库配置 (必须修改)
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD_123!@#
REDIS_PASSWORD=CHANGE_THIS_REDIS_PASSWORD_456!@#

# 安全配置 (必须修改)
SECRET_KEY=CHANGE_THIS_TO_A_VERY_STRONG_RANDOM_SECRET_KEY

# 域名配置
BACKEND_CORS_ORIGINS=["https://your-domain.com"]
REACT_APP_API_BASE_URL=https://your-domain.com/api/v1
```

### Docker Compose配置

| 服务 | 端口 | 描述 |
|------|------|------|
| `nginx` | 80/443 | 反向代理和静态文件服务 |
| `frontend` | 3000 | React开发服务器 |
| `backend` | 8000 | FastAPI后端服务 |
| `postgres` | 5432 | PostgreSQL数据库 |
| `redis` | 6379 | Redis缓存服务 |
| `pgadmin` | 5050 | 数据库管理界面 |

## 🧪 测试

### 前端测试
```bash
cd frontend

# 单元测试
npm run test

# 端到端测试
npm run test:e2e

# 测试覆盖率
npm run test:coverage
```

### 后端测试
```bash
cd backend

# 运行所有测试
pytest

# 测试覆盖率报告
pytest --cov=app --cov-report=html

# 性能测试
pytest tests/test_performance.py
```

## 📊 监控和维护

### 健康检查
```bash
# 系统健康状态
curl http://localhost:8000/health

# 服务状态检查
docker-compose ps

# 资源使用情况
docker stats
```

### 日志管理
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend

# 查看错误日志
docker-compose logs backend | grep ERROR
```

### 数据备份
```bash
# 自动备份
./scripts/backup.sh

# 手动数据库备份
docker-compose exec postgres pg_dump -U trademaster trademaster_web > backup.sql
```

## 🛡️ 安全最佳实践

1. **强密码策略**：生产环境必须使用强密码
2. **HTTPS配置**：生产环境启用SSL/TLS
3. **定期更新**：及时更新依赖包和安全补丁
4. **访问控制**：配置防火墙和网络安全组
5. **数据加密**：敏感数据加密存储
6. **审计日志**：启用操作审计和监控告警

## 🐛 常见问题

### 端口冲突
```bash
# 检查端口占用
lsof -i :80
lsof -i :8000

# 修改端口配置
# 编辑 docker-compose.yml 中的端口映射
```

### 数据库连接失败
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 重启数据库服务
docker-compose restart postgres
```

### API请求失败
```bash
# 检查CORS配置
grep CORS .env

# 检查API健康状态
curl http://localhost:8000/api/v1/health
```

更多故障排除信息请参考：[故障排除指南](docs/support/troubleshooting.md)

## 🤝 贡献指南

我们欢迎社区贡献！请阅读：

1. [贡献指南](docs/project/CONTRIBUTING.md)
2. [开发规范](docs/development/coding-standards.md)
3. [提交规范](docs/development/commit-guidelines.md)

### 快速贡献流程

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 创建 Pull Request

## 📞 支持和联系

- 📖 **文档**: [在线文档](https://trademaster.readthedocs.io/)
- 🐛 **问题报告**: [GitHub Issues](https://github.com/TradeMaster-NTU/TradeMaster/issues)
- 💬 **社区讨论**: [GitHub Discussions](https://github.com/TradeMaster-NTU/TradeMaster/discussions)
- 📧 **邮件联系**: support@trademaster.ai
- 🌐 **官方网站**: https://trademaster.ai

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🔄 更新日志

### v1.0.0 (2025-08-15)
- ✨ 完整的Web界面系统
- 🔐 用户认证和权限管理
- 📈 策略管理和训练系统
- 📊 数据处理和可视化
- 🤖 TradeMaster核心集成
- 📱 响应式前端界面
- 🐳 Docker容器化部署
- 📚 完善的文档体系

### 未来规划
- 🔄 **v1.1.0**: 移动端适配和PWA支持
- 🧠 **v1.2.0**: AI助手和智能推荐
- 🌐 **v1.3.0**: 多语言国际化支持
- 📊 **v2.0.0**: 微服务架构升级

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=TradeMaster-NTU/TradeMaster&type=Date)](https://star-history.com/#TradeMaster-NTU/TradeMaster&Date)

---

**TradeMaster Web Interface** - 让量化交易更简单、更高效、更智能 🚀

[![建设状态](https://img.shields.io/badge/状态-积极开发中-green.svg)](https://github.com/TradeMaster-NTU/TradeMaster)
[![许可证](https://img.shields.io/badge/许可证-MIT-blue.svg)](LICENSE)
[![版本](https://img.shields.io/badge/版本-v1.0.0-brightgreen.svg)](https://github.com/TradeMaster-NTU/TradeMaster/releases)