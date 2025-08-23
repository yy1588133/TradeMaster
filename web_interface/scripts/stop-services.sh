#!/bin/bash

# ==================== TradeMaster Web Interface 服务停止脚本 ====================
# 该脚本用于安全停止所有相关服务，支持优雅关闭和数据备份
# 使用方法: ./scripts/stop-services.sh [环境] [选项]
# 环境: dev, prod, integrated, all
# 选项: --force, --backup, --cleanup, --preserve-data

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
FORCE_STOP=false
CREATE_BACKUP=false
CLEANUP_RESOURCES=false
PRESERVE_DATA=true
GRACEFUL_TIMEOUT=30
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
    echo "    TradeMaster Web Interface 服务停止脚本 v1.0.0"
    echo "=============================================================="
    echo -e "${NC}"
    echo "环境: $ENVIRONMENT"
    echo "停止时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================================="
    echo
}

show_usage() {
    echo "使用方法: $0 [环境] [选项]"
    echo
    echo "环境选项:"
    echo "  dev         停止开发环境服务"
    echo "  prod        停止生产环境服务"
    echo "  integrated  停止集成环境服务"
    echo "  all         停止所有环境服务"
    echo
    echo "停止选项:"
    echo "  --force          强制停止服务（使用docker kill）"
    echo "  --backup         停止前创建数据备份"
    echo "  --cleanup        清理相关资源（镜像、网络、卷）"
    echo "  --preserve-data  保留数据（默认）"
    echo "  --remove-data    删除所有数据"
    echo "  --timeout        优雅停止超时时间（秒，默认30）"
    echo "  --verbose        详细输出"
    echo "  --help           显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 dev"
    echo "  $0 prod --backup --cleanup"
    echo "  $0 all --force"
    echo "  $0 integrated --timeout 60"
    echo
}

parse_arguments() {
    for arg in "$@"; do
        case $arg in
            --force)
                FORCE_STOP=true
                ;;
            --backup)
                CREATE_BACKUP=true
                ;;
            --cleanup)
                CLEANUP_RESOURCES=true
                ;;
            --preserve-data)
                PRESERVE_DATA=true
                ;;
            --remove-data)
                PRESERVE_DATA=false
                ;;
            --timeout)
                shift
                GRACEFUL_TIMEOUT=${1:-30}
                ;;
            --verbose)
                VERBOSE=true
                set -x
                ;;
            --help)
                show_usage
                exit 0
                ;;
            dev|prod|integrated|all)
                ENVIRONMENT=$arg
                ;;
            *)
                if [[ "$arg" != "$0" && "$arg" != "${GRACEFUL_TIMEOUT}" ]]; then
                    log_error "未知参数: $arg"
                    show_usage
                    exit 1
                fi
                ;;
        esac
    done
}

# ==================== 备份函数 ====================
create_data_backup() {
    if [[ "$CREATE_BACKUP" != "true" ]]; then
        return 0
    fi
    
    log_step "创建数据备份..."
    
    local backup_dir="backups/stop_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 备份数据库
    backup_database "$backup_dir"
    
    # 备份Redis数据
    backup_redis "$backup_dir"
    
    # 备份数据卷
    backup_volumes "$backup_dir"
    
    # 记录备份信息
    cat > "$backup_dir/backup.info" << EOF
Backup Type: Service Stop Backup
Backup Date: $(date)
Environment: $ENVIRONMENT
Project Root: $PROJECT_ROOT
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "Unknown")

Services Status Before Stop:
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep trademaster || echo "No running services")

Volumes Before Stop:
$(docker volume ls | grep trademaster || echo "No TradeMaster volumes")
EOF
    
    log_success "备份创建完成: $backup_dir"
    echo "$backup_dir" > .last_stop_backup
}

backup_database() {
    local backup_dir="$1"
    
    local db_containers
    case $ENVIRONMENT in
        "dev")
            db_containers=("trademaster-postgres-dev")
            ;;
        "prod")
            db_containers=("trademaster-postgres-prod")
            ;;
        "integrated")
            db_containers=("trademaster-postgres")
            ;;
        "all")
            db_containers=("trademaster-postgres-dev" "trademaster-postgres-prod" "trademaster-postgres")
            ;;
    esac
    
    for container in "${db_containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            log_info "备份数据库: $container"
            
            local backup_file="$backup_dir/${container}_$(date +%Y%m%d_%H%M%S).sql"
            
            if docker exec "$container" pg_dump -U trademaster -d trademaster_web > "$backup_file" 2>/dev/null; then
                log_success "数据库备份完成: $backup_file"
            else
                log_warning "数据库备份失败: $container"
            fi
        fi
    done
}

backup_redis() {
    local backup_dir="$1"
    
    local redis_containers
    case $ENVIRONMENT in
        "dev")
            redis_containers=("trademaster-redis-dev")
            ;;
        "prod")
            redis_containers=("trademaster-redis-prod")
            ;;
        "integrated")
            redis_containers=("trademaster-redis")
            ;;
        "all")
            redis_containers=("trademaster-redis-dev" "trademaster-redis-prod" "trademaster-redis")
            ;;
    esac
    
    for container in "${redis_containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            log_info "备份Redis数据: $container"
            
            # 触发Redis保存
            docker exec "$container" redis-cli BGSAVE >/dev/null 2>&1 || true
            sleep 2
            
            # 复制RDB文件
            if docker cp "$container:/data/dump.rdb" "$backup_dir/${container}_dump.rdb" 2>/dev/null; then
                log_success "Redis备份完成: ${container}_dump.rdb"
            else
                log_warning "Redis备份失败: $container"
            fi
        fi
    done
}

backup_volumes() {
    local backup_dir="$1"
    
    log_info "备份数据卷..."
    
    local volumes
    case $ENVIRONMENT in
        "dev")
            volumes=("trademaster-postgres-dev-data" "trademaster-redis-dev-data")
            ;;
        "prod")
            volumes=("trademaster-postgres-prod-data" "trademaster-redis-prod-data" "trademaster-backend-prod-data")
            ;;
        "integrated")
            volumes=("trademaster-postgres-data" "trademaster-redis-data" "trademaster-shared-data")
            ;;
        "all")
            volumes=($(docker volume ls --format '{{.Name}}' | grep trademaster))
            ;;
    esac
    
    for volume in "${volumes[@]}"; do
        if docker volume ls --format '{{.Name}}' | grep -q "^${volume}$"; then
            log_info "备份数据卷: $volume"
            
            # 使用临时容器备份卷数据
            docker run --rm -v "$volume:/source:ro" -v "$(pwd)/$backup_dir:/backup" \
                alpine tar -czf "/backup/${volume}.tar.gz" -C /source . 2>/dev/null || {
                log_warning "数据卷备份失败: $volume"
            }
        fi
    done
}

# ==================== 服务停止函数 ====================
stop_services_by_environment() {
    local env="$1"
    
    case $env in
        "dev")
            stop_development_services
            ;;
        "prod")
            stop_production_services
            ;;
        "integrated")
            stop_integrated_services
            ;;
        "all")
            stop_all_services
            ;;
        *)
            log_error "未知环境: $env"
            exit 1
            ;;
    esac
}

stop_development_services() {
    log_step "停止开发环境服务..."
    
    if [[ -f "docker-compose.dev.yml" ]]; then
        if [[ "$FORCE_STOP" == "true" ]]; then
            log_info "强制停止开发环境服务..."
            docker-compose -f docker-compose.dev.yml kill
        else
            log_info "优雅停止开发环境服务..."
            timeout "$GRACEFUL_TIMEOUT" docker-compose -f docker-compose.dev.yml down --timeout "$GRACEFUL_TIMEOUT" || {
                log_warning "优雅停止超时，执行强制停止..."
                docker-compose -f docker-compose.dev.yml kill
            }
        fi
        
        # 停止工具服务
        docker-compose -f docker-compose.dev.yml --profile tools down 2>/dev/null || true
        
        log_success "开发环境服务已停止"
    else
        log_warning "未找到开发环境配置文件"
    fi
}

stop_production_services() {
    log_step "停止生产环境服务..."
    
    if [[ -f "docker-compose.prod.yml" ]]; then
        if [[ "$FORCE_STOP" == "true" ]]; then
            log_info "强制停止生产环境服务..."
            docker-compose -f docker-compose.prod.yml kill
        else
            log_info "优雅停止生产环境服务..."
            
            # 首先停止前端服务以停止新请求
            docker-compose -f docker-compose.prod.yml stop frontend nginx 2>/dev/null || true
            sleep 5
            
            # 然后停止后端服务
            docker-compose -f docker-compose.prod.yml stop backend 2>/dev/null || true
            sleep 5
            
            # 最后停止数据服务
            timeout "$GRACEFUL_TIMEOUT" docker-compose -f docker-compose.prod.yml down --timeout "$GRACEFUL_TIMEOUT" || {
                log_warning "优雅停止超时，执行强制停止..."
                docker-compose -f docker-compose.prod.yml kill
            }
        fi
        
        # 停止监控服务
        docker-compose -f docker-compose.prod.yml --profile monitoring down 2>/dev/null || true
        
        log_success "生产环境服务已停止"
    else
        log_warning "未找到生产环境配置文件"
    fi
}

stop_integrated_services() {
    log_step "停止集成环境服务..."
    
    # 切换到主项目目录
    cd ..
    
    if [[ -f "docker-compose.extended.yml" ]]; then
        if [[ "$FORCE_STOP" == "true" ]]; then
            log_info "强制停止集成环境服务..."
            docker-compose -f docker-compose.yml -f docker-compose.extended.yml kill
        else
            log_info "优雅停止集成环境服务..."
            timeout "$GRACEFUL_TIMEOUT" docker-compose -f docker-compose.yml -f docker-compose.extended.yml down --timeout "$GRACEFUL_TIMEOUT" || {
                log_warning "优雅停止超时，执行强制停止..."
                docker-compose -f docker-compose.yml -f docker-compose.extended.yml kill
            }
        fi
        
        log_success "集成环境服务已停止"
    else
        log_warning "未找到集成环境配置文件"
    fi
    
    # 切换回原目录
    cd web_interface
}

stop_all_services() {
    log_step "停止所有环境服务..."
    
    # 找到所有TradeMaster相关容器
    local all_containers=$(docker ps --format '{{.Names}}' | grep trademaster || true)
    
    if [[ -n "$all_containers" ]]; then
        log_info "发现以下TradeMaster容器:"
        echo "$all_containers" | sed 's/^/  - /'
        
        if [[ "$FORCE_STOP" == "true" ]]; then
            log_info "强制停止所有容器..."
            echo "$all_containers" | xargs -r docker kill
        else
            log_info "优雅停止所有容器..."
            echo "$all_containers" | xargs -r docker stop --time "$GRACEFUL_TIMEOUT"
        fi
        
        log_success "所有TradeMaster服务已停止"
    else
        log_info "未发现运行中的TradeMaster服务"
    fi
}

# ==================== 资源清理函数 ====================
cleanup_resources() {
    if [[ "$CLEANUP_RESOURCES" != "true" ]]; then
        return 0
    fi
    
    log_step "清理相关资源..."
    
    # 清理停止的容器
    cleanup_containers
    
    # 清理网络
    cleanup_networks
    
    # 清理镜像
    cleanup_images
    
    # 清理数据卷（如果不保留数据）
    if [[ "$PRESERVE_DATA" != "true" ]]; then
        cleanup_volumes
    fi
    
    log_success "资源清理完成"
}

cleanup_containers() {
    log_info "清理停止的容器..."
    
    local stopped_containers=$(docker ps -a --filter "status=exited" --format '{{.Names}}' | grep trademaster || true)
    
    if [[ -n "$stopped_containers" ]]; then
        echo "$stopped_containers" | xargs -r docker rm
        log_success "已清理停止的容器"
    else
        log_info "无需清理的停止容器"
    fi
}

cleanup_networks() {
    log_info "清理未使用的网络..."
    
    local networks
    case $ENVIRONMENT in
        "dev")
            networks=("trademaster-dev-network")
            ;;
        "prod")
            networks=("trademaster-external" "trademaster-frontend" "trademaster-backend" "trademaster-monitoring")
            ;;
        "integrated")
            networks=("trademaster-network")
            ;;
        "all")
            networks=($(docker network ls --format '{{.Name}}' | grep trademaster))
            ;;
    esac
    
    for network in "${networks[@]}"; do
        if docker network ls --format '{{.Name}}' | grep -q "^${network}$"; then
            if docker network rm "$network" 2>/dev/null; then
                log_success "已清理网络: $network"
            else
                log_warning "网络清理失败（可能仍在使用中）: $network"
            fi
        fi
    done
}

cleanup_images() {
    log_info "清理未使用的镜像..."
    
    # 清理悬挂镜像
    local dangling_images=$(docker images -f "dangling=true" -q | grep -v "^$" || true)
    if [[ -n "$dangling_images" ]]; then
        echo "$dangling_images" | xargs -r docker rmi
        log_success "已清理悬挂镜像"
    fi
    
    # 清理TradeMaster镜像（如果指定）
    if [[ "$ENVIRONMENT" == "all" ]]; then
        local tm_images=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep trademaster || true)
        if [[ -n "$tm_images" ]]; then
            echo -n "是否删除所有TradeMaster镜像？这将需要重新构建 (y/N): "
            read -r response
            if [[ "$response" == "y" || "$response" == "Y" ]]; then
                echo "$tm_images" | xargs -r docker rmi
                log_success "已清理TradeMaster镜像"
            fi
        fi
    fi
}

cleanup_volumes() {
    log_warning "准备删除数据卷，这将永久删除所有数据！"
    echo -n "确认删除所有数据？(yes/NO): "
    read -r confirmation
    
    if [[ "$confirmation" == "yes" ]]; then
        log_info "清理数据卷..."
        
        local volumes
        case $ENVIRONMENT in
            "dev")
                volumes=($(docker volume ls --format '{{.Name}}' | grep "trademaster.*dev"))
                ;;
            "prod")
                volumes=($(docker volume ls --format '{{.Name}}' | grep "trademaster.*prod"))
                ;;
            "integrated")
                volumes=($(docker volume ls --format '{{.Name}}' | grep trademaster | grep -v dev | grep -v prod))
                ;;
            "all")
                volumes=($(docker volume ls --format '{{.Name}}' | grep trademaster))
                ;;
        esac
        
        for volume in "${volumes[@]}"; do
            if docker volume rm "$volume" 2>/dev/null; then
                log_success "已删除数据卷: $volume"
            else
                log_warning "数据卷删除失败（可能仍在使用中）: $volume"
            fi
        done
    else
        log_info "取消数据卷清理"
    fi
}

# ==================== 状态检查函数 ====================
verify_stop_status() {
    log_step "验证服务停止状态..."
    
    local running_containers=$(docker ps --format '{{.Names}}' | grep trademaster || true)
    
    if [[ -z "$running_containers" ]]; then
        log_success "所有TradeMaster服务已完全停止"
        return 0
    else
        log_warning "以下服务仍在运行:"
        echo "$running_containers" | sed 's/^/  - /'
        
        if [[ "$FORCE_STOP" == "true" ]]; then
            log_info "执行强制清理..."
            echo "$running_containers" | xargs -r docker kill
            echo "$running_containers" | xargs -r docker rm
            log_success "强制清理完成"
        else
            log_error "部分服务未能正常停止"
            return 1
        fi
    fi
}

# ==================== 报告生成函数 ====================
generate_stop_report() {
    log_step "生成停止报告..."
    
    local report_file="logs/stop_report_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
=== TradeMaster Web Interface 服务停止报告 ===
停止时间: $(date)
环境: $ENVIRONMENT
项目路径: $PROJECT_ROOT
执行选项:
  - 强制停止: $FORCE_STOP
  - 创建备份: $CREATE_BACKUP
  - 清理资源: $CLEANUP_RESOURCES
  - 保留数据: $PRESERVE_DATA

=== 停止前容器状态 ===
$(cat logs/pre_stop_containers.log 2>/dev/null || echo "未记录")

=== 当前容器状态 ===
$(docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.CreatedAt}}" | grep trademaster || echo "无TradeMaster相关容器")

=== 当前网络状态 ===
$(docker network ls | grep trademaster || echo "无TradeMaster相关网络")

=== 当前数据卷状态 ===
$(docker volume ls | grep trademaster || echo "无TradeMaster相关数据卷")

停止状态: 成功
EOF
    
    log_success "停止报告已生成: $report_file"
}

# ==================== 主函数 ====================
main() {
    # 解析参数
    parse_arguments "$@"
    
    # 显示横幅
    show_banner
    
    # 确认操作
    if [[ "$FORCE_STOP" == "true" || "$CLEANUP_RESOURCES" == "true" || "$PRESERVE_DATA" != "true" ]]; then
        echo -e "${YELLOW}警告: 您即将执行可能影响数据的操作${NC}"
        echo "环境: $ENVIRONMENT"
        echo "强制停止: $FORCE_STOP"
        echo "清理资源: $CLEANUP_RESOURCES"
        echo "保留数据: $PRESERVE_DATA"
        echo
        echo -n "确认继续？(y/N): "
        read -r response
        if [[ "$response" != "y" && "$response" != "Y" ]]; then
            log_info "操作已取消"
            exit 0
        fi
    fi
    
    # 记录停止前状态
    mkdir -p logs
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" > logs/pre_stop_containers.log
    
    # 执行停止流程
    log_step "开始服务停止流程..."
    
    # 1. 创建备份
    create_data_backup
    
    # 2. 停止服务
    stop_services_by_environment "$ENVIRONMENT"
    
    # 3. 验证停止状态
    if verify_stop_status; then
        # 4. 清理资源
        cleanup_resources
        
        # 5. 生成报告
        generate_stop_report
        
        show_success_message
    else
        handle_stop_failure
    fi
}

show_success_message() {
    echo
    echo -e "${GREEN}=============================================================="
    echo -e "    🛑 服务停止完成！"
    echo -e "==============================================================${NC}"
    echo
    echo "停止环境: $ENVIRONMENT"
    echo "停止时间: $(date)"
    echo
    
    if [[ "$CREATE_BACKUP" == "true" && -f ".last_stop_backup" ]]; then
        echo "数据备份: $(cat .last_stop_backup)"
    fi
    
    echo "资源清理: $([ "$CLEANUP_RESOURCES" == "true" ] && echo "已执行" || echo "未执行")"
    echo "数据保留: $([ "$PRESERVE_DATA" == "true" ] && echo "是" || echo "否")"
    echo
    
    echo "管理命令:"
    echo "  - 重新启动服务: ./scripts/deploy.sh $ENVIRONMENT"
    echo "  - 查看停止的容器: docker ps -a | grep trademaster"
    echo "  - 清理系统: docker system prune"
    echo
    echo -e "${GREEN}停止完成！${NC}"
}

handle_stop_failure() {
    log_error "服务停止过程中遇到问题"
    
    # 收集错误信息
    local error_log="logs/stop_error_$(date +%Y%m%d_%H%M%S).log"
    
    {
        echo "=== 服务停止失败报告 ==="
        echo "时间: $(date)"
        echo "环境: $ENVIRONMENT"
        echo
        echo "=== 当前运行容器 ==="
        docker ps | grep trademaster || echo "无运行容器"
        echo
        echo "=== 停止的容器 ==="
        docker ps -a --filter "status=exited" | grep trademaster || echo "无停止容器"
        echo
        echo "=== 系统资源 ==="
        docker system df
    } > "$error_log"
    
    log_error "错误日志已保存到: $error_log"
    
    echo -n "是否强制清理所有相关资源？(y/N): "
    read -r response
    if [[ "$response" == "y" || "$response" == "Y" ]]; then
        FORCE_STOP=true
        CLEANUP_RESOURCES=true
        log_info "执行强制清理..."
        stop_services_by_environment "$ENVIRONMENT"
        cleanup_resources
    fi
    
    exit 1
}

# ==================== 脚本入口 ====================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi