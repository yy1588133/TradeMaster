#!/bin/bash

# ==================== TradeMaster Backend 健康检查脚本 ====================
# 该脚本用于Docker容器的健康检查，确保服务正常运行

set -e

# 配置
HEALTH_CHECK_URL="http://localhost:8000/api/v1/health"
TIMEOUT=10
MAX_RETRIES=3

# 日志函数
log_info() {
    echo "[HEALTH-CHECK] $(date '+%Y-%m-%d %H:%M:%S') - INFO: $1"
}

log_error() {
    echo "[HEALTH-CHECK] $(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" >&2
}

# 检查HTTP端点
check_http_endpoint() {
    log_info "检查HTTP端点: $HEALTH_CHECK_URL"
    
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -f -s --max-time $TIMEOUT "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log_info "HTTP端点检查通过 (尝试 $i/$MAX_RETRIES)"
            return 0
        else
            log_error "HTTP端点检查失败 (尝试 $i/$MAX_RETRIES)"
            if [ $i -lt $MAX_RETRIES ]; then
                sleep 2
            fi
        fi
    done
    
    return 1
}

# 检查数据库连接
check_database_connection() {
    log_info "检查数据库连接"
    
    python3 -c "
import asyncio
import asyncpg
import os
import sys

async def check_db():
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print('DATABASE_URL环境变量未设置')
            return False
            
        conn = await asyncpg.connect(database_url)
        await conn.fetchval('SELECT 1')
        await conn.close()
        return True
    except Exception as e:
        print(f'数据库连接检查失败: {e}')
        return False

if not asyncio.run(check_db()):
    sys.exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "数据库连接检查通过"
        return 0
    else
        log_error "数据库连接检查失败"
        return 1
    fi
}

# 检查Redis连接
check_redis_connection() {
    log_info "检查Redis连接"
    
    python3 -c "
import redis
import os
import sys
from urllib.parse import urlparse

try:
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print('REDIS_URL环境变量未设置')
        sys.exit(1)
        
    parsed = urlparse(redis_url)
    r = redis.Redis(
        host=parsed.hostname,
        port=parsed.port,
        db=int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0,
        socket_timeout=5,
        decode_responses=True
    )
    r.ping()
except Exception as e:
    print(f'Redis连接检查失败: {e}')
    sys.exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "Redis连接检查通过"
        return 0
    else
        log_error "Redis连接检查失败"
        return 1
    fi
}

# 检查进程状态
check_process_status() {
    log_info "检查进程状态"
    
    # 检查uvicorn进程是否运行
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        log_info "Uvicorn进程运行正常"
        return 0
    else
        log_error "未找到Uvicorn进程"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间"
    
    # 检查根目录可用空间（至少100MB）
    available_kb=$(df / | tail -1 | awk '{print $4}')
    available_mb=$((available_kb / 1024))
    
    if [ $available_mb -gt 100 ]; then
        log_info "磁盘空间充足 (${available_mb}MB可用)"
        return 0
    else
        log_error "磁盘空间不足 (${available_mb}MB可用，需要至少100MB)"
        return 1
    fi
}

# 检查内存使用
check_memory_usage() {
    log_info "检查内存使用"
    
    # 获取内存使用情况
    if [ -f /proc/meminfo ]; then
        mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        mem_available=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        
        if [ -n "$mem_total" ] && [ -n "$mem_available" ]; then
            mem_used_percent=$(( (mem_total - mem_available) * 100 / mem_total ))
            
            if [ $mem_used_percent -lt 90 ]; then
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
    log_info "开始健康检查..."
    
    local checks_passed=0
    local total_checks=6
    
    # 必需的检查
    if check_http_endpoint; then
        ((checks_passed++))
    fi
    
    if check_process_status; then
        ((checks_passed++))
    fi
    
    if check_database_connection; then
        ((checks_passed++))
    fi
    
    if check_redis_connection; then
        ((checks_passed++))
    fi
    
    # 可选的检查（不影响最终结果）
    if check_disk_space; then
        ((checks_passed++))
    fi
    
    if check_memory_usage; then
        ((checks_passed++))
    fi
    
    log_info "健康检查完成：$checks_passed/$total_checks 项检查通过"
    
    # 至少需要前4项检查通过
    if [ $checks_passed -ge 4 ]; then
        log_info "健康检查通过"
        return 0
    else
        log_error "健康检查失败"
        return 1
    fi
}

# 快速健康检查（仅检查HTTP端点）
quick_health_check() {
    log_info "执行快速健康检查..."
    
    if check_http_endpoint; then
        log_info "快速健康检查通过"
        return 0
    else
        log_error "快速健康检查失败"
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