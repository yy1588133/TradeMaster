# ==================== TradeMaster Backend Makefile ====================
# 后端特定的管理命令

# 环境变量
.PHONY: help install dev test lint format clean migrate db-* docker-*
.DEFAULT_GOAL := help

# 颜色定义
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BLUE := \033[34m
RESET := \033[0m

# Python相关配置
PYTHON := python
PIP := pip
VENV := venv
VENV_ACTIVATE := $(VENV)/bin/activate

# 检测操作系统
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM := macos
endif
ifdef OS
    ifeq ($(OS),Windows_NT)
        PLATFORM := windows
        VENV_ACTIVATE := $(VENV)/Scripts/activate
        PYTHON := python
    endif
endif

help: ## 显示帮助信息
	@echo "$(GREEN)TradeMaster Backend Commands$(RESET)"
	@echo "$(BLUE)可用命令:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'

# ==================== 环境管理 ====================
install: ## 🔧 安装所有依赖
	@echo "$(GREEN)🔧 安装后端依赖...$(RESET)"
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then $(PIP) install -r requirements-dev.txt; fi
	@echo "$(GREEN)✅ 依赖安装完成$(RESET)"

install-dev: ## 🛠️ 安装开发依赖
	@echo "$(BLUE)🛠️ 安装开发依赖...$(RESET)"
	$(PIP) install -r requirements-dev.txt
	$(PIP) install pre-commit black isort flake8 mypy bandit safety
	@echo "$(GREEN)✅ 开发依赖安装完成$(RESET)"

setup: ## 🚀 初始化开发环境
	@echo "$(GREEN)🚀 初始化后端开发环境...$(RESET)"
	$(PYTHON) scripts/setup.py
	@echo "$(GREEN)✅ 开发环境初始化完成$(RESET)"

venv: ## 🐍 创建虚拟环境
	@echo "$(BLUE)🐍 创建虚拟环境...$(RESET)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✅ 虚拟环境创建完成$(RESET)"
	@echo "$(YELLOW)激活命令: source $(VENV_ACTIVATE)$(RESET)"

# ==================== 开发服务 ====================
dev: ## 🚀 启动开发服务器
	@echo "$(GREEN)🚀 启动后端开发服务器...$(RESET)"
	$(PYTHON) scripts/dev.py

dev-debug: ## 🐛 启动调试模式服务器
	@echo "$(BLUE)🐛 启动调试模式服务器...$(RESET)"
	$(PYTHON) scripts/dev.py --debug

dev-prod: ## 🌟 使用生产配置启动
	@echo "$(GREEN)🌟 使用生产配置启动...$(RESET)"
	gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

run: ## ▶️ 直接运行应用
	@echo "$(BLUE)▶️ 直接运行应用...$(RESET)"
	$(PYTHON) app/main.py

# ==================== 测试 ====================
test: ## 🧪 运行所有测试
	@echo "$(GREEN)🧪 运行后端测试...$(RESET)"
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ 测试完成$(RESET)"

test-unit: ## 🔬 运行单元测试
	@echo "$(BLUE)🔬 运行单元测试...$(RESET)"
	pytest tests/unit/ -v

test-integration: ## 🔄 运行集成测试
	@echo "$(BLUE)🔄 运行集成测试...$(RESET)"
	pytest tests/integration/ -v

test-e2e: ## 🌐 运行端到端测试
	@echo "$(BLUE)🌐 运行端到端测试...$(RESET)"
	pytest tests/e2e/ -v

test-watch: ## 👀 监控测试
	@echo "$(BLUE)👀 监控测试变化...$(RESET)"
	pytest-watch tests/ --runner "pytest --cov=app"

test-coverage: ## 📊 生成测试覆盖率报告
	@echo "$(BLUE)📊 生成测试覆盖率报告...$(RESET)"
	pytest tests/ --cov=app --cov-report=html --cov-report=xml --cov-report=term
	@echo "$(GREEN)✅ 覆盖率报告生成完成: htmlcov/index.html$(RESET)"

test-performance: ## ⚡ 性能测试
	@echo "$(BLUE)⚡ 运行性能测试...$(RESET)"
	pytest tests/performance/ -v --benchmark-only

# ==================== 代码质量 ====================
lint: ## 🔍 运行所有代码检查
	@echo "$(GREEN)🔍 运行代码质量检查...$(RESET)"
	@$(MAKE) lint-flake8
	@$(MAKE) lint-mypy
	@$(MAKE) lint-security
	@echo "$(GREEN)✅ 代码检查完成$(RESET)"

lint-flake8: ## 🐍 Flake8代码风格检查
	@echo "$(BLUE)🐍 Flake8检查...$(RESET)"
	flake8 app/ tests/ scripts/ --statistics

lint-mypy: ## 📝 MyPy类型检查
	@echo "$(BLUE)📝 MyPy类型检查...$(RESET)"
	mypy app/ --ignore-missing-imports

lint-security: ## 🔒 安全检查
	@echo "$(BLUE)🔒 安全检查...$(RESET)"
	bandit -r app/ -ll
	safety check

format: ## ✨ 格式化代码
	@echo "$(GREEN)✨ 格式化代码...$(RESET)"
	black app/ tests/ scripts/
	isort app/ tests/ scripts/
	@echo "$(GREEN)✅ 代码格式化完成$(RESET)"

format-check: ## 👀 检查代码格式
	@echo "$(BLUE)👀 检查代码格式...$(RESET)"
	black --check app/ tests/ scripts/
	isort --check-only app/ tests/ scripts/

pre-commit: ## 🎯 运行pre-commit检查
	@echo "$(BLUE)🎯 运行pre-commit检查...$(RESET)"
	pre-commit run --all-files

pre-commit-install: ## 📥 安装pre-commit钩子
	@echo "$(BLUE)📥 安装pre-commit钩子...$(RESET)"
	pre-commit install
	@echo "$(GREEN)✅ pre-commit钩子安装完成$(RESET)"

# ==================== 数据库管理 ====================
db-upgrade: ## 📈 升级数据库到最新版本
	@echo "$(BLUE)📈 升级数据库...$(RESET)"
	alembic upgrade head
	@echo "$(GREEN)✅ 数据库升级完成$(RESET)"

db-downgrade: ## 📉 降级数据库一个版本
	@echo "$(BLUE)📉 降级数据库...$(RESET)"
	alembic downgrade -1
	@echo "$(GREEN)✅ 数据库降级完成$(RESET)"

db-migration: ## 📝 创建新的数据库迁移
	@echo "$(BLUE)📝 创建数据库迁移...$(RESET)"
	@read -p "迁移描述: " desc; \
	alembic revision --autogenerate -m "$$desc"
	@echo "$(GREEN)✅ 迁移文件创建完成$(RESET)"

db-current: ## 📍 显示当前数据库版本
	@echo "$(BLUE)📍 当前数据库版本:$(RESET)"
	alembic current

db-history: ## 📜 显示迁移历史
	@echo "$(BLUE)📜 迁移历史:$(RESET)"
	alembic history

db-reset: ## 🔄 重置数据库
	@echo "$(YELLOW)⚠️ 重置数据库将删除所有数据！$(RESET)"
	@read -p "确认重置数据库? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		alembic downgrade base && \
		alembic upgrade head && \
		$(PYTHON) app/scripts/init_database.py && \
		echo "$(GREEN)✅ 数据库重置完成$(RESET)"; \
	else \
		echo "$(BLUE)ℹ️ 数据库重置已取消$(RESET)"; \
	fi

db-init: ## 🗄️ 初始化数据库数据
	@echo "$(BLUE)🗄️ 初始化数据库数据...$(RESET)"
	$(PYTHON) app/scripts/init_database.py
	@echo "$(GREEN)✅ 数据库初始化完成$(RESET)"

# ==================== Docker操作 ====================
docker-build: ## 🐳 构建Docker镜像
	@echo "$(BLUE)🐳 构建后端Docker镜像...$(RESET)"
	docker build -t trademaster-backend -f ../docker/backend/Dockerfile .
	@echo "$(GREEN)✅ Docker镜像构建完成$(RESET)"

docker-run: ## 🚀 运行Docker容器
	@echo "$(BLUE)🚀 运行后端Docker容器...$(RESET)"
	docker run -p 8000:8000 --env-file .env trademaster-backend

docker-shell: ## 🐚 进入Docker容器shell
	@echo "$(BLUE)🐚 进入Docker容器...$(RESET)"
	docker run -it --rm trademaster-backend /bin/bash

# ==================== 工具命令 ====================
deps-check: ## 📦 检查依赖包
	@echo "$(BLUE)📦 检查依赖包...$(RESET)"
	$(PIP) list --outdated
	safety check

deps-update: ## ⬆️ 更新依赖包
	@echo "$(BLUE)⬆️ 更新依赖包...$(RESET)"
	$(PIP) list --outdated --format=json | jq -r '.[] | .name' | xargs -I {} $(PIP) install --upgrade {}

freeze: ## 🧊 生成requirements.txt
	@echo "$(BLUE)🧊 生成requirements文件...$(RESET)"
	$(PIP) freeze > requirements-frozen.txt
	@echo "$(GREEN)✅ requirements-frozen.txt 生成完成$(RESET)"

docs: ## 📚 生成API文档
	@echo "$(BLUE)📚 生成API文档...$(RESET)"
	$(PYTHON) -c "from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json
	@echo "$(GREEN)✅ API文档生成完成$(RESET)"

# ==================== 监控和调试 ====================
logs: ## 📜 查看应用日志
	@echo "$(BLUE)📜 查看应用日志...$(RESET)"
	tail -f logs/dev.log

logs-error: ## 🔥 查看错误日志
	@echo "$(BLUE)🔥 查看错误日志...$(RESET)"
	grep -i error logs/dev.log | tail -20

health: ## 🏥 健康检查
	@echo "$(BLUE)🏥 检查后端健康状态...$(RESET)"
	@curl -f http://localhost:8000/health || echo "$(RED)❌ 后端服务不可用$(RESET)"

profile: ## 📊 性能分析
	@echo "$(BLUE)📊 运行性能分析...$(RESET)"
	$(PYTHON) -m cProfile -o profile.stats app/main.py
	@echo "$(GREEN)✅ 性能分析完成: profile.stats$(RESET)"

# ==================== 清理操作 ====================
clean: ## 🧹 清理临时文件
	@echo "$(GREEN)🧹 清理后端临时文件...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/ 2>/dev/null || true
	rm -rf logs/*.log temp/* uploads/temp/* 2>/dev/null || true
	@echo "$(GREEN)✅ 清理完成$(RESET)"

clean-venv: ## 🗑️ 删除虚拟环境
	@echo "$(YELLOW)⚠️ 删除虚拟环境...$(RESET)"
	rm -rf $(VENV)
	@echo "$(GREEN)✅ 虚拟环境删除完成$(RESET)"

clean-all: ## 🗑️ 完全清理
	@echo "$(YELLOW)⚠️ 完全清理...$(RESET)"
	@$(MAKE) clean
	@$(MAKE) clean-venv
	@echo "$(GREEN)✅ 完全清理完成$(RESET)"

# ==================== 生产部署 ====================
build: ## 🔨 构建生产版本
	@echo "$(GREEN)🔨 构建生产版本...$(RESET)"
	$(PYTHON) -m build
	@echo "$(GREEN)✅ 构建完成$(RESET)"

deploy-check: ## ✅ 部署前检查
	@echo "$(BLUE)✅ 部署前检查...$(RESET)"
	@$(MAKE) test
	@$(MAKE) lint
	@$(MAKE) security-audit
	@echo "$(GREEN)✅ 部署检查通过$(RESET)"

security-audit: ## 🔐 安全审计
	@echo "$(BLUE)🔐 安全审计...$(RESET)"
	bandit -r app/ -f json -o security-report.json || true
	safety check --json --output security-deps.json || true
	@echo "$(GREEN)✅ 安全审计完成$(RESET)"

# ==================== 备份和恢复 ====================
backup: ## 💾 备份数据
	@echo "$(BLUE)💾 备份数据...$(RESET)"
	mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	cp -r alembic/versions/ backups/$(shell date +%Y%m%d_%H%M%S)/migrations/
	@echo "$(GREEN)✅ 数据备份完成$(RESET)"

# ==================== 调试工具 ====================
shell: ## 🐚 启动Python shell
	@echo "$(BLUE)🐚 启动Python shell...$(RESET)"
	$(PYTHON) -i -c "from app.main import app; from app.core.config import get_settings; settings = get_settings()"

ipython: ## 🐍 启动IPython shell
	@echo "$(BLUE)🐍 启动IPython shell...$(RESET)"
	ipython -i -c "from app.main import app; from app.core.config import get_settings; settings = get_settings()"

# ==================== 信息显示 ====================
info: ## ℹ️ 显示项目信息
	@echo "$(GREEN)📋 TradeMaster Backend 项目信息$(RESET)"
	@echo "Python版本: $(shell $(PYTHON) --version)"
	@echo "项目路径: $(PWD)"
	@echo "虚拟环境: $(VENV)"
	@echo "平台: $(PLATFORM)"
	@echo "配置文件: .env"
	@echo "服务地址: http://localhost:8000"
	@echo "API文档: http://localhost:8000/docs"

env-info: ## 🌍 显示环境信息
	@echo "$(BLUE)🌍 环境变量信息:$(RESET)"
	@$(PYTHON) -c "from app.core.config import get_settings; settings = get_settings(); print(f'Debug: {settings.DEBUG}'); print(f'Environment: {getattr(settings, \"ENVIRONMENT\", \"development\")}'); print(f'Database: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}')"

# ==================== 特殊目标 ====================
.PHONY: *