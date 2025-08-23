#!/bin/bash

# ==================== TradeMaster Web Interface 日志收集脚本 ====================
# 该脚本用于收集所有服务的日志信息，支持故障排查和性能分析
# 使用方法: ./scripts/collect-logs.sh [环境] [选项]
# 环境: dev, prod, integrated, all
# 选项: --since, --follow, --export, --analyze

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
SINCE_TIME="1h"
FOLLOW_MODE=false
EXPORT_LOGS=false
ANALYZE_LOGS=false
OUTPUT_DIR="logs/collected_$(date +%Y%m%d_%H%M%S)"
VERBOSE=false
LINES_LIMIT=1000

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
    echo "    TradeMaster Web Interface 日志收集脚本 v1.0.0"
    echo "=============================================================="
    echo -e "${NC}"
    echo "环境: $ENVIRONMENT"
    echo "时间范围: $SINCE_TIME"
    echo "收集时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================================="
    echo
}

show_usage() {
    echo "使用方法: $0 [环境] [选项]"
    echo
    echo "环境选项:"
    echo "  dev         收集开发环境日志"
    echo "  prod        收集生产环境日志"
    echo "  integrated  收集集成环境日志"
    echo "  all         收集所有环境日志"
    echo
    echo "时间选项:"
    echo "  --since     指定时间范围 (默认: 1h)"
    echo "              格式: 1h, 30m, 2d, 2023-01-01T00:00:00"
    echo "  --lines     限制输出行数 (默认: 1000)"
    echo
    echo "输出选项:"
    echo "  --follow    跟踪实时日志输出"
    echo "  --export    导出日志到文件"
    echo "  --analyze   分析日志并生成报告"
    echo "  --verbose   详细输出"
    echo "  --help      显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 dev --since 2h"
    echo "  $0 prod --export --analyze"
    echo "  $0 all --follow"
    echo "  $0 integrated --since 1d --lines 5000"
    echo
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --since)
                SINCE_TIME="$2"
                shift 2
                ;;
            --lines)
                LINES_LIMIT="$2"
                shift 2
                ;;
            --follow)
                FOLLOW_MODE=true
                shift
                ;;
            --export)
                EXPORT_LOGS=true
                shift
                ;;
            --analyze)
                ANALYZE_LOGS=true
                EXPORT_LOGS=true  # 分析需要导出
                shift
                ;;
            --verbose)
                VERBOSE=true
                set -x
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            dev|prod|integrated|all)
                ENVIRONMENT=$1
                shift
                ;;
            *)
                if [[ "$1" != "$0" ]]; then
                    log_error "未知参数: $1"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# ==================== 容器发现函数 ====================
discover_containers() {
    local env="$1"
    local containers=()
    
    case $env in
        "dev")
            containers=(
                "trademaster-postgres-dev"
                "trademaster-redis-dev"
                "trademaster-backend-dev"
                "trademaster-frontend-dev"
                "trademaster-nginx-dev"
                "trademaster-pgadmin-dev"
                "trademaster-redis-commander-dev"
                "trademaster-mailhog-dev"
            )
            ;;
        "prod")
            containers=(
                "trademaster-postgres-prod"
                "trademaster-redis-prod"
                "trademaster-backend-prod"
                "trademaster-frontend-prod"
                "trademaster-nginx-prod"
                "trademaster-prometheus-prod"
                "trademaster-grafana-prod"
                "trademaster-backup-prod"
            )
            ;;
        "integrated")
            containers=(
                "trademaster-postgres"
                "trademaster-redis"
                "trademaster-backend"
                "trademaster-frontend"
                "trademaster-nginx"
                "trademaster-api"
            )
            ;;
        "all")
            # 自动发现所有TradeMaster相关容器
            containers=($(docker ps -a --format '{{.Names}}' | grep trademaster))
            ;;
    esac
    
    # 过滤出实际存在的容器
    local existing_containers=()
    for container in "${containers[@]}"; do
        if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
            existing_containers+=("$container")
        fi
    done
    
    echo "${existing_containers[@]}"
}

# ==================== 日志收集函数 ====================
collect_container_logs() {
    local container="$1"
    local output_file="$2"
    
    log_info "收集容器日志: $container"
    
    # 检查容器是否存在
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        log_warning "容器不存在: $container"
        return 1
    fi
    
    # 获取容器状态
    local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
    
    if [[ "$EXPORT_LOGS" == "true" ]]; then
        # 导出模式：写入文件
        {
            echo "=== 容器日志: $container ==="
            echo "收集时间: $(date)"
            echo "容器状态: $status"
            echo "时间范围: $SINCE_TIME"
            echo "========================================"
            echo
            
            # 收集日志
            if [[ "$FOLLOW_MODE" == "true" ]]; then
                docker logs --since "$SINCE_TIME" -f "$container" 2>&1 &
            else
                docker logs --since "$SINCE_TIME" --tail "$LINES_LIMIT" "$container" 2>&1
            fi
            
            echo
            echo "======== 日志收集完成 ========"
            echo
        } >> "$output_file" 2>&1
    else
        # 显示模式：直接输出
        echo -e "${CYAN}=== 容器日志: $container ===${NC}"
        echo "容器状态: $status"
        echo "时间范围: $SINCE_TIME"
        echo "----------------------------------------"
        
        if [[ "$FOLLOW_MODE" == "true" ]]; then
            docker logs --since "$SINCE_TIME" -f "$container" 2>&1 &
        else
            docker logs --since "$SINCE_TIME" --tail "$LINES_LIMIT" "$container" 2>&1
        fi
        echo
    fi
}

collect_system_info() {
    if [[ "$EXPORT_LOGS" != "true" ]]; then
        return 0
    fi
    
    local info_file="$OUTPUT_DIR/system_info.txt"
    
    log_info "收集系统信息..."
    
    {
        echo "=== TradeMaster Web Interface 系统信息 ==="
        echo "收集时间: $(date)"
        echo "环境: $ENVIRONMENT"
        echo "主机: $(hostname)"
        echo "操作系统: $(uname -a)"
        echo
        
        echo "=== Docker 信息 ==="
        docker version 2>/dev/null || echo "Docker版本信息获取失败"
        echo
        docker info 2>/dev/null || echo "Docker系统信息获取失败"
        echo
        
        echo "=== Docker Compose 信息 ==="
        docker-compose --version 2>/dev/null || echo "Docker Compose版本信息获取失败"
        echo
        
        echo "=== 容器状态 ==="
        docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.CreatedAt}}" | grep trademaster || echo "无TradeMaster相关容器"
        echo
        
        echo "=== 镜像信息 ==="
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep trademaster || echo "无TradeMaster相关镜像"
        echo
        
        echo "=== 网络信息 ==="
        docker network ls | grep trademaster || echo "无TradeMaster相关网络"
        echo
        
        echo "=== 数据卷信息 ==="
        docker volume ls | grep trademaster || echo "无TradeMaster相关数据卷"
        echo
        
        echo "=== 系统资源 ==="
        echo "磁盘使用:"
        df -h | head -1
        df -h | grep -E "(/$|/var|/opt)" || true
        echo
        echo "内存使用:"
        free -h
        echo
        echo "CPU信息:"
        lscpu | grep -E "(Model name|CPU\(s\)|Thread|Core)" || true
        echo
        echo "负载信息:"
        uptime
        echo
        
        echo "=== Docker 资源使用 ==="
        docker system df
        echo
        
        echo "=== 运行中容器资源使用 ==="
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | grep trademaster || echo "无运行中的TradeMaster容器"
        
    } > "$info_file"
    
    log_success "系统信息已保存: $info_file"
}

collect_configuration_files() {
    if [[ "$EXPORT_LOGS" != "true" ]]; then
        return 0
    fi
    
    local config_dir="$OUTPUT_DIR/configurations"
    mkdir -p "$config_dir"
    
    log_info "收集配置文件..."
    
    # 复制Docker Compose文件
    for file in docker-compose*.yml; do
        if [[ -f "$file" ]]; then
            cp "$file" "$config_dir/"
        fi
    done
    
    # 复制环境配置文件
    for file in .env*; do
        if [[ -f "$file" && "$file" != ".env.example" ]]; then
            # 复制但隐藏敏感信息
            sed 's/\(PASSWORD\|SECRET\|KEY\)=.*/\1=***HIDDEN***/g' "$file" > "$config_dir/$(basename "$file")"
        fi
    done
    
    # 复制Nginx配置
    if [[ -d "docker/nginx" ]]; then
        cp -r docker/nginx "$config_dir/"
    fi
    
    # 收集容器配置信息
    {
        echo "=== 容器配置信息 ==="
        echo "收集时间: $(date)"
        echo
        
        for container in $(discover_containers "$ENVIRONMENT"); do
            if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
                echo "--- 容器: $container ---"
                docker inspect "$container" 2>/dev/null | jq '.[] | {
                    Name: .Name,
                    Image: .Config.Image,
                    Status: .State.Status,
                    RestartPolicy: .HostConfig.RestartPolicy,
                    Ports: .NetworkSettings.Ports,
                    Mounts: .Mounts,
                    Environment: .Config.Env
                }' 2>/dev/null || echo "配置信息获取失败"
                echo
            fi
        done
    } > "$config_dir/container_configs.json"
    
    log_success "配置文件已保存到: $config_dir"
}

# ==================== 日志分析函数 ====================
analyze_logs() {
    if [[ "$ANALYZE_LOGS" != "true" ]]; then
        return 0
    fi
    
    log_step "分析日志文件..."
    
    local analysis_file="$OUTPUT_DIR/log_analysis.txt"
    local error_summary="$OUTPUT_DIR/error_summary.txt"
    
    {
        echo "=== TradeMaster Web Interface 日志分析报告 ==="
        echo "分析时间: $(date)"
        echo "环境: $ENVIRONMENT"
        echo "时间范围: $SINCE_TIME"
        echo "=============================================="
        echo
        
        # 总体统计
        echo "=== 总体统计 ==="
        local total_lines=0
        local error_lines=0
        local warning_lines=0
        
        for log_file in "$OUTPUT_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                local file_lines=$(wc -l < "$log_file")
                local file_errors=$(grep -ic "error\|exception\|fail\|fatal" "$log_file" 2>/dev/null || echo 0)
                local file_warnings=$(grep -ic "warning\|warn" "$log_file" 2>/dev/null || echo 0)
                
                total_lines=$((total_lines + file_lines))
                error_lines=$((error_lines + file_errors))
                warning_lines=$((warning_lines + file_warnings))
                
                echo "$(basename "$log_file"): $file_lines 行, $file_errors 错误, $file_warnings 警告"
            fi
        done
        
        echo "总计: $total_lines 行, $error_lines 错误, $warning_lines 警告"
        echo
        
        # 错误分析
        echo "=== 错误分析 ==="
        
        # 统计错误类型
        echo "常见错误模式:"
        for log_file in "$OUTPUT_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                grep -i "error\|exception\|fail\|fatal" "$log_file" 2>/dev/null | \
                    sed 's/.*\(error\|exception\|fail\|fatal\)[^:]*:*\s*\(.*\)/\2/' | \
                    sort | uniq -c | sort -nr | head -10 | \
                    sed "s/^/  $(basename "$log_file"): /"
            fi
        done
        echo
        
        # 性能分析
        echo "=== 性能分析 ==="
        
        # 响应时间分析
        echo "HTTP响应时间分析:"
        for log_file in "$OUTPUT_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                # 寻找响应时间模式
                grep -oE "[0-9]+\.[0-9]+s|[0-9]+ms" "$log_file" 2>/dev/null | head -20 | \
                    sed "s/^/  $(basename "$log_file"): /"
            fi
        done
        echo
        
        # 内存使用分析
        echo "内存使用警告:"
        for log_file in "$OUTPUT_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                grep -i "memory\|oom\|out of memory" "$log_file" 2>/dev/null | head -10 | \
                    sed "s/^/  $(basename "$log_file"): /"
            fi
        done
        echo
        
        # 连接问题分析
        echo "=== 连接问题分析 ==="
        echo "数据库连接问题:"
        for log_file in "$OUTPUT_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                grep -i "connection.*database\|database.*connection\|postgresql" "$log_file" 2>/dev/null | \
                    grep -i "error\|fail\|timeout" | head -10 | \
                    sed "s/^/  $(basename "$log_file"): /"
            fi
        done
        echo
        
        echo "Redis连接问题:"
        for log_file in "$OUTPUT_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                grep -i "redis.*connection\|connection.*redis" "$log_file" 2>/dev/null | \
                    grep -i "error\|fail\|timeout" | head -10 | \
                    sed "s/^/  $(basename "$log_file"): /"
            fi
        done
        echo
        
        # 建议
        echo "=== 建议和推荐操作 ==="
        
        if [[ $error_lines -gt 100 ]]; then
            echo "- 发现大量错误日志($error_lines 条)，建议立即检查系统状态"
        fi
        
        if [[ $warning_lines -gt 50 ]]; then
            echo "- 发现较多警告信息($warning_lines 条)，建议关注系统性能"
        fi
        
        # 检查是否有频繁重启
        local restart_count=$(grep -r "started\|restarted" "$OUTPUT_DIR"/*.log 2>/dev/null | wc -l)
        if [[ $restart_count -gt 5 ]]; then
            echo "- 检测到频繁重启($restart_count 次)，建议检查服务稳定性"
        fi
        
        # 检查磁盘空间警告
        if grep -q "disk.*full\|no space" "$OUTPUT_DIR"/*.log 2>/dev/null; then
            echo "- 检测到磁盘空间问题，建议立即清理磁盘空间"
        fi
        
        echo
        echo "详细错误信息请查看: $error_summary"
        
    } > "$analysis_file"
    
    # 生成错误摘要
    {
        echo "=== 错误详细信息 ==="
        echo "生成时间: $(date)"
        echo "========================"
        echo
        
        for log_file in "$OUTPUT_DIR"/*.log; do
            if [[ -f "$log_file" ]]; then
                echo "--- $(basename "$log_file") ---"
                grep -n -i "error\|exception\|fail\|fatal" "$log_file" 2>/dev/null | head -50
                echo
            fi
        done
    } > "$error_summary"
    
    log_success "日志分析完成: $analysis_file"
}

# ==================== 主收集流程 ====================
collect_all_logs() {
    local containers=($(discover_containers "$ENVIRONMENT"))
    
    if [[ ${#containers[@]} -eq 0 ]]; then
        log_warning "未发现任何TradeMaster容器"
        return 1
    fi
    
    log_info "发现 ${#containers[@]} 个容器: ${containers[*]}"
    
    if [[ "$EXPORT_LOGS" == "true" ]]; then
        mkdir -p "$OUTPUT_DIR"
        log_info "日志将导出到: $OUTPUT_DIR"
    fi
    
    # 收集系统信息
    collect_system_info
    
    # 收集配置文件
    collect_configuration_files
    
    # 收集各容器日志
    for container in "${containers[@]}"; do
        local log_file=""
        if [[ "$EXPORT_LOGS" == "true" ]]; then
            log_file="$OUTPUT_DIR/${container}.log"
        fi
        
        collect_container_logs "$container" "$log_file"
        
        if [[ "$FOLLOW_MODE" != "true" ]]; then
            echo "----------------------------------------"
        fi
    done
    
    # 等待跟踪模式的后台进程
    if [[ "$FOLLOW_MODE" == "true" ]]; then
        log_info "按 Ctrl+C 停止日志跟踪"
        wait
    fi
    
    # 分析日志
    analyze_logs
    
    if [[ "$EXPORT_LOGS" == "true" ]]; then
        generate_collection_report
    fi
}

generate_collection_report() {
    local report_file="$OUTPUT_DIR/collection_report.txt"
    
    {
        echo "=== TradeMaster 日志收集报告 ==="
        echo "收集时间: $(date)"
        echo "环境: $ENVIRONMENT"
        echo "时间范围: $SINCE_TIME"
        echo "输出目录: $OUTPUT_DIR"
        echo "==============================="
        echo
        
        echo "=== 收集的文件 ==="
        find "$OUTPUT_DIR" -type f -exec ls -lh {} \; | while read -r line; do
            echo "  $line"
        done
        echo
        
        echo "=== 目录大小 ==="
        du -sh "$OUTPUT_DIR"
        echo
        
        echo "=== 收集摘要 ==="
        local total_files=$(find "$OUTPUT_DIR" -name "*.log" | wc -l)
        local total_size=$(du -sh "$OUTPUT_DIR" | cut -f1)
        
        echo "日志文件数: $total_files"
        echo "总大小: $total_size"
        echo "收集完成时间: $(date)"
        
    } > "$report_file"
    
    log_success "收集报告已生成: $report_file"
}

# ==================== 实时监控模式 ====================
start_real_time_monitoring() {
    if [[ "$FOLLOW_MODE" != "true" ]]; then
        return 0
    fi
    
    log_info "启动实时日志监控模式"
    log_info "按 Ctrl+C 停止监控"
    
    # 创建命名管道用于日志聚合
    local pipe_dir="/tmp/trademaster_logs_$$"
    mkdir -p "$pipe_dir"
    
    # 清理函数
    cleanup_monitoring() {
        log_info "停止实时监控"
        pkill -P $$ 2>/dev/null || true
        rm -rf "$pipe_dir" 2>/dev/null || true
        exit 0
    }
    
    trap cleanup_monitoring SIGINT SIGTERM
    
    # 启动各容器日志跟踪
    local containers=($(discover_containers "$ENVIRONMENT"))
    
    for container in "${containers[@]}"; do
        {
            while true; do
                if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
                    docker logs -f --since "$SINCE_TIME" "$container" 2>&1 | \
                        sed "s/^/[${container}] /"
                else
                    sleep 5
                fi
            done
        } &
    done
    
    wait
}

# ==================== 主函数 ====================
main() {
    # 解析参数
    parse_arguments "$@"
    
    # 显示横幅
    show_banner
    
    # 检查Docker环境
    if ! docker info &>/dev/null; then
        log_error "Docker未运行或无法访问"
        exit 1
    fi
    
    # 执行日志收集
    if [[ "$FOLLOW_MODE" == "true" ]]; then
        start_real_time_monitoring
    else
        collect_all_logs
        show_completion_message
    fi
}

show_completion_message() {
    echo
    echo -e "${GREEN}=============================================================="
    echo -e "    📋 日志收集完成！"
    echo -e "==============================================================${NC}"
    echo
    echo "收集环境: $ENVIRONMENT"
    echo "时间范围: $SINCE_TIME"
    
    if [[ "$EXPORT_LOGS" == "true" ]]; then
        echo "输出目录: $OUTPUT_DIR"
        echo "总大小: $(du -sh "$OUTPUT_DIR" | cut -f1)"
        
        echo
        echo "生成的文件:"
        find "$OUTPUT_DIR" -type f -name "*.txt" -o -name "*.log" -o -name "*.json" | while read -r file; do
            echo "  - $(basename "$file")"
        done
        
        if [[ "$ANALYZE_LOGS" == "true" ]]; then
            echo
            echo "分析报告:"
            echo "  - 日志分析: $OUTPUT_DIR/log_analysis.txt"
            echo "  - 错误摘要: $OUTPUT_DIR/error_summary.txt"
        fi
    fi
    
    echo
    echo "后续操作建议:"
    echo "  - 查看分析报告了解系统状态"
    echo "  - 根据错误信息进行问题排查"
    echo "  - 定期收集日志监控系统健康"
    echo
    echo -e "${GREEN}收集完成！${NC}"
}

# ==================== 脚本入口 ====================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi