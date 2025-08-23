@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo  TradeMaster 智能端口检测启动脚本
echo ==========================================
echo.

REM 设置项目目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"
cd /d "%PROJECT_DIR%"

echo [INFO] 项目目录: %PROJECT_DIR%

REM 验证项目结构
if not exist "frontend" (
    echo [ERROR] 前端目录未找到
    pause
    exit /b 1
)
if not exist "backend" (
    echo [ERROR] 后端目录未找到
    pause
    exit /b 1
)

echo.
echo ==========================================
echo [步骤 1/3] 智能端口检测
echo ==========================================

REM 检测可用的后端端口 (从8000开始)
set BACKEND_PORT=8000
:check_backend_port
netstat -ano | findstr ":!BACKEND_PORT!" >nul 2>&1
if errorlevel 1 (
    echo [OK] 后端端口 !BACKEND_PORT! 可用
    goto check_frontend_port
) else (
    echo [WARN] 端口 !BACKEND_PORT! 被占用，尝试下一个端口...
    set /a BACKEND_PORT+=1
    if !BACKEND_PORT! GTR 8010 (
        echo [ERROR] 8000-8010端口范围内没有可用端口
        pause
        exit /b 1
    )
    goto check_backend_port
)

:check_frontend_port
REM 检测可用的前端端口 (从3000开始)
set FRONTEND_PORT=3000
:check_frontend_port_loop
netstat -ano | findstr ":!FRONTEND_PORT!" >nul 2>&1
if errorlevel 1 (
    echo [OK] 前端端口 !FRONTEND_PORT! 可用
    goto create_env_files
) else (
    echo [WARN] 端口 !FRONTEND_PORT! 被占用，尝试下一个端口...
    set /a FRONTEND_PORT+=1
    if !FRONTEND_PORT! GTR 3010 (
        echo [ERROR] 3000-3010端口范围内没有可用端口
        pause
        exit /b 1
    )
    goto check_frontend_port_loop
)

:create_env_files
echo.
echo ==========================================
echo [步骤 2/3] 生成动态环境配置
echo ==========================================

REM 创建前端环境变量文件
echo [INFO] 生成前端环境配置 (.env.local)
cd /d "%PROJECT_DIR%\frontend"

(
echo # TradeMaster 动态生成的环境配置
echo # 生成时间: %date% %time%
echo.
echo # 开发环境API配置
echo VITE_API_BASE_URL=http://localhost:!BACKEND_PORT!/api/v1
echo VITE_WS_URL=ws://localhost:!BACKEND_PORT!/ws
echo VITE_API_TIMEOUT=30000
echo.
echo # 开发调试配置
echo VITE_DEBUG=true
echo VITE_DEBUG_API=true
echo NODE_ENV=development
echo VITE_APP_ENV=development
echo.
echo # 应用基础配置
echo VITE_APP_NAME=TradeMaster Web
echo VITE_APP_VERSION=1.0.0
echo.
echo # 端口信息 ^(注释^)
echo # 后端端口: !BACKEND_PORT!
echo # 前端端口: !FRONTEND_PORT!
) > .env.local

echo [OK] 前端环境配置已生成: frontend\.env.local

echo.
echo ==========================================
echo [步骤 3/3] 启动服务
echo ==========================================

REM 启动前端服务
echo [INFO] 启动前端服务 (端口: !FRONTEND_PORT!)
start "TradeMaster Frontend" cmd /k "cd /d "%PROJECT_DIR%\frontend" && set PORT=!FRONTEND_PORT! && npm run dev"

REM 等待前端服务启动
timeout /t 3 /nobreak >nul

REM 启动后端服务
cd /d "%PROJECT_DIR%\backend"
echo [INFO] 当前后端目录: %CD%

REM 检测入口点
set MAIN_MODULE=
if exist "app\main.py" (
    echo [OK] 使用生产入口点: app\main.py
    set MAIN_MODULE=app.main:app
) else if exist "dev_main.py" (
    echo [OK] 使用开发入口点: dev_main.py
    set MAIN_MODULE=dev_main:app
) else if exist "simple_main.py" (
    echo [OK] 使用测试入口点: simple_main.py
    set MAIN_MODULE=simple_main:app
) else (
    echo [ERROR] 未找到有效的后端入口点
    pause
    exit /b 1
)

echo [INFO] 启动后端服务 (端口: !BACKEND_PORT!)
start "TradeMaster Backend" cmd /k "cd /d "%CD%" && call .venv\Scripts\activate.bat && uvicorn !MAIN_MODULE! --reload --host 0.0.0.0 --port !BACKEND_PORT!"

echo.
echo ==========================================
echo     🎉 TradeMaster 服务已启动
echo ==========================================
echo.
echo  📊 前端界面:  http://localhost:!FRONTEND_PORT!
echo  🔧 后端API:   http://localhost:!BACKEND_PORT!
echo  📚 API文档:   http://localhost:!BACKEND_PORT!/api/v1/docs
echo  💾 环境配置:  frontend\.env.local
echo.
echo  ✅ 前后端服务在独立窗口中运行
echo  🔄 等待30-60秒完成初始化
echo  🛑 关闭服务窗口可停止服务
echo  🔧 如需重新检测端口，请重新运行此脚本
echo.

REM 显示配置信息
echo ==========================================
echo     📋 当前配置信息
echo ==========================================
echo.
echo  🔌 检测到的可用端口:
echo     - 后端端口: !BACKEND_PORT!
echo     - 前端端口: !FRONTEND_PORT!
echo.
echo  📁 生成的配置文件:
echo     - frontend\.env.local (动态生成)
echo.
echo  🚀 服务状态:
echo     - 前端: 启动中... (约15秒完成)
echo     - 后端: 启动中... (约10秒完成)
echo.

echo [SUCCESS] TradeMaster Web界面智能启动完成！
pause