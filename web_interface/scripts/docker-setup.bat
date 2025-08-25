@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo     TradeMaster Docker 数据库服务启动
echo ==========================================
echo.

REM 设置工作目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"
cd /d "%PROJECT_DIR%"

echo [INFO] 项目目录: %PROJECT_DIR%

REM 检查Docker环境
echo.
echo ==========================================
echo [步骤 1/4] Docker 环境检查
echo ==========================================

REM 检查Docker Desktop是否运行
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop 未运行或未安装
    echo.
    echo 请确保:
    echo 1. 已安装 Docker Desktop
    echo 2. Docker Desktop 正在运行
    echo 3. 当前用户有权限访问Docker
    echo.
    echo Docker Desktop 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [OK] Docker Desktop 运行正常
docker version --format "Docker版本: {{.Server.Version}}"

REM 检查Docker Compose
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose 不可用
    pause
    exit /b 1
)

echo [OK] Docker Compose 可用
docker compose version

echo.
echo ==========================================
echo [步骤 2/4] 端口冲突检查
echo ==========================================

REM 检查PostgreSQL端口15432
netstat -ano | findstr ":15432" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] 端口15432已被占用，检查占用进程...
    netstat -ano | findstr ":15432"
    echo.
    echo 是否停止现有Docker服务? (Y/N)
    set /p choice=
    if /i "!choice!"=="Y" (
        echo [INFO] 停止现有Docker服务...
        docker compose -f docker-compose.services.yml down 2>nul
    ) else (
        echo [ERROR] 端口冲突，无法启动服务
        pause
        exit /b 1
    )
)

REM 检查Redis端口16379
netstat -ano | findstr ":16379" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] 端口16379已被占用，将尝试停止现有服务
    docker compose -f docker-compose.services.yml down 2>nul
)

echo [OK] 端口检查完成

echo.
echo ==========================================
echo [步骤 3/4] 数据目录准备
echo ==========================================

REM 创建数据目录
if not exist "data" mkdir data
if not exist "data\postgresql" mkdir data\postgresql
if not exist "data\redis" mkdir data\redis

echo [OK] 数据目录创建: %PROJECT_DIR%\data

REM 设置环境变量
set "POSTGRES_PASSWORD=TradeMaster2024!"
set "REDIS_PASSWORD=TradeMaster2024!"

echo [INFO] 环境变量设置完成

echo.
echo ==========================================
echo [步骤 4/4] 启动 Docker 服务
echo ==========================================

REM 启动数据库服务
echo [INFO] 启动PostgreSQL + Redis服务...
docker compose -f docker-compose.services.yml up -d

if errorlevel 1 (
    echo [ERROR] Docker服务启动失败
    echo.
    echo 查看错误日志:
    docker compose -f docker-compose.services.yml logs
    pause
    exit /b 1
)

echo [OK] Docker服务启动成功

REM 等待服务启动
echo.
echo [INFO] 等待服务初始化 (30秒)...
timeout /t 30 /nobreak >nul

echo.
echo ==========================================
echo [步骤 5/4] 服务健康检查
echo ==========================================

REM 检查PostgreSQL健康状态
echo [INFO] 检查PostgreSQL连接...
docker exec trademaster_postgresql pg_isready -U trademaster -d trademaster_web >nul 2>&1
if errorlevel 1 (
    echo [WARN] PostgreSQL服务未就绪，等待更长时间...
    timeout /t 15 /nobreak >nul
    docker exec trademaster_postgresql pg_isready -U trademaster -d trademaster_web >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] PostgreSQL服务启动失败
        echo 查看日志: docker compose -f docker-compose.services.yml logs postgresql
        pause
        exit /b 1
    )
)
echo [OK] PostgreSQL服务正常

REM 检查Redis健康状态
echo [INFO] 检查Redis连接...
docker exec trademaster_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Redis服务启动失败
    echo 查看日志: docker compose -f docker-compose.services.yml logs redis
    pause
    exit /b 1
)
echo [OK] Redis服务正常

echo.
echo ==========================================
echo     🎉 Docker数据库服务启动完成
echo ==========================================
echo.
echo  📊 服务状态:
echo     PostgreSQL: localhost:15432
echo     Redis:      localhost:16379
echo.
echo  🔧 管理命令:
echo     停止服务: docker compose -f docker-compose.services.yml down
echo     查看日志: docker compose -f docker-compose.services.yml logs
echo     重启服务: docker compose -f docker-compose.services.yml restart
echo.
echo  📁 数据目录: %PROJECT_DIR%\data
echo  📝 配置文件: .env.docker
echo.
echo  ✅ 数据库服务已就绪，可以启动后端应用
echo.

REM 显示容器状态
echo ==========================================
echo     📋 Docker 容器状态
echo ==========================================
docker compose -f docker-compose.services.yml ps

echo.
echo [INFO] Docker数据库服务配置完成！
echo [INFO] 请使用 .env.docker 配置启动后端应用
echo.

pause