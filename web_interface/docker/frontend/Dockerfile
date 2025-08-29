# ==================== 多阶段构建配置 ====================
# 基础阶段：Node.js环境（回到稳定的slim镜像）
FROM node:18-slim AS base

# 设置构建参数
ARG BUILD_ENV=production
ARG REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
ARG REACT_APP_WS_URL=ws://localhost:8000/ws

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 优化npm配置（临时使用npm，确保兼容性）
RUN npm config set registry https://registry.npmmirror.com && \
    npm config set cache /tmp/.npm && \
    npm config set progress false && \
    npm config set audit false

# ==================== 依赖安装阶段 ====================
FROM base AS dependencies

# 复制package.json文件
COPY web_interface/frontend/package.json ./

# 安装依赖并暴力修复rollup问题
RUN npm install --verbose && \
    # 暴力修复：直接创建缺失的rollup二进制文件链接
    cd /app/node_modules/@rollup/ && \
    # 如果存在glibc版本，创建musl版本的软链接
    if [ -d "rollup-linux-x64-gnu" ]; then \
        ln -sf rollup-linux-x64-gnu rollup-linux-x64-musl; \
        echo "Created rollup-linux-x64-musl symlink to rollup-linux-x64-gnu"; \
    fi && \
    # 如果不存在，手动安装glibc版本然后创建链接
    if [ ! -d "rollup-linux-x64-gnu" ]; then \
        cd /app && npm install @rollup/rollup-linux-x64-gnu --force --no-save; \
        cd /app/node_modules/@rollup/ && ln -sf rollup-linux-x64-gnu rollup-linux-x64-musl; \
        echo "Installed and linked rollup-linux-x64-gnu to rollup-linux-x64-musl"; \
    fi && \
    # 验证修复结果
    ls -la /app/node_modules/@rollup/ && \
    # 清理npm缓存
    npm cache clean --force

# ==================== 构建阶段 ====================
FROM dependencies AS builder

# 设置环境变量
ENV NODE_ENV=production
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL
ENV GENERATE_SOURCEMAP=false
ENV INLINE_RUNTIME_CHUNK=false

# 复制源代码
COPY web_interface/frontend/src ./src
COPY web_interface/frontend/public ./public
COPY web_interface/frontend/index.html .
COPY web_interface/frontend/vite.config.ts .
COPY web_interface/frontend/tsconfig.json .
COPY web_interface/frontend/tsconfig.node.json .

# 构建应用（使用npm）
RUN npm run build:no-tsc && \
    # 验证构建结果
    ls -la dist/ && \
    # 清理不需要的文件
    rm -rf node_modules/.cache || true

# ==================== 生产运行阶段 ====================
FROM nginx:alpine AS production

# 安装额外工具
RUN apk add --no-cache \
    curl \
    jq \
    && rm -rf /var/cache/apk/*

# 创建nginx目录（用户和组已存在于基础镜像中）
RUN mkdir -p /var/log/nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx /var/cache/nginx

# 从构建阶段复制构建产物
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY --chown=nginx:nginx docker/frontend/nginx.conf /etc/nginx/nginx.conf
COPY --chown=nginx:nginx docker/frontend/default.conf /etc/nginx/conf.d/default.conf

# 创建健康检查脚本
COPY --chown=nginx:nginx docker/frontend/health-check.sh /health-check.sh
RUN chmod +x /health-check.sh

# 创建启动脚本
COPY --chown=nginx:nginx docker/frontend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD /health-check.sh

# 暴露端口
EXPOSE 80 443

# 切换到nginx用户
USER nginx

# 设置启动命令
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

# ==================== 开发阶段 ====================
FROM dependencies AS development

# 安装系统工具（Alpine Linux需要的工具）
RUN apk add --no-cache \
    xdg-utils \
    && rm -rf /var/cache/apk/*

# 安装npm开发工具
RUN npm install -g serve@14.2.1

# 验证关键依赖包存在（使用npm）
RUN npm list @typescript-eslint/eslint-plugin @typescript-eslint/parser || \
    (echo "Missing TypeScript ESLint dependencies. Installing..." && \
     npm install --save-dev @typescript-eslint/eslint-plugin@^6.10.0 @typescript-eslint/parser@^6.10.0)

# 设置环境变量
ENV NODE_ENV=development
ENV REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
ENV REACT_APP_WS_URL=ws://localhost:8000/ws

# 复制源代码
COPY web_interface/frontend/src ./src
COPY web_interface/frontend/public ./public
COPY web_interface/frontend/index.html .
COPY web_interface/frontend/vite.config.ts .
COPY web_interface/frontend/tsconfig.json .
COPY web_interface/frontend/tsconfig.node.json .
COPY web_interface/frontend/.eslintrc.cjs .
COPY web_interface/frontend/.prettierrc .

# 暴露开发服务器端口
EXPOSE 3000

# 开发环境启动命令（使用npm）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# ==================== 测试阶段 ====================
FROM dependencies AS test

# 复制所有源代码
COPY web_interface/frontend/ .

# 运行测试（使用npm）
RUN npm run lint && \
    npm run type-check && \
    echo "所有测试通过"

# ==================== 元数据标签 ====================
LABEL maintainer="TradeMaster Team <team@trademaster.ai>" \
      version="1.0.0" \
      description="TradeMaster Web Interface Frontend" \
      org.opencontainers.image.title="TradeMaster Frontend" \
      org.opencontainers.image.description="React frontend for TradeMaster Web Interface" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/TradeMaster-NTU/TradeMaster" \
      org.opencontainers.image.licenses="MIT"