# ==================== TradeMaster Web Interface Makefile ====================
# 统一的项目管理命令
# 使用方法: make <command>

# 环境变量
.PHONY: help setup clean dev build test deploy lint format docker health check-deps
.DEFAULT_GOAL := help

# 颜色定义
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BLUE := \033[34m
RESET := \033[0m

# 项目信息
PROJECT_NAME := TradeMaster Web Interface
VERSION := 1.0.0
PYTHON_VERSION := 3.9
NODE_VERSION := 18

help: ## 显示帮助信息
	@echo "$(GREEN)$(PROJECT_NAME) v$(VERSION)$(RESET)"
	@echo "$(BLUE)可用命令:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'

# ==================== 环境初始化 ====================
setup: ## 🚀 初始化完整开发环境
	@echo "$(GREEN)🚀 初始化 $(PROJECT_NAME) 开发环境...$(RESET)"
	@$(MAKE) check-deps
	@$(MAKE) setup-backend
	@$(MAKE) setup-frontend
	@$(MAKE) setup-tools
	@echo "$(GREEN)✅ 开发环境初始化完成!$(RESET)"

setup-backend: ## 🐍 设置后端Python环境
	@echo "$(BLUE)🐍 设置后端Python环境...$(RESET)"
	cd web_interface/backend && \
	python -m venv venv && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	pip install --upgrade pip setuptools wheel && \
	pip install -r requirements.txt && \
	cp .env.example .env && \
	alembic upgrade head
	@echo "$(GREEN)✅ 后端环境设置完成$(RESET)"

setup-frontend: ## 🌐 设置前端Node.js环境
	@echo "$(BLUE)🌐 设置前端Node.js环境...$(RESET)"
	cd web_interface/frontend && \
	pnpm install && \
	cp ../frontend/.env.development.example .env.development
	@echo "$(GREEN)✅ 前端环境设置完成$(RESET)"

setup-tools: ## 🔧 安装开发工具
	@echo "$(BLUE)🔧 安装开发工具...$(RESET)"
	cd web_interface && \
	python -m pip install --user pre-commit && \
	pre-commit install
	@echo "$(GREEN)✅ 开发工具安装完成$(RESET)"

check-deps: ## 🔍 检查系统依赖
	@echo "$(BLUE)🔍 检查系统依赖...$(RESET)"
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)❌ Python 3 未安装$(RESET)"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "$(RED)❌ Node.js 未安装$(RESET)"; exit 1; }
	@command -v pnpm >/dev/null 2>&1 || { echo "$(RED)❌ pnpm 未安装，请安装: npm install -g pnpm$(RESET)"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "$(YELLOW)⚠️  Docker 未安装，Docker相关功能不可用$(RESET)"; }
	@echo "$(GREEN)✅ 依赖检查完成$(RESET)"

# ==================== 开发服务 ====================
dev: ## 🚀 启动完整开发环境
	@echo "$(GREEN)🚀 启动 $(PROJECT_NAME) 开发环境...$(RESET)"
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## 🐍 启动后端开发服务器
	@echo "$(BLUE)🐍 启动后端开发服务器...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	python scripts/dev.py

dev-frontend: ## 🌐 启动前端开发服务器
	@echo "$(BLUE)🌐 启动前端开发服务器...$(RESET)"
	cd web_interface/frontend && \
	pnpm dev

dev-services: ## 🐳 启动开发服务依赖 (数据库、Redis等)
	@echo "$(BLUE)🐳 启动开发服务依赖...$(RESET)"
	cd web_interface && \
	docker-compose -f docker-compose.dev.yml up -d postgres redis
	@echo "$(GREEN)✅ 开发服务依赖启动完成$(RESET)"

dev-full: ## 🌟 启动完整开发环境 (包含服务依赖)
	@$(MAKE) dev-services
	@sleep 5
	@$(MAKE) dev

# ==================== 构建和部署 ====================
build: ## 🔨 构建整个项目
	@echo "$(GREEN)🔨 构建 $(PROJECT_NAME)...$(RESET)"
	@$(MAKE) build-backend
	@$(MAKE) build-frontend
	@echo "$(GREEN)✅ 项目构建完成$(RESET)"

build-backend: ## 🐍 构建后端
	@echo "$(BLUE)🐍 构建后端...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	python -m build
	@echo "$(GREEN)✅ 后端构建完成$(RESET)"

build-frontend: ## 🌐 构建前端
	@echo "$(BLUE)🌐 构建前端...$(RESET)"
	cd web_interface/frontend && \
	pnpm build
	@echo "$(GREEN)✅ 前端构建完成$(RESET)"

build-docker: ## 🐳 构建Docker镜像
	@echo "$(BLUE)🐳 构建Docker镜像...$(RESET)"
	cd web_interface && \
	docker-compose -f docker-compose.prod.yml build
	@echo "$(GREEN)✅ Docker镜像构建完成$(RESET)"

# ==================== 测试 ====================
test: ## 🧪 运行所有测试
	@echo "$(GREEN)🧪 运行所有测试...$(RESET)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend
	@echo "$(GREEN)✅ 所有测试完成$(RESET)"

test-backend: ## 🐍 运行后端测试
	@echo "$(BLUE)🐍 运行后端测试...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ 后端测试完成$(RESET)"

test-frontend: ## 🌐 运行前端测试
	@echo "$(BLUE)🌐 运行前端测试...$(RESET)"
	cd web_interface/frontend && \
	pnpm test
	@echo "$(GREEN)✅ 前端测试完成$(RESET)"

test-e2e: ## 🔄 运行端到端测试
	@echo "$(BLUE)🔄 运行端到端测试...$(RESET)"
	cd web_interface && \
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@echo "$(GREEN)✅ 端到端测试完成$(RESET)"

test-coverage: ## 📊 生成测试覆盖率报告
	@echo "$(BLUE)📊 生成测试覆盖率报告...$(RESET)"
	@$(MAKE) test-backend
	cd web_interface/frontend && pnpm test:coverage
	@echo "$(GREEN)✅ 测试覆盖率报告生成完成$(RESET)"

# ==================== 代码质量 ====================
lint: ## 🔍 运行代码检查
	@echo "$(GREEN)🔍 运行代码检查...$(RESET)"
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend
	@echo "$(GREEN)✅ 代码检查完成$(RESET)"

lint-backend: ## 🐍 后端代码检查
	@echo "$(BLUE)🐍 后端代码检查...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	flake8 app/ tests/ && \
	mypy app/ && \
	bandit -r app/
	@echo "$(GREEN)✅ 后端代码检查完成$(RESET)"

lint-frontend: ## 🌐 前端代码检查
	@echo "$(BLUE)🌐 前端代码检查...$(RESET)"
	cd web_interface/frontend && \
	pnpm lint && \
	pnpm type-check
	@echo "$(GREEN)✅ 前端代码检查完成$(RESET)"

format: ## ✨ 格式化代码
	@echo "$(GREEN)✨ 格式化代码...$(RESET)"
	@$(MAKE) format-backend
	@$(MAKE) format-frontend
	@echo "$(GREEN)✅ 代码格式化完成$(RESET)"

format-backend: ## 🐍 格式化后端代码
	@echo "$(BLUE)🐍 格式化后端代码...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	black app/ tests/ scripts/ && \
	isort app/ tests/ scripts/
	@echo "$(GREEN)✅ 后端代码格式化完成$(RESET)"

format-frontend: ## 🌐 格式化前端代码
	@echo "$(BLUE)🌐 格式化前端代码...$(RESET)"
	cd web_interface/frontend && \
	pnpm format
	@echo "$(GREEN)✅ 前端代码格式化完成$(RESET)"

# ==================== 数据库管理 ====================
db-upgrade: ## 📈 升级数据库
	@echo "$(BLUE)📈 升级数据库...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	alembic upgrade head
	@echo "$(GREEN)✅ 数据库升级完成$(RESET)"

db-downgrade: ## 📉 降级数据库
	@echo "$(BLUE)📉 降级数据库...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	alembic downgrade -1
	@echo "$(GREEN)✅ 数据库降级完成$(RESET)"

db-migration: ## 📝 创建数据库迁移
	@echo "$(BLUE)📝 创建数据库迁移...$(RESET)"
	@read -p "迁移描述: " desc; \
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	alembic revision --autogenerate -m "$$desc"
	@echo "$(GREEN)✅ 数据库迁移创建完成$(RESET)"

db-reset: ## 🔄 重置数据库
	@echo "$(YELLOW)⚠️  重置数据库将删除所有数据！$(RESET)"
	@read -p "确认重置数据库? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		cd web_interface/backend && \
		(. venv/bin/activate || venv/Scripts/activate) && \
		alembic downgrade base && \
		alembic upgrade head && \
		python scripts/init_database.py; \
		echo "$(GREEN)✅ 数据库重置完成$(RESET)"; \
	else \
		echo "$(BLUE)ℹ️  数据库重置已取消$(RESET)"; \
	fi

# ==================== Docker操作 ====================
docker-dev: ## 🐳 启动Docker开发环境
	@echo "$(BLUE)🐳 启动Docker开发环境...$(RESET)"
	cd web_interface && \
	docker-compose -f docker-compose.dev.yml up --build
	@echo "$(GREEN)✅ Docker开发环境启动完成$(RESET)"

docker-prod: ## 🚀 启动Docker生产环境
	@echo "$(BLUE)🚀 启动Docker生产环境...$(RESET)"
	cd web_interface && \
	docker-compose -f docker-compose.prod.yml up -d --build
	@echo "$(GREEN)✅ Docker生产环境启动完成$(RESET)"

docker-stop: ## 🛑 停止Docker容器
	@echo "$(BLUE)🛑 停止Docker容器...$(RESET)"
	cd web_interface && \
	docker-compose -f docker-compose.dev.yml down && \
	docker-compose -f docker-compose.prod.yml down
	@echo "$(GREEN)✅ Docker容器停止完成$(RESET)"

docker-clean: ## 🧹 清理Docker资源
	@echo "$(BLUE)🧹 清理Docker资源...$(RESET)"
	docker system prune -f
	docker volume prune -f
	docker network prune -f
	@echo "$(GREEN)✅ Docker资源清理完成$(RESET)"

# ==================== 部署操作 ====================
deploy-dev: ## 🚀 部署到开发环境
	@echo "$(BLUE)🚀 部署到开发环境...$(RESET)"
	@$(MAKE) build
	@$(MAKE) docker-dev
	@echo "$(GREEN)✅ 开发环境部署完成$(RESET)"

deploy-prod: ## 🌟 部署到生产环境
	@echo "$(BLUE)🌟 部署到生产环境...$(RESET)"
	@$(MAKE) test
	@$(MAKE) build
	@$(MAKE) docker-prod
	@echo "$(GREEN)✅ 生产环境部署完成$(RESET)"

# ==================== 监控和维护 ====================
health: ## 🏥 检查服务健康状态
	@echo "$(BLUE)🏥 检查服务健康状态...$(RESET)"
	@echo "检查后端服务..."
	@curl -f http://localhost:8000/health || echo "$(RED)❌ 后端服务不可用$(RESET)"
	@echo "检查前端服务..."
	@curl -f http://localhost:3000 || echo "$(RED)❌ 前端服务不可用$(RESET)"
	@echo "检查TradeMaster服务..."
	@curl -f http://localhost:8080/health || echo "$(RED)❌ TradeMaster服务不可用$(RESET)"
	@echo "$(GREEN)✅ 健康检查完成$(RESET)"

logs: ## 📜 查看应用日志
	@echo "$(BLUE)📜 查看应用日志...$(RESET)"
	cd web_interface && \
	docker-compose logs --tail=100 -f

logs-backend: ## 📜 查看后端日志
	@echo "$(BLUE)📜 查看后端日志...$(RESET)"
	cd web_interface && \
	docker-compose logs --tail=100 -f backend

logs-frontend: ## 📜 查看前端日志
	@echo "$(BLUE)📜 查看前端日志...$(RESET)"
	cd web_interface && \
	docker-compose logs --tail=100 -f frontend

performance: ## 📊 性能检查
	@echo "$(BLUE)📊 运行性能检查...$(RESET)"
	@$(MAKE) -f scripts/performance-check.mk

security: ## 🔒 安全检查
	@echo "$(BLUE)🔒 运行安全检查...$(RESET)"
	@$(MAKE) -f scripts/security-check.mk

# ==================== 清理操作 ====================
clean: ## 🧹 清理项目文件
	@echo "$(GREEN)🧹 清理项目文件...$(RESET)"
	@$(MAKE) clean-backend
	@$(MAKE) clean-frontend
	@$(MAKE) clean-docker
	@echo "$(GREEN)✅ 项目清理完成$(RESET)"

clean-backend: ## 🐍 清理后端文件
	@echo "$(BLUE)🐍 清理后端文件...$(RESET)"
	cd web_interface/backend && \
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
	find . -type f -name "*.pyc" -delete 2>/dev/null || true && \
	rm -rf build/ dist/ *.egg-info/ .coverage htmlcov/ .pytest_cache/ 2>/dev/null || true
	@echo "$(GREEN)✅ 后端文件清理完成$(RESET)"

clean-frontend: ## 🌐 清理前端文件
	@echo "$(BLUE)🌐 清理前端文件...$(RESET)"
	cd web_interface/frontend && \
	rm -rf node_modules/.cache dist/ coverage/ .nyc_output/ 2>/dev/null || true
	@echo "$(GREEN)✅ 前端文件清理完成$(RESET)"

clean-docker: ## 🐳 清理Docker文件
	@echo "$(BLUE)🐳 清理Docker文件...$(RESET)"
	@$(MAKE) docker-clean
	@echo "$(GREEN)✅ Docker文件清理完成$(RESET)"

clean-all: ## 🗑️  完全清理 (包括依赖)
	@echo "$(YELLOW)⚠️  完全清理将删除所有依赖包！$(RESET)"
	@read -p "确认完全清理? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(MAKE) clean && \
		cd web_interface/backend && rm -rf venv/ && \
		cd ../frontend && rm -rf node_modules/ && \
		echo "$(GREEN)✅ 完全清理完成$(RESET)"; \
	else \
		echo "$(BLUE)ℹ️  完全清理已取消$(RESET)"; \
	fi

# ==================== 工具命令 ====================
install-tools: ## 🔧 安装额外开发工具
	@echo "$(BLUE)🔧 安装额外开发工具...$(RESET)"
	pip install --user black isort flake8 mypy bandit safety
	npm install -g @antfu/ni pnpm-check-updates npm-check-updates
	@echo "$(GREEN)✅ 开发工具安装完成$(RESET)"

update-deps: ## 📦 更新依赖包
	@echo "$(BLUE)📦 更新依赖包...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	pip list --outdated && \
	cd ../frontend && \
	pnpm update --interactive
	@echo "$(GREEN)✅ 依赖包更新检查完成$(RESET)"

gen-requirements: ## 📄 生成requirements文件
	@echo "$(BLUE)📄 生成requirements文件...$(RESET)"
	cd web_interface/backend && \
	(. venv/bin/activate || venv/Scripts/activate) && \
	pip freeze > requirements-frozen.txt
	@echo "$(GREEN)✅ requirements文件生成完成$(RESET)"

backup: ## 💾 备份重要数据
	@echo "$(BLUE)💾 备份重要数据...$(RESET)"
	mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	cp -r web_interface/backend/alembic/versions/ backups/$(shell date +%Y%m%d_%H%M%S)/
	@echo "$(GREEN)✅ 数据备份完成$(RESET)"

# ==================== 开发辅助 ====================
dev-reset: ## 🔄 重置开发环境
	@echo "$(YELLOW)⚠️  重置开发环境将清理所有配置！$(RESET)"
	@read -p "确认重置开发环境? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(MAKE) clean-all && \
		$(MAKE) setup && \
		echo "$(GREEN)✅ 开发环境重置完成$(RESET)"; \
	else \
		echo "$(BLUE)ℹ️  开发环境重置已取消$(RESET)"; \
	fi

quick-start: ## ⚡ 快速启动 (首次使用)
	@echo "$(GREEN)⚡ $(PROJECT_NAME) 快速启动...$(RESET)"
	@$(MAKE) setup
	@$(MAKE) dev-services
	@sleep 10
	@$(MAKE) dev
	@echo "$(GREEN)🎉 欢迎使用 $(PROJECT_NAME)!$(RESET)"

info: ## ℹ️  显示项目信息
	@echo "$(GREEN)📋 $(PROJECT_NAME) 项目信息$(RESET)"
	@echo "版本: $(VERSION)"
	@echo "Python版本要求: $(PYTHON_VERSION)+"
	@echo "Node.js版本要求: $(NODE_VERSION)+"
	@echo "项目路径: $(PWD)"
	@echo "配置文件:"
	@echo "  - web_interface/.env.dev (开发环境)"
	@echo "  - web_interface/.env.prod.template (生产环境模板)"
	@echo "服务地址:"
	@echo "  - 前端: http://localhost:3000"
	@echo "  - 后端: http://localhost:8000"
	@echo "  - API文档: http://localhost:8000/docs"
	@echo "  - TradeMaster: http://localhost:8080"

# ==================== 特殊目标 ====================
.PHONY: *