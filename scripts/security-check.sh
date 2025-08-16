#!/bin/bash
# ==================== TradeMaster Web Interface 安全检查脚本 ====================
# 
# 功能:
# - 依赖漏洞扫描
# - 代码安全分析
# - 配置安全检查
# - Docker安全扫描
# - 敏感信息检测
# - 权限和访问控制检查
#
# 使用方法:
#   ./scripts/security-check.sh [options]
#
# 选项:
#   --dependencies  检查依赖漏洞
#   --code          代码安全分析
#   --config        配置安全检查
#   --docker        Docker安全扫描
#   --secrets       敏感信息检测
#   --permissions   权限检查
#   --report        生成安全报告
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
SECURITY="🔒"
VULNERABILITY="🚨"
SHIELD="🛡️"
KEY="🔑"
DOCKER="🐳"
REPORT="📋"

# 默认配置
CHECK_DEPENDENCIES=false
CHECK_CODE=false
CHECK_CONFIG=false
CHECK_DOCKER=false
CHECK_SECRETS=false
CHECK_PERMISSIONS=false
GENERATE_REPORT=false
HELP=false

# 如果没有指定检查类型，则检查所有
CHECK_ALL=true

# 参数解析
for arg in "$@"; do
    case $arg in
        --dependencies)
            CHECK_DEPENDENCIES=true
            CHECK_ALL=false
            shift
            ;;
        --code)
            CHECK_CODE=true
            CHECK_ALL=false
            shift
            ;;
        --config)
            CHECK_CONFIG=true
            CHECK_ALL=false
            shift
            ;;
        --docker)
            CHECK_DOCKER=true
            CHECK_ALL=false
            shift
            ;;
        --secrets)
            CHECK_SECRETS=true
            CHECK_ALL=false
            shift
            ;;
        --permissions)
            CHECK_PERMISSIONS=true
            CHECK_ALL=false
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

# 如果没有指定特定检查，运行所有检查
if [ "$CHECK_ALL" = true ]; then
    CHECK_DEPENDENCIES=true
    CHECK_CODE=true
    CHECK_CONFIG=true
    CHECK_DOCKER=true
    CHECK_SECRETS=true
    CHECK_PERMISSIONS=true
    GENERATE_REPORT=true
fi

# 帮助信息
show_help() {
    echo -e "${BLUE}TradeMaster Web Interface 安全检查脚本${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./scripts/security-check.sh [options]"
    echo ""
    echo "检查选项:"
    echo "  --dependencies  检查依赖漏洞"
    echo "  --code          代码安全分析"
    echo "  --config        配置安全检查"
    echo "  --docker        Docker安全扫描"
    echo "  --secrets       敏感信息检测"
    echo "  --permissions   权限检查"
    echo ""
    echo "其他选项:"
    echo "  --report        生成安全报告"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/security-check.sh                    # 完整安全检查"
    echo "  ./scripts/security-check.sh --dependencies     # 仅检查依赖漏洞"
    echo "  ./scripts/security-check.sh --secrets --report # 敏感信息检测+报告"
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

print_vulnerability() {
    echo -e "${VULNERABILITY} ${RED}$1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 创建安全报告目录
create_report_dir() {
    local report_dir="security-reports"
    mkdir -p $report_dir
    echo $report_dir
}

# 依赖漏洞扫描
check_dependencies_vulnerabilities() {
    print_header "${VULNERABILITY} 依赖漏洞扫描"
    
    local vulnerabilities_found=0
    
    # Python依赖检查
    print_info "检查Python依赖漏洞..."
    cd web_interface/backend
    
    if [ -f "requirements.txt" ]; then
        # 使用safety检查Python依赖
        if command_exists safety; then
            print_info "运行safety安全检查..."
            if safety check -r requirements.txt --json > ../../security-reports/python-vulnerabilities.json 2>/dev/null; then
                print_success "Python依赖安全检查完成"
            else
                local safety_output=$(safety check -r requirements.txt 2>&1 || true)
                if echo "$safety_output" | grep -i "vulnerability\|CVE" >/dev/null; then
                    print_vulnerability "发现Python依赖漏洞"
                    echo "$safety_output"
                    vulnerabilities_found=1
                else
                    print_success "未发现Python依赖漏洞"
                fi
            fi
        else
            print_warning "safety工具未安装，跳过Python依赖检查"
            print_info "安装命令: pip install safety"
        fi
        
        # 使用pip-audit检查（如果可用）
        if command_exists pip-audit; then
            print_info "运行pip-audit检查..."
            if ! pip-audit -r requirements.txt --format=json --output=../../security-reports/pip-audit.json; then
                print_warning "pip-audit检查发现问题"
                vulnerabilities_found=1
            fi
        fi
    else
        print_warning "requirements.txt文件不存在"
    fi
    
    cd ../..
    
    # Node.js依赖检查
    print_info "检查Node.js依赖漏洞..."
    cd web_interface/frontend
    
    if [ -f "package.json" ]; then
        # 使用npm audit
        if command_exists npm; then
            print_info "运行npm audit..."
            local npm_audit_output=$(npm audit --json 2>/dev/null || true)
            
            if [ -n "$npm_audit_output" ]; then
                echo "$npm_audit_output" > ../../security-reports/npm-audit.json
                
                local vulnerabilities=$(echo "$npm_audit_output" | grep -o '"vulnerabilities":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "0")
                
                if [ "$vulnerabilities" != "0" ] && [ -n "$vulnerabilities" ]; then
                    print_vulnerability "发现 $vulnerabilities 个Node.js依赖漏洞"
                    npm audit --audit-level moderate
                    vulnerabilities_found=1
                else
                    print_success "未发现Node.js依赖漏洞"
                fi
            fi
        fi
        
        # 使用pnpm audit (如果使用pnpm)
        if command_exists pnpm && [ -f "pnpm-lock.yaml" ]; then
            print_info "运行pnpm audit..."
            if ! pnpm audit --json > ../../security-reports/pnpm-audit.json 2>/dev/null; then
                print_warning "pnpm audit检查发现问题"
            fi
        fi
        
        # 使用yarn audit (如果使用yarn)
        if command_exists yarn && [ -f "yarn.lock" ]; then
            print_info "运行yarn audit..."
            if ! yarn audit --json > ../../security-reports/yarn-audit.json 2>/dev/null; then
                print_warning "yarn audit检查发现问题"
            fi
        fi
    else
        print_warning "package.json文件不存在"
    fi
    
    cd ../..
    
    return $vulnerabilities_found
}

# 代码安全分析
check_code_security() {
    print_header "${SHIELD} 代码安全分析"
    
    local security_issues=0
    
    # Python代码安全检查
    print_info "检查Python代码安全..."
    cd web_interface/backend
    
    # 使用bandit检查Python安全问题
    if command_exists bandit; then
        print_info "运行bandit安全扫描..."
        if bandit -r . -f json -o ../../security-reports/bandit-report.json >/dev/null 2>&1; then
            print_success "Python代码安全检查完成"
        else
            print_warning "bandit发现潜在安全问题"
            bandit -r . --severity-level medium
            security_issues=1
        fi
    else
        print_warning "bandit工具未安装，跳过Python安全检查"
        print_info "安装命令: pip install bandit"
    fi
    
    # 检查硬编码密码和密钥
    print_info "检查硬编码凭据..."
    local suspicious_patterns=(
        "password\s*=\s*['\"][^'\"]*['\"]"
        "secret\s*=\s*['\"][^'\"]*['\"]"
        "api_key\s*=\s*['\"][^'\"]*['\"]"
        "token\s*=\s*['\"][^'\"]*['\"]"
    )
    
    for pattern in "${suspicious_patterns[@]}"; do
        local matches=$(grep -r -i -E "$pattern" . --exclude-dir=venv --exclude-dir=__pycache__ --exclude="*.pyc" 2>/dev/null || true)
        if [ -n "$matches" ]; then
            print_warning "发现可疑的硬编码凭据:"
            echo "$matches" | head -5
            security_issues=1
        fi
    done
    
    cd ../..
    
    # JavaScript/TypeScript代码安全检查
    print_info "检查前端代码安全..."
    cd web_interface/frontend
    
    # 检查console.log调试信息
    local console_logs=$(find src -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | \
                        xargs grep -n "console\." 2>/dev/null || true)
    if [ -n "$console_logs" ]; then
        local log_count=$(echo "$console_logs" | wc -l)
        print_warning "发现 $log_count 个console调试语句（生产环境应移除）"
        echo "$console_logs" | head -5
    fi
    
    # 检查eval使用
    local eval_usage=$(find src -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | \
                      xargs grep -n "eval(" 2>/dev/null || true)
    if [ -n "$eval_usage" ]; then
        print_vulnerability "发现eval()使用（安全风险）:"
        echo "$eval_usage"
        security_issues=1
    fi
    
    # 检查innerHTML使用
    local innerhtml_usage=$(find src -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | \
                           xargs grep -n "innerHTML" 2>/dev/null || true)
    if [ -n "$innerhtml_usage" ]; then
        print_warning "发现innerHTML使用（XSS风险）:"
        echo "$innerhtml_usage" | head -5
    fi
    
    cd ../..
    
    return $security_issues
}

# 配置安全检查
check_configuration_security() {
    print_header "${KEY} 配置安全检查"
    
    local config_issues=0
    
    # 检查环境变量文件
    print_info "检查环境变量安全..."
    
    local env_files=(
        ".env"
        ".env.local"
        ".env.development"
        ".env.production"
        "web_interface/frontend/.env"
        "web_interface/frontend/.env.local"
        "web_interface/frontend/.env.development"
        "web_interface/frontend/.env.production"
        "web_interface/backend/.env"
        "web_interface/backend/.env.local"
    )
    
    for env_file in "${env_files[@]}"; do
        if [ -f "$env_file" ]; then
            print_info "检查 $env_file..."
            
            # 检查是否包含敏感信息
            local sensitive_patterns=(
                "PASSWORD"
                "SECRET"
                "KEY"
                "TOKEN"
                "API_KEY"
                "PRIVATE"
            )
            
            for pattern in "${sensitive_patterns[@]}"; do
                local sensitive_vars=$(grep -i "$pattern" "$env_file" 2>/dev/null || true)
                if [ -n "$sensitive_vars" ]; then
                    print_warning "在 $env_file 中发现敏感配置:"
                    echo "$sensitive_vars" | sed 's/=.*/=***/' # 隐藏值
                fi
            done
            
            # 检查文件权限
            if [ -r "$env_file" ]; then
                local file_perms
                if command_exists stat; then
                    file_perms=$(stat -f%A "$env_file" 2>/dev/null || stat -c%a "$env_file" 2>/dev/null || echo "unknown")
                    if [ "$file_perms" != "600" ] && [ "$file_perms" != "unknown" ]; then
                        print_warning "$env_file 文件权限过宽: $file_perms (建议: 600)"
                        config_issues=1
                    fi
                fi
            fi
        fi
    done
    
    # 检查Docker配置安全
    print_info "检查Docker配置安全..."
    
    local docker_files=(
        "Dockerfile"
        "docker-compose.yml"
        "docker-compose.override.yml"
        "web_interface/frontend/Dockerfile"
        "web_interface/backend/Dockerfile"
    )
    
    for docker_file in "${docker_files[@]}"; do
        if [ -f "$docker_file" ]; then
            print_info "检查 $docker_file..."
            
            # 检查是否使用root用户
            if grep -q "USER root" "$docker_file" 2>/dev/null; then
                print_warning "$docker_file 使用root用户运行（安全风险）"
                config_issues=1
            fi
            
            # 检查是否暴露敏感端口
            local exposed_ports=$(grep -E "EXPOSE|ports:" "$docker_file" 2>/dev/null || true)
            if echo "$exposed_ports" | grep -E "22|3389|5432|3306|27017" >/dev/null; then
                print_warning "$docker_file 暴露敏感端口:"
                echo "$exposed_ports"
            fi
            
            # 检查是否有硬编码秘密
            if grep -E "(PASSWORD|SECRET|KEY|TOKEN)" "$docker_file" 2>/dev/null | grep -v "ENV.*=" >/dev/null; then
                print_warning "$docker_file 可能包含硬编码秘密"
                config_issues=1
            fi
        fi
    done
    
    # 检查数据库配置
    print_info "检查数据库配置安全..."
    
    if [ -f "web_interface/backend/app/core/config.py" ]; then
        local db_config=$(grep -E "(POSTGRES|MYSQL|MONGO)" "web_interface/backend/app/core/config.py" 2>/dev/null || true)
        if echo "$db_config" | grep -E "localhost|127.0.0.1" >/dev/null; then
            print_info "数据库配置使用本地连接"
        fi
        
        if echo "$db_config" | grep -E "password.*=.*['\"].*['\"]" >/dev/null; then
            print_warning "数据库配置可能包含硬编码密码"
            config_issues=1
        fi
    fi
    
    return $config_issues
}

# Docker安全扫描
check_docker_security() {
    print_header "${DOCKER} Docker安全扫描"
    
    if ! command_exists docker; then
        print_warning "Docker未安装，跳过Docker安全检查"
        return 0
    fi
    
    local docker_issues=0
    
    # 检查运行中的容器
    print_info "检查运行中的Docker容器..."
    
    local running_containers=$(docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null || true)
    if [ -n "$running_containers" ]; then
        echo "$running_containers"
        
        # 检查容器权限
        docker ps -q | while read container_id; do
            if [ -n "$container_id" ]; then
                local container_info=$(docker inspect "$container_id" 2>/dev/null || true)
                if echo "$container_info" | grep -q '"Privileged": true'; then
                    local container_name=$(docker inspect --format='{{.Name}}' "$container_id" 2>/dev/null | sed 's/^\///')
                    print_warning "容器 $container_name 以特权模式运行（安全风险）"
                    docker_issues=1
                fi
            fi
        done
    else
        print_info "没有运行中的容器"
    fi
    
    # 检查镜像安全
    print_info "检查Docker镜像..."
    
    local trademaster_images=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -i trademaster 2>/dev/null || true)
    if [ -n "$trademaster_images" ]; then
        echo "$trademaster_images" | while read image; do
            if [ -n "$image" ]; then
                print_info "检查镜像: $image"
                
                # 使用docker scout检查漏洞（如果可用）
                if command_exists docker && docker scout version >/dev/null 2>&1; then
                    print_info "运行Docker Scout漏洞扫描..."
                    docker scout cves "$image" 2>/dev/null || print_warning "Docker Scout扫描失败"
                fi
                
                # 检查镜像历史
                local image_history=$(docker history --no-trunc "$image" 2>/dev/null | grep -i -E "(password|secret|key|token)" || true)
                if [ -n "$image_history" ]; then
                    print_warning "镜像历史中可能包含敏感信息"
                    docker_issues=1
                fi
            fi
        done
    fi
    
    # 检查Docker守护进程配置
    if [ -f "/etc/docker/daemon.json" ]; then
        print_info "检查Docker守护进程配置..."
        local daemon_config=$(cat /etc/docker/daemon.json 2>/dev/null || true)
        if echo "$daemon_config" | grep -q '"userns-remap"'; then
            print_success "已启用用户命名空间重映射"
        else
            print_warning "未启用用户命名空间重映射（建议启用）"
        fi
    fi
    
    return $docker_issues
}

# 敏感信息检测
check_secrets() {
    print_header "${KEY} 敏感信息检测"
    
    local secrets_found=0
    
    print_info "扫描代码中的敏感信息..."
    
    # 定义敏感信息模式
    local secret_patterns=(
        # API Keys
        "api[_-]?key['\"\s]*[:=]['\"\s]*[a-zA-Z0-9]{20,}"
        "apikey['\"\s]*[:=]['\"\s]*[a-zA-Z0-9]{20,}"
        
        # JWT Tokens
        "jwt['\"\s]*[:=]['\"\s]*[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"
        
        # Database URLs
        "postgres://[^'\"\s]*"
        "mysql://[^'\"\s]*"
        "mongodb://[^'\"\s]*"
        
        # AWS Keys
        "AKIA[0-9A-Z]{16}"
        "aws[_-]?secret[_-]?access[_-]?key"
        
        # GitHub Tokens
        "ghp_[a-zA-Z0-9]{36}"
        "github[_-]?token"
        
        # 私钥标识
        "-----BEGIN [A-Z ]*PRIVATE KEY-----"
        "-----BEGIN RSA PRIVATE KEY-----"
        
        # 通用密码模式
        "password['\"\s]*[:=]['\"\s]*['\"][^'\"]{8,}['\"]"
        "secret['\"\s]*[:=]['\"\s]*['\"][^'\"]{8,}['\"]"
    )
    
    # 扫描目录
    local scan_dirs=(
        "web_interface/backend"
        "web_interface/frontend/src"
        "scripts"
        "."
    )
    
    for dir in "${scan_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_info "扫描目录: $dir"
            
            for pattern in "${secret_patterns[@]}"; do
                local matches=$(find "$dir" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.json" -o -name "*.yml" -o -name "*.yaml" \) \
                               -not -path "*/node_modules/*" \
                               -not -path "*/venv/*" \
                               -not -path "*/__pycache__/*" \
                               -not -path "*/dist/*" \
                               -not -path "*/build/*" \
                               -exec grep -l -E "$pattern" {} \; 2>/dev/null || true)
                
                if [ -n "$matches" ]; then
                    print_vulnerability "发现潜在敏感信息:"
                    echo "$matches" | while read file; do
                        if [ -n "$file" ]; then
                            local line_matches=$(grep -n -E "$pattern" "$file" 2>/dev/null | head -3)
                            echo "  文件: $file"
                            echo "$line_matches" | sed 's/^/    /'
                        fi
                    done
                    secrets_found=1
                fi
            done
        fi
    done
    
    # 检查git历史中的敏感信息（如果是git仓库）
    if [ -d ".git" ]; then
        print_info "检查Git历史中的敏感信息..."
        
        # 使用git-secrets工具（如果安装）
        if command_exists git-secrets; then
            print_info "运行git-secrets扫描..."
            if ! git secrets --scan; then
                print_warning "git-secrets发现潜在问题"
                secrets_found=1
            fi
        else
            print_info "git-secrets未安装，跳过Git历史扫描"
            print_info "安装命令: https://github.com/awslabs/git-secrets"
        fi
        
        # 简单的提交消息检查
        local commit_secrets=$(git log --oneline -n 100 | grep -i -E "(password|secret|key|token|api)" || true)
        if [ -n "$commit_secrets" ]; then
            print_warning "提交消息中发现敏感词汇:"
            echo "$commit_secrets" | head -5
        fi
    fi
    
    return $secrets_found
}

# 权限检查
check_permissions() {
    print_header "${SHIELD} 权限和访问控制检查"
    
    local permission_issues=0
    
    # 检查重要文件权限
    print_info "检查文件权限..."
    
    local important_files=(
        ".env"
        ".env.local"
        "web_interface/backend/.env"
        "web_interface/frontend/.env"
        "scripts/dev-setup.sh"
        "scripts/security-check.sh"
        "scripts/performance-check.sh"
    )
    
    for file in "${important_files[@]}"; do
        if [ -f "$file" ]; then
            if command_exists stat; then
                local file_perms
                file_perms=$(stat -f%A "$file" 2>/dev/null || stat -c%a "$file" 2>/dev/null || echo "unknown")
                
                case "$file" in
                    *.env*)
                        if [ "$file_perms" != "600" ] && [ "$file_perms" != "unknown" ]; then
                            print_warning "$file 权限过宽: $file_perms (建议: 600)"
                            permission_issues=1
                        fi
                        ;;
                    *.sh)
                        if [ "$file_perms" != "755" ] && [ "$file_perms" != "unknown" ]; then
                            print_info "$file 权限: $file_perms (建议: 755)"
                        fi
                        ;;
                esac
            fi
        fi
    done
    
    # 检查目录权限
    print_info "检查目录权限..."
    
    local important_dirs=(
        "web_interface/backend/venv"
        "web_interface/frontend/node_modules"
        "security-reports"
        "performance-reports"
    )
    
    for dir in "${important_dirs[@]}"; do
        if [ -d "$dir" ]; then
            if command_exists stat; then
                local dir_perms
                dir_perms=$(stat -f%A "$dir" 2>/dev/null || stat -c%a "$dir" 2>/dev/null || echo "unknown")
                
                if [ "$dir_perms" != "755" ] && [ "$dir_perms" != "unknown" ]; then
                    print_info "$dir 权限: $dir_perms"
                fi
            fi
        fi
    done
    
    # 检查用户和组
    print_info "当前用户: $(whoami)"
    print_info "当前组: $(id -gn 2>/dev/null || echo "unknown")"
    
    # 检查sudo权限（可选）
    if command_exists sudo; then
        if sudo -n true 2>/dev/null; then
            print_warning "当前用户具有sudo权限（注意安全）"
        fi
    fi
    
    return $permission_issues
}

# 生成安全报告
generate_security_report() {
    print_header "${REPORT} 生成安全报告"
    
    local report_dir=$(create_report_dir)
    local report_file="$report_dir/security-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > $report_file << EOF
# TradeMaster Web Interface 安全检查报告

## 报告信息

- 生成时间: $(date)
- 检查版本: TradeMaster Security Check v1.0
- 系统信息: $(uname -s) $(uname -r)
- 扫描用户: $(whoami)

## 执行摘要

本报告包含对TradeMaster Web Interface项目的全面安全评估，涵盖：
- 依赖漏洞扫描
- 代码安全分析  
- 配置安全检查
- Docker安全评估
- 敏感信息检测
- 权限和访问控制检查

## 检查结果汇总

EOF
    
    # 添加检查结果
    if [ -f "$report_dir/python-vulnerabilities.json" ]; then
        echo "### Python依赖漏洞" >> $report_file
        echo "- 检查状态: 已完成" >> $report_file
        echo "- 详细报告: python-vulnerabilities.json" >> $report_file
        echo "" >> $report_file
    fi
    
    if [ -f "$report_dir/npm-audit.json" ]; then
        echo "### Node.js依赖漏洞" >> $report_file
        echo "- 检查状态: 已完成" >> $report_file
        echo "- 详细报告: npm-audit.json" >> $report_file
        echo "" >> $report_file
    fi
    
    if [ -f "$report_dir/bandit-report.json" ]; then
        echo "### Python代码安全" >> $report_file
        echo "- 检查状态: 已完成" >> $report_file
        echo "- 详细报告: bandit-report.json" >> $report_file
        echo "" >> $report_file
    fi
    
    cat >> $report_file << EOF

## 安全建议

### 高优先级建议
1. **依赖更新**: 定期更新所有依赖包到最新安全版本
2. **环境变量保护**: 确保所有.env文件权限设置为600
3. **敏感信息清理**: 移除代码中的硬编码凭据和调试信息
4. **Docker安全**: 避免使用特权模式运行容器

### 中优先级建议
1. **代码审查**: 实施代码审查流程，关注安全问题
2. **自动化扫描**: 在CI/CD流程中集成安全扫描
3. **访问控制**: 实施最小权限原则
4. **监控告警**: 设置安全事件监控和告警

### 低优先级建议
1. **文档完善**: 更新安全相关文档
2. **培训**: 开展团队安全意识培训
3. **工具优化**: 评估和引入更多安全工具

## 合规性检查

### OWASP Top 10 对照
- [ ] A1: 注入攻击防护
- [ ] A2: 身份验证失效防护
- [ ] A3: 敏感数据暴露防护
- [ ] A4: XML外部实体防护
- [ ] A5: 访问控制失效防护
- [ ] A6: 安全配置错误防护
- [ ] A7: 跨站脚本攻击防护
- [ ] A8: 不安全反序列化防护
- [ ] A9: 已知漏洞组件防护
- [ ] A10: 不足的日志记录防护

## 持续改进建议

1. **定期扫描**: 建议每周运行一次安全扫描
2. **自动化集成**: 将安全检查集成到CI/CD流程
3. **威胁建模**: 定期更新威胁模型
4. **事件响应**: 建立安全事件响应流程

## 联系信息

如有安全问题或疑问，请联系安全团队。

---
*本报告由TradeMaster安全检查脚本自动生成*
EOF
    
    print_success "安全报告生成完成: $report_file"
    
    # 显示报告摘要
    print_info "报告摘要:"
    echo "  - 报告文件: $report_file"
    echo "  - 检查项目: $(find $report_dir -name "*.json" | wc -l) 个详细报告"
    echo "  - 建议优先处理高优先级安全问题"
    
    if command_exists code; then
        read -p "是否在VS Code中打开安全报告？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            code $report_file
        fi
    fi
}

# 主函数
main() {
    print_header "${SECURITY} TradeMaster Web Interface 安全检查"
    
    echo -e "${SHIELD} ${CYAN}开始安全检查...${NC}"
    echo ""
    
    # 创建报告目录
    create_report_dir >/dev/null
    
    local total_issues=0
    
    # 运行指定的检查
    if [ "$CHECK_DEPENDENCIES" = true ]; then
        check_dependencies_vulnerabilities
        total_issues=$((total_issues + $?))
    fi
    
    if [ "$CHECK_CODE" = true ]; then
        check_code_security
        total_issues=$((total_issues + $?))
    fi
    
    if [ "$CHECK_CONFIG" = true ]; then
        check_configuration_security
        total_issues=$((total_issues + $?))
    fi
    
    if [ "$CHECK_DOCKER" = true ]; then
        check_docker_security
        total_issues=$((total_issues + $?))
    fi
    
    if [ "$CHECK_SECRETS" = true ]; then
        check_secrets
        total_issues=$((total_issues + $?))
    fi
    
    if [ "$CHECK_PERMISSIONS" = true ]; then
        check_permissions
        total_issues=$((total_issues + $?))
    fi
    
    # 生成报告
    if [ "$GENERATE_REPORT" = true ]; then
        generate_security_report
    fi
    
    print_header "安全检查完成"
    
    if [ $total_issues -eq 0 ]; then
        print_success "安全检查完成！未发现严重安全问题 🎉"
    else
        print_warning "安全检查完成！发现 $total_issues 类安全问题需要关注"
    fi
    
    echo ""
    print_info "建议："
    echo "  - 定期运行安全检查"
    echo "  - 及时修复发现的安全问题"
    echo "  - 在CI/CD中集成安全扫描"
    echo "  - 保持依赖包更新"
    echo "  - 遵循安全最佳实践"
}

# 错误处理
trap 'print_error "安全检查脚本执行失败"; exit 1' ERR

# 运行主函数
main "$@"