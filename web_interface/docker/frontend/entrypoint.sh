#!/bin/bash

# ==================== TradeMaster Frontend 启动脚本 ====================
# 该脚本负责前端Nginx服务的启动和配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 环境变量默认值
export BACKEND_HOST=${BACKEND_HOST:-"backend"}
export BACKEND_PORT=${BACKEND_PORT:-"8000"}
export NGINX_WORKER_PROCESSES=${NGINX_WORKER_PROCESSES:-"auto"}
export NGINX_WORKER_CONNECTIONS=${NGINX_WORKER_CONNECTIONS:-"1024"}

# 创建必需的目录
create_directories() {
    log_info "创建必需的目录..."
    
    directories=(
        "/var/log/nginx"
        "/var/cache/nginx"
        "/var/run/nginx"
        "/tmp/nginx"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
    
    # 设置目录权限
    chown -R nginx:nginx /var/log/nginx /var/cache/nginx /var/run/nginx /tmp/nginx 2>/dev/null || true
    
    log_success "目录创建完成"
}

# 验证静态文件
validate_static_files() {
    log_info "验证静态文件..."
    
    if [ ! -d "/usr/share/nginx/html" ]; then
        log_error "静态文件目录不存在: /usr/share/nginx/html"
        exit 1
    fi
    
    if [ ! -f "/usr/share/nginx/html/index.html" ]; then
        log_error "主页面文件不存在: /usr/share/nginx/html/index.html"
        exit 1
    fi
    
    # 检查文件权限
    if [ ! -r "/usr/share/nginx/html/index.html" ]; then
        log_error "无法读取主页面文件"
        exit 1
    fi
    
    # 统计文件数量
    file_count=$(find /usr/share/nginx/html -type f | wc -l)
    log_info "发现 $file_count 个静态文件"
    
    log_success "静态文件验证通过"
}

# 验证Nginx配置
validate_nginx_config() {
    log_info "验证Nginx配置..."
    
    if [ ! -f "/etc/nginx/nginx.conf" ]; then
        log_error "Nginx主配置文件不存在"
        exit 1
    fi
    
    if [ ! -f "/etc/nginx/conf.d/default.conf" ]; then
        log_error "Nginx站点配置文件不存在"
        exit 1
    fi
    
    # 测试配置文件语法
    if nginx -t 2>/dev/null; then
        log_success "Nginx配置验证通过"
    else
        log_error "Nginx配置验证失败"
        nginx -t
        exit 1
    fi
}

# 动态配置Nginx
configure_nginx() {
    log_info "配置Nginx参数..."
    
    # 创建运行时配置
    cat > /tmp/nginx-runtime.conf << EOF
# 运行时配置覆盖
worker_processes ${NGINX_WORKER_PROCESSES};

events {
    worker_connections ${NGINX_WORKER_CONNECTIONS};
}
EOF
    
    # 替换upstream配置中的后端地址
    if [ -f "/etc/nginx/conf.d/default.conf" ]; then
        # 动态替换backend地址
        sed -i "s/server backend:8000/server ${BACKEND_HOST}:${BACKEND_PORT}/g" /etc/nginx/conf.d/default.conf
        log_info "后端服务地址配置为: ${BACKEND_HOST}:${BACKEND_PORT}"
    fi
    
    log_success "Nginx配置完成"
}

# 等待后端服务
wait_for_backend() {
    log_info "等待后端服务启动..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$BACKEND_HOST" "$BACKEND_PORT" 2>/dev/null; then
            log_success "后端服务已就绪 (${BACKEND_HOST}:${BACKEND_PORT})"
            return 0
        fi
        
        log_info "等待后端服务... (尝试 $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_warning "无法连接到后端服务，但继续启动前端服务"
    return 0
}

# 预热缓存
warm_cache() {
    log_info "预热Nginx缓存..."
    
    # 等待Nginx启动
    sleep 2
    
    # 预热主要页面
    urls=(
        "http://localhost/health"
        "http://localhost/"
    )
    
    for url in "${urls[@]}"; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
            log_info "预热成功: $url"
        else
            log_warning "预热失败: $url"
        fi
    done
    
    log_success "缓存预热完成"
}

# 设置文件权限
set_permissions() {
    log_info "设置文件权限..."
    
    # 设置静态文件权限
    find /usr/share/nginx/html -type f -exec chmod 644 {} \;
    find /usr/share/nginx/html -type d -exec chmod 755 {} \;
    
    # 设置日志目录权限
    chmod 755 /var/log/nginx
    
    log_success "文件权限设置完成"
}

# 信号处理函数
cleanup() {
    log_info "接收到停止信号，正在关闭Nginx..."
    
    # 优雅停止Nginx
    nginx -s quit
    
    log_success "Nginx已安全关闭"
    exit 0
}

# 设置信号处理
trap cleanup SIGTERM SIGINT

# 主启动流程
main() {
    log_info "开始启动TradeMaster Frontend服务..."
    log_info "环境信息: BACKEND=${BACKEND_HOST}:${BACKEND_PORT}"
    
    # 创建必需目录
    create_directories
    
    # 设置文件权限
    set_permissions
    
    # 验证静态文件
    validate_static_files
    
    # 配置Nginx
    configure_nginx
    
    # 验证配置
    validate_nginx_config
    
    # 等待后端服务（可选）
    wait_for_backend
    
    log_success "所有初始化步骤完成，启动Nginx服务..."
    
    # 如果没有传入参数，使用默认启动命令
    if [ $# -eq 0 ]; then
        log_info "使用默认启动命令"
        # 启动Nginx并在后台预热缓存
        (sleep 5 && warm_cache) &
        exec nginx -g "daemon off;"
    else
        log_info "使用自定义启动命令: $@"
        exec "$@"
    fi
}

# 如果直接运行此脚本，执行主函数
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi