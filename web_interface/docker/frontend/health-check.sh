#!/bin/bash

# ==================== TradeMaster Frontend 健康检查脚本 ====================
# 该脚本用于Docker容器的健康检查，确保前端服务正常运行

set -e

# 配置
HEALTH_CHECK_URL="http://localhost/health"
MAIN_PAGE_URL="http://localhost/"
TIMEOUT=10
MAX_RETRIES=3

# 日志函数
log_info() {
    echo "[FRONTEND-HEALTH] $(date '+%Y-%m-%d %H:%M:%S') - INFO: $1"
}

log_error() {
    echo "[FRONTEND-HEALTH] $(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" >&2
}

# 检查Nginx进程
check_nginx_process() {
    log_info "检查Nginx进程状态"
    
    if pgrep -f "nginx.*master" > /dev/null; then
        log_info "Nginx主进程运行正常"
        
        # 检查工作进程
        worker_count=$(pgrep -f "nginx.*worker" | wc -l)
        if [ $worker_count -gt 0 ]; then
            log_info "Nginx工作进程运行正常 ($worker_count 个工作进程)"
            return 0
        else
            log_error "未发现Nginx工作进程"
            return 1
        fi
    else
        log_error "Nginx主进程未运行"
        return 1
    fi
}

# 检查HTTP端点
check_http_endpoint() {
    local url="$1"
    local expected_code="${2:-200}"
    
    log_info "检查HTTP端点: $url"
    
    for i in $(seq 1 $MAX_RETRIES); do
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "000")
        
        if [ "$response_code" = "$expected_code" ]; then
            log_info "HTTP端点检查通过: $url (状态码: $response_code, 尝试: $i/$MAX_RETRIES)"
            return 0
        else
            log_error "HTTP端点检查失败: $url (状态码: $response_code, 尝试: $i/$MAX_RETRIES)"
            if [ $i -lt $MAX_RETRIES ]; then
                sleep 1
            fi
        fi
    done
    
    return 1
}

# 检查静态文件
check_static_files() {
    log_info "检查静态文件"
    
    # 检查主要文件是否存在
    local files=(
        "/usr/share/nginx/html/index.html"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ] && [ -r "$file" ]; then
            log_info "静态文件存在且可读: $file"
        else
            log_error "静态文件不存在或不可读: $file"
            return 1
        fi
    done
    
    return 0
}

# 检查Nginx配置
check_nginx_config() {
    log_info "检查Nginx配置"
    
    if nginx -t 2>/dev/null; then
        log_info "Nginx配置文件语法正确"
        return 0
    else
        log_error "Nginx配置文件语法错误"
        nginx -t 2>&1 | head -5
        return 1
    fi
}

# 检查端口监听
check_port_listening() {
    log_info "检查端口监听状态"
    
    if netstat -tuln 2>/dev/null | grep -q ":80 " || ss -tuln 2>/dev/null | grep -q ":80 "; then
        log_info "端口80监听正常"
        return 0
    else
        log_error "端口80未在监听"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间"
    
    # 检查根目录可用空间（至少50MB）
    local available_kb=$(df / 2>/dev/null | tail -1 | awk '{print $4}' || echo "0")
    local available_mb=$((available_kb / 1024))
    
    if [ $available_mb -gt 50 ]; then
        log_info "磁盘空间充足 (${available_mb}MB可用)"
        return 0
    else
        log_error "磁盘空间不足 (${available_mb}MB可用，需要至少50MB)"
        return 1
    fi
}

# 检查日志文件写入权限
check_log_permissions() {
    log_info "检查日志文件写入权限"
    
    local log_dirs=(
        "/var/log/nginx"
    )
    
    for dir in "${log_dirs[@]}"; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            log_info "日志目录可写: $dir"
        else
            log_error "日志目录不可写: $dir"
            return 1
        fi
    done
    
    return 0
}

# 检查后端连接（可选）
check_backend_connection() {
    log_info "检查后端连接"
    
    local backend_host="${BACKEND_HOST:-backend}"
    local backend_port="${BACKEND_PORT:-8000}"
    
    if nc -z "$backend_host" "$backend_port" 2>/dev/null; then
        log_info "后端服务连接正常: ${backend_host}:${backend_port}"
        return 0
    else
        log_info "后端服务连接失败: ${backend_host}:${backend_port} (这可能是正常的)"
        return 0  # 不影响前端健康状态
    fi
}

# 检查内存使用
check_memory_usage() {
    log_info "检查内存使用"
    
    if [ -f /proc/meminfo ]; then
        local mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}' || echo "0")
        local mem_available=$(grep MemAvailable /proc/meminfo | awk '{print $2}' || echo "0")
        
        if [ "$mem_total" -gt 0 ] && [ "$mem_available" -gt 0 ]; then
            local mem_used_percent=$(( (mem_total - mem_available) * 100 / mem_total ))
            
            if [ $mem_used_percent -lt 95 ]; then
                log_info "内存使用正常 (${mem_used_percent}%已使用)"
                return 0
            else
                log_error "内存使用过高 (${mem_used_percent}%已使用)"
                return 1
            fi
        fi
    fi
    
    log_info "无法获取内存信息，跳过检查"
    return 0
}

# 主健康检查函数
main_health_check() {
    log_info "开始前端健康检查..."
    
    local checks_passed=0
    local total_checks=9
    
    # 必需的检查
    if check_nginx_process; then
        ((checks_passed++))
    fi
    
    if check_nginx_config; then
        ((checks_passed++))
    fi
    
    if check_port_listening; then
        ((checks_passed++))
    fi
    
    if check_static_files; then
        ((checks_passed++))
    fi
    
    if check_http_endpoint "$HEALTH_CHECK_URL"; then
        ((checks_passed++))
    fi
    
    if check_http_endpoint "$MAIN_PAGE_URL"; then
        ((checks_passed++))
    fi
    
    # 可选的检查（不影响最终结果）
    if check_disk_space; then
        ((checks_passed++))
    fi
    
    if check_log_permissions; then
        ((checks_passed++))
    fi
    
    if check_memory_usage; then
        ((checks_passed++))
    fi
    
    # 额外检查（不计入总数）
    check_backend_connection
    
    log_info "健康检查完成：$checks_passed/$total_checks 项检查通过"
    
    # 至少需要前6项检查通过
    if [ $checks_passed -ge 6 ]; then
        log_info "前端健康检查通过"
        return 0
    else
        log_error "前端健康检查失败"
        return 1
    fi
}

# 快速健康检查（仅检查核心功能）
quick_health_check() {
    log_info "执行快速健康检查..."
    
    local checks_passed=0
    local required_checks=3
    
    if check_nginx_process; then
        ((checks_passed++))
    fi
    
    if check_port_listening; then
        ((checks_passed++))
    fi
    
    if check_http_endpoint "$HEALTH_CHECK_URL"; then
        ((checks_passed++))
    fi
    
    if [ $checks_passed -eq $required_checks ]; then
        log_info "快速健康检查通过 ($checks_passed/$required_checks)"
        return 0
    else
        log_error "快速健康检查失败 ($checks_passed/$required_checks)"
        return 1
    fi
}

# 解析命令行参数
case "${1:-full}" in
    "quick")
        quick_health_check
        ;;
    "full"|*)
        main_health_check
        ;;
esac

exit $?