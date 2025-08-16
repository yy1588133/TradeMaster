#!/bin/bash
# ==================== TradeMaster Web Interface 性能检查脚本 ====================
# 
# 功能:
# - 后端性能分析
# - 前端构建分析 
# - Docker镜像大小检查
# - 数据库性能检查
# - 内存和CPU使用分析
#
# 使用方法:
#   ./scripts/performance-check.sh [options]
#
# 选项:
#   --backend       检查后端性能
#   --frontend      检查前端性能
#   --docker        检查Docker镜像
#   --database      检查数据库性能
#   --load-test     运行负载测试
#   --report        生成详细报告
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
ROCKET="🚀"
PERFORMANCE="⚡"
BACKEND="🐍"
FRONTEND="🌐"
DOCKER="🐳"
DATABASE="🗄️"
REPORT="📊"

# 默认配置
CHECK_BACKEND=false
CHECK_FRONTEND=false
CHECK_DOCKER=false
CHECK_DATABASE=false
LOAD_TEST=false
GENERATE_REPORT=false
HELP=false

# 如果没有指定检查类型，则检查所有
CHECK_ALL=true

# 参数解析
for arg in "$@"; do
    case $arg in
        --backend)
            CHECK_BACKEND=true
            CHECK_ALL=false
            shift
            ;;
        --frontend)
            CHECK_FRONTEND=true
            CHECK_ALL=false
            shift
            ;;
        --docker)
            CHECK_DOCKER=true
            CHECK_ALL=false
            shift
            ;;
        --database)
            CHECK_DATABASE=true
            CHECK_ALL=false
            shift
            ;;
        --load-test)
            LOAD_TEST=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --help)
            HELP=true
            shift
            ;;
        *)
            echo -e "${ERROR} ${RED}未知参数: $arg${NC}"
            exit 1
            ;;
    esac
done

# 如果没有指定特定检查，运行基本检查
if [ "$CHECK_ALL" = true ]; then
    CHECK_BACKEND=true
    CHECK_FRONTEND=true
    CHECK_DOCKER=true
fi

# 帮助信息
show_help() {
    echo -e "${BLUE}TradeMaster Web Interface 性能检查脚本${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/performance-check.sh [options]"
    echo ""
    echo "检查选项:"
    echo "  --backend       检查后端性能"
    echo "  --frontend      检查前端性能"
    echo "  --docker        检查Docker镜像"
    echo "  --database      检查数据库性能"
    echo ""
    echo "测试选项:"
    echo "  --load-test     运行负载测试"
    echo "  --report        生成详细报告"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/performance-check.sh                    # 基本性能检查"
    echo "  ./scripts/performance-check.sh --backend --report # 后端性能详细报告"
    echo "  ./scripts/performance-check.sh --load-test        # 运行负载测试"
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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 格式化字节大小
format_bytes() {
    local bytes=$1
    local kb=$((bytes / 1024))
    local mb=$((kb / 1024))
    local gb=$((mb / 1024))
    
    if [ $gb -gt 0 ]; then
        echo "${gb}GB"
    elif [ $mb -gt 0 ]; then
        echo "${mb}MB"
    elif [ $kb -gt 0 ]; then
        echo "${kb}KB"
    else
        echo "${bytes}B"
    fi
}

# 检查系统资源
check_system_resources() {
    print_header "系统资源检查"
    
    # CPU信息
    if command_exists nproc; then
        local cpu_cores=$(nproc)
        print_info "CPU核心数: $cpu_cores"
    fi
    
    # 内存信息
    if [ -f "/proc/meminfo" ]; then
        local total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        local available_mem=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        print_info "总内存: $(format_bytes $((total_mem * 1024)))"
        print_info "可用内存: $(format_bytes $((available_mem * 1024)))"
    elif command_exists free; then
        print_info "内存信息:"
        free -h
    fi
    
    # 磁盘空间
    print_info "磁盘空间:"
    df -h . | tail -1 | awk '{print "  使用: "$3" / "$2" ("$5")"}'
}

# 后端性能检查
check_backend_performance() {
    print_header "${BACKEND} 后端性能检查"
    
    cd web_interface/backend
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        print_error "虚拟环境不存在，请先运行设置脚本"
        cd ../..
        return 1
    fi
    
    source venv/bin/activate || . venv/Scripts/activate
    
    # Python性能分析
    print_info "运行Python性能分析..."
    if python -c "import cProfile" 2>/dev/null; then
        # 创建性能测试脚本
        cat > performance_test.py << 'EOF'
import asyncio
import time
from app.main import app
from fastapi.testclient import TestClient

def test_app_performance():
    client = TestClient(app)
    
    # 测试基本端点
    start_time = time.time()
    response = client.get("/health")
    health_time = time.time() - start_time
    
    print(f"Health check: {health_time:.3f}s")
    
    # 测试API端点
    start_time = time.time()
    response = client.get("/api/v1/strategies")
    api_time = time.time() - start_time
    
    print(f"API response: {api_time:.3f}s")

if __name__ == "__main__":
    test_app_performance()
EOF
        
        python -m cProfile -o backend_profile.stats performance_test.py
        rm performance_test.py
        
        print_success "Python性能分析完成: backend_profile.stats"
    else
        print_warning "cProfile不可用，跳过性能分析"
    fi
    
    # 检查依赖包大小
    print_info "检查Python依赖包大小..."
    if command_exists pip; then
        pip list --format=freeze | wc -l | xargs echo "已安装包数量:"
        
        # 显示最大的包
        print_info "最大的依赖包:"
        pip show $(pip list --format=freeze | cut -d'=' -f1) 2>/dev/null | \
        grep -E "^(Name|Location)" | \
        paste - - | \
        head -5 || true
    fi
    
    # 检查导入时间
    print_info "检查模块导入时间..."
    python -X importtime -c "from app.main import app" 2>&1 | \
    grep "import time" | \
    sort -k2 -nr | \
    head -5 || true
    
    cd ../..
}

# 前端性能检查
check_frontend_performance() {
    print_header "${FRONTEND} 前端性能检查"
    
    cd web_interface/frontend
    
    # 检查依赖
    if [ ! -d "node_modules" ]; then
        print_error "前端依赖未安装，请先运行: pnpm install"
        cd ../..
        return 1
    fi
    
    # 构建分析
    print_info "分析构建结果..."
    if [ -f "dist/stats.html" ]; then
        print_success "构建分析报告已存在: dist/stats.html"
    else
        print_info "生成构建分析..."
        pnpm build:analyze
        print_success "构建分析完成: dist/stats.html"
    fi
    
    # Bundle大小分析
    if [ -d "dist/assets" ]; then
        print_info "Bundle大小分析:"
        
        find dist/assets -name "*.js" | while read file; do
            if [ -f "$file" ]; then
                local file_size
                if command_exists stat; then
                    # Linux/macOS
                    file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
                else
                    file_size=$(wc -c < "$file")
                fi
                
                local file_name=$(basename "$file")
                local size_kb=$((file_size / 1024))
                
                if [ $size_kb -gt 500 ]; then
                    print_warning "  $file_name: ${size_kb}KB (过大)"
                elif [ $size_kb -gt 200 ]; then
                    print_info "  $file_name: ${size_kb}KB"
                else
                    echo "  $file_name: ${size_kb}KB"
                fi
            fi
        done
        
        # 总体大小
        local total_size
        if command_exists du; then
            total_size=$(du -sh dist | cut -f1)
            print_info "总构建大小: $total_size"
        fi
    fi
    
    # 依赖分析
    print_info "分析依赖包大小..."
    if command_exists pnpm && pnpm list --depth=0 >/dev/null 2>&1; then
        local dep_count=$(pnpm list --depth=0 --json | jq '.[] | .dependencies | length' 2>/dev/null || echo "unknown")
        print_info "依赖包数量: $dep_count"
        
        # node_modules大小
        if [ -d "node_modules" ]; then
            local node_modules_size
            if command_exists du; then
                node_modules_size=$(du -sh node_modules 2>/dev/null | cut -f1)
                print_info "node_modules大小: $node_modules_size"
            fi
        fi
    fi
    
    # 检查TypeScript编译时间
    print_info "检查TypeScript编译性能..."
    local start_time=$(date +%s.%N)
    pnpm type-check >/dev/null 2>&1 || true
    local end_time=$(date +%s.%N)
    local compile_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")
    print_info "TypeScript编译时间: ${compile_time}秒"
    
    cd ../..
}

# Docker性能检查
check_docker_performance() {
    print_header "${DOCKER} Docker镜像性能检查"
    
    if ! command_exists docker; then
        print_warning "Docker未安装，跳过Docker性能检查"
        return
    fi
    
    cd web_interface
    
    # 检查镜像大小
    print_info "检查Docker镜像大小..."
    
    local images=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep trademaster || echo "")
    
    if [ -n "$images" ]; then
        echo "$images" | while read line; do
            if [ "$line" != "" ] && [[ ! "$line" =~ ^REPOSITORY ]]; then
                local image=$(echo "$line" | awk '{print $1}')
                local size=$(echo "$line" | awk '{print $2}')
                
                # 检查大小是否合理 (假设合理大小 < 2GB)
                local size_num=$(echo "$size" | sed 's/[^0-9.]//g')
                local size_unit=$(echo "$size" | sed 's/[0-9.]//g')
                
                if [[ "$size_unit" == "GB" ]] && (( $(echo "$size_num > 2" | bc -l 2>/dev/null || echo 0) )); then
                    print_warning "  $image: $size (较大)"
                elif [[ "$size_unit" == "MB" ]] && (( $(echo "$size_num > 1000" | bc -l 2>/dev/null || echo 0) )); then
                    print_warning "  $image: $size (较大)"
                else
                    print_info "  $image: $size"
                fi
            fi
        done
    else
        print_info "未找到TradeMaster相关镜像"
    fi
    
    # 镜像层分析
    print_info "分析镜像层..."
    local backend_image=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "backend" | head -1)
    local frontend_image=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "frontend" | head -1)
    
    if [ -n "$backend_image" ]; then
        print_info "后端镜像层数:"
        docker history --no-trunc "$backend_image" | wc -l | xargs echo "  层数:"
    fi
    
    if [ -n "$frontend_image" ]; then
        print_info "前端镜像层数:"
        docker history --no-trunc "$frontend_image" | wc -l | xargs echo "  层数:"
    fi
    
    cd ..
}

# 数据库性能检查
check_database_performance() {
    print_header "${DATABASE} 数据库性能检查"
    
    cd web_interface/backend
    
    # 检查数据库连接
    source venv/bin/activate || . venv/Scripts/activate
    
    # 创建数据库性能检查脚本
    cat > db_performance_test.py << 'EOF'
import asyncio
import time
import asyncpg
from app.core.config import get_settings

async def check_db_performance():
    settings = get_settings()
    
    try:
        # 连接测试
        start_time = time.time()
        conn = await asyncpg.connect(
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        connect_time = time.time() - start_time
        print(f"数据库连接时间: {connect_time:.3f}秒")
        
        # 简单查询测试
        start_time = time.time()
        result = await conn.fetchval("SELECT 1")
        query_time = time.time() - start_time
        print(f"简单查询时间: {query_time:.3f}秒")
        
        # 数据库信息
        version = await conn.fetchval("SELECT version()")
        print(f"数据库版本: {version.split()[1] if version else 'Unknown'}")
        
        # 连接数检查
        connections = await conn.fetchval("SELECT count(*) FROM pg_stat_activity")
        print(f"当前连接数: {connections}")
        
        await conn.close()
        
        return True
        
    except Exception as e:
        print(f"数据库性能检查失败: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(check_db_performance())
    if not result:
        exit(1)
EOF
    
    if python db_performance_test.py; then
        print_success "数据库性能检查通过"
    else
        print_warning "数据库性能检查失败，请检查数据库连接"
    fi
    
    rm db_performance_test.py
    
    cd ../..
}

# 负载测试
run_load_test() {
    print_header "${PERFORMANCE} 负载测试"
    
    if ! command_exists curl; then
        print_warning "curl未安装，跳过负载测试"
        return
    fi
    
    print_info "运行基本负载测试..."
    
    # 检查服务是否运行
    if ! curl -s http://localhost:8000/health >/dev/null; then
        print_warning "后端服务未运行，请先启动服务"
        return
    fi
    
    # 简单的并发测试
    print_info "测试并发请求..."
    
    local start_time=$(date +%s.%N)
    
    # 运行10个并发请求
    for i in {1..10}; do
        curl -s http://localhost:8000/health >/dev/null &
    done
    wait
    
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")
    
    print_info "10个并发请求完成时间: ${total_time}秒"
    
    # 如果有wrk工具，运行更详细的测试
    if command_exists wrk; then
        print_info "运行详细负载测试 (30秒)..."
        wrk -t4 -c10 -d30s http://localhost:8000/health
    else
        print_info "安装wrk工具可以进行更详细的负载测试"
    fi
}

# 生成性能报告
generate_performance_report() {
    print_header "${REPORT} 生成性能报告"
    
    local report_dir="performance-reports"
    local report_file="$report_dir/performance-report-$(date +%Y%m%d_%H%M%S).md"
    
    mkdir -p $report_dir
    
    cat > $report_file << EOF
# TradeMaster Web Interface 性能报告

## 报告信息

- 生成时间: $(date)
- 系统信息: $(uname -s) $(uname -r)
- 主机名: $(hostname)

## 系统资源

EOF
    
    # 添加系统资源信息
    if command_exists nproc; then
        echo "- CPU核心数: $(nproc)" >> $report_file
    fi
    
    if [ -f "/proc/meminfo" ]; then
        local total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        echo "- 总内存: $(format_bytes $((total_mem * 1024)))" >> $report_file
    fi
    
    df -h . | tail -1 | awk '{print "- 磁盘使用: "$3" / "$2" ("$5")"}' >> $report_file
    
    cat >> $report_file << EOF

## 构建大小分析

### 前端构建
EOF
    
    # 前端构建大小
    if [ -d "web_interface/frontend/dist" ]; then
        local frontend_size
        if command_exists du; then
            frontend_size=$(du -sh web_interface/frontend/dist 2>/dev/null | cut -f1 || echo "unknown")
            echo "- 前端构建大小: $frontend_size" >> $report_file
        fi
        
        echo "" >> $report_file
        echo "#### 主要文件:" >> $report_file
        
        find web_interface/frontend/dist/assets -name "*.js" -o -name "*.css" 2>/dev/null | \
        head -10 | \
        while read file; do
            if [ -f "$file" ]; then
                local file_size
                if command_exists stat; then
                    file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
                    local size_kb=$((file_size / 1024))
                    local file_name=$(basename "$file")
                    echo "- $file_name: ${size_kb}KB" >> $report_file
                fi
            fi
        done
    fi
    
    cat >> $report_file << EOF

### Docker镜像
EOF
    
    # Docker镜像大小
    if command_exists docker; then
        echo "" >> $report_file
        docker images --format "- {{.Repository}}:{{.Tag}}: {{.Size}}" | \
        grep trademaster >> $report_file 2>/dev/null || echo "- 未找到TradeMaster镜像" >> $report_file
    fi
    
    cat >> $report_file << EOF

## 性能建议

### 前端优化建议
- 使用代码分割减少初始bundle大小
- 启用Gzip/Brotli压缩
- 优化图片和字体资源
- 使用CDN加速静态资源

### 后端优化建议  
- 使用数据库连接池
- 启用Redis缓存
- 优化数据库查询
- 使用异步处理长时间任务

### Docker优化建议
- 使用多阶段构建减少镜像大小
- 优化Dockerfile层缓存
- 使用.dockerignore减少构建上下文
- 使用Alpine Linux基础镜像

## 监控建议

- 配置APM工具监控应用性能
- 设置日志聚合和分析
- 监控数据库性能指标
- 配置告警规则

EOF
    
    print_success "性能报告生成完成: $report_file"
    
    if command_exists code; then
        read -p "是否在VS Code中打开报告？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            code $report_file
        fi
    fi
}

# 主函数
main() {
    print_header "${PERFORMANCE} TradeMaster Web Interface 性能检查"
    
    echo -e "${ROCKET} ${CYAN}开始性能检查...${NC}"
    echo ""
    
    # 检查系统资源
    check_system_resources
    
    # 运行指定的检查
    if [ "$CHECK_BACKEND" = true ]; then
        check_backend_performance
    fi
    
    if [ "$CHECK_FRONTEND" = true ]; then
        check_frontend_performance
    fi
    
    if [ "$CHECK_DOCKER" = true ]; then
        check_docker_performance
    fi
    
    if [ "$CHECK_DATABASE" = true ]; then
        check_database_performance
    fi
    
    # 运行负载测试
    if [ "$LOAD_TEST" = true ]; then
        run_load_test
    fi
    
    # 生成报告
    if [ "$GENERATE_REPORT" = true ]; then
        generate_performance_report
    fi
    
    print_header "性能检查完成"
    print_success "性能检查已完成！📊"
    
    echo ""
    print_info "建议："
    echo "  - 定期运行性能检查"
    echo "  - 监控关键性能指标"
    echo "  - 优化识别出的性能瓶颈"
    echo "  - 在CI/CD中集成性能测试"
}

# 错误处理
trap 'print_error "性能检查脚本执行失败"; exit 1' ERR

# 运行主函数
main "$@"