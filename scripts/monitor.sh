#!/bin/bash
# ==================== TradeMaster Web Interface 系统监控脚本 ====================
# 
# 功能:
# - 实时系统资源监控
# - 应用性能监控
# - 服务健康检查
# - 日志监控和分析
# - 告警通知
#
# 使用方法:
#   ./scripts/monitor.sh [options]
#
# 选项:
#   --system        系统资源监控
#   --services      服务健康检查
#   --logs          日志监控
#   --performance   性能监控
#   --alerts        启用告警
#   --dashboard     启动监控面板
#   --duration      监控持续时间（秒，默认60）
#   --interval      监控间隔（秒，默认5）
#   --help          显示帮助信息

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 图标定义
SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
INFO="ℹ️"
MONITOR="📊"
HEART="💓"
CHART="📈"
ALERT="🚨"
CLOCK="⏰"
SYSTEM="🖥️"
SERVICE="🔧"
LOG="📝"

# 默认配置
MONITOR_SYSTEM=false
MONITOR_SERVICES=false
MONITOR_LOGS=false
MONITOR_PERFORMANCE=false
ENABLE_ALERTS=false
SHOW_DASHBOARD=false
MONITOR_DURATION=60
MONITOR_INTERVAL=5
HELP=false

# 如果没有指定监控类型，则监控所有
MONITOR_ALL=true

# 告警阈值
CPU_THRESHOLD=80
MEMORY_THRESHOLD=80
DISK_THRESHOLD=90
RESPONSE_TIME_THRESHOLD=2000  # 毫秒

# 参数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --system)
            MONITOR_SYSTEM=true
            MONITOR_ALL=false
            shift
            ;;
        --services)
            MONITOR_SERVICES=true
            MONITOR_ALL=false
            shift
            ;;
        --logs)
            MONITOR_LOGS=true
            MONITOR_ALL=false
            shift
            ;;
        --performance)
            MONITOR_PERFORMANCE=true
            MONITOR_ALL=false
            shift
            ;;
        --alerts)
            ENABLE_ALERTS=true
            shift
            ;;
        --dashboard)
            SHOW_DASHBOARD=true
            shift
            ;;
        --duration)
            MONITOR_DURATION="$2"
            shift 2
            ;;
        --interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        --help)
            HELP=true
            shift
            ;;
        *)
            echo -e "${ERROR} ${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

# 如果没有指定特定监控，运行基本监控
if [ "$MONITOR_ALL" = true ]; then
    MONITOR_SYSTEM=true
    MONITOR_SERVICES=true
    MONITOR_PERFORMANCE=true
fi

# 帮助信息
show_help() {
    echo -e "${BLUE}TradeMaster Web Interface 系统监控脚本${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/monitor.sh [options]"
    echo ""
    echo "监控选项:"
    echo "  --system        系统资源监控"
    echo "  --services      服务健康检查"
    echo "  --logs          日志监控"
    echo "  --performance   性能监控"
    echo ""
    echo "其他选项:"
    echo "  --alerts        启用告警"
    echo "  --dashboard     启动监控面板"
    echo "  --duration N    监控持续时间（秒，默认60）"
    echo "  --interval N    监控间隔（秒，默认5）"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/monitor.sh                           # 基本监控"
    echo "  ./scripts/monitor.sh --system --alerts         # 系统监控+告警"
    echo "  ./scripts/monitor.sh --dashboard --duration 300 # 5分钟监控面板"
    echo ""
}

if [ "$HELP" = true ]; then
    show_help
    exit 0
fi

# 工具函数
print_header() {
    echo ""
    echo -e "${PURPLE}==================== $1 ====================${NC}"
    echo ""
}

print_success() {
    echo -e "${SUCCESS} ${GREEN}$1${NC}"
}

print_error() {
    echo -e "${ERROR} ${RED}$1${NC}"
}

print_warning() {
    echo -e "${WARNING} ${YELLOW}$1${NC}"
}

print_info() {
    echo -e "${INFO} ${BLUE}$1${NC}"
}

print_alert() {
    echo -e "${ALERT} ${RED}告警: $1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 获取时间戳
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# 格式化字节
format_bytes() {
    local bytes=$1
    local units=("B" "KB" "MB" "GB" "TB")
    local unit=0
    
    while [ $bytes -gt 1024 ] && [ $unit -lt $((${#units[@]} - 1)) ]; do
        bytes=$((bytes / 1024))
        unit=$((unit + 1))
    done
    
    echo "${bytes}${units[$unit]}"
}

# 发送告警
send_alert() {
    local message="$1"
    local severity="$2"
    local timestamp=$(get_timestamp)
    
    echo "[$timestamp] $severity: $message" >> monitor-alerts.log
    
    if [ "$ENABLE_ALERTS" = true ]; then
        print_alert "$message"
        # 这里可以集成邮件、Slack、钉钉等通知
    fi
}

# 系统资源监控
monitor_system_resources() {
    local cpu_usage=0
    local memory_usage=0
    local disk_usage=0
    
    # CPU使用率
    if command_exists top; then
        # 获取CPU使用率（不同系统命令可能不同）
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            cpu_usage=$(top -l 1 -s 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' 2>/dev/null || echo "0")
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//' 2>/dev/null || echo "0")
        else
            # Windows/其他
            cpu_usage=$(wmic cpu get loadpercentage /value 2>/dev/null | grep "LoadPercentage" | cut -d'=' -f2 2>/dev/null || echo "0")
        fi
    fi
    
    # 内存使用率
    if [ -f "/proc/meminfo" ]; then
        # Linux
        local total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        local available_mem=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        memory_usage=$(( (total_mem - available_mem) * 100 / total_mem ))
    elif command_exists free; then
        # 使用free命令
        memory_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        memory_usage=$(vm_stat | awk '/Pages active/ {active=$3} /Pages inactive/ {inactive=$3} /Pages speculative/ {spec=$3} /Pages wired/ {wired=$3} /Pages free/ {free=$3} END {gsub(/\./, "", active); gsub(/\./, "", inactive); gsub(/\./, "", spec); gsub(/\./, "", wired); gsub(/\./, "", free); total=active+inactive+spec+wired+free; used=active+inactive+spec+wired; print int(used/total*100)}')
    fi
    
    # 磁盘使用率
    if command_exists df; then
        disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
    fi
    
    # 显示系统资源信息
    echo -e "${SYSTEM} $(get_timestamp) - 系统资源:"
    echo "  CPU使用率: ${cpu_usage}%"
    echo "  内存使用率: ${memory_usage}%"
    echo "  磁盘使用率: ${disk_usage}%"
    
    # 检查告警阈值
    if [ "$cpu_usage" -gt "$CPU_THRESHOLD" ]; then
        send_alert "CPU使用率过高: ${cpu_usage}%" "HIGH"
    fi
    
    if [ "$memory_usage" -gt "$MEMORY_THRESHOLD" ]; then
        send_alert "内存使用率过高: ${memory_usage}%" "HIGH"
    fi
    
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        send_alert "磁盘使用率过高: ${disk_usage}%" "HIGH"
    fi
    
    # 负载平均值（Linux/macOS）
    if [ -f "/proc/loadavg" ]; then
        local load_avg=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
        echo "  负载平均值: $load_avg"
    elif command_exists uptime; then
        local load_avg=$(uptime | awk -F'load average:' '{print $2}')
        echo "  负载平均值:$load_avg"
    fi
    
    # 网络连接数
    if command_exists ss; then
        local connections=$(ss -tuln | wc -l)
        echo "  网络连接数: $connections"
    elif command_exists netstat; then
        local connections=$(netstat -tuln 2>/dev/null | wc -l)
        echo "  网络连接数: $connections"
    fi
}

# 服务健康检查
monitor_services() {
    echo -e "${SERVICE} $(get_timestamp) - 服务健康检查:"
    
    local services_healthy=true
    
    # 检查后端服务
    print_info "检查后端服务..."
    if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
        local backend_response_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:8000/health 2>/dev/null)
        local backend_ms=$(echo "$backend_response_time * 1000" | bc -l 2>/dev/null | cut -d. -f1)
        echo "  后端服务: ${SUCCESS} 响应时间: ${backend_ms}ms"
        
        if [ "$backend_ms" -gt "$RESPONSE_TIME_THRESHOLD" ]; then
            send_alert "后端服务响应时间过长: ${backend_ms}ms" "MEDIUM"
        fi
    else
        echo "  后端服务: ${ERROR} 不可访问"
        send_alert "后端服务不可访问" "HIGH"
        services_healthy=false
    fi
    
    # 检查前端服务
    print_info "检查前端服务..."
    if curl -s -f http://localhost:3000 >/dev/null 2>&1; then
        local frontend_response_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:3000 2>/dev/null)
        local frontend_ms=$(echo "$frontend_response_time * 1000" | bc -l 2>/dev/null | cut -d. -f1)
        echo "  前端服务: ${SUCCESS} 响应时间: ${frontend_ms}ms"
        
        if [ "$frontend_ms" -gt "$RESPONSE_TIME_THRESHOLD" ]; then
            send_alert "前端服务响应时间过长: ${frontend_ms}ms" "MEDIUM"
        fi
    else
        echo "  前端服务: ${WARNING} 不可访问（可能未启动）"
    fi
    
    # 检查数据库连接
    print_info "检查数据库连接..."
    cd web_interface/backend
    
    if [ -d "venv" ]; then
        source venv/bin/activate || . venv/Scripts/activate
        
        # 创建数据库连接测试脚本
        cat > db_health_check.py << 'EOF'
import asyncio
import asyncpg
from app.core.config import get_settings

async def check_db_health():
    try:
        settings = get_settings()
        conn = await asyncpg.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        
        # 简单查询测试
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        return result == 1
        
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(check_db_health())
    exit(0 if result else 1)
EOF
        
        if python db_health_check.py >/dev/null 2>&1; then
            echo "  数据库: ${SUCCESS} 连接正常"
        else
            echo "  数据库: ${ERROR} 连接失败"
            send_alert "数据库连接失败" "HIGH"
            services_healthy=false
        fi
        
        rm db_health_check.py
    else
        echo "  数据库: ${WARNING} 无法检查（虚拟环境不存在）"
    fi
    
    cd ../..
    
    # 检查Redis（如果配置了）
    if command_exists redis-cli; then
        if redis-cli ping >/dev/null 2>&1; then
            echo "  Redis: ${SUCCESS} 连接正常"
        else
            echo "  Redis: ${WARNING} 连接失败"
        fi
    fi
    
    if [ "$services_healthy" = true ]; then
        print_success "所有服务运行正常"
    else
        print_error "部分服务存在问题"
    fi
}

# 性能监控
monitor_performance() {
    echo -e "${CHART} $(get_timestamp) - 性能监控:"
    
    # API性能测试
    print_info "API性能测试..."
    
    local api_endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/api/v1/strategies"
        "http://localhost:8000/docs"
    )
    
    for endpoint in "${api_endpoints[@]}"; do
        if curl -s -f "$endpoint" >/dev/null 2>&1; then
            local response_time=$(curl -s -w "%{time_total},%{http_code},%{size_download}" -o /dev/null "$endpoint" 2>/dev/null)
            local time_ms=$(echo "$response_time" | cut -d',' -f1 | awk '{print int($1*1000)}')
            local http_code=$(echo "$response_time" | cut -d',' -f2)
            local size_bytes=$(echo "$response_time" | cut -d',' -f3)
            
            echo "  $(basename "$endpoint"): ${time_ms}ms (${http_code}) $(format_bytes $size_bytes)"
            
            if [ "$time_ms" -gt "$RESPONSE_TIME_THRESHOLD" ]; then
                send_alert "API响应时间过长: $endpoint ${time_ms}ms" "MEDIUM"
            fi
        fi
    done
    
    # 进程监控
    print_info "进程监控..."
    
    # 查找Python进程（后端）
    local python_processes=$(pgrep -f "python.*main" 2>/dev/null || true)
    if [ -n "$python_processes" ]; then
        echo "$python_processes" | while read pid; do
            if [ -n "$pid" ]; then
                local process_info
                if command_exists ps; then
                    process_info=$(ps -p "$pid" -o pid,pcpu,pmem,etime,cmd --no-headers 2>/dev/null || true)
                    if [ -n "$process_info" ]; then
                        echo "  Python进程: $process_info"
                    fi
                fi
            fi
        done
    else
        echo "  Python进程: 未运行"
    fi
    
    # 查找Node.js进程（前端）
    local node_processes=$(pgrep -f "node.*vite\|node.*dev" 2>/dev/null || true)
    if [ -n "$node_processes" ]; then
        echo "$node_processes" | while read pid; do
            if [ -n "$pid" ]; then
                local process_info
                if command_exists ps; then
                    process_info=$(ps -p "$pid" -o pid,pcpu,pmem,etime,cmd --no-headers 2>/dev/null || true)
                    if [ -n "$process_info" ]; then
                        echo "  Node.js进程: $process_info"
                    fi
                fi
            fi
        done
    else
        echo "  Node.js进程: 未运行"
    fi
}

# 日志监控
monitor_logs() {
    echo -e "${LOG} $(get_timestamp) - 日志监控:"
    
    local log_files=(
        "web_interface/backend/logs/app.log"
        "web_interface/backend/logs/error.log"
        "web_interface/frontend/logs/vite.log"
        "monitor-alerts.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            local file_size
            if command_exists stat; then
                file_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null)
                echo "  $(basename "$log_file"): $(format_bytes $file_size)"
                
                # 检查最近的错误
                local recent_errors=$(tail -100 "$log_file" | grep -i -E "(error|exception|failed|critical)" | wc -l)
                if [ "$recent_errors" -gt 0 ]; then
                    echo "    最近错误数: $recent_errors"
                    if [ "$recent_errors" -gt 10 ]; then
                        send_alert "日志中发现大量错误: $log_file ($recent_errors 个)" "MEDIUM"
                    fi
                fi
            fi
        else
            echo "  $(basename "$log_file"): 不存在"
        fi
    done
    
    # 检查磁盘空间（日志可能占用大量空间）
    local log_disk_usage
    if command_exists du; then
        log_disk_usage=$(du -sh web_interface/*/logs 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "0")
        if [ -n "$log_disk_usage" ] && [ "$log_disk_usage" != "0" ]; then
            echo "  日志总大小: ${log_disk_usage}"
        fi
    fi
}

# 监控面板
show_dashboard() {
    clear
    
    while true; do
        echo -e "${MONITOR} ${CYAN}TradeMaster 监控面板${NC}"
        echo "==============================================="
        echo "时间: $(get_timestamp)"
        echo "监控间隔: ${MONITOR_INTERVAL}秒"
        echo "==============================================="
        
        if [ "$MONITOR_SYSTEM" = true ]; then
            monitor_system_resources
            echo ""
        fi
        
        if [ "$MONITOR_SERVICES" = true ]; then
            monitor_services
            echo ""
        fi
        
        if [ "$MONITOR_PERFORMANCE" = true ]; then
            monitor_performance
            echo ""
        fi
        
        if [ "$MONITOR_LOGS" = true ]; then
            monitor_logs
            echo ""
        fi
        
        echo "==============================================="
        echo "按 Ctrl+C 停止监控"
        echo ""
        
        sleep "$MONITOR_INTERVAL"
        clear
    done
}

# 生成监控报告
generate_monitor_report() {
    local report_file="monitor-report-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "TradeMaster Web Interface 监控报告"
        echo "=================================="
        echo "生成时间: $(get_timestamp)"
        echo ""
        
        echo "系统资源状态:"
        monitor_system_resources
        echo ""
        
        echo "服务健康状态:"
        monitor_services
        echo ""
        
        echo "性能状态:"
        monitor_performance
        echo ""
        
        echo "日志状态:"
        monitor_logs
        echo ""
        
        if [ -f "monitor-alerts.log" ]; then
            echo "最近告警:"
            tail -20 monitor-alerts.log
        fi
        
    } > "$report_file"
    
    print_success "监控报告已生成: $report_file"
}

# 主函数
main() {
    print_header "${MONITOR} TradeMaster Web Interface 系统监控"
    
    echo -e "${HEART} ${CYAN}开始监控...${NC}"
    echo ""
    
    if [ "$SHOW_DASHBOARD" = true ]; then
        # 显示监控面板
        trap 'echo -e "\n${INFO} 监控已停止"; generate_monitor_report; exit 0' INT
        show_dashboard
    else
        # 运行指定时间的监控
        local start_time=$(date +%s)
        local end_time=$((start_time + MONITOR_DURATION))
        
        echo "监控将运行 $MONITOR_DURATION 秒，间隔 $MONITOR_INTERVAL 秒"
        echo ""
        
        while [ $(date +%s) -lt $end_time ]; do
            if [ "$MONITOR_SYSTEM" = true ]; then
                monitor_system_resources
                echo ""
            fi
            
            if [ "$MONITOR_SERVICES" = true ]; then
                monitor_services
                echo ""
            fi
            
            if [ "$MONITOR_PERFORMANCE" = true ]; then
                monitor_performance
                echo ""
            fi
            
            if [ "$MONITOR_LOGS" = true ]; then
                monitor_logs
                echo ""
            fi
            
            echo "----------------------------------------"
            sleep "$MONITOR_INTERVAL"
        done
        
        generate_monitor_report
    fi
    
    print_header "监控完成"
    print_success "监控任务已完成！📊"
    
    if [ -f "monitor-alerts.log" ]; then
        local alert_count=$(wc -l < monitor-alerts.log)
        if [ "$alert_count" -gt 0 ]; then
            print_warning "监控期间产生了 $alert_count 条告警，请查看 monitor-alerts.log"
        fi
    fi
}

# 错误处理
trap 'print_error "监控脚本执行失败"; exit 1' ERR

# 运行主函数
main "$@"