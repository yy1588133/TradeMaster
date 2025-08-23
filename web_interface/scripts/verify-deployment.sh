#!/bin/bash

# ==================== TradeMaster Web Interface 部署验证脚本 ====================
# 该脚本用于验证部署状态，检查服务健康状况和连通性
# 使用方法: ./scripts/verify-deployment.sh [环境] [选项]
# 环境: dev, prod, integrated
# 选项: --detailed, --fix-issues, --export-report

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
DETAILED_CHECK=false
FIX_ISSUES=false
EXPORT_REPORT=false
REPORT_FILE=""

# 验证结果统计
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# ==================== 日志函数 ====================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
    ((WARNING_CHECKS++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED_CHECKS++))
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    ((TOTAL_CHECKS++))
}

# ==================== 工具函数 ====================
show_banner() {
    echo -e "${CYAN}"
    echo "=============================================================="
    echo "    TradeMaster Web Interface 部署验证脚本 v1.0.0"
    echo "=============================================================="
    echo -e "${NC}"
    echo "环境: $ENVIRONMENT"
    echo "验证时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================================="
    echo
}

show_usage() {
    echo "使用方法: $0 [环境] [选项]"
    echo
    echo "环境选项:"
    echo "  dev         验证开发环境部署"
    echo "  prod        验证生产环境部署"
    echo "  integrated  验证集成环境部署"
    echo
    echo "验证选项:"
    echo "  --detailed      详细验证模式"
    echo "  --fix-issues    自动修复可修复的问题"
    echo "  --export-report 导出验证报告"
    echo "  --help          显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 dev"
    echo "  $0 prod --detailed --export-report"
    echo "  $0 integrated --fix-issues"
    echo
}

parse_arguments() {
    for arg in "$@"; do
        case $arg in
            --detailed)
                DETAILED_CHECK=true
                ;;
            --fix-issues)
                FIX_ISSUES=true
                ;;
            --export-report)
                EXPORT_REPORT=true
                REPORT_FILE="logs/verification_report_$(date +%Y%m%d_%H%M%S).json"
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

# ==================== 基础验证函数 ====================
check_docker_status() {
    log_step "检查Docker环境状态"
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker守护进程未运行"
        return 1
    fi
    
    local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_success "Docker运行正常 (版本: $docker_version)"
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装"
        return 1
    fi
    
    log_success "Docker Compose可用"
    return 0
}

check_containers_status() {
    log_step "检查容器运行状态"
    
    local compose_file=""
    case $ENVIRONMENT in
        "dev")
            compose_file="docker-compose.dev.yml"
            ;;
        "prod")
            compose_file="docker-compose.prod.yml"
            ;;
        "integrated")
            compose_file="../docker-compose.extended.yml"
            ;;
    esac
    
    if [[ ! -f "$compose_file" ]]; then
        log_error "找不到compose文件: $compose_file"
        return 1
    fi
    
    # 获取应该运行的服务列表
    local expected_services
    case $ENVIRONMENT in
        "dev")
            expected_services=("postgres" "redis" "backend" "frontend" "nginx")
            ;;
        "prod")
            expected_services=("postgres" "redis" "backend" "frontend" "nginx")
            ;;
        "integrated")
            expected_services=("postgres" "redis" "backend" "frontend" "nginx" "trademaster-api")
            ;;
    esac
    
    local all_running=true
    
    for service in "${expected_services[@]}"; do
        local container_name
        case $ENVIRONMENT in
            "dev")
                container_name="trademaster-${service}-dev"
                ;;
            "prod")
                container_name="trademaster-${service}-prod"
                ;;
            "integrated")
                if [[ "$service" == "trademaster-api" ]]; then
                    container_name="trademaster-api"
                else
                    container_name="trademaster-${service}"
                fi
                ;;
        esac
        
        if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
            local status=$(docker inspect --format='{{.State.Status}}' "$container_name")
            if [[ "$status" == "running" ]]; then
                log_success "容器 $container_name 运行正常"
            else
                log_error "容器 $container_name 状态异常: $status"
                all_running=false
            fi
        else
            log_error "容器 $container_name 未运行"
            all_running=false
        fi
    done
    
    return $([ "$all_running" = true ])
}

check_container_health() {
    log_step "检查容器健康状态"
    
    local containers
    case $ENVIRONMENT in
        "dev")
            containers=("trademaster-postgres-dev" "trademaster-redis-dev" "trademaster-backend-dev" "trademaster-nginx-dev")
            ;;
        "prod")
            containers=("trademaster-postgres-prod" "trademaster-redis-prod")
            ;;
        "integrated")
            containers=("trademaster-postgres" "trademaster-redis" "trademaster-backend" "trademaster-nginx")
            ;;
    esac
    
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            local health=$(docker inspect --format='{{if .Config.Healthcheck}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container" 2>/dev/null)
            
            case $health in
                "healthy")
                    log_success "容器 $container 健康检查通过"
                    ;;
                "unhealthy")
                    log_error "容器 $container 健康检查失败"
                    if [[ "$DETAILED_CHECK" == "true" ]]; then
                        show_container_health_details "$container"
                    fi
                    ;;
                "starting")
                    log_warning "容器 $container 健康检查启动中"
                    ;;
                "no-healthcheck")
                    log_warning "容器 $container 未配置健康检查"
                    ;;
                *)
                    log_warning "容器 $container 健康状态未知: $health"
                    ;;
            esac
        fi
    done
}

show_container_health_details() {
    local container="$1"
    echo "    健康检查详情:"
    docker inspect --format='{{range .State.Health.Log}}    - {{.Start}}: {{.Output}}{{end}}' "$container" | tail -3
}

# ==================== 网络验证函数 ====================
check_networks() {
    log_step "检查Docker网络配置"
    
    local expected_networks
    case $ENVIRONMENT in
        "dev")
            expected_networks=("trademaster-dev-network")
            ;;
        "prod")
            expected_networks=("trademaster-external" "trademaster-frontend" "trademaster-backend")
            ;;
        "integrated")
            expected_networks=("trademaster-network")
            ;;
    esac
    
    for network in "${expected_networks[@]}"; do
        if docker network ls --format '{{.Name}}' | grep -q "^${network}$"; then
            log_success "网络 $network 存在"
            
            if [[ "$DETAILED_CHECK" == "true" ]]; then
                check_network_connectivity "$network"
            fi
        else
            log_error "网络 $network 不存在"
        fi
    done
}

check_network_connectivity() {
    local network="$1"
    local connected_containers=$(docker network inspect "$network" --format='{{range .Containers}}{{.Name}} {{end}}')
    
    if [[ -n "$connected_containers" ]]; then
        log_success "网络 $network 已连接容器: $connected_containers"
    else
        log_warning "网络 $network 无已连接容器"
    fi
}

# ==================== 服务连通性验证函数 ====================
check_database_connectivity() {
    log_step "检查数据库连接"
    
    local db_container
    case $ENVIRONMENT in
        "dev")
            db_container="trademaster-postgres-dev"
            ;;
        "prod")
            db_container="trademaster-postgres-prod"
            ;;
        "integrated")
            db_container="trademaster-postgres"
            ;;
    esac
    
    if docker exec "$db_container" pg_isready -U trademaster &>/dev/null; then
        log_success "PostgreSQL数据库连接正常"
        
        if [[ "$DETAILED_CHECK" == "true" ]]; then
            check_database_tables "$db_container"
        fi
    else
        log_error "PostgreSQL数据库连接失败"
        
        if [[ "$FIX_ISSUES" == "true" ]]; then
            attempt_database_fix "$db_container"
        fi
    fi
}

check_database_tables() {
    local db_container="$1"
    local table_count=$(docker exec "$db_container" psql -U trademaster -d trademaster_web -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")
    
    if [[ "$table_count" -gt 0 ]]; then
        log_success "数据库包含 $table_count 个表"
    else
        log_warning "数据库表为空，可能需要运行迁移"
    fi
}

attempt_database_fix() {
    local db_container="$1"
    log_info "尝试修复数据库连接..."
    
    # 重启数据库容器
    docker restart "$db_container"
    sleep 10
    
    if docker exec "$db_container" pg_isready -U trademaster &>/dev/null; then
        log_success "数据库修复成功"
    else
        log_error "数据库修复失败"
    fi
}

check_redis_connectivity() {
    log_step "检查Redis连接"
    
    local redis_container
    case $ENVIRONMENT in
        "dev")
            redis_container="trademaster-redis-dev"
            ;;
        "prod")
            redis_container="trademaster-redis-prod"
            ;;
        "integrated")
            redis_container="trademaster-redis"
            ;;
    esac
    
    if docker exec "$redis_container" redis-cli ping | grep -q "PONG"; then
        log_success "Redis连接正常"
        
        if [[ "$DETAILED_CHECK" == "true" ]]; then
            check_redis_memory "$redis_container"
        fi
    else
        log_error "Redis连接失败"
        
        if [[ "$FIX_ISSUES" == "true" ]]; then
            attempt_redis_fix "$redis_container"
        fi
    fi
}

check_redis_memory() {
    local redis_container="$1"
    local memory_info=$(docker exec "$redis_container" redis-cli info memory | grep used_memory_human)
    log_success "Redis内存使用: $memory_info"
}

attempt_redis_fix() {
    local redis_container="$1"
    log_info "尝试修复Redis连接..."
    
    docker restart "$redis_container"
    sleep 5
    
    if docker exec "$redis_container" redis-cli ping | grep -q "PONG"; then
        log_success "Redis修复成功"
    else
        log_error "Redis修复失败"
    fi
}

# ==================== HTTP服务验证函数 ====================
check_backend_api() {
    log_step "检查后端API服务"
    
    local api_url
    case $ENVIRONMENT in
        "dev")
            api_url="http://localhost:8000"
            ;;
        "prod"|"integrated")
            api_url="http://localhost:8080"
            ;;
    esac
    
    # 检查健康端点
    if curl -f -s "${api_url}/api/v1/health" >/dev/null; then
        log_success "后端API健康检查通过"
        
        if [[ "$DETAILED_CHECK" == "true" ]]; then
            check_api_endpoints "$api_url"
        fi
    else
        log_error "后端API健康检查失败"
        
        if [[ "$FIX_ISSUES" == "true" ]]; then
            attempt_backend_fix
        fi
    fi
}

check_api_endpoints() {
    local base_url="$1"
    local endpoints=("/api/v1/health" "/api/v1/auth/login" "/api/v1/strategies" "/api/v1/data")
    
    for endpoint in "${endpoints[@]}"; do
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" "${base_url}${endpoint}" || echo "000")
        
        case $status_code in
            200|401|422)  # 200=OK, 401=需要认证, 422=验证错误都是正常的
                log_success "端点 $endpoint 响应正常 (${status_code})"
                ;;
            000)
                log_error "端点 $endpoint 无法连接"
                ;;
            *)
                log_warning "端点 $endpoint 响应码: $status_code"
                ;;
        esac
    done
}

attempt_backend_fix() {
    log_info "尝试修复后端服务..."
    
    local backend_container
    case $ENVIRONMENT in
        "dev")
            backend_container="trademaster-backend-dev"
            ;;
        "prod")
            backend_container="trademaster-backend-prod"
            ;;
        "integrated")
            backend_container="trademaster-backend"
            ;;
    esac
    
    docker restart "$backend_container"
    sleep 15
    
    # 重新检查
    local api_url
    case $ENVIRONMENT in
        "dev")
            api_url="http://localhost:8000"
            ;;
        "prod"|"integrated")
            api_url="http://localhost:8080"
            ;;
    esac
    
    if curl -f -s "${api_url}/api/v1/health" >/dev/null; then
        log_success "后端服务修复成功"
    else
        log_error "后端服务修复失败"
    fi
}

check_frontend_service() {
    log_step "检查前端服务"
    
    local frontend_url
    case $ENVIRONMENT in
        "dev")
            frontend_url="http://localhost:3000"
            ;;
        "prod"|"integrated")
            frontend_url="http://localhost"
            ;;
    esac
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$frontend_url" || echo "000")
    
    case $status_code in
        200)
            log_success "前端服务响应正常"
            
            if [[ "$DETAILED_CHECK" == "true" ]]; then
                check_frontend_assets "$frontend_url"
            fi
            ;;
        000)
            log_error "前端服务无法连接"
            
            if [[ "$FIX_ISSUES" == "true" ]]; then
                attempt_frontend_fix
            fi
            ;;
        *)
            log_warning "前端服务响应码: $status_code"
            ;;
    esac
}

check_frontend_assets() {
    local base_url="$1"
    local assets=("/static/js/" "/static/css/" "/favicon.ico")
    
    for asset in "${assets[@]}"; do
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" "${base_url}${asset}" 2>/dev/null || echo "000")
        
        if [[ "$status_code" == "200" ]]; then
            log_success "前端资源 $asset 可访问"
        else
            log_warning "前端资源 $asset 访问异常 (${status_code})"
        fi
    done
}

attempt_frontend_fix() {
    log_info "尝试修复前端服务..."
    
    local frontend_container
    case $ENVIRONMENT in
        "dev")
            frontend_container="trademaster-frontend-dev"
            ;;
        "prod")
            frontend_container="trademaster-frontend-prod"
            ;;
        "integrated")
            frontend_container="trademaster-frontend"
            ;;
    esac
    
    docker restart "$frontend_container"
    sleep 10
    
    local frontend_url
    case $ENVIRONMENT in
        "dev")
            frontend_url="http://localhost:3000"
            ;;
        "prod"|"integrated")
            frontend_url="http://localhost"
            ;;
    esac
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$frontend_url" || echo "000")
    
    if [[ "$status_code" == "200" ]]; then
        log_success "前端服务修复成功"
    else
        log_error "前端服务修复失败"
    fi
}

# ==================== 数据卷验证函数 ====================
check_data_volumes() {
    log_step "检查数据卷状态"
    
    local expected_volumes
    case $ENVIRONMENT in
        "dev")
            expected_volumes=("trademaster-postgres-dev-data" "trademaster-redis-dev-data")
            ;;
        "prod")
            expected_volumes=("trademaster-postgres-prod-data" "trademaster-redis-prod-data" "trademaster-backend-prod-data")
            ;;
        "integrated")
            expected_volumes=("trademaster-postgres-data" "trademaster-redis-data" "trademaster-shared-data")
            ;;
    esac
    
    for volume in "${expected_volumes[@]}"; do
        if docker volume ls --format '{{.Name}}' | grep -q "^${volume}$"; then
            log_success "数据卷 $volume 存在"
            
            if [[ "$DETAILED_CHECK" == "true" ]]; then
                check_volume_usage "$volume"
            fi
        else
            log_error "数据卷 $volume 不存在"
        fi
    done
}

check_volume_usage() {
    local volume="$1"
    local mount_point=$(docker volume inspect "$volume" --format='{{.Mountpoint}}' 2>/dev/null)
    
    if [[ -n "$mount_point" && -d "$mount_point" ]]; then
        local size=$(du -sh "$mount_point" 2>/dev/null | cut -f1)
        log_success "数据卷 $volume 大小: $size"
    else
        log_warning "无法检查数据卷 $volume 使用情况"
    fi
}

# ==================== 性能验证函数 ====================
check_resource_usage() {
    log_step "检查资源使用情况"
    
    # 检查Docker系统资源
    local docker_stats=$(docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}")
    echo "Docker系统资源使用:"
    echo "$docker_stats"
    
    # 检查容器资源使用
    if [[ "$DETAILED_CHECK" == "true" ]]; then
        log_info "容器资源使用情况:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | grep trademaster || true
    fi
}

# ==================== 日志验证函数 ====================
check_service_logs() {
    log_step "检查服务日志"
    
    local services
    case $ENVIRONMENT in
        "dev")
            services=("postgres" "redis" "backend" "frontend")
            ;;
        "prod")
            services=("postgres" "redis" "backend" "frontend")
            ;;
        "integrated")
            services=("postgres" "redis" "backend" "frontend")
            ;;
    esac
    
    for service in "${services[@]}"; do
        local container_name
        case $ENVIRONMENT in
            "dev")
                container_name="trademaster-${service}-dev"
                ;;
            "prod")
                container_name="trademaster-${service}-prod"
                ;;
            "integrated")
                container_name="trademaster-${service}"
                ;;
        esac
        
        if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
            local error_count=$(docker logs "$container_name" --since 1h 2>&1 | grep -i "error\|exception\|fail" | wc -l)
            
            if [[ "$error_count" -eq 0 ]]; then
                log_success "服务 $service 日志正常"
            else
                log_warning "服务 $service 最近1小时有 $error_count 个错误日志"
                
                if [[ "$DETAILED_CHECK" == "true" ]]; then
                    echo "    最近错误:"
                    docker logs "$container_name" --since 1h 2>&1 | grep -i "error\|exception\|fail" | tail -3 | sed 's/^/    /'
                fi
            fi
        fi
    done
}

# ==================== 集成验证函数 ====================
check_trademaster_integration() {
    if [[ "$ENVIRONMENT" == "integrated" ]]; then
        log_step "检查TradeMaster集成"
        
        # 检查TradeMaster API
        if curl -f -s "http://localhost:8080/api/v1/health" >/dev/null; then
            log_success "TradeMaster API响应正常"
            
            # 检查Web界面与TradeMaster的集成
            if curl -f -s "http://localhost/api/v1/trademaster/status" >/dev/null; then
                log_success "Web界面与TradeMaster集成正常"
            else
                log_warning "Web界面与TradeMaster集成可能存在问题"
            fi
        else
            log_error "TradeMaster API无法访问"
        fi
    fi
}

# ==================== 报告生成函数 ====================
generate_verification_report() {
    if [[ "$EXPORT_REPORT" != "true" ]]; then
        return 0
    fi
    
    log_step "生成验证报告"
    
    mkdir -p "$(dirname "$REPORT_FILE")"
    
    cat > "$REPORT_FILE" << EOF
{
  "verification_report": {
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "environment": "$ENVIRONMENT",
    "summary": {
      "total_checks": $TOTAL_CHECKS,
      "passed_checks": $PASSED_CHECKS,
      "failed_checks": $FAILED_CHECKS,
      "warning_checks": $WARNING_CHECKS,
      "success_rate": "$(echo "scale=2; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc -l)%"
    },
    "system_info": {
      "docker_version": "$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)",
      "compose_version": "$(docker-compose --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo 'N/A')",
      "host_os": "$(uname -s)",
      "timestamp": "$(date)"
    },
    "containers": $(docker ps --format '{"name":"{{.Names}}","status":"{{.Status}}","ports":"{{.Ports}}"}' | jq -s .),
    "networks": $(docker network ls --format '{"name":"{{.Name}}","driver":"{{.Driver}}","scope":"{{.Scope}}"}' | jq -s .),
    "volumes": $(docker volume ls --format '{"name":"{{.Name}}","driver":"{{.Driver}}"}' | jq -s .)
  }
}
EOF
    
    log_success "验证报告已导出: $REPORT_FILE"
}

# ==================== 主验证流程 ====================
run_all_checks() {
    log_step "开始验证流程"
    
    # 基础检查
    check_docker_status
    check_containers_status
    check_container_health
    
    # 网络检查
    check_networks
    
    # 服务连通性检查
    check_database_connectivity
    check_redis_connectivity
    
    # HTTP服务检查
    check_backend_api
    check_frontend_service
    
    # 数据卷检查
    check_data_volumes
    
    # 资源使用检查
    if [[ "$DETAILED_CHECK" == "true" ]]; then
        check_resource_usage
    fi
    
    # 日志检查
    check_service_logs
    
    # 集成检查
    check_trademaster_integration
    
    # 生成报告
    generate_verification_report
}

show_summary() {
    echo
    echo -e "${CYAN}=============================================================="
    echo -e "    验证结果摘要"
    echo -e "==============================================================${NC}"
    echo
    echo "验证环境: $ENVIRONMENT"
    echo "验证时间: $(date)"
    echo
    echo -e "总检查项: ${BLUE}$TOTAL_CHECKS${NC}"
    echo -e "通过检查: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "失败检查: ${RED}$FAILED_CHECKS${NC}"
    echo -e "警告检查: ${YELLOW}$WARNING_CHECKS${NC}"
    
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        local success_rate=$(echo "scale=1; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc -l)
        echo -e "成功率: ${success_rate}%"
    fi
    
    echo
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        echo -e "${GREEN}🎉 部署验证通过！所有核心服务运行正常。${NC}"
        
        case $ENVIRONMENT in
            "dev")
                echo
                echo "访问地址:"
                echo "  - Web界面: http://localhost:3000"
                echo "  - API文档: http://localhost:8000/docs"
                echo "  - 数据库管理: http://localhost:5050"
                ;;
            "prod")
                echo
                echo "访问地址:"
                echo "  - Web界面: http://localhost"
                echo "  - 监控面板: http://localhost:3001"
                ;;
            "integrated")
                echo
                echo "访问地址:"
                echo "  - 统一入口: http://localhost"
                echo "  - TradeMaster API: http://localhost:8080"
                ;;
        esac
    else
        echo -e "${RED}❌ 部署验证失败！发现 $FAILED_CHECKS 个关键问题需要解决。${NC}"
        
        if [[ "$FIX_ISSUES" != "true" ]]; then
            echo
            echo "建议："
            echo "1. 使用 --fix-issues 参数尝试自动修复问题"
            echo "2. 查看详细日志排查具体原因"
            echo "3. 使用 ./scripts/collect-logs.sh 收集详细日志"
        fi
    fi
    
    if [[ "$EXPORT_REPORT" == "true" ]]; then
        echo
        echo -e "详细报告已导出: ${BLUE}$REPORT_FILE${NC}"
    fi
    
    echo
    echo "=============================================================="
}

# ==================== 主函数 ====================
main() {
    # 解析参数
    parse_arguments "$@"
    
    # 显示横幅
    show_banner
    
    # 运行所有检查
    run_all_checks
    
    # 显示摘要
    show_summary
    
    # 返回适当的退出码
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# ==================== 脚本入口 ====================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi