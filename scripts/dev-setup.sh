#!/bin/bash
# ==================== TradeMaster Web Interface 开发环境一键设置脚本 ====================
# 
# 功能:
# - 检查系统要求
# - 安装依赖
# - 初始化开发环境
# - 启动开发服务
#
# 使用方法:
#   ./scripts/dev-setup.sh [options]
#
# 选项:
#   --skip-deps     跳过依赖安装
#   --skip-db       跳过数据库初始化
#   --skip-services 跳过服务启动
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
WRENCH="🔧"
DATABASE="🗄️"
GLOBE="🌐"
PYTHON="🐍"
NODE="📦"

# 参数解析
SKIP_DEPS=false
SKIP_DB=false
SKIP_SERVICES=false
HELP=false

for arg in "$@"; do
    case $arg in
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --skip-db)
            SKIP_DB=true
            shift
            ;;
        --skip-services)
            SKIP_SERVICES=true
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

# 帮助信息
show_help() {
    echo -e "${BLUE}TradeMaster Web Interface 开发环境设置脚本${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/dev-setup.sh [options]"
    echo ""
    echo "选项:"
    echo "  --skip-deps      跳过依赖安装"
    echo "  --skip-db        跳过数据库初始化"
    echo "  --skip-services  跳过服务启动"
    echo "  --help           显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/dev-setup.sh                    # 完整设置"
    echo "  ./scripts/dev-setup.sh --skip-deps       # 跳过依赖安装"
    echo "  ./scripts/dev-setup.sh --skip-services   # 跳过服务启动"
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

# 检查版本
check_version() {
    local cmd=$1
    local min_version=$2
    local current_version
    
    case $cmd in
        python|python3)
            current_version=$(python3 --version 2>&1 | cut -d' ' -f2)
            ;;
        node)
            current_version=$(node --version 2>&1 | cut -c2-)
            ;;
        docker)
            current_version=$(docker --version 2>&1 | cut -d' ' -f3 | cut -d',' -f1)
            ;;
        *)
            return 0
            ;;
    esac
    
    # 简单的版本比较 (仅适用于x.y.z格式)
    if [ "$(printf '%s\n' "$min_version" "$current_version" | sort -V | head -n1)" = "$min_version" ]; then
        return 0
    else
        return 1
    fi
}

# 主函数
main() {
    print_header "TradeMaster Web Interface 开发环境设置"
    
    echo -e "${ROCKET} ${CYAN}欢迎使用 TradeMaster Web Interface 开发环境设置脚本！${NC}"
    echo -e "${INFO} 这个脚本将帮助您快速设置完整的开发环境"
    echo ""
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
        DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        DISTRO="macOS"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="Windows"
        DISTRO="Windows"
    else
        OS="Unknown"
        DISTRO="Unknown"
    fi
    
    print_info "检测到操作系统: $OS ($DISTRO)"
    
    # 检查系统要求
    check_system_requirements
    
    # 安装依赖
    if [ "$SKIP_DEPS" = false ]; then
        install_dependencies
    else
        print_warning "跳过依赖安装"
    fi
    
    # 设置项目
    setup_project
    
    # 初始化数据库
    if [ "$SKIP_DB" = false ]; then
        setup_database
    else
        print_warning "跳过数据库设置"
    fi
    
    # 启动服务
    if [ "$SKIP_SERVICES" = false ]; then
        start_services
    else
        print_warning "跳过服务启动"
    fi
    
    # 显示完成信息
    show_completion_info
}

# 检查系统要求
check_system_requirements() {
    print_header "检查系统要求"
    
    local errors=0
    
    # 检查 Python
    if command_exists python3; then
        if check_version python3 "3.9.0"; then
            print_success "Python 3.9+ 已安装: $(python3 --version)"
        else
            print_error "Python 版本过低，需要 3.9+，当前版本: $(python3 --version)"
            errors=$((errors + 1))
        fi
    else
        print_error "Python 3 未安装"
        errors=$((errors + 1))
    fi
    
    # 检查 Node.js
    if command_exists node; then
        if check_version node "18.0.0"; then
            print_success "Node.js 18+ 已安装: $(node --version)"
        else
            print_error "Node.js 版本过低，需要 18+，当前版本: $(node --version)"
            errors=$((errors + 1))
        fi
    else
        print_error "Node.js 未安装"
        errors=$((errors + 1))
    fi
    
    # 检查 pnpm
    if command_exists pnpm; then
        print_success "pnpm 已安装: $(pnpm --version)"
    else
        print_warning "pnpm 未安装，将自动安装"
    fi
    
    # 检查 Docker
    if command_exists docker; then
        if check_version docker "20.0.0"; then
            print_success "Docker 20+ 已安装: $(docker --version)"
        else
            print_warning "Docker 版本较低，建议升级到 20+"
        fi
    else
        print_warning "Docker 未安装，某些功能可能不可用"
    fi
    
    # 检查 Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose 已安装"
    else
        print_warning "Docker Compose 未安装，某些功能可能不可用"
    fi
    
    # 检查 Git
    if command_exists git; then
        print_success "Git 已安装: $(git --version)"
    else
        print_error "Git 未安装"
        errors=$((errors + 1))
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "发现 $errors 个问题，请先安装缺失的依赖"
        echo ""
        print_info "安装指南:"
        echo "  Python 3.9+: https://www.python.org/downloads/"
        echo "  Node.js 18+:  https://nodejs.org/"
        echo "  Docker:       https://www.docker.com/get-started"
        echo "  Git:          https://git-scm.com/downloads"
        exit 1
    fi
    
    print_success "系统要求检查通过"
}

# 安装依赖
install_dependencies() {
    print_header "安装项目依赖"
    
    # 安装 pnpm（如果需要）
    if ! command_exists pnpm; then
        print_info "安装 pnpm..."
        npm install -g pnpm
        print_success "pnpm 安装完成"
    fi
    
    # 安装后端依赖
    print_info "${PYTHON} 安装后端 Python 依赖..."
    cd web_interface/backend
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        print_info "创建 Python 虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate || . venv/Scripts/activate
    
    # 升级 pip
    pip install --upgrade pip setuptools wheel
    
    # 安装依赖
    pip install -r requirements.txt
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
    
    print_success "后端依赖安装完成"
    
    # 安装前端依赖
    print_info "${NODE} 安装前端 Node.js 依赖..."
    cd ../frontend
    
    pnpm install
    
    print_success "前端依赖安装完成"
    
    cd ../..
}

# 设置项目
setup_project() {
    print_header "设置项目配置"
    
    # 创建环境配置文件
    if [ ! -f "web_interface/backend/.env" ]; then
        print_info "创建后端环境配置文件..."
        cp web_interface/backend/.env.example web_interface/backend/.env
        print_success "后端 .env 文件创建完成"
    else
        print_info "后端 .env 文件已存在"
    fi
    
    # 创建前端环境配置文件
    if [ ! -f "web_interface/frontend/.env.development" ]; then
        print_info "创建前端环境配置文件..."
        # 前端环境文件已经存在了
        print_success "前端环境配置已就绪"
    else
        print_info "前端环境配置文件已存在"
    fi
    
    # 安装 pre-commit hooks
    if command_exists pre-commit; then
        print_info "安装 pre-commit hooks..."
        pre-commit install
        print_success "Pre-commit hooks 安装完成"
    else
        print_warning "pre-commit 未安装，跳过 hooks 安装"
    fi
    
    # 创建必要的目录
    print_info "创建项目目录结构..."
    mkdir -p web_interface/backend/logs
    mkdir -p web_interface/backend/uploads
    mkdir -p web_interface/backend/temp
    mkdir -p web_interface/frontend/coverage
    
    # 创建 .gitkeep 文件
    touch web_interface/backend/logs/.gitkeep
    touch web_interface/backend/uploads/.gitkeep
    touch web_interface/backend/temp/.gitkeep
    
    print_success "项目目录结构创建完成"
}

# 设置数据库
setup_database() {
    print_header "设置数据库"
    
    # 检查是否有 Docker 服务
    if command_exists docker && (command_exists docker-compose || docker compose version >/dev/null 2>&1); then
        print_info "${DATABASE} 启动数据库服务..."
        
        cd web_interface
        
        # 使用 docker-compose 或 docker compose
        if command_exists docker-compose; then
            COMPOSE_CMD="docker-compose"
        else
            COMPOSE_CMD="docker compose"
        fi
        
        # 启动数据库和 Redis
        $COMPOSE_CMD -f docker-compose.dev.yml up -d postgres redis
        
        print_success "数据库服务启动完成"
        
        # 等待数据库就绪
        print_info "等待数据库就绪..."
        sleep 10
        
        # 运行数据库迁移
        print_info "运行数据库迁移..."
        cd backend
        source venv/bin/activate || . venv/Scripts/activate
        
        # 检查 alembic 配置
        if [ -f "alembic.ini" ]; then
            alembic upgrade head
            print_success "数据库迁移完成"
        else
            print_warning "未找到 alembic.ini，跳过数据库迁移"
        fi
        
        cd ../..
    else
        print_warning "Docker 服务不可用，请手动设置数据库"
        print_info "数据库配置信息:"
        echo "  PostgreSQL: localhost:5432"
        echo "  用户名: trademaster"
        echo "  密码: dev_password_123"
        echo "  数据库: trademaster_web"
        echo ""
        echo "  Redis: localhost:6379"
    fi
}

# 启动服务
start_services() {
    print_header "启动开发服务"
    
    print_info "启动开发服务器..."
    print_info "前端服务: http://localhost:3000"
    print_info "后端服务: http://localhost:8000"
    print_info "API 文档: http://localhost:8000/docs"
    
    echo ""
    print_info "使用以下命令启动服务:"
    echo ""
    echo -e "${CYAN}# 启动所有服务${NC}"
    echo "make dev"
    echo ""
    echo -e "${CYAN}# 或者分别启动${NC}"
    echo "make dev-backend    # 启动后端服务"
    echo "make dev-frontend   # 启动前端服务"
    echo ""
    echo -e "${CYAN}# 使用 Docker${NC}"
    echo "make docker-dev     # 使用 Docker 启动开发环境"
    echo ""
    
    read -p "是否现在启动开发服务？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "${ROCKET} 启动开发服务..."
        make dev
    else
        print_info "您可以稍后使用 'make dev' 启动开发服务"
    fi
}

# 显示完成信息
show_completion_info() {
    print_header "设置完成"
    
    echo -e "${SUCCESS} ${GREEN}TradeMaster Web Interface 开发环境设置完成！${NC}"
    echo ""
    
    print_info "下一步操作:"
    echo ""
    echo -e "${CYAN}1. 编辑环境配置文件:${NC}"
    echo "   web_interface/backend/.env     # 后端配置"
    echo "   web_interface/frontend/.env.development  # 前端配置"
    echo ""
    
    echo -e "${CYAN}2. 启动开发服务:${NC}"
    echo "   make dev                       # 启动所有服务"
    echo "   make dev-backend              # 仅启动后端"
    echo "   make dev-frontend             # 仅启动前端"
    echo ""
    
    echo -e "${CYAN}3. 运行测试:${NC}"
    echo "   make test                     # 运行所有测试"
    echo "   make test-backend            # 运行后端测试"
    echo "   make test-frontend           # 运行前端测试"
    echo ""
    
    echo -e "${CYAN}4. 代码质量检查:${NC}"
    echo "   make lint                     # 代码检查"
    echo "   make format                   # 代码格式化"
    echo ""
    
    echo -e "${CYAN}5. 访问应用:${NC}"
    echo "   前端应用: http://localhost:3000"
    echo "   后端 API: http://localhost:8000"
    echo "   API 文档: http://localhost:8000/docs"
    echo ""
    
    echo -e "${CYAN}6. 获取帮助:${NC}"
    echo "   make help                     # 查看所有可用命令"
    echo "   make info                     # 查看项目信息"
    echo ""
    
    print_success "享受编码的乐趣！🎉"
}

# 错误处理
trap 'print_error "脚本执行失败，请检查错误信息"; exit 1' ERR

# 运行主函数
main "$@"