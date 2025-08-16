# TradeMaster Web Interface 🚀

TradeMaster Web Interface 是一个现代化的量化交易策略管理和分析平台，提供直观的Web界面用于策略开发、回测、实盘交易和风险管理。

## ✨ 特性

### 🎯 核心功能
- **策略管理**: 完整的策略生命周期管理
- **实时监控**: 实时策略性能监控和风险控制
- **回测分析**: 强大的历史数据回测和分析工具
- **可视化分析**: 丰富的图表和数据可视化
- **用户权限**: 多用户支持和细粒度权限控制

### 🛠️ 技术特性
- **现代化架构**: React + FastAPI + PostgreSQL
- **响应式设计**: 支持桌面和移动设备
- **实时通信**: WebSocket 实时数据推送
- **高性能**: 优化的前后端性能
- **安全性**: 完整的身份验证和授权机制
- **可扩展**: 模块化设计，易于扩展

## 🏗️ 技术栈

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI组件**: Ant Design + Tailwind CSS
- **图表库**: Apache ECharts
- **状态管理**: Redux Toolkit + RTK Query
- **测试**: Vitest + Testing Library

### 后端
- **框架**: FastAPI + Python 3.8+
- **数据库**: PostgreSQL + Redis
- **ORM**: SQLAlchemy + Alembic
- **身份验证**: JWT + OAuth2
- **文档**: OpenAPI/Swagger 自动生成
- **测试**: Pytest + AsyncIO

### 开发工具
- **容器化**: Docker + Docker Compose
- **代码质量**: ESLint + Prettier + Black + isort
- **预提交**: pre-commit hooks
- **CI/CD**: GitHub Actions
- **监控**: 自定义监控脚本

## 🚀 快速开始

### 📋 系统要求

- **Node.js**: >= 18.0.0
- **Python**: >= 3.8
- **PostgreSQL**: >= 12.0
- **Redis**: >= 6.0 (可选，用于缓存)
- **Docker**: >= 20.10 (可选，用于容器化部署)

### 🛠️ 一键环境设置

```bash
# 克隆项目
git clone https://github.com/your-org/trademaster-web-interface.git
cd trademaster-web-interface

# 一键设置开发环境
./scripts/dev-setup.sh

# 或者使用 Makefile
make setup
```

### 🏃‍♂️ 启动开发服务

```bash
# 启动所有服务
make dev

# 或者分别启动
make dev-backend    # 启动后端服务 (http://localhost:8000)
make dev-frontend   # 启动前端服务 (http://localhost:3000)
```

### 🐳 Docker 快速启动

```bash
# 构建并启动所有服务
docker-compose up --build

# 或者使用 Makefile
make docker-dev
```

## 📖 详细文档

### 🔧 开发指南

- [开发环境设置](docs/development/setup.md)
- [代码规范](docs/development/coding-standards.md)
- [Git工作流](docs/development/git-workflow.md)
- [测试指南](docs/development/testing.md)

### 🏗️ 架构文档

- [系统架构](docs/architecture/system-overview.md)
- [数据库设计](docs/architecture/database-schema.md)
- [API文档](docs/api/README.md)
- [前端架构](docs/frontend/architecture.md)

### 🚀 部署指南

- [生产环境部署](docs/deployment/production.md)
- [Docker部署](docs/deployment/docker.md)
- [性能优化](docs/deployment/performance.md)
- [监控和日志](docs/deployment/monitoring.md)

## 🛠️ 开发命令

### 📦 包管理

```bash
# 安装依赖
make install            # 安装所有依赖
make install-backend    # 仅安装后端依赖
make install-frontend   # 仅安装前端依赖

# 更新依赖
make update-deps        # 更新所有依赖
```

### 🔍 代码质量

```bash
# 代码格式化
make format             # 格式化所有代码
make format-backend     # 格式化后端代码
make format-frontend    # 格式化前端代码

# 代码检查
make lint               # 检查所有代码
make lint-backend       # 检查后端代码
make lint-frontend      # 检查前端代码

# 类型检查
make type-check         # TypeScript类型检查
make mypy              # Python类型检查
```

### 🧪 测试

```bash
# 运行所有测试
make test               # 运行所有测试
make test-backend       # 运行后端测试
make test-frontend      # 运行前端测试

# 测试覆盖率
make test-coverage      # 生成测试覆盖率报告

# 监听模式测试
make test-watch         # 文件变更时自动运行测试
```

### 🏗️ 构建

```bash
# 构建项目
make build              # 构建所有项目
make build-backend      # 构建后端
make build-frontend     # 构建前端

# Docker构建
make docker-build       # 构建Docker镜像
make docker-push        # 推送Docker镜像
```

### 📊 监控和分析

```bash
# 性能检查
./scripts/performance-check.sh              # 完整性能检查
./scripts/performance-check.sh --backend    # 后端性能检查
./scripts/performance-check.sh --report     # 生成性能报告

# 安全检查
./scripts/security-check.sh                 # 完整安全检查
./scripts/security-check.sh --dependencies  # 依赖漏洞扫描
./scripts/security-check.sh --report       # 生成安全报告

# 系统监控
./scripts/monitor.sh                        # 系统监控
./scripts/monitor.sh --dashboard           # 监控面板
./scripts/monitor.sh --duration 300        # 监控5分钟
```

## 🔧 配置说明

### 🌍 环境变量

项目使用环境变量进行配置，主要配置文件：

- **后端配置**: `web_interface/backend/.env`
- **前端配置**: `web_interface/frontend/.env`

#### 后端环境变量

```bash
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trademaster
POSTGRES_PASSWORD=your_password
POSTGRES_DB=trademaster

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT配置
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 其他配置
DEBUG=true
LOG_LEVEL=INFO
```

#### 前端环境变量

```bash
# API配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# 应用配置
VITE_APP_NAME=TradeMaster
VITE_APP_VERSION=1.0.0
```

### ⚙️ 详细配置

- [后端配置说明](docs/configuration/backend.md)
- [前端配置说明](docs/configuration/frontend.md)
- [数据库配置](docs/configuration/database.md)

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详细信息。

### 📋 贡献流程

1. **Fork** 项目到您的GitHub账户
2. **创建** 功能分支 (`git checkout -b feature/AmazingFeature`)
3. **提交** 您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. **推送** 到分支 (`git push origin feature/AmazingFeature`)
5. **创建** Pull Request

### 🔍 代码审查

所有代码都需要经过审查才能合并：

- 自动化测试必须通过
- 代码质量检查必须通过
- 至少一个维护者的审查批准

## 🐛 问题报告

如果您发现了bug或有功能建议，请：

1. **搜索** 现有的 [Issues](https://github.com/your-org/trademaster-web-interface/issues)
2. **创建** 新的Issue，详细描述问题
3. **提供** 复现步骤和环境信息

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

### 🌟 核心贡献者

- [贡献者列表](CONTRIBUTORS.md)

### 🛠️ 使用的开源项目

- [React](https://reactjs.org/) - 用户界面构建
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [PostgreSQL](https://www.postgresql.org/) - 强大的关系型数据库
- [Ant Design](https://ant.design/) - 企业级UI设计语言
- [Vite](https://vitejs.dev/) - 下一代前端构建工具

## 📞 联系我们

- **项目主页**: [GitHub Repository](https://github.com/your-org/trademaster-web-interface)
- **文档**: [在线文档](https://docs.trademaster.example.com)
- **问题报告**: [GitHub Issues](https://github.com/your-org/trademaster-web-interface/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-org/trademaster-web-interface/discussions)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个Star！ ⭐**

[![GitHub stars](https://img.shields.io/github/stars/your-org/trademaster-web-interface?style=social)](https://github.com/your-org/trademaster-web-interface/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/your-org/trademaster-web-interface?style=social)](https://github.com/your-org/trademaster-web-interface/network/members)

</div>

## 🚀 项目状态

[![Build Status](https://github.com/your-org/trademaster-web-interface/workflows/CI/badge.svg)](https://github.com/your-org/trademaster-web-interface/actions)
[![codecov](https://codecov.io/gh/your-org/trademaster-web-interface/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/trademaster-web-interface)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node Version](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

<div align="center">
  <sub>Built with ❤️ by the TradeMaster team</sub>
</div>