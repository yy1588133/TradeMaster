@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 🚀 TradeMaster Web Interface 非Docker部署启动脚本
echo ==================================================

echo ✅ 检查运行环境...

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Node.js 未安装
    pause
    exit /b 1
)

REM 检查包管理器
pnpm --version >nul 2>&1
if errorlevel 1 (
    npm --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ 错误: npm 或 pnpm 未安装
        pause
        exit /b 1
    ) else (
        set PACKAGE_MANAGER=npm
    )
) else (
    set PACKAGE_MANAGER=pnpm
)

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Python 未安装
    pause
    exit /b 1
)

REM PostgreSQL检查跳过 - 使用简化版后端
echo ⚠️  跳过PostgreSQL检查（使用简化版后端）

echo ✅ 环境检查完成
for /f "tokens=*" %%i in ('node --version') do echo    - Node.js: %%i
echo    - 包管理器: !PACKAGE_MANAGER!
for /f "tokens=*" %%i in ('python --version') do echo    - Python: %%i

REM 进入项目根目录
cd /d "%~dp0"

echo.
echo 📦 配置前端环境...
cd frontend

if not exist "node_modules" (
    echo 安装前端依赖...
    !PACKAGE_MANAGER! install
) else (
    echo 前端依赖已安装
)

echo 启动前端开发服务器...
start "TradeMaster Frontend" cmd /c "!PACKAGE_MANAGER! run dev"

cd ..

echo.
echo 🐍 配置后端环境...
cd backend

REM 创建虚拟环境
if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
)

echo 激活虚拟环境...
call venv\Scripts\activate.bat

if not exist "requirements-installed.flag" (
    echo 安装后端依赖...
    pip install -r requirements-minimal.txt
    echo. > requirements-installed.flag
) else (
    echo 后端依赖已安装
)

REM 创建必要目录
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "temp" mkdir temp
if not exist "static" mkdir static
if not exist "media" mkdir media
if not exist "data" mkdir data
if not exist "models" mkdir models
if not exist "checkpoints" mkdir checkpoints
if not exist "exports" mkdir exports

REM 设置环境变量
set ENVIRONMENT=development
set DEBUG=true
set DATABASE_URL=postgresql://trademaster:dev_password_123@localhost:5432/trademaster_web

echo 数据库连接跳过 - 使用简化版后端

echo 启动简化版后端开发服务器...
start "TradeMaster Backend" cmd /c "call venv\Scripts\activate.bat && uvicorn simple_main:app --reload --host 0.0.0.0 --port 8000"

cd ..

echo.
echo ⏳ 等待服务启动...
timeout /t 8 /nobreak >nul

echo.
echo 🔍 检查服务状态...

REM 检查前端服务 - 改进的检测方式
echo 检查前端服务状态...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:3100' -TimeoutSec 5 -UseBasicParsing; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  前端服务可能还在启动中，请稍后在浏览器中访问 http://localhost:3100
) else (
    echo ✅ 前端服务正常 (http://localhost:3100)
)

REM 检查后端服务 - 改进的检测方式
echo 检查后端服务状态...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5 -UseBasicParsing; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  后端服务可能还在启动中，请稍后访问 http://localhost:8000/health
) else (
    echo ✅ 后端服务正常 (http://localhost:8000)
)

echo.
echo 🎉 部署完成！
echo ==================================================
echo 📱 前端地址: http://localhost:3100
echo 🔗 后端API: http://localhost:8000
echo 📖 API文档: http://localhost:8000/docs
echo ❤️  健康检查: http://localhost:8000/health
echo.
echo 💡 提示：
echo    - 使用简化版后端，无需PostgreSQL
echo    - 前端和后端在独立窗口中运行
echo    - 关闭对应窗口即可停止服务
echo    - 如遇问题，请检查对应窗口的错误信息
echo.

pause