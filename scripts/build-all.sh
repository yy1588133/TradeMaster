#!/bin/bash
# ==================== TradeMaster Web Interface 构建脚本 ====================
# 
# 功能:
# - 构建前端和后端
# - 创建Docker镜像
# - 生成部署包
# - 优化和压缩
#
# 使用方法:
#   ./scripts/build-all.sh [options]
#
# 选项:
#   --frontend-only  只构建前端
#   --backend-only   只构建后端
#   --docker         构建Docker镜像
#   --production     生产环境构建
#   --analyze        分析构建结果
#   --clean          构建前清理
#   --help           显示帮助信息

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
BUILD="🔨"
DOCKER="🐳"
FRONTEND="🌐"
BACKEND="🐍"
PACKAGE="📦"

# 默认配置
BUILD_FRONTEND=true
BUILD_BACKEND=true
BUILD_DOCKER=false
PRODUCTION=false
ANALYZE=false
CLEAN=false
HELP=false

# 参数解析
for arg in "$@"; do
    case $arg in
        --frontend-only)
            BUILD_FRONTEND=true
            BUILD_BACKEND=false
            shift
            ;;
        --backend-only)
            BUILD_BACKEND=true
            BUILD_FRONTEND=false
            shift
            ;;
        --docker)
            BUILD_DOCKER=true
            shift
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        --analyze)
            ANALYZE=true
            shift
            ;;
        --clean)
            CLEAN=true
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
    echo -e "${BLUE}TradeMaster Web Interface 构建脚本${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/build-all.sh [options]"
    echo ""
    echo "构建选项:"
    echo "  --frontend-only  只构建前端"
    echo "  --backend-only   只构建后端"
    echo "  --docker         构建Docker镜像"
    echo ""
    echo "模式选项:"
    echo "  --production     生产环境构建（优化）"
    echo "  --analyze        分析构建结果"
    echo "  --clean          构建前清理旧文件"
    echo "  --help           显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/build-all.sh                    # 构建前端和后端"
    echo "  ./scripts/build-all.sh --production       # 生产环境构建"
    echo "  ./scripts/build-all.sh --docker           # 构建Docker镜像"
    echo "  ./scripts/build-all.sh --frontend-only --analyze  # 只构建前端并分析"
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

# 检查项目根目录
check_project_root() {
    if [ ! -f "Makefile" ] || [ ! -d "web_interface" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi
}

# 获取版本信息
get_version() {
    if [ -f "pyproject.toml" ]; then
        VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
    else
        VERSION="1.0.0"
    fi
    
    # 如果是开发版本，添加git commit
    if [ "$PRODUCTION" = false ]; then
        if command_exists git && [ -d ".git" ]; then
            GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
            VERSION="$VERSION-dev-$GIT_COMMIT"
        fi
    fi
    
    echo $VERSION
}

# 清理构建文件
clean_build() {
    print_header "🧹 清理构建文件"
    
    if [ "$BUILD_FRONTEND" = true ]; then
        print_info "清理前端构建文件..."
        rm -rf web_interface/frontend/dist
        rm -rf web_interface/frontend/coverage
        rm -rf web_interface/frontend/.eslintcache
        rm -rf web_interface/frontend/node_modules/.cache
        print_success "前端文件清理完成"
    fi
    
    if [ "$BUILD_BACKEND" = true ]; then
        print_info "清理后端构建文件..."
        rm -rf web_interface/backend/dist
        rm -rf web_interface/backend/build
        rm -rf web_interface/backend/*.egg-info
        rm -rf web_interface/backend/htmlcov
        find web_interface/backend -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find web_interface/backend -name "*.pyc" -delete 2>/dev/null || true
        print_success "后端文件清理完成"
    fi
    
    # 清理Docker构建缓存
    if [ "$BUILD_DOCKER" = true ] && command_exists docker; then
        print_info "清理Docker构建缓存..."
        docker builder prune -f >/dev/null 2>&1 || true
        print_success "Docker缓存清理完成"
    fi
}

# 检查构建依赖
check_build_dependencies() {
    print_header "检查构建依赖"
    
    local missing_deps=0
    
    if [ "$BUILD_FRONTEND" = true ]; then
        # 检查Node.js和pnpm
        if ! command_exists node; then
            print_error "Node.js 未安装"
            missing_deps=$((missing_deps + 1))
        fi
        
        if ! command_exists pnpm; then
            print_error "pnpm 未安装"
            missing_deps=$((missing_deps + 1))
        fi
        
        # 检查前端依赖
        if [ ! -d "web_interface/frontend/node_modules" ]; then
            print_error "前端依赖未安装，请运行: cd web_interface/frontend && pnpm install"
            missing_deps=$((missing_deps + 1))
        fi
    fi
    
    if [ "$BUILD_BACKEND" = true ]; then
        # 检查Python
        if ! command_exists python3; then
            print_error "Python 3 未安装"
            missing_deps=$((missing_deps + 1))
        fi
        
        # 检查后端虚拟环境
        if [ ! -f "web_interface/backend/venv/bin/python" ] && [ ! -f "web_interface/backend/venv/Scripts/python.exe" ]; then
            print_error "后端虚拟环境未找到，请运行: cd web_interface/backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
            missing_deps=$((missing_deps + 1))
        fi
    fi
    
    if [ "$BUILD_DOCKER" = true ]; then
        if ! command_exists docker; then
            print_error "Docker 未安装"
            missing_deps=$((missing_deps + 1))
        fi
    fi
    
    if [ $missing_deps -gt 0 ]; then
        print_error "发现 $missing_deps 个依赖问题，请先解决"
        exit 1
    fi
    
    print_success "构建依赖检查通过"
}

# 构建前端
build_frontend() {
    print_header "${FRONTEND} 构建前端"
    
    cd web_interface/frontend
    
    # 设置环境变量
    if [ "$PRODUCTION" = true ]; then
        export NODE_ENV=production
        export VITE_APP_ENV=production
        export VITE_DROP_CONSOLE=true
        export VITE_SOURCEMAP=false
        print_info "使用生产环境配置"
    else
        export NODE_ENV=development
        export VITE_APP_ENV=development
        export VITE_DROP_CONSOLE=false
        export VITE_SOURCEMAP=true
        print_info "使用开发环境配置"
    fi
    
    # 运行构建
    print_info "开始前端构建..."
    local start_time=$(date +%s)
    
    if [ "$PRODUCTION" = true ]; then
        pnpm build
    else
        pnpm build
    fi
    
    local end_time=$(date +%s)
    local build_time=$((end_time - start_time))
    
    print_success "前端构建完成 (${build_time}秒)"
    
    # 显示构建结果
    if [ -d "dist" ]; then
        local dist_size=$(du -sh dist | cut -f1)
        print_info "构建输出大小: $dist_size"
        
        # 显示主要文件
        print_info "主要文件:"
        find dist -name "*.js" -o -name "*.css" | head -10 | while read file; do
            local file_size=$(du -sh "$file" | cut -f1)
            local file_name=$(basename "$file")
            echo "  $file_name: $file_size"
        done
    fi
    
    # 分析构建结果
    if [ "$ANALYZE" = true ]; then
        print_info "分析构建结果..."
        
        if [ -f "dist/stats.html" ]; then
            print_success "构建分析报告: web_interface/frontend/dist/stats.html"
        fi
        
        # 检查bundle大小
        if [ -d "dist/assets" ]; then
            print_info "Bundle 大小分析:"
            find dist/assets -name "*.js" | while read file; do
                local file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
                local file_name=$(basename "$file")
                local size_kb=$((file_size / 1024))
                
                if [ $size_kb -gt 500 ]; then
                    print_warning "$file_name: ${size_kb}KB (较大)"
                else
                    print_info "$file_name: ${size_kb}KB"
                fi
            done
        fi
    fi
    
    cd ../..
}

# 构建后端
build_backend() {
    print_header "${BACKEND} 构建后端"
    
    cd web_interface/backend
    
    # 激活虚拟环境
    source venv/bin/activate || . venv/Scripts/activate
    
    # 安装构建工具
    if ! python -c "import build" 2>/dev/null; then
        print_info "安装构建工具..."
        pip install build wheel
    fi
    
    # 运行构建
    print_info "开始后端构建..."
    local start_time=$(date +%s)
    
    python -m build
    
    local end_time=$(date +%s)
    local build_time=$((end_time - start_time))
    
    print_success "后端构建完成 (${build_time}秒)"
    
    # 显示构建结果
    if [ -d "dist" ]; then
        local dist_size=$(du -sh dist | cut -f1)
        print_info "构建输出大小: $dist_size"
        
        print_info "构建文件:"
        ls -la dist/
    fi
    
    cd ../..
}

# 构建Docker镜像
build_docker() {
    print_header "${DOCKER} 构建Docker镜像"
    
    local version=$(get_version)
    local image_tag="trademaster/web-interface:$version"
    local latest_tag="trademaster/web-interface:latest"
    
    cd web_interface
    
    print_info "构建Docker镜像: $image_tag"
    
    # 构建参数
    local build_args=""
    build_args="$build_args --build-arg VERSION=$version"
    build_args="$build_args --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    
    if command_exists git && [ -d "../.git" ]; then
        local git_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
        build_args="$build_args --build-arg VCS_REF=$git_commit"
    fi
    
    # 使用Docker Compose构建
    if command_exists docker-compose; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    local start_time=$(date +%s)
    
    if [ "$PRODUCTION" = true ]; then
        $COMPOSE_CMD -f docker-compose.prod.yml build $build_args
    else
        $COMPOSE_CMD -f docker-compose.dev.yml build $build_args
    fi
    
    local end_time=$(date +%s)
    local build_time=$((end_time - start_time))
    
    print_success "Docker镜像构建完成 (${build_time}秒)"
    
    # 标记镜像
    if [ "$PRODUCTION" = true ]; then
        docker tag $image_tag $latest_tag
        print_info "镜像标签: $image_tag, $latest_tag"
    else
        print_info "镜像标签: $image_tag"
    fi
    
    # 显示镜像信息
    local image_size=$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "trademaster/web-interface" | head -1 | awk '{print $3}')
    print_info "镜像大小: $image_size"
    
    cd ..
}

# 创建部署包
create_deployment_package() {
    print_header "${PACKAGE} 创建部署包"
    
    local version=$(get_version)
    local package_name="trademaster-web-$version"
    local package_dir="dist/$package_name"
    
    print_info "创建部署包: $package_name"
    
    # 创建部署目录
    rm -rf dist
    mkdir -p $package_dir
    
    # 复制构建产物
    if [ "$BUILD_FRONTEND" = true ] && [ -d "web_interface/frontend/dist" ]; then
        cp -r web_interface/frontend/dist $package_dir/frontend
        print_info "已包含前端构建文件"
    fi
    
    if [ "$BUILD_BACKEND" = true ] && [ -d "web_interface/backend/dist" ]; then
        cp -r web_interface/backend/dist $package_dir/backend
        print_info "已包含后端构建文件"
    fi
    
    # 复制Docker配置
    if [ -d "web_interface/docker" ]; then
        cp -r web_interface/docker $package_dir/
    fi
    
    # 复制配置文件
    [ -f "web_interface/docker-compose.prod.yml" ] && cp web_interface/docker-compose.prod.yml $package_dir/
    [ -f "web_interface/.env.prod.template" ] && cp web_interface/.env.prod.template $package_dir/
    
    # 复制文档
    [ -f "README.md" ] && cp README.md $package_dir/
    [ -f "LICENSE" ] && cp LICENSE $package_dir/
    [ -f "CHANGELOG.md" ] && cp CHANGELOG.md $package_dir/
    
    # 创建安装脚本
    cat > $package_dir/install.sh << 'EOF'
#!/bin/bash
# TradeMaster Web Interface 安装脚本

set -e

VERSION="__VERSION__"
echo "🚀 安装 TradeMaster Web Interface $VERSION"

# 检查Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建环境配置
if [ ! -f ".env.prod" ]; then
    if [ -f ".env.prod.template" ]; then
        cp .env.prod.template .env.prod
        echo "📝 已创建 .env.prod 配置文件"
        echo "⚠️  请编辑 .env.prod 文件，配置您的生产环境参数"
        echo ""
        echo "重要配置项："
        echo "  - POSTGRES_PASSWORD: 数据库密码"
        echo "  - REDIS_PASSWORD: Redis密码"
        echo "  - SECRET_KEY: JWT密钥"
        echo "  - BACKEND_CORS_ORIGINS: 允许的域名"
        echo ""
        read -p "配置完成后按Enter继续..."
    else
        echo "❌ 未找到配置模板文件"
        exit 1
    fi
fi

# 启动服务
echo "🐳 启动服务..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker-compose.prod.yml up -d
else
    docker compose -f docker-compose.prod.yml up -d
fi

echo "✅ 安装完成！"
echo ""
echo "访问地址:"
echo "  前端应用: http://localhost"
echo "  后端API: http://localhost/api/v1"
echo "  API文档: http://localhost/api/v1/docs"
echo ""
echo "管理命令:"
echo "  停止服务: docker-compose -f docker-compose.prod.yml down"
echo "  查看日志: docker-compose -f docker-compose.prod.yml logs"
echo "  重启服务: docker-compose -f docker-compose.prod.yml restart"
EOF
    
    # 替换版本号
    sed -i.bak "s/__VERSION__/$version/g" $package_dir/install.sh && rm $package_dir/install.sh.bak
    chmod +x $package_dir/install.sh
    
    # 创建压缩包
    cd dist
    tar -czf $package_name.tar.gz $package_name/
    zip -r $package_name.zip $package_name/ >/dev/null
    cd ..
    
    local package_size=$(du -sh dist/$package_name.tar.gz | cut -f1)
    print_success "部署包创建完成: dist/$package_name.tar.gz ($package_size)"
    
    print_info "部署包内容:"
    echo "  📦 压缩包: dist/$package_name.tar.gz"
    echo "  📦 ZIP包: dist/$package_name.zip"
    echo "  🚀 安装脚本: install.sh"
    echo "  📖 说明文档: README.md"
}

# 主函数
main() {
    print_header "${BUILD} TradeMaster Web Interface 构建系统"
    
    local version=$(get_version)
    echo -e "${ROCKET} ${CYAN}构建版本: $version${NC}"
    
    if [ "$PRODUCTION" = true ]; then
        echo -e "${INFO} ${GREEN}生产环境构建${NC}"
    else
        echo -e "${INFO} ${YELLOW}开发环境构建${NC}"
    fi
    echo ""
    
    # 检查项目根目录
    check_project_root
    
    # 清理构建文件
    if [ "$CLEAN" = true ]; then
        clean_build
    fi
    
    # 检查构建依赖
    check_build_dependencies
    
    # 执行构建
    local start_time=$(date +%s)
    
    if [ "$BUILD_FRONTEND" = true ]; then
        build_frontend
    fi
    
    if [ "$BUILD_BACKEND" = true ]; then
        build_backend
    fi
    
    if [ "$BUILD_DOCKER" = true ]; then
        build_docker
    fi
    
    # 创建部署包
    if [ "$BUILD_FRONTEND" = true ] || [ "$BUILD_BACKEND" = true ]; then
        create_deployment_package
    fi
    
    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))
    
    # 显示构建结果
    print_header "构建完成"
    
    echo -e "${SUCCESS} ${GREEN}构建成功完成！${NC}"
    echo -e "${INFO} 总用时: ${total_time}秒"
    echo -e "${INFO} 构建版本: $version"
    echo ""
    
    if [ "$BUILD_FRONTEND" = true ]; then
        echo -e "${FRONTEND} 前端构建: web_interface/frontend/dist/"
    fi
    
    if [ "$BUILD_BACKEND" = true ]; then
        echo -e "${BACKEND} 后端构建: web_interface/backend/dist/"
    fi
    
    if [ "$BUILD_DOCKER" = true ]; then
        echo -e "${DOCKER} Docker镜像: trademaster/web-interface:$version"
    fi
    
    if [ -d "dist" ]; then
        echo -e "${PACKAGE} 部署包: dist/trademaster-web-$version.tar.gz"
    fi
    
    print_success "构建流程完成！🎉"
}

# 错误处理
trap 'print_error "构建失败，请检查错误信息"; exit 1' ERR

# 运行主函数
main "$@"