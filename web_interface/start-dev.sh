#!/bin/bash
# TradeMaster Web Interface 非Docker部署启动脚本

set -e

echo "🚀 TradeMaster Web Interface 非Docker部署启动脚本"
echo "=================================================="

# 检查环境
echo "✅ 检查运行环境..."

# 检查 Node.js 和 npm/pnpm
if ! command -v node &> /dev/null; then
    echo "❌ 错误: Node.js 未安装"
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    if ! command -v npm &> /dev/null; then
        echo "❌ 错误: npm 或 pnpm 未安装"
        exit 1
    fi
    PACKAGE_MANAGER="npm"
else
    PACKAGE_MANAGER="pnpm"
fi

# 检查 Python
if ! command -v python &> /dev/null; then
    echo "❌ 错误: Python 未安装"
    exit 1
fi

# 检查 PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ 错误: PostgreSQL 未安装"
    exit 1
fi

echo "✅ 环境检查完成"
echo "   - Node.js: $(node --version)"
echo "   - 包管理器: $PACKAGE_MANAGER"
echo "   - Python: $(python --version)"
echo "   - PostgreSQL: $(psql --version | head -n1)"

# 进入项目根目录
cd "$(dirname "$0")"

# 配置前端
echo ""
echo "📦 配置前端环境..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    $PACKAGE_MANAGER install
else
    echo "前端依赖已安装"
fi

# 启动前端开发服务器
echo "启动前端开发服务器..."
$PACKAGE_MANAGER run dev &
FRONTEND_PID=$!
echo "前端服务器 PID: $FRONTEND_PID"

cd ..

# 配置后端
echo ""
echo "🐍 配置后端环境..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "激活虚拟环境并安装依赖..."
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

if [ ! -f "requirements-installed.flag" ]; then
    echo "安装后端依赖..."
    pip install -r requirements-minimal.txt
    touch requirements-installed.flag
else
    echo "后端依赖已安装"
fi

# 创建必要目录
mkdir -p logs uploads temp static media data models checkpoints exports

# 设置环境变量
export ENVIRONMENT=development
export DEBUG=true
export DATABASE_URL=postgresql://trademaster:dev_password_123@localhost:5432/trademaster_web

# 检查数据库连接（可选）
echo "检查数据库连接..."
python -c "
import asyncpg
import asyncio
async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://postgres@localhost:5432/postgres')
        await conn.close()
        print('✅ 数据库连接正常')
    except Exception as e:
        print(f'⚠️  数据库连接失败: {e}')
        print('   请确保PostgreSQL服务正在运行')
asyncio.run(test_db())
"

# 启动后端服务器
echo "启动后端开发服务器..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "后端服务器 PID: $BACKEND_PID"

cd ..

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "🔍 检查服务状态..."

# 检查前端服务
if curl -s http://localhost:3100 > /dev/null; then
    echo "✅ 前端服务正常 (http://localhost:3100)"
else
    echo "❌ 前端服务启动失败"
fi

# 检查后端服务
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务正常 (http://localhost:8000)"
else
    echo "❌ 后端服务启动失败"
fi

echo ""
echo "🎉 部署完成！"
echo "=================================================="
echo "📱 前端地址: http://localhost:3100"
echo "🔗 后端API: http://localhost:8000"
echo "📖 API文档: http://localhost:8000/docs"
echo "❤️  健康检查: http://localhost:8000/health"
echo ""
echo "📝 进程 ID:"
echo "   前端 PID: $FRONTEND_PID"
echo "   后端 PID: $BACKEND_PID"
echo ""
echo "🛑 停止服务："
echo "   kill $FRONTEND_PID $BACKEND_PID"
echo ""
echo "💡 提示："
echo "   - 确保PostgreSQL服务正在运行"
echo "   - 如需Redis功能，请安装Redis并启动服务"
echo "   - 查看日志: backend/logs/app.log"

# 保存PID到文件
echo "$FRONTEND_PID" > .frontend.pid
echo "$BACKEND_PID" > .backend.pid

echo ""
echo "按 Ctrl+C 停止所有服务..."

# 等待中断信号
trap 'echo "正在停止服务..."; kill $FRONTEND_PID $BACKEND_PID 2>/dev/null; rm -f .frontend.pid .backend.pid; exit' INT

wait