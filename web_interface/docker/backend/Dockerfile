# ==================== 多阶段构建配置 ====================
# 构建阶段：安装依赖和编译代码
# 使用官方Python镜像 - 如果国内源失败则回退到官方源
FROM python:3.11-slim AS builder

# 设置构建参数
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
ARG BUILD_ENV=production
ARG BUILD_DATE

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（构建时需要）
# 现代Debian系统APT源配置
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends --fix-broken \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器 - 快速现代化Python包管理
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ uv==0.6.14

# 创建应用用户和目录
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# 复制依赖文件 - 使用完整版以支持TradeMaster全功能
COPY web_interface/backend/requirements-docker-full.txt ./requirements.txt

# 使用uv创建虚拟环境并安装依赖 - 10倍速度提升
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
# 设置更长的超时时间
ENV UV_HTTP_TIMEOUT=120
RUN uv pip install --no-cache-dir -r requirements.txt --python=/app/.venv/bin/python --index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# 复制TradeMaster源代码并安装为可编辑模式
COPY trademaster ./trademaster
COPY setup.py ./setup.py
COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md

# 使用uv安装TradeMaster包 (可编辑模式)
RUN uv pip install -e . --python=/app/.venv/bin/python

# ==================== 运行阶段：最小化生产镜像 ====================
FROM python:3.11-slim AS production

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/app/.venv/bin:$PATH \
    PYTHONPATH=/app \
    TRADEMASTER_ROOT=/app

# 安装运行时依赖
# 现代Debian系统APT源配置 - 包含OpenCV和图形库依赖
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends --fix-broken \
    libpq5 \
    curl \
    netcat-traditional \
    libglx-mesa0 \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户和目录，设置正确权限
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app /app/data /app/logs /app/uploads /app/temp \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

# 从构建阶段复制虚拟环境
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# 切换到应用目录
WORKDIR /app

# 复制TradeMaster源代码 (可编辑模式安装需要)
COPY --from=builder --chown=appuser:appuser /app/trademaster ./trademaster
COPY --from=builder --chown=appuser:appuser /app/setup.py ./setup.py
COPY --from=builder --chown=appuser:appuser /app/pyproject.toml ./pyproject.toml

# 复制应用代码
COPY --chown=appuser:appuser web_interface/backend/app ./app
COPY --chown=appuser:appuser web_interface/backend/alembic ./alembic
COPY --chown=appuser:appuser web_interface/backend/alembic.ini .

# 复制启动脚本和工具
COPY --chown=appuser:appuser web_interface/docker/backend/entrypoint.sh /entrypoint.sh
COPY --chown=appuser:appuser web_interface/docker/backend/wait-for-it.sh /wait-for-it.sh
COPY --chown=appuser:appuser web_interface/docker/backend/db_test.py /app/db_test.py

# 设置脚本执行权限
RUN chmod +x /entrypoint.sh /wait-for-it.sh

# 创建健康检查脚本
COPY --chown=appuser:appuser web_interface/docker/backend/health-check.sh /health-check.sh
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

# ==================== 开发阶段已移除 ====================
# 注意: 开发阶段已移除以解决网络连接问题和优化构建性能
# 开发调试功能通过Docker volume挂载和本地开发环境实现

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