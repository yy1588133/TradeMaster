#!/bin/bash

# ==================== TradeMaster Web Interface 健康检查脚本 ====================
# 该脚本用于快速检查服务健康状态，支持不同的检查级别
# 使用方法: ./scripts/health-check.sh [环境] [检查级别] [选项]
# 环境: dev, prod, integrated
# 检查级别: quick, detailed, continuous

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
CHECK_LEVEL=${2:-"quick"}
CONTINUOUS_MODE=false
CHECK_INTERVAL=30
OUTPUT_FORMAT="text"
ALERT_THRESHOLD=3
FAILED_COUNT=0

# ==================== 日志函数 ====================
log_info() {
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "{\"level\":\"info\",\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"message\":\"$1\"}"
    else
        echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') - $1"
    fi
}

log_success() {
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "{\"level\":\"success\",\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"message\":\"$1\"}"
    else
        echo -e "${GREEN}[✓]${NC} $1"
    fi
}

log_warning() {
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "{\"level\":\"warning\",\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"message\":\"$1\"}"
    else
        echo -e "${YELLOW}[⚠]${NC} $1"
    fi
}

log_error() {
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "{\"level\":\"error\",\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"message\":\"$1\"}"
    else
        echo -e "${RED}[✗]${NC} $1"
    fi
}

log_critical() {
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "{\"level\":\"critical\",\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"message\":\"$1\"}"
    else
        echo -e "${RED}[CRITICAL]${NC} $1"
    fi
    ((FAILED_COUNT++))
}

# ==================== 工具函数 ====================
show_banner() {
    if [[ "$OUTPUT_FORMAT" != "json" ]]; then
        echo -e "${CYAN}"
        echo "=============================================================="
        echo "    TradeMaster Web Interface 健康检查脚本 v1.0.0"
        echo "=============================================================="
        echo -e "${NC}"
        echo "环境: $ENVIRONMENT"
        echo "检查级别: $CHECK_LEVEL"
        echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "=============================================================="
        echo
    fi
}

show_usage() {
    echo "使用方法: $0 [环境] [检查级别] [选项]"
    echo
    echo "环境选项:"
    echo "  dev         开发环境健康检查"
    echo "  prod        生产环境健康检查"
    echo "  integrated  集成环境健康检查"
    echo
    echo "检查级别:"
    echo "  quick       快速健康检查 (默认)"
    echo "  detailed    详细健康检查"
    echo "  continuous  持续监控模式"
    echo
    echo "输出选项:"
    echo "  --json      JSON格式输出"
    echo "  --interval  持续模式检查间隔(秒，默认30)"
    echo "  --quiet     静默模式，仅输出错误"
    echo "  --help      显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 dev quick"
    echo "  $0 prod detailed --json"
    echo "  $0 integrated continuous --interval 60"
    echo
}

parse_arguments() {
    for arg in "$@"; do
        case $arg in
            --json)
                OUTPUT_FORMAT="json"
                ;;
            --interval)
                shift
                CHECK_INTERVAL=${1:-30}
                ;;
            --quiet)
                OUTPUT_FORMAT="quiet"
                ;;
            --help)
                show_usage
                exit 0
                ;;
            dev|prod|integrated)
                ENVIRONMENT=$arg
                ;;
            quick|detailed|continuous)
                CHECK_LEVEL=$arg
                if [[ "$CHECK_LEVEL" == "continuous" ]]; then
                    CONTINUOUS_MODE=true
                fi
                ;;
            *)
                if [[ "$arg" != "$0" ]]; then
                    log_error "未知参数: $arg"
                    show_usage
                    exit 1
                fi
                ;;
        esac
    done
}

# ==================== 核心健康检查函数 ====================
check_container_status() {
    local service="$1"
    local container_name="$2"
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        local status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null)
        local health=$(docker inspect --format='{{if .Config.Healthcheck}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container_name" 2>/dev/null)
        
        case $status in
            "running")
                case $health in
                    "healthy")
                        log_success "$service 容器运行正常且健康"
                        return 0
                        ;;
                    "unhealthy")
                        log_critical "$service 容器运行但健康检查失败"
                        return 1
                        ;;
                    "starting")
                        log_warning "$service 容器健康检查启动中"
                        return 2
                        ;;
                    "no-healthcheck")
                        log_success "$service 容器运行正常 (无健康检查)"
                        return 0
                        ;;
                    *)
                        log_warning "$service 容器运行但健康状态未知: $health"
                        return 2
                        ;;
                esac
                ;;
            "restarting")
                log_warning "$service 容器正在重启"
                return 2
                ;;
            "paused")
                log_warning "$service 容器已暂停"
                return 2
                ;;
            "exited")
                log_critical "$service 容器已退出"
                return 1
                ;;
            *)
                log_critical "$service 容器状态异常: $status"
                return 1
                ;;
        esac
    else
        log_critical "$service 容器未运行"
        return 1
    fi
}

check_database_health() {
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
    
    if ! check_container_status "PostgreSQL数据库" "$db_container"; then
        return 1
    fi
    
    # 检查数据库连接
    if docker exec "$db_container" pg_isready -U trademaster -d trademaster_web &>/dev/null; then
        log_success "数据库连接正常"
        
        if [[ "$CHECK_LEVEL" == "detailed" ]]; then
            # 检查数据库性能
            local connections=$(docker exec "$db_container" psql -U trademaster -d trademaster_web -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ')
            log_info "活跃数据库连接数: $connections"
            
            # 检查数据库大小
            local db_size=$(docker exec "$db_container" psql -U trademaster -d trademaster_web -t -c "SELECT pg_size_pretty(pg_database_size('trademaster_web'));" 2>/dev/null | tr -d ' ')
            log_info "数据库大小: $db_size"
        fi
        
        return 0
    else
        log_critical "数据库连接失败"
        return 1
    fi
}

check_redis_health() {
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
    
    if ! check_container_status "Redis缓存" "$redis_container"; then
        return 1
    fi
    
    # 检查Redis连接
    if docker exec "$redis_container" redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis连接正常"
        
        if [[ "$CHECK_LEVEL" == "detailed" ]]; then
            # 检查Redis内存使用
            local memory_used=$(docker exec "$redis_container" redis-cli info memory 2>/dev/null | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
            log_info "Redis内存使用: $memory_used"
            
            # 检查Redis连接数
            local clients=$(docker exec "$redis_container" redis-cli info clients 2>/dev/null | grep "connected_clients:" | cut -d: -f2 | tr -d '\r')
            log_info "Redis连接数: $clients"
        fi
        
        return 0
    else
        log_critical "Redis连接失败"
        return 1
    fi
}

check_backend_health() {
    local backend_container
    local api_url
    
    case $ENVIRONMENT in
        "dev")
            backend_container="trademaster-backend-dev"
            api_url="http://localhost:8000"
            ;;
        "prod")
            backend_container="trademaster-backend-prod"
            api_url="http://localhost:8080"
            ;;
        "integrated")
            backend_container="trademaster-backend"
            api_url="http://localhost:8080"
            ;;
    esac
    
    if ! check_container_status "后端服务" "$backend_container"; then
        return 1
    fi
    
    # 检查API健康端点
    local start_time=$(date +%s)
    if curl -f -s --max-time 10 "${api_url}/api/v1/health" >/dev/null 2>&1; then
        local end_time=$(date +%s)
        local response_time=$((end_time - start_time))
        
        if [[ $response_time -lt 3 ]]; then
            log_success "后端API响应正常 (${response_time}s)"
        else
            log_warning "后端API响应较慢 (${response_time}s)"
        fi
        
        if [[ "$CHECK_LEVEL" == "detailed" ]]; then
            # 检查API端点
            check_api_endpoints "$api_url"
        fi
        
        return 0
    else
        log_critical "后端API健康检查失败"
        return 1
    fi
}

check_api_endpoints() {
    local base_url="$1"
    local endpoints=("/api/v1/health" "/api/v1/auth/login" "/api/v1/strategies")
    
    for endpoint in "${endpoints[@]}"; do
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${base_url}${endpoint}" 2>/dev/null || echo "000")
        
        case $status_code in
            200)
                log_success "API端点 $endpoint 正常"
                ;;
            401|422)
                log_success "API端点 $endpoint 正常 (需要认证)"
                ;;
            000)
                log_error "API端点 $endpoint 无法连接"
                ;;
            5*)
                log_error "API端点 $endpoint 服务器错误 ($status_code)"
                ;;
            *)
                log_warning "API端点 $endpoint 响应异常 ($status_code)"
                ;;
        esac
    done
}

check_frontend_health() {
    local frontend_container
    local frontend_url
    
    case $ENVIRONMENT in
        "dev")
            frontend_container="trademaster-frontend-dev"
            frontend_url="http://localhost:3000"
            ;;
        "prod")
            frontend_container="trademaster-frontend-prod"
            frontend_url="http://localhost"
            ;;
        "integrated")
            frontend_container="trademaster-frontend"
            frontend_url="http://localhost"
            ;;
    esac
    
    if ! check_container_status "前端服务" "$frontend_container"; then
        return 1
    fi
    
    # 检查前端访问
    local start_time=$(date +%s)
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$frontend_url" 2>/dev/null || echo "000")
    local end_time=$(date +%s)
    local response_time=$((end_time - start_time))
    
    case $status_code in
        200)
            if [[ $response_time -lt 5 ]]; then
                log_success "前端服务响应正常 (${response_time}s)"
            else
                log_warning "前端服务响应较慢 (${response_time}s)"
            fi
            return 0
            ;;
        000)
            log_critical "前端服务无法连接"
            return 1
            ;;
        *)
            log_error "前端服务响应异常 ($status_code)"
            return 1
            ;;
    esac
}

check_nginx_health() {
    local nginx_container
    
    case $ENVIRONMENT in
        "dev")
            nginx_container="trademaster-nginx-dev"
            ;;
        "prod")
            nginx_container="trademaster-nginx-prod"
            ;;
        "integrated")
            nginx_container="trademaster-nginx"
            ;;
    esac
    
    if ! check_container_status "Nginx网关" "$nginx_container"; then
        return 1
    fi
    
    # 检查Nginx配置
    if docker exec "$nginx_container" nginx -t &>/dev/null; then
        log_success "Nginx配置正常"
        return 0
    else
        log_critical "Nginx配置错误"
        return 1
    fi
}

# ==================== 系统资源检查 ====================
check_system_resources() {
    if [[ "$CHECK_LEVEL" != "detailed" ]]; then
        return 0
    fi
    
    # 检查磁盘空间
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $disk_usage -lt 80 ]]; then
        log_success "磁盘使用率正常 (${disk_usage}%)"
    elif [[ $disk_usage -lt 90 ]]; then
        log_warning "磁盘使用率较高 (${disk_usage}%)"
    else
        log_critical "磁盘空间不足 (${disk_usage}%)"
    fi
    
    # 检查内存使用
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [[ $memory_usage -lt 80 ]]; then
        log_success "内存使用率正常 (${memory_usage}%)"
    elif [[ $memory_usage -lt 90 ]]; then
        log_warning "内存使用率较高 (${memory_usage}%)"
    else
        log_critical "内存使用率过高 (${memory_usage}%)"
    fi
    
    # 检查CPU负载
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local load_percentage=$(echo "scale=0; $load_avg * 100 / $cpu_cores" | bc -l)
    
    if [[ ${load_percentage%.*} -lt 70 ]]; then
        log_success "CPU负载正常 (${load_avg})"
    elif [[ ${load_percentage%.*} -lt 90 ]]; then
        log_warning "CPU负载较高 (${load_avg})"
    else
        log_critical "CPU负载过高 (${load_avg})"
    fi
}

# ==================== 集成检查 ====================
check_integration_health() {
    if [[ "$ENVIRONMENT" != "integrated" ]]; then
        return 0
    fi
    
    # 检查TradeMaster API
    if curl -f -s --max-time 10 "http://localhost:8080/api/v1/health" >/dev/null 2>&1; then
        log_success "TradeMaster核心API正常"
        
        # 检查Web界面与TradeMaster的集成
        if curl -f -s --max-time 10 "http://localhost/api/v1/trademaster/status" >/dev/null 2>&1; then
            log_success "Web界面与TradeMaster集成正常"
        else
            log_warning "Web界面与TradeMaster集成可能存在问题"
        fi
    else
        log_critical "TradeMaster核心API无法访问"
        return 1
    fi
    
    return 0
}

# ==================== 主检查流程 ====================
run_health_checks() {
    local overall_status=0
    
    # 重置失败计数
    FAILED_COUNT=0
    
    # 数据库健康检查
    if ! check_database_health; then
        overall_status=1
    fi
    
    # Redis健康检查
    if ! check_redis_health; then
        overall_status=1
    fi
    
    # 后端健康检查
    if ! check_backend_health; then
        overall_status=1
    fi
    
    # 前端健康检查
    if ! check_frontend_health; then
        overall_status=1
    fi
    
    # Nginx健康检查
    if ! check_nginx_health; then
        overall_status=1
    fi
    
    # 系统资源检查
    check_system_resources
    
    # 集成检查
    if ! check_integration_health; then
        overall_status=1
    fi
    
    return $overall_status
}

# ==================== 输出格式化 ====================
output_health_status() {
    local status="$1"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        cat << EOF
{
  "timestamp": "$timestamp",
  "environment": "$ENVIRONMENT",
  "status": "$([ $status -eq 0 ] && echo "healthy" || echo "unhealthy")",
  "failed_checks": $FAILED_COUNT,
  "check_level": "$CHECK_LEVEL"
}
EOF
    elif [[ "$OUTPUT_FORMAT" != "quiet" ]]; then
        echo
        if [[ $status -eq 0 ]]; then
            echo -e "${GREEN}🎉 所有服务健康检查通过！${NC}"
        else
            echo -e "${RED}❌ 发现 $FAILED_COUNT 个健康问题！${NC}"
        fi
        echo
    fi
}

# ==================== 持续监控模式 ====================
continuous_monitoring() {
    log_info "启动持续监控模式，检查间隔: ${CHECK_INTERVAL}秒"
    log_info "按 Ctrl+C 停止监控"
    
    local consecutive_failures=0
    
    while true; do
        if [[ "$OUTPUT_FORMAT" != "json" && "$OUTPUT_FORMAT" != "quiet" ]]; then
            echo "========== $(date '+%Y-%m-%d %H:%M:%S') =========="
        fi
        
        if run_health_checks; then
            consecutive_failures=0
            if [[ "$OUTPUT_FORMAT" != "quiet" ]]; then
                log_success "健康检查通过"
            fi
        else
            ((consecutive_failures++))
            log_error "健康检查失败 (连续失败: $consecutive_failures 次)"
            
            # 连续失败达到阈值时发出警报
            if [[ $consecutive_failures -ge $ALERT_THRESHOLD ]]; then
                log_critical "连续健康检查失败 $consecutive_failures 次，请立即检查系统状态！"
                
                # 这里可以添加警报通知逻辑
                # send_alert "TradeMaster健康检查连续失败"
            fi
        fi
        
        output_health_status $?
        
        sleep "$CHECK_INTERVAL"
    done
}

# ==================== 信号处理 ====================
cleanup() {
    if [[ "$CONTINUOUS_MODE" == "true" ]]; then
        log_info "停止持续监控模式"
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# ==================== 主函数 ====================
main() {
    # 解析参数
    parse_arguments "$@"
    
    # 显示横幅 (非JSON模式)
    if [[ "$CONTINUOUS_MODE" != "true" ]]; then
        show_banner
    fi
    
    # 执行健康检查
    if [[ "$CONTINUOUS_MODE" == "true" ]]; then
        continuous_monitoring
    else
        if run_health_checks; then
            output_health_status 0
            exit 0
        else
            output_health_status 1
            exit 1
        fi
    fi
}

# ==================== 脚本入口 ====================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi