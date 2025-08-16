#!/bin/bash

# ==================== TradeMaster Web Interface 一键部署脚本 ====================
# 该脚本提供完整的部署自动化功能，包括环境检查、构建、部署和验证
# 使用方法: ./scripts/deploy.sh [环境] [选项]
# 环境: dev, prod, integrated
# 选项: --no-build, --force, --backup, --rollback

set -e

# ==================== 脚本配置 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 默认配置
ENVIRONMENT=${1:-"dev"}
BUILD_IMAGES=true
FORCE_REBUILD=false
CREATE_BACKUP=false
ROLLBACK_MODE=false
VERBOSE=false

# ==================== 日志函数 ====================
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# ==================== 工具函数 ====================
show_banner() {
    echo -e "${CYAN}"
    echo "=============================================================="
    echo "    TradeMaster Web Interface 部署脚本 v1.0.0"
    echo "=============================================================="
    echo -e "${NC}"
    echo "环境: $ENVIRONMENT"
    echo "项目路径: $PROJECT_ROOT"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================================="
    echo
}

show_usage() {
    echo "使用方法: $0 [环境] [选项]"
    echo
    echo "环境选项:"
    echo "  dev         开发环境部署"
    echo "  prod        生产环境部署"
    echo "  integrated  集成环境部署（包含TradeMaster核心）"
    echo
    echo "部署选项:"
    echo "  --no-build    跳过镜像构建"
    echo "  --force       强制重新构建镜像"
    echo "  --backup      部署前创建备份"
    echo "  --rollback    回滚到上一个版本"
    echo "  --verbose     详细输出"
    echo "  --help        显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 dev"
    echo "  $0 prod --backup --force"
    echo "  $0 integrated --no-build"
    echo
}

parse_arguments() {
    for arg in "$@"; do
        case $arg in
            --no-build)
                BUILD_IMAGES=false
                ;;
            --force)
                FORCE_REBUILD=true
                ;;
            --backup)
                CREATE_BACKUP=true
                ;;
            --rollback)
                ROLLBACK_MODE=true
                ;;
            --verbose)
                VERBOSE=true
                set -x
                ;;
            --help)
                show_usage
                exit 0
                ;;
            dev|prod|integrated)
                ENVIRONMENT=$arg
                ;;
            *)
                log_error "未知参数: $arg"
                show_usage
                exit 1
                ;;
        esac
    done
}

# ==================== 环境检查函数 ====================
check_prerequisites() {
    log_step "检查系统环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装或不可用"
        exit 1
    fi
    
    local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_info "Docker版本: $docker_version"
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装或不可用"
        exit 1
    fi
    
    # 检查Docker守护进程
    if ! docker info &> /dev/null; then
        log_error "Docker守护进程未运行"
        exit 1
    fi
    
    # 检查磁盘空间
    local available_space=$(df . | tail -1 | awk '{print $4}')
    local available_gb=$((available_space / 1024 / 1024))
    
    if [ $available_gb -lt 5 ]; then
        log_error "磁盘空间不足，需要至少5GB可用空间，当前可用: ${available_gb}GB"
        exit 1
    fi
    
    log_info "可用磁盘空间: ${available_gb}GB"
    
    # 检查端口占用
    check_port_availability
    
    log_success "系统环境检查通过"
}

check_port_availability() {
    local ports=()
    
    case $ENVIRONMENT in
        "dev")
            ports=(3000 8000 80 5432 6379 5050 8081 8025)
            ;;
        "prod")
            ports=(80 443 8080 5432 6379 9090 3001)
            ;;
        "integrated")
            ports=(80 443 8080 5432 6379)
            ;;
    esac
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "端口 $port 已被占用"
            if [[ "$ENVIRONMENT" != "dev" ]]; then
                log_error "生产环境不允许端口冲突"
                exit 1
            fi
        fi
    done
}

check_configuration() {
    log_step "检查配置文件..."
    
    local env_file=""
    case $ENVIRONMENT in
        "dev")
            env_file=".env.dev"
            ;;
        "prod")
            env_file=".env.prod"
            if [[ ! -f "$env_file" ]]; then
                log_warning "生产环境配置文件不存在，尝试从模板创建"
                if [[ -f ".env.prod.template" ]]; then
                    cp ".env.prod.template" "$env_file"
                    log_error "请编辑 $env_file 文件，填入实际的生产环境配置"
                    exit 1
                fi
            fi
            ;;
        "integrated")
            env_file="../.env"
            if [[ ! -f "$env_file" ]]; then
                log_warning "集成环境配置文件不存在，尝试从模板创建"
                if [[ -f "../.env.integrated.template" ]]; then
                    cp "../.env.integrated.template" "$env_file"
                    log_error "请编辑 $env_file 文件，填入实际配置"
                    exit 1
                fi
            fi
            ;;
    esac
    
    if [[ -f "$env_file" ]]; then
        log_info "使用配置文件: $env_file"
        
        # 检查关键配置项
        if [[ "$ENVIRONMENT" == "prod" ]]; then
            check_production_security "$env_file"
        fi
    else
        log_error "配置文件不存在: $env_file"
        exit 1
    fi
    
    log_success "配置文件检查通过"
}

check_production_security() {
    local env_file="$1"
    local security_issues=()
    
    # 检查默认密码
    if grep -q "CHANGE_THIS" "$env_file"; then
        security_issues+=("发现默认密码，必须修改")
    fi
    
    # 检查DEBUG模式
    if grep -q "DEBUG=true" "$env_file"; then
        security_issues+=("生产环境不应启用DEBUG模式")
    fi
    
    # 检查密钥长度
    local secret_key=$(grep "SECRET_KEY=" "$env_file" | cut -d'=' -f2)
    if [[ ${#secret_key} -lt 32 ]]; then
        security_issues+=("SECRET_KEY长度不足，至少需要32位")
    fi
    
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        log_error "生产环境安全检查失败:"
        for issue in "${security_issues[@]}"; do
            log_error "  - $issue"
        done
        exit 1
    fi
    
    log_success "生产环境安全检查通过"
}

# ==================== 数据管理函数 ====================
create_directories() {
    log_step "创建必需的目录..."
    
    local dirs=(
        "docker/volumes"
        "docker/volumes/postgres_data"
        "docker/volumes/postgres_backups"
        "docker/volumes/redis_data"
        "docker/volumes/backend_data"
        "docker/volumes/backend_logs"
        "docker/volumes/backend_uploads"
        "docker/volumes/frontend_logs"
        "docker/volumes/nginx_logs"
        "temp"
        "logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
    
    # 设置权限
    chmod 755 docker/volumes
    chmod 700 docker/volumes/postgres_data docker/volumes/redis_data
    
    log_success "目录创建完成"
}

backup_data() {
    if [[ "$CREATE_BACKUP" != "true" ]]; then
        return 0
    fi
    
    log_step "创建数据备份..."
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 停止服务以确保数据一致性
    stop_services
    
    # 备份数据卷
    if [[ -d "docker/volumes" ]]; then
        log_info "备份数据卷..."
        tar -czf "$backup_dir/volumes.tar.gz" docker/volumes/
    fi
    
    # 备份配置文件
    log_info "备份配置文件..."
    cp -r docker/ "$backup_dir/" 2>/dev/null || true
    cp .env* "$backup_dir/" 2>/dev/null || true
    
    # 记录备份信息
    cat > "$backup_dir/backup.info" << EOF
Backup Date: $(date)
Environment: $ENVIRONMENT
Project Root: $PROJECT_ROOT
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "Unknown")
Docker Images:
$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}" | grep trademaster || true)
EOF
    
    log_success "备份创建完成: $backup_dir"
    echo "$backup_dir" > .last_backup
}

# ==================== Docker管理函数 ====================
build_images() {
    if [[ "$BUILD_IMAGES" != "true" ]]; then
        log_info "跳过镜像构建"
        return 0
    fi
    
    log_step "构建Docker镜像..."
    
    local build_args="--build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    
    if [[ "$FORCE_REBUILD" == "true" ]]; then
        build_args="$build_args --no-cache"
        log_info "强制重新构建镜像"
    fi
    
    case $ENVIRONMENT in
        "dev")
            log_info "构建开发环境镜像..."
            docker-compose -f docker-compose.dev.yml build $build_args
            ;;
        "prod")
            log_info "构建生产环境镜像..."
            docker-compose -f docker-compose.prod.yml build $build_args
            ;;
        "integrated")
            log_info "构建集成环境镜像..."
            cd ..
            docker-compose -f docker-compose.extended.yml build $build_args
            cd web_interface
            ;;
    esac
    
    log_success "镜像构建完成"
}

deploy_services() {
    log_step "部署服务..."
    
    case $ENVIRONMENT in
        "dev")
            log_info "启动开发环境服务..."
            docker-compose -f docker-compose.dev.yml up -d
            ;;
        "prod")
            log_info "启动生产环境服务..."
            docker-compose -f docker-compose.prod.yml up -d
            ;;
        "integrated")
            log_info "启动集成环境服务..."
            cd ..
            docker-compose -f docker-compose.yml -f docker-compose.extended.yml up -d
            cd web_interface
            ;;
    esac
    
    log_success "服务部署完成"
}

stop_services() {
    log_step "停止现有服务..."
    
    case $ENVIRONMENT in
        "dev")
            docker-compose -f docker-compose.dev.yml down || true
            ;;
        "prod")
            docker-compose -f docker-compose.prod.yml down || true
            ;;
        "integrated")
            cd ..
            docker-compose -f docker-compose.yml -f docker-compose.extended.yml down || true
            cd web_interface
            ;;
    esac
    
    log_success "服务停止完成"
}

# ==================== 验证函数 ====================
wait_for_services() {
    log_step "等待服务启动..."
    
    local max_wait=300  # 5分钟
    local wait_time=0
    local check_interval=10
    
    while [[ $wait_time -lt $max_wait ]]; do
        if check_service_health; then
            log_success "所有服务已就绪"
            return 0
        fi
        
        log_info "等待服务启动... (${wait_time}s/${max_wait}s)"
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
    done
    
    log_error "服务启动超时"
    return 1
}

check_service_health() {
    local all_healthy=true
    
    case $ENVIRONMENT in
        "dev")
            # 检查开发环境服务
            if ! curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
                all_healthy=false
            fi
            if ! curl -f http://localhost:3000 >/dev/null 2>&1; then
                all_healthy=false
            fi
            ;;
        "prod"|"integrated")
            # 检查生产/集成环境服务
            if ! curl -f http://localhost/health >/dev/null 2>&1; then
                all_healthy=false
            fi
            if ! curl -f http://localhost:8080/health >/dev/null 2>&1; then
                all_healthy=false
            fi
            ;;
    esac
    
    return $([ "$all_healthy" = true ])
}

run_post_deploy_tasks() {
    log_step "执行部署后任务..."
    
    # 运行数据库迁移
    run_database_migrations
    
    # 清理旧镜像
    cleanup_old_images
    
    # 生成部署报告
    generate_deploy_report
    
    log_success "部署后任务完成"
}

run_database_migrations() {
    log_info "运行数据库迁移..."
    
    local backend_container=""
    case $ENVIRONMENT in
        "dev")
            backend_container="trademaster-backend-dev"
            ;;
        "prod")
            backend_container="trademaster-backend-prod"
            ;;
        "integrated")
            backend_container="trademaster-web-backend"
            ;;
    esac
    
    if docker ps | grep -q "$backend_container"; then
        docker exec "$backend_container" alembic upgrade head || log_warning "数据库迁移失败或无需迁移"
    else
        log_warning "后端容器未运行，跳过数据库迁移"
    fi
}

cleanup_old_images() {
    log_info "清理旧镜像..."
    
    # 清理悬挂镜像
    docker image prune -f >/dev/null 2>&1 || true
    
    # 清理旧的构建缓存
    docker builder prune -f >/dev/null 2>&1 || true
    
    log_info "镜像清理完成"
}

generate_deploy_report() {
    log_info "生成部署报告..."
    
    local report_file="logs/deploy_$(date +%Y%m%d_%H%M%S).log"
    
    cat > "$report_file" << EOF
=== TradeMaster Web Interface 部署报告 ===
部署时间: $(date)
环境: $ENVIRONMENT
项目路径: $PROJECT_ROOT
Git提交: $(git rev-parse HEAD 2>/dev/null || echo "Unknown")

=== 容器状态 ===
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")

=== 镜像信息 ===
$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep trademaster || echo "无TradeMaster相关镜像")

=== 网络信息 ===
$(docker network ls | grep trademaster || echo "无TradeMaster相关网络")

=== 数据卷信息 ===
$(docker volume ls | grep trademaster || echo "无TradeMaster相关数据卷")

=== 服务健康检查 ===
Backend Health: $(curl -s http://localhost:8000/api/v1/health 2>/dev/null && echo "OK" || echo "FAIL")
Frontend Health: $(curl -s http://localhost/health 2>/dev/null && echo "OK" || echo "FAIL")

部署状态: 成功
EOF
    
    log_success "部署报告已生成: $report_file"
}

# ==================== 主函数 ====================
main() {
    # 解析参数
    parse_arguments "$@"
    
    # 显示横幅
    show_banner
    
    # 回滚模式
    if [[ "$ROLLBACK_MODE" == "true" ]]; then
        perform_rollback
        return 0
    fi
    
    # 执行部署流程
    log_step "开始部署流程..."
    
    # 1. 环境检查
    check_prerequisites
    check_configuration
    
    # 2. 数据准备
    create_directories
    backup_data
    
    # 3. 停止现有服务
    stop_services
    
    # 4. 构建和部署
    build_images
    deploy_services
    
    # 5. 验证部署
    if wait_for_services; then
        run_post_deploy_tasks
        show_success_message
    else
        handle_deploy_failure
    fi
}

perform_rollback() {
    log_step "执行回滚操作..."
    
    local last_backup=$(cat .last_backup 2>/dev/null || echo "")
    if [[ -z "$last_backup" || ! -d "$last_backup" ]]; then
        log_error "未找到可用的备份"
        exit 1
    fi
    
    log_info "回滚到备份: $last_backup"
    
    # 停止服务
    stop_services
    
    # 恢复数据
    if [[ -f "$last_backup/volumes.tar.gz" ]]; then
        log_info "恢复数据卷..."
        rm -rf docker/volumes/
        tar -xzf "$last_backup/volumes.tar.gz"
    fi
    
    # 启动服务
    deploy_services
    
    if wait_for_services; then
        log_success "回滚完成"
    else
        log_error "回滚失败"
        exit 1
    fi
}

show_success_message() {
    echo
    echo -e "${GREEN}=============================================================="
    echo -e "    🎉 部署成功完成！"
    echo -e "==============================================================${NC}"
    echo
    echo "环境: $ENVIRONMENT"
    echo "部署时间: $(date)"
    echo
    
    case $ENVIRONMENT in
        "dev")
            echo "访问地址:"
            echo "  - Web界面: http://localhost:3000"
            echo "  - API文档: http://localhost:8000/docs"
            echo "  - pgAdmin: http://localhost:5050"
            echo "  - Redis管理: http://localhost:8081"
            echo "  - 邮件测试: http://localhost:8025"
            ;;
        "prod")
            echo "访问地址:"
            echo "  - Web界面: http://localhost"
            echo "  - TradeMaster API: http://localhost:8080"
            echo "  - 监控面板: http://localhost:3001 (如果启用)"
            ;;
        "integrated")
            echo "访问地址:"
            echo "  - 统一入口: http://localhost"
            echo "  - Web界面: http://localhost"
            echo "  - TradeMaster API: http://localhost:8080"
            ;;
    esac
    
    echo
    echo "管理命令:"
    echo "  - 查看状态: docker-compose ps"
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 重启服务: docker-compose restart"
    echo "  - 停止服务: docker-compose down"
    echo
    echo -e "${GREEN}部署完成！${NC}"
}

handle_deploy_failure() {
    log_error "部署失败"
    
    # 收集错误信息
    log_info "收集错误信息..."
    
    local error_log="logs/deploy_error_$(date +%Y%m%d_%H%M%S).log"
    {
        echo "=== 部署失败报告 ==="
        echo "时间: $(date)"
        echo "环境: $ENVIRONMENT"
        echo
        echo "=== 容器状态 ==="
        docker ps -a
        echo
        echo "=== 服务日志 ==="
        case $ENVIRONMENT in
            "dev")
                docker-compose -f docker-compose.dev.yml logs --tail=50
                ;;
            "prod")
                docker-compose -f docker-compose.prod.yml logs --tail=50
                ;;
            "integrated")
                cd ..
                docker-compose -f docker-compose.extended.yml logs --tail=50
                cd web_interface
                ;;
        esac
    } > "$error_log"
    
    log_error "错误日志已保存到: $error_log"
    
    # 询问是否回滚
    if [[ -f ".last_backup" ]]; then
        echo -n "是否回滚到上一个版本？(y/N): "
        read -r response
        if [[ "$response" == "y" || "$response" == "Y" ]]; then
            perform_rollback
        fi
    fi
    
    exit 1
}

# ==================== 脚本入口 ====================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi