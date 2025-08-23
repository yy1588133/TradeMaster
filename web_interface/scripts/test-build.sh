#!/bin/bash

# TradeMaster Frontend Build Test Script
# 此脚本用于测试前端构建流程并验证输出

set -e  # 遇到错误时立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DIST_DIR="$FRONTEND_DIR/dist"

log_info "开始前端构建测试..."
log_info "项目根目录: $PROJECT_ROOT"
log_info "前端目录: $FRONTEND_DIR"

# 检查前端目录是否存在
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# 检查package.json是否存在
if [ ! -f "package.json" ]; then
    log_error "package.json文件不存在"
    exit 1
fi

log_success "找到前端项目目录"

# 检查依赖是否已安装
log_info "检查依赖安装状态..."
if [ ! -d "node_modules" ]; then
    log_warning "node_modules目录不存在，正在安装依赖..."
    if command -v pnpm >/dev/null 2>&1; then
        pnpm install
    elif command -v npm >/dev/null 2>&1; then
        npm install
    else
        log_error "未找到包管理器 (pnpm 或 npm)"
        exit 1
    fi
else
    log_success "依赖已安装"
fi

# 清理之前的构建
log_info "清理之前的构建产物..."
if [ -d "$DIST_DIR" ]; then
    rm -rf "$DIST_DIR"
    log_success "清理完成"
else
    log_info "无需清理，dist目录不存在"
fi

# 运行TypeScript类型检查
log_info "运行TypeScript类型检查..."
if command -v pnpm >/dev/null 2>&1; then
    pnpm type-check
elif command -v npm >/dev/null 2>&1; then
    npm run type-check
else
    npx tsc --noEmit
fi
log_success "TypeScript类型检查通过"

# 运行ESLint检查
log_info "运行ESLint检查..."
if command -v pnpm >/dev/null 2>&1; then
    pnpm lint
elif command -v npm >/dev/null 2>&1; then
    npm run lint
else
    npx eslint . --ext ts,tsx
fi
log_success "ESLint检查通过"

# 执行生产构建
log_info "执行生产构建..."
if command -v pnpm >/dev/null 2>&1; then
    pnpm build:prod
elif command -v npm >/dev/null 2>&1; then
    npm run build:prod
else
    npx vite build --mode production
fi

# 验证构建结果
log_info "验证构建结果..."

# 检查dist目录是否生成
if [ ! -d "$DIST_DIR" ]; then
    log_error "构建失败：dist目录未生成"
    exit 1
fi

log_success "dist目录已生成"

# 检查关键文件
REQUIRED_FILES=(
    "index.html"
    "assets"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -e "$DIST_DIR/$file" ]; then
        log_success "找到必需文件/目录: $file"
    else
        log_error "缺少必需文件/目录: $file"
        exit 1
    fi
done

# 检查assets目录内容
ASSETS_DIR="$DIST_DIR/assets"
if [ -d "$ASSETS_DIR" ]; then
    JS_FILES=$(find "$ASSETS_DIR" -name "*.js" | wc -l)
    CSS_FILES=$(find "$ASSETS_DIR" -name "*.css" | wc -l)
    
    log_info "构建产物统计:"
    log_info "  JavaScript文件: $JS_FILES"
    log_info "  CSS文件: $CSS_FILES"
    
    if [ "$JS_FILES" -eq 0 ]; then
        log_error "未找到JavaScript文件"
        exit 1
    fi
    
    if [ "$CSS_FILES" -eq 0 ]; then
        log_warning "未找到CSS文件（可能正常）"
    fi
else
    log_error "assets目录不存在"
    exit 1
fi

# 检查文件大小
log_info "检查构建产物大小..."
TOTAL_SIZE=$(du -sh "$DIST_DIR" | cut -f1)
log_info "总构建大小: $TOTAL_SIZE"

# 检查gzip压缩后的大小（如果有gzip命令）
if command -v gzip >/dev/null 2>&1; then
    log_info "测试gzip压缩效果..."
    TEMP_DIR=$(mktemp -d)
    cp -r "$DIST_DIR"/* "$TEMP_DIR"/
    find "$TEMP_DIR" -type f \( -name "*.js" -o -name "*.css" -o -name "*.html" \) -exec gzip {} \; -exec mv {}.gz {} \;
    GZIPPED_SIZE=$(du -sh "$TEMP_DIR" | cut -f1)
    log_info "gzip压缩后大小: $GZIPPED_SIZE"
    rm -rf "$TEMP_DIR"
fi

# 验证HTML文件
log_info "验证HTML文件..."
if [ -f "$DIST_DIR/index.html" ]; then
    if grep -q "<script" "$DIST_DIR/index.html"; then
        log_success "HTML文件包含JavaScript引用"
    else
        log_warning "HTML文件可能缺少JavaScript引用"
    fi
    
    if grep -q "<link.*stylesheet" "$DIST_DIR/index.html"; then
        log_success "HTML文件包含CSS引用"
    else
        log_warning "HTML文件可能缺少CSS引用"
    fi
fi

# 测试生产预览（可选）
if [ "$1" = "--preview" ]; then
    log_info "启动生产预览服务器..."
    if command -v pnpm >/dev/null 2>&1; then
        pnpm preview &
    elif command -v npm >/dev/null 2>&1; then
        npm run preview &
    else
        npx vite preview &
    fi
    
    PREVIEW_PID=$!
    log_info "预览服务器PID: $PREVIEW_PID"
    log_info "预览地址: http://localhost:4173"
    log_info "按Ctrl+C停止预览服务器"
    
    # 等待用户停止
    trap "kill $PREVIEW_PID 2>/dev/null; exit 0" INT
    wait $PREVIEW_PID
fi

log_success "===================="
log_success "前端构建测试完成！"
log_success "===================="
log_info "构建产物位置: $DIST_DIR"
log_info "总大小: $TOTAL_SIZE"

# 输出构建产物清单
log_info "构建产物清单:"
find "$DIST_DIR" -type f | sort | while read -r file; do
    size=$(du -h "$file" | cut -f1)
    relative_path=${file#$DIST_DIR/}
    echo "  $relative_path ($size)"
done

log_success "构建成功，可以用于生产部署！"