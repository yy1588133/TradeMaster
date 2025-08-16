# 开发环境设置指南

本指南将帮助您快速设置TradeMaster Web Interface的开发环境。

## 📋 系统要求

### 必需软件

- **Node.js**: >= 18.0.0 ([下载](https://nodejs.org/))
- **Python**: >= 3.8 ([下载](https://python.org/downloads/))
- **PostgreSQL**: >= 12.0 ([下载](https://postgresql.org/download/))
- **Git**: 最新版本 ([下载](https://git-scm.com/downloads))

### 推荐软件

- **Redis**: >= 6.0 ([下载](https://redis.io/download)) - 用于缓存和会话存储
- **Docker**: >= 20.10 ([下载](https://docker.com/get-started)) - 用于容器化开发
- **VS Code**: 推荐的IDE ([下载](https://code.visualstudio.com/))

### 包管理器

- **前端**: pnpm (推荐) 或 npm
- **后端**: pip + virtualenv

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-org/trademaster-web-interface.git
cd trademaster-web-interface
```

### 2. 一键环境设置

我们提供了自动化脚本来简化设置过程：

```bash
# 使用设置脚本（推荐）
./scripts/dev-setup.sh

# 或使用 Makefile
make setup
```

### 3. 验证安装

```bash
# 检查安装状态
make check-env

# 运行测试确保一切正常
make test
```

## 🔧 手动设置步骤

如果自动化脚本遇到问题，您可以按照以下步骤手动设置：

### 1. 数据库设置

#### PostgreSQL 设置

```bash
# 启动 PostgreSQL 服务
sudo service postgresql start  # Linux
brew services start postgresql # macOS

# 创建数据库和用户
sudo -u postgres psql
```

```sql
-- 在 PostgreSQL 控制台中执行
CREATE USER trademaster WITH PASSWORD 'your_password';
CREATE DATABASE trademaster OWNER trademaster;
GRANT ALL PRIVILEGES ON DATABASE trademaster TO trademaster;
\q
```

#### Redis 设置（可选）

```bash
# 启动 Redis 服务
sudo service redis-server start  # Linux
brew services start redis        # macOS

# 测试连接
redis-cli ping
```

### 2. 后端设置

```bash
cd web_interface/backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 复制环境变量文件
cp .env.template .env

# 编辑环境变量
nano .env  # 或使用您喜欢的编辑器
```

#### 后端环境变量配置

在 `web_interface/backend/.env` 文件中配置：

```bash
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trademaster
POSTGRES_PASSWORD=your_password
POSTGRES_DB=trademaster

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT 配置
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]

# 外部服务配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-email-password
```

#### 数据库迁移

```bash
# 运行数据库迁移
alembic upgrade head

# 创建初始数据（可选）
python scripts/init_db.py
```

### 3. 前端设置

```bash
cd web_interface/frontend

# 安装 pnpm（如果未安装）
npm install -g pnpm

# 安装依赖
pnpm install

# 复制环境变量文件
cp .env.development.template .env.development

# 编辑环境变量
nano .env.development
```

#### 前端环境变量配置

在 `web_interface/frontend/.env.development` 文件中配置：

```bash
# API 配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000

# 应用配置
VITE_APP_NAME=TradeMaster
VITE_APP_VERSION=1.0.0
VITE_APP_DESCRIPTION=量化交易策略管理平台

# 功能开关
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_DEBUG=true

# 外部服务
VITE_SENTRY_DSN=your-sentry-dsn
VITE_GOOGLE_ANALYTICS_ID=your-ga-id
```

## 🏃‍♂️ 启动开发服务

### 同时启动所有服务

```bash
# 在项目根目录
make dev

# 或者使用脚本
./scripts/dev-start.sh
```

### 分别启动服务

#### 启动后端服务

```bash
cd web_interface/backend
source venv/bin/activate

# 使用 FastAPI 开发服务器
python scripts/dev.py

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在以下地址启动：
- **API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

#### 启动前端服务

```bash
cd web_interface/frontend

# 启动开发服务器
pnpm dev

# 或使用 npm
npm run dev
```

前端服务将在 http://localhost:3000 启动

## 🐳 Docker 开发环境

### 使用 Docker Compose

```bash
# 构建并启动所有服务
docker-compose -f docker-compose.dev.yml up --build

# 后台运行
docker-compose -f docker-compose.dev.yml up -d --build

# 停止服务
docker-compose -f docker-compose.dev.yml down
```

### 单独使用 Docker

#### 后端容器

```bash
cd web_interface/backend

# 构建镜像
docker build -t trademaster-backend:dev .

# 运行容器
docker run -p 8000:8000 --env-file .env trademaster-backend:dev
```

#### 前端容器

```bash
cd web_interface/frontend

# 构建镜像
docker build -t trademaster-frontend:dev .

# 运行容器
docker run -p 3000:3000 trademaster-frontend:dev
```

## 💻 IDE 配置

### VS Code 配置

我们提供了完整的 VS Code 配置：

1. **扩展安装**：
   ```bash
   # VS Code 会自动提示安装推荐扩展
   # 或手动安装 .vscode/extensions.json 中的扩展
   ```

2. **工作区设置**：
   - 代码格式化配置
   - 调试配置
   - 任务配置

3. **调试配置**：
   - 后端 FastAPI 调试
   - 前端 React 调试
   - 数据库连接调试

### 其他 IDE

#### PyCharm/WebStorm

1. 导入项目
2. 配置 Python 解释器（虚拟环境）
3. 配置 Node.js 解释器
4. 设置代码格式化规则

## 🛠️ 开发工具

### 代码质量工具

```bash
# 安装 pre-commit hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files

# 代码格式化
make format

# 代码检查
make lint
```

### 测试工具

```bash
# 运行所有测试
make test

# 运行特定测试
make test-backend
make test-frontend

# 测试覆盖率
make test-coverage

# 监听模式
make test-watch
```

### 性能和安全工具

```bash
# 性能检查
./scripts/performance-check.sh

# 安全检查
./scripts/security-check.sh

# 系统监控
./scripts/monitor.sh --dashboard
```

## 🔍 故障排除

### 常见问题

#### 1. 端口冲突

```bash
# 检查端口占用
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 终止进程
kill -9 <PID>
```

#### 2. 数据库连接失败

```bash
# 检查 PostgreSQL 状态
sudo service postgresql status

# 检查连接
psql -h localhost -U trademaster -d trademaster
```

#### 3. Python 依赖问题

```bash
# 清理并重新安装
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Node.js 依赖问题

```bash
# 清理缓存
pnpm store prune
rm -rf node_modules
pnpm install

# 或使用 npm
npm cache clean --force
rm -rf node_modules
npm install
```

#### 5. Docker 问题

```bash
# 清理 Docker 资源
docker system prune -a

# 重新构建镜像
docker-compose build --no-cache
```

### 调试技巧

#### 后端调试

1. **使用 VS Code 调试器**：
   - 设置断点
   - F5 启动调试模式
   - 使用调试控制台

2. **日志调试**：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger(__name__)
   logger.debug("Debug message")
   ```

#### 前端调试

1. **浏览器开发者工具**：
   - Console 查看日志
   - Network 查看网络请求
   - React DevTools 检查组件

2. **VS Code 调试**：
   - 设置断点
   - 启动调试配置

## 📚 下一步

完成环境设置后，建议阅读：

- [代码规范](coding-standards.md)
- [Git 工作流](git-workflow.md)
- [测试指南](testing.md)
- [API 文档](../api/README.md)

## 🆘 获取帮助

如果您在设置过程中遇到问题：

1. 检查 [故障排除](#-故障排除) 部分
2. 搜索 [GitHub Issues](https://github.com/your-org/trademaster-web-interface/issues)
3. 创建新的 Issue 详细描述问题
4. 加入 [GitHub Discussions](https://github.com/your-org/trademaster-web-interface/discussions) 讨论

---

恭喜！您的开发环境已设置完成。开始享受开发吧！🎉