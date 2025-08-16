#!/bin/bash
# ==================== TradeMaster Web Interface 全面测试脚本 ====================
# 
# 功能:
# - 运行所有测试套件
# - 生成测试报告
# - 代码覆盖率分析
# - 性能测试
# - 安全检查
#
# 使用方法:
#   ./scripts/test-all.sh [options]
#
# 选项:
#   --unit          只运行单元测试
#   --integration   只运行集成测试
#   --e2e           只运行端到端测试
#   --coverage      生成覆盖率报告
#   --performance   运行性能测试
#   --security      运行安全检查
#   --ci            CI模式（简化输出）
#   --parallel      并行运行测试
#   --fail-fast     遇到失败立即停止
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
TEST="🧪"
COVERAGE="📊"
SECURITY="🔒"
PERFORMANCE="⚡"
BACKEND="🐍"
FRONTEND="🌐"

# 默认配置
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false
RUN_COVERAGE=false
RUN_PERFORMANCE=false
RUN_SECURITY=false
CI_MODE=false
PARALLEL=false
FAIL_FAST=false
HELP=false

# 如果没有指定特定测试类型，则运行所有测试
RUN_ALL=true

# 参数解析
for arg in "$@"; do
    case $arg in
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --e2e)
            RUN_E2E=true
            RUN_ALL=false
            shift
            ;;
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --performance)
            RUN_PERFORMANCE=true
            shift
            ;;
        --security)
            RUN_SECURITY=true
            shift
            ;;
        --ci)
            CI_MODE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
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

# 如果没有指定任何测试类型，运行所有基本测试
if [ "$RUN_ALL" = true ]; then
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_COVERAGE=true
fi

# 帮助信息
show_help() {
    echo -e "${BLUE}TradeMaster Web Interface 测试脚本${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/test-all.sh [options]"
    echo ""
    echo "测试类型选项:"
    echo "  --unit          只运行单元测试"
    echo "  --integration   只运行集成测试"
    echo "  --e2e           只运行端到端测试"
    echo ""
    echo "附加功能选项:"
    echo "  --coverage      生成覆盖率报告"
    echo "  --performance   运行性能测试"
    echo "  --security      运行安全检查"
    echo ""
    echo "执行控制选项:"
    echo "  --ci            CI模式（简化输出）"
    echo "  --parallel      并行运行测试"
    echo "  --fail-fast     遇到失败立即停止"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/test-all.sh                    # 运行所有基本测试"
    echo "  ./scripts/test-all.sh --unit --coverage # 运行单元测试并生成覆盖率"
    echo "  ./scripts/test-all.sh --parallel --ci   # 并行运行，CI模式"
    echo "  ./scripts/test-all.sh --e2e             # 只运行端到端测试"
    echo ""
}

if [ "$HELP" = true ]; then
    show_help
    exit 0
fi

# 工具函数
print_header() {
    if [ "$CI_MODE" = false ]; then
        echo ""
        echo -e "${PURPLE}==================== $1 ====================${NC}"
        echo ""
    else
        echo "::group::$1"
    fi
}

print_end_group() {
    if [ "$CI_MODE" = true ]; then
        echo "::endgroup::"
    fi
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

# 检查项目根目录
check_project_root() {
    if [ ! -f "Makefile" ] || [ ! -d "web_interface" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    print_header "检查测试依赖"
    
    local missing_deps=0
    
    # 检查后端依赖
    if [ ! -f "web_interface/backend/venv/bin/python" ] && [ ! -f "web_interface/backend/venv/Scripts/python.exe" ]; then
        print_error "后端虚拟环境未找到，请先运行 make setup"
        missing_deps=$((missing_deps + 1))
    fi
    
    # 检查前端依赖
    if [ ! -d "web_interface/frontend/node_modules" ]; then
        print_error "前端依赖未安装，请先运行 pnpm install"
        missing_deps=$((missing_deps + 1))
    fi
    
    if [ $missing_deps -gt 0 ]; then
        print_error "发现 $missing_deps 个依赖问题，请先运行 ./scripts/dev-setup.sh"
        exit 1
    fi
    
    print_success "测试依赖检查通过"
    print_end_group
}

# 启动测试服务
start_test_services() {
    print_header "启动测试服务"
    
    if command_exists docker && (command_exists docker-compose || docker compose version >/dev/null 2>&1); then
        print_info "启动测试数据库服务..."
        
        cd web_interface
        
        # 使用 docker-compose 或 docker compose
        if command_exists docker-compose; then
            COMPOSE_CMD="docker-compose"
        else
            COMPOSE_CMD="docker compose"
        fi
        
        # 启动测试服务
        $COMPOSE_CMD -f docker-compose.dev.yml up -d postgres redis
        
        print_success "测试服务启动完成"
        
        # 等待服务就绪
        print_info "等待服务就绪..."
        sleep 5
        
        cd ..
    else
        print_warning "Docker 不可用，使用本地服务"
    fi
    
    print_end_group
}

# 停止测试服务
stop_test_services() {
    if command_exists docker && (command_exists docker-compose || docker compose version >/dev/null 2>&1); then
        print_info "停止测试服务..."
        
        cd web_interface
        
        if command_exists docker-compose; then
            COMPOSE_CMD="docker-compose"
        else
            COMPOSE_CMD="docker compose"
        fi
        
        $COMPOSE_CMD -f docker-compose.dev.yml down
        
        cd ..
        
        print_success "测试服务已停止"
    fi
}

# 运行后端测试
run_backend_tests() {
    local test_type=$1
    local extra_args=$2
    
    print_header "${BACKEND} 后端${test_type}测试"
    
    cd web_interface/backend
    
    # 激活虚拟环境
    source venv/bin/activate || . venv/Scripts/activate
    
    # 设置测试环境变量
    export TESTING=1
    export DATABASE_URL="postgresql://trademaster:dev_password_123@localhost:5432/trademaster_test"
    export REDIS_URL="redis://localhost:6379/1"
    export SECRET_KEY="test-secret-key"
    
    # 构建pytest命令
    local pytest_cmd="pytest"
    
    # 添加并行选项
    if [ "$PARALLEL" = true ]; then
        pytest_cmd="$pytest_cmd -n auto"
    fi
    
    # 添加fail-fast选项
    if [ "$FAIL_FAST" = true ]; then
        pytest_cmd="$pytest_cmd -x"
    fi
    
    # 添加覆盖率选项
    if [ "$RUN_COVERAGE" = true ]; then
        pytest_cmd="$pytest_cmd --cov=app --cov-report=html --cov-report=xml --cov-report=term-missing"
    fi
    
    # 添加CI模式选项
    if [ "$CI_MODE" = true ]; then
        pytest_cmd="$pytest_cmd --tb=short -q"
    else
        pytest_cmd="$pytest_cmd -v"
    fi
    
    # 运行特定类型的测试
    case $test_type in
        "单元")
            pytest_cmd="$pytest_cmd tests/unit/ $extra_args"
            ;;
        "集成")
            pytest_cmd="$pytest_cmd tests/integration/ $extra_args"
            ;;
        "端到端")
            pytest_cmd="$pytest_cmd tests/e2e/ $extra_args"
            ;;
        *)
            pytest_cmd="$pytest_cmd tests/ $extra_args"
            ;;
    esac
    
    print_info "运行命令: $pytest_cmd"
    
    if eval $pytest_cmd; then
        print_success "后端${test_type}测试通过"
        BACKEND_TEST_SUCCESS=true
    else
        print_error "后端${test_type}测试失败"
        BACKEND_TEST_SUCCESS=false
        if [ "$FAIL_FAST" = true ]; then
            cd ../..
            print_end_group
            exit 1
        fi
    fi
    
    cd ../..
    print_end_group
}

# 运行前端测试
run_frontend_tests() {
    local test_type=$1
    local extra_args=$2
    
    print_header "${FRONTEND} 前端${test_type}测试"
    
    cd web_interface/frontend
    
    # 构建测试命令
    local test_cmd="pnpm test"
    
    # 添加覆盖率选项
    if [ "$RUN_COVERAGE" = true ]; then
        test_cmd="pnpm test:coverage"
    fi
    
    # 添加CI模式选项
    if [ "$CI_MODE" = true ]; then
        test_cmd="$test_cmd --reporter=junit --outputFile=test-results.xml"
    fi
    
    # 运行特定类型的测试
    case $test_type in
        "单元")
            test_cmd="$test_cmd -- --run src/**/*.test.{ts,tsx} $extra_args"
            ;;
        "集成")
            test_cmd="$test_cmd -- --run tests/integration/**/*.test.{ts,tsx} $extra_args"
            ;;
        "端到端")
            test_cmd="$test_cmd -- --run tests/e2e/**/*.test.{ts,tsx} $extra_args"
            ;;
        *)
            test_cmd="$test_cmd -- --run $extra_args"
            ;;
    esac
    
    print_info "运行命令: $test_cmd"
    
    if eval $test_cmd; then
        print_success "前端${test_type}测试通过"
        FRONTEND_TEST_SUCCESS=true
    else
        print_error "前端${test_type}测试失败"
        FRONTEND_TEST_SUCCESS=false
        if [ "$FAIL_FAST" = true ]; then
            cd ../..
            print_end_group
            exit 1
        fi
    fi
    
    cd ../..
    print_end_group
}

# 运行性能测试
run_performance_tests() {
    print_header "${PERFORMANCE} 性能测试"
    
    print_info "运行后端性能测试..."
    cd web_interface/backend
    source venv/bin/activate || . venv/Scripts/activate
    
    if python -c "import pytest_benchmark" 2>/dev/null; then
        pytest tests/performance/ --benchmark-only --benchmark-json=benchmark.json
        print_success "后端性能测试完成"
    else
        print_warning "pytest-benchmark 未安装，跳过后端性能测试"
    fi
    
    cd ..
    
    print_info "运行前端性能测试..."
    cd frontend
    
    # 运行构建时间测试
    if pnpm build:analyze >/dev/null 2>&1; then
        print_success "前端构建分析完成"
    else
        print_warning "前端构建分析失败"
    fi
    
    cd ../..
    print_end_group
}

# 运行安全检查
run_security_tests() {
    print_header "${SECURITY} 安全检查"
    
    print_info "运行后端安全检查..."
    cd web_interface/backend
    source venv/bin/activate || . venv/Scripts/activate
    
    # Bandit 安全检查
    if command_exists bandit; then
        bandit -r app/ -f json -o security-report.json || true
        print_success "Bandit 安全检查完成"
    else
        print_warning "Bandit 未安装，跳过安全检查"
    fi
    
    # Safety 依赖安全检查
    if command_exists safety; then
        safety check --json --output safety-report.json || true
        print_success "Safety 依赖检查完成"
    else
        print_warning "Safety 未安装，跳过依赖安全检查"
    fi
    
    cd ..
    
    print_info "运行前端安全检查..."
    cd frontend
    
    # npm audit
    if pnpm audit --json > audit-report.json 2>/dev/null; then
        print_success "前端依赖安全检查完成"
    else
        print_warning "前端依赖安全检查发现问题"
    fi
    
    cd ../..
    print_end_group
}

# 生成测试报告
generate_test_report() {
    print_header "📋 生成测试报告"
    
    local report_dir="test-reports"
    mkdir -p $report_dir
    
    # 收集测试结果
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # 后端测试结果
    if [ -f "web_interface/backend/coverage.xml" ]; then
        cp web_interface/backend/coverage.xml $report_dir/backend-coverage.xml
        cp -r web_interface/backend/htmlcov $report_dir/backend-coverage-html 2>/dev/null || true
    fi
    
    # 前端测试结果
    if [ -f "web_interface/frontend/coverage/coverage.xml" ]; then
        cp web_interface/frontend/coverage/coverage.xml $report_dir/frontend-coverage.xml
        cp -r web_interface/frontend/coverage $report_dir/frontend-coverage-html 2>/dev/null || true
    fi
    
    # 安全报告
    if [ -f "web_interface/backend/security-report.json" ]; then
        cp web_interface/backend/security-report.json $report_dir/
    fi
    
    if [ -f "web_interface/backend/safety-report.json" ]; then
        cp web_interface/backend/safety-report.json $report_dir/
    fi
    
    if [ -f "web_interface/frontend/audit-report.json" ]; then
        cp web_interface/frontend/audit-report.json $report_dir/
    fi
    
    # 性能报告
    if [ -f "web_interface/backend/benchmark.json" ]; then
        cp web_interface/backend/benchmark.json $report_dir/
    fi
    
    # 生成汇总报告
    cat > $report_dir/summary.md << EOF
# TradeMaster Web Interface 测试报告

## 测试概览

- 测试时间: $(date)
- 测试环境: $(uname -s) $(uname -r)
- Python版本: $(python3 --version 2>&1)
- Node.js版本: $(node --version 2>&1)

## 测试结果

### 后端测试
- 状态: $([ "$BACKEND_TEST_SUCCESS" = true ] && echo "✅ 通过" || echo "❌ 失败")

### 前端测试
- 状态: $([ "$FRONTEND_TEST_SUCCESS" = true ] && echo "✅ 通过" || echo "❌ 失败")

## 报告文件

- 后端覆盖率: [backend-coverage.xml](./backend-coverage.xml)
- 前端覆盖率: [frontend-coverage.xml](./frontend-coverage.xml)
- 安全检查: [security-report.json](./security-report.json)
- 依赖检查: [safety-report.json](./safety-report.json)

EOF
    
    print_success "测试报告生成完成: $report_dir/"
    print_end_group
}

# 主函数
main() {
    print_header "${TEST} TradeMaster Web Interface 测试套件"
    
    if [ "$CI_MODE" = false ]; then
        echo -e "${ROCKET} ${CYAN}开始运行测试套件...${NC}"
        echo ""
    fi
    
    # 初始化测试结果变量
    BACKEND_TEST_SUCCESS=true
    FRONTEND_TEST_SUCCESS=true
    
    # 检查项目根目录
    check_project_root
    
    # 检查依赖
    check_dependencies
    
    # 启动测试服务
    start_test_services
    
    # 运行测试
    if [ "$RUN_UNIT" = true ]; then
        run_backend_tests "单元"
        run_frontend_tests "单元"
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        run_backend_tests "集成"
        run_frontend_tests "集成"
    fi
    
    if [ "$RUN_E2E" = true ]; then
        run_backend_tests "端到端"
        run_frontend_tests "端到端"
    fi
    
    # 运行附加测试
    if [ "$RUN_PERFORMANCE" = true ]; then
        run_performance_tests
    fi
    
    if [ "$RUN_SECURITY" = true ]; then
        run_security_tests
    fi
    
    # 生成测试报告
    if [ "$RUN_COVERAGE" = true ] || [ "$RUN_SECURITY" = true ] || [ "$RUN_PERFORMANCE" = true ]; then
        generate_test_report
    fi
    
    # 停止测试服务
    stop_test_services
    
    # 显示结果
    print_header "测试结果汇总"
    
    if [ "$BACKEND_TEST_SUCCESS" = true ] && [ "$FRONTEND_TEST_SUCCESS" = true ]; then
        print_success "所有测试通过！🎉"
        exit 0
    else
        print_error "部分测试失败！"
        [ "$BACKEND_TEST_SUCCESS" = false ] && print_error "后端测试失败"
        [ "$FRONTEND_TEST_SUCCESS" = false ] && print_error "前端测试失败"
        exit 1
    fi
    
    print_end_group
}

# 错误处理
trap 'print_error "测试脚本执行失败"; stop_test_services; exit 1' ERR

# 退出时清理
trap 'stop_test_services' EXIT

# 运行主函数
main "$@"