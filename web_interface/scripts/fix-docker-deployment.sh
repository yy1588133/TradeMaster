#!/bin/bash

# ==================== TradeMaster Docker 部署问题修复脚本 ====================
# 该脚本解决Docker容器化部署过程中的权限和依赖问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查Docker环境
check_docker_environment() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 清理旧的容器和镜像
cleanup_old_containers() {
    log_info "清理旧的容器和镜像..."
    
    # 停止并删除容器
    docker-compose -f docker-compose.dev.yml down --remove-orphans || true
    
    # 删除相关镜像
    docker images | grep "trademaster" | awk '{print $3}' | xargs -r docker rmi -f || true
    
    log_success "旧容器清理完成"
}

# 创建必需的目录
create_required_directories() {
    log_info "创建必需的目录..."
    
    directories=(
        "docker/volumes/postgres_dev"
        "docker/volumes/redis_dev"
        "logs"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
    
    # 设置目录权限（适合开发环境）
    chmod -R 755 docker/volumes/ logs/ 2>/dev/null || true
    
    log_success "目录创建完成"
}

# 验证前端依赖
verify_frontend_dependencies() {
    log_info "验证前端依赖..."
    
    cd frontend
    
    # 检查package.json中的关键依赖
    if ! grep -q "@typescript-eslint/eslint-plugin" package.json; then
        log_warning "添加缺失的TypeScript ESLint依赖"
        npm install --save-dev @typescript-eslint/eslint-plugin@^6.10.0 @typescript-eslint/parser@^6.10.0 || true
    fi
    
    cd ..
    log_success "前端依赖验证完成"
}

# 构建并启动服务
build_and_start_services() {
    log_info "构建并启动服务..."
    
    # 使用no-cache构建确保应用最新修复
    docker-compose -f docker-compose.dev.yml build --no-cache
    
    # 启动服务
    docker-compose -f docker-compose.dev.yml up -d
    
    log_success "服务启动完成"
}

# 验证服务状态
verify_services() {
    log_info "验证服务状态..."
    
    # 等待服务启动
    sleep 30
    
    # 检查容器状态
    docker-compose -f docker-compose.dev.yml ps
    
    # 检查后端健康状态
    log_info "检查后端服务..."
    for i in {1..10}; do
        if curl -f -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            log_success "后端服务运行正常"
            break
        else
            log_warning "等待后端服务启动 (尝试 $i/10)"
            sleep 10
        fi
    done
    
    # 检查前端服务
    log_info "检查前端服务..."
    for i in {1..5}; do
        if curl -f -s http://localhost:3100 > /dev/null 2>&1; then
            log_success "前端服务运行正常"
            break
        else
            log_warning "等待前端服务启动 (尝试 $i/5)"
            sleep 10
        fi
    done
}

# 显示服务信息
show_service_info() {
    log_info "服务访问信息："
    echo ""
    echo "🌐 前端Web界面: http://localhost:3100"
    echo "📚 后端API文档: http://localhost:8000/docs"
    echo "🗄️ 数据库管理: http://localhost:5050 (pgAdmin)"
    echo "🔍 Redis管理: http://localhost:8081 (Redis Commander)"
    echo ""
    echo "🔧 管理命令："
    echo "  查看日志: docker-compose -f docker-compose.dev.yml logs -f"
    echo "  重启服务: docker-compose -f docker-compose.dev.yml restart"
    echo "  停止服务: docker-compose -f docker-compose.dev.yml down"
    echo ""
}

# 主函数
main() {
    log_info "开始修复TradeMaster Docker部署问题..."
    
    # 检查是否在正确的目录
    if [ ! -f "docker-compose.dev.yml" ]; then
        log_error "请在web_interface目录下运行此脚本"
        exit 1
    fi
    
    check_docker_environment
    cleanup_old_containers
    create_required_directories
    verify_frontend_dependencies
    build_and_start_services
    verify_services
    show_service_info
    
    log_success "Docker部署问题修复完成！"
}

# 错误处理
trap 'log_error "脚本执行失败，请检查错误信息"; exit 1' ERR

# 运行主函数
main "$@"