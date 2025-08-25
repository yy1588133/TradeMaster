@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo "    TradeMaster 服务停止脚本"
echo ==========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"
cd /d "%PROJECT_DIR%"

echo [INFO] 项目目录: %PROJECT_DIR%

REM 检查部署方案
set "DEPLOY_SCHEME_FILE=.deploy-scheme"
set "DEPLOY_SCHEME="

if exist "%DEPLOY_SCHEME_FILE%" (
    set /p DEPLOY_SCHEME=<%DEPLOY_SCHEME_FILE%
    echo [INFO] 检测到部署方案: !DEPLOY_SCHEME!
) else (
    echo [WARN] 未找到部署方案配置，尝试所有停止方法
    set "DEPLOY_SCHEME=all"
)

echo.
echo ==========================================
echo "    正在停止TradeMaster服务..."
echo ==========================================
echo.

if /i "!DEPLOY_SCHEME!"=="full-docker" (
    call :stop_docker_services
) else if /i "!DEPLOY_SCHEME!"=="docker-db" (
    call :stop_mixed_services
    call :stop_docker_database
) else if /i "!DEPLOY_SCHEME!"=="native" (
    call :stop_mixed_services
) else (
    echo [INFO] 尝试停止所有可能的服务...
    call :stop_all_services
)

echo.
echo ==========================================
echo "    🛑 服务停止完成"
echo ==========================================
echo.
pause
goto :eof

:stop_docker_services
echo [INFO] 停止Docker完整容器化服务...

REM 检查Docker环境
docker --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker未安装，跳过Docker服务停止
    goto :eof
)

REM 停止Docker Compose服务
if exist "docker-compose.yml" (
    echo [INFO] 停止主要Docker服务...
    docker compose down
    
    if not errorlevel 1 (
        echo [OK] Docker主服务已停止
    ) else (
        echo [WARN] Docker主服务停止时出现警告
    )
) else (
    echo [WARN] docker-compose.yml不存在，跳过主服务停止
)

REM 停止其他可能的Docker服务
call :stop_docker_database
goto :eof

:stop_docker_database
echo [INFO] 停止Docker数据库服务...

if exist "docker-compose.services.yml" (
    echo [INFO] 停止Docker数据库容器...
    docker compose -f docker-compose.services.yml down
    
    if not errorlevel 1 (
        echo [OK] Docker数据库服务已停止
    ) else (
        echo [WARN] Docker数据库服务停止时出现警告
    )
) else (
    echo [WARN] docker-compose.services.yml不存在，跳过数据库服务停止
)
goto :eof

:stop_mixed_services
echo [INFO] 停止前后端本地服务...

REM 查找并关闭前后端进程
echo [INFO] 查找TradeMaster相关进程...

REM 通过窗口标题关闭前后端服务
taskkill /FI "WINDOWTITLE:TradeMaster Frontend*" /F >nul 2>&1
if not errorlevel 1 (
    echo [OK] 前端服务已停止
) else (
    echo [WARN] 未找到前端服务进程或停止失败
)

taskkill /FI "WINDOWTITLE:TradeMaster Backend*" /F >nul 2>&1
if not errorlevel 1 (
    echo [OK] 后端服务已停止
) else (
    echo [WARN] 未找到后端服务进程或停止失败
)

REM 尝试通过端口关闭服务
echo [INFO] 检查端口占用情况...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do (
    echo [INFO] 停止占用端口3000的进程 %%a
    taskkill /PID %%a /F >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo [INFO] 停止占用端口8000的进程 %%a
    taskkill /PID %%a /F >nul 2>&1
)

goto :eof

:stop_all_services
echo [INFO] 停止所有可能的TradeMaster服务...

REM 停止Docker服务
call :stop_docker_services

REM 停止本地服务
call :stop_mixed_services

REM 停止Windows原生数据库服务（如果正在运行）
echo [INFO] 检查Windows原生数据库服务...

sc query postgresql-x64-14 2>nul | find "RUNNING" >nul
if not errorlevel 1 (
    echo [INFO] 停止PostgreSQL服务...
    net stop postgresql-x64-14 >nul 2>&1
    if not errorlevel 1 (
        echo [OK] PostgreSQL服务已停止
    ) else (
        echo [WARN] PostgreSQL服务停止失败（可能需要管理员权限）
    )
) else (
    echo [INFO] PostgreSQL服务未在运行
)

sc query Redis 2>nul | find "RUNNING" >nul
if not errorlevel 1 (
    echo [INFO] 停止Redis服务...
    net stop Redis >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Redis服务已停止
    ) else (
        echo [WARN] Redis服务停止失败（可能需要管理员权限）
    )
) else (
    echo [INFO] Redis服务未在运行
)

echo [OK] 所有服务停止操作完成
goto :eof