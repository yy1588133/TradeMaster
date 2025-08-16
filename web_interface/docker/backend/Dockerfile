# ==================== 多阶段构建配置 ====================
# 构建阶段：安装依赖和编译代码
FROM python:3.11-slim-bullseye as builder

# 设置构建参数
ARG PIP_INDEX_URL=https://pypi.org/simple/
ARG BUILD_ENV=production

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（构建时需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户和目录
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# 复制依赖文件
COPY backend/requirements.txt .

# 安装Python依赖到用户目录
RUN pip install --user --no-cache-dir -r requirements.txt

# ==================== 运行阶段：最小化生产镜像 ====================
FROM python:3.11-slim-bullseye as production

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    PYTHONPATH=/app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户和目录
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app /app/data /app/logs /app/uploads \
    && chown -R appuser:appuser /app

# 从构建阶段复制Python包
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# 切换到应用目录
WORKDIR /app

# 复制应用代码
COPY --chown=appuser:appuser backend/app ./app
COPY --chown=appuser:appuser backend/alembic ./alembic
COPY --chown=appuser:appuser backend/alembic.ini .

# 复制启动脚本
COPY --chown=appuser:appuser docker/backend/entrypoint.sh /entrypoint.sh
COPY --chown=appuser:appuser docker/backend/wait-for-it.sh /wait-for-it.sh

# 设置脚本执行权限
RUN chmod +x /entrypoint.sh /wait-for-it.sh

# 创建健康检查脚本
COPY --chown=appuser:appuser docker/backend/health-check.sh /health-check.sh
RUN chmod +x /health-check.sh

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /health-check.sh

# 暴露端口
EXPOSE 8000

# 设置默认命令
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==================== 开发阶段：包含开发工具 ====================
FROM production as development

# 切换回root用户安装开发工具
USER root

# 安装开发工具
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0 \
    pytest-mock==3.12.0 \
    black==23.11.0 \
    isort==5.12.0 \
    flake8==6.1.0 \
    mypy==1.7.1 \
    pre-commit==3.6.0 \
    ipython \
    debugpy

# 安装额外的开发依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# 切换回应用用户
USER appuser

# 开发环境默认启动命令（支持热重载）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==================== 元数据标签 ====================
LABEL maintainer="TradeMaster Team <team@trademaster.ai>" \
      version="1.0.0" \
      description="TradeMaster Web Interface Backend API" \
      org.opencontainers.image.title="TradeMaster Backend" \
      org.opencontainers.image.description="FastAPI backend for TradeMaster Web Interface" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/TradeMaster-NTU/TradeMaster" \
      org.opencontainers.image.licenses="MIT"