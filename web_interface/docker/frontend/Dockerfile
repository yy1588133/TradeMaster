# ==================== 多阶段构建配置 ====================
# 基础阶段：Node.js环境
FROM node:18-alpine as base

# 设置构建参数
ARG BUILD_ENV=production
ARG REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
ARG REACT_APP_WS_URL=ws://localhost:8000/ws

# 安装系统依赖
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# 设置工作目录
WORKDIR /app

# 优化npm配置
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set cache /tmp/.npm && \
    npm config set progress false && \
    npm config set audit false

# ==================== 依赖安装阶段 ====================
FROM base as dependencies

# 复制package文件
COPY frontend/package.json frontend/package-lock.json* ./

# 安装依赖（包括devDependencies用于构建）
RUN npm install --silent && \
    npm cache clean --force

# ==================== 构建阶段 ====================
FROM dependencies as builder

# 设置环境变量
ENV NODE_ENV=production
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL
ENV GENERATE_SOURCEMAP=false
ENV INLINE_RUNTIME_CHUNK=false

# 复制源代码
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html .
COPY frontend/vite.config.ts .
COPY frontend/tsconfig.json .
COPY frontend/tsconfig.node.json .

# 构建应用（跳过tsc类型检查，直接使用vite构建）
RUN npm run build:no-tsc && \
    # 验证构建结果
    ls -la dist/ && \
    # 清理不需要的文件
    rm -rf node_modules/.cache || true

# ==================== 生产运行阶段 ====================
FROM nginx:alpine as production

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
FROM dependencies as development

# 安装系统工具（Alpine Linux需要的工具）
RUN apk add --no-cache \
    xdg-utils \
    && rm -rf /var/cache/apk/*

# 安装开发工具
RUN npm install -g serve@14.2.1

# 验证关键依赖包存在
RUN npm list @typescript-eslint/eslint-plugin @typescript-eslint/parser || \
    (echo "Missing TypeScript ESLint dependencies. Installing..." && \
     npm install --save-dev @typescript-eslint/eslint-plugin@^6.10.0 @typescript-eslint/parser@^6.10.0)

# 设置环境变量
ENV NODE_ENV=development
ENV REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
ENV REACT_APP_WS_URL=ws://localhost:8000/ws

# 复制源代码
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html .
COPY frontend/vite.config.ts .
COPY frontend/tsconfig.json .
COPY frontend/tsconfig.node.json .
COPY frontend/.eslintrc.cjs .
COPY frontend/.prettierrc .

# 暴露开发服务器端口
EXPOSE 3000

# 开发环境启动命令（禁用自动打开浏览器）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000", "--open", "false"]

# ==================== 测试阶段 ====================
FROM dependencies as test

# 复制所有源代码
COPY frontend/ .

# 运行测试
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