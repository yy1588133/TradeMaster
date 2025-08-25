@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo   TradeMaster Windows原生数据库服务安装
echo ==========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 此脚本需要管理员权限运行
    echo.
    echo 请右键点击脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo [OK] 已获得管理员权限

REM 设置工作目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"
cd /d "%PROJECT_DIR%"

echo [INFO] 项目目录: %PROJECT_DIR%

echo.
echo ==========================================
echo [步骤 1/5] 包管理器检查和安装
echo ==========================================

REM 检查Chocolatey是否已安装
where choco >nul 2>&1
if errorlevel 1 (
    echo [INFO] Chocolatey 未安装，正在安装...
    
    REM 安装Chocolatey
    powershell -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    
    if errorlevel 1 (
        echo [ERROR] Chocolatey 安装失败
        echo.
        echo 请手动安装Chocolatey或使用Docker方案
        echo 访问: https://chocolatey.org/install
        pause
        exit /b 1
    )
    
    REM 刷新环境变量
    call refreshenv
    
    REM 再次检查
    where choco >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Chocolatey 安装后仍不可用，请重启命令行
        pause
        exit /b 1
    )
) else (
    echo [OK] Chocolatey 已安装
)

choco --version

echo.
echo ==========================================
echo [步骤 2/5] PostgreSQL 服务安装
echo ==========================================

REM 检查PostgreSQL是否已安装
sc query postgresql-x64-14 >nul 2>&1
if not errorlevel 1 (
    echo [OK] PostgreSQL 服务已存在
    sc query postgresql-x64-14 | find "RUNNING" >nul
    if not errorlevel 1 (
        echo [OK] PostgreSQL 服务正在运行
        goto check_redis
    ) else (
        echo [INFO] 启动 PostgreSQL 服务...
        net start postgresql-x64-14
        goto check_redis
    )
)

REM 检查是否已通过Chocolatey安装
where psql >nul 2>&1
if not errorlevel 1 (
    echo [OK] PostgreSQL 已安装，检查服务状态...
    REM 尝试启动现有服务
    net start postgresql* >nul 2>&1
    goto check_redis
)

echo [INFO] 安装 PostgreSQL...
choco install postgresql14 --params '/Password:TradeMaster2024!' -y

if errorlevel 1 (
    echo [ERROR] PostgreSQL 安装失败
    echo.
    echo 请检查网络连接或手动安装PostgreSQL
    pause
    exit /b 1
)

echo [OK] PostgreSQL 安装完成

REM 等待服务启动
timeout /t 10 /nobreak >nul

REM 启动PostgreSQL服务
net start postgresql-x64-14 >nul 2>&1
if errorlevel 1 (
    echo [WARN] PostgreSQL 服务启动失败，尝试手动启动...
    sc start postgresql-x64-14 >nul 2>&1
)

:check_redis
echo.
echo ==========================================
echo [步骤 3/5] Redis 服务安装
echo ==========================================

REM 检查Redis是否已安装
sc query Redis >nul 2>&1
if not errorlevel 1 (
    echo [OK] Redis 服务已存在
    sc query Redis | find "RUNNING" >nul
    if not errorlevel 1 (
        echo [OK] Redis 服务正在运行
        goto configure_db
    ) else (
        echo [INFO] 启动 Redis 服务...
        net start Redis
        goto configure_db
    )
)

REM 检查是否已通过Chocolatey安装
where redis-server >nul 2>&1
if not errorlevel 1 (
    echo [OK] Redis 已安装，检查服务状态...
    net start Redis* >nul 2>&1
    goto configure_db
)

echo [INFO] 安装 Redis...
choco install redis-64 -y

if errorlevel 1 (
    echo [ERROR] Redis 安装失败
    echo.
    echo 请检查网络连接或手动安装Redis
    pause
    exit /b 1
)

echo [OK] Redis 安装完成

REM 等待服务启动
timeout /t 5 /nobreak >nul

REM 启动Redis服务
net start Redis >nul 2>&1
if errorlevel 1 (
    echo [WARN] Redis 服务启动失败，尝试手动启动...
    sc start Redis >nul 2>&1
)

:configure_db
echo.
echo ==========================================
echo [步骤 4/5] 数据库配置
echo ==========================================

REM 等待PostgreSQL完全启动
echo [INFO] 等待PostgreSQL服务完全启动...
timeout /t 15 /nobreak >nul

REM 配置PostgreSQL数据库和用户
echo [INFO] 配置PostgreSQL数据库...

REM 创建数据库和用户的SQL脚本
echo CREATE DATABASE trademaster_web; > temp_init.sql
echo CREATE USER trademaster WITH PASSWORD 'TradeMaster2024!'; >> temp_init.sql
echo GRANT ALL PRIVILEGES ON DATABASE trademaster_web TO trademaster; >> temp_init.sql
echo ALTER USER trademaster CREATEDB; >> temp_init.sql

REM 执行数据库初始化
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -d postgres -f temp_init.sql >nul 2>&1
if errorlevel 1 (
    echo [WARN] 数据库初始化失败，可能已存在
) else (
    echo [OK] 数据库初始化完成
)

REM 清理临时文件
del temp_init.sql >nul 2>&1

REM 测试数据库连接
echo [INFO] 测试数据库连接...
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U trademaster -d trademaster_web -c "SELECT version();" >nul 2>&1
if errorlevel 1 (
    echo [WARN] 数据库连接测试失败，请检查配置
) else (
    echo [OK] 数据库连接正常
)

REM 配置Redis密码
echo [INFO] 配置Redis认证...
redis-cli config set requirepass "TradeMaster2024!" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Redis密码设置失败
) else (
    echo [OK] Redis密码配置完成
)

echo.
echo ==========================================
echo [步骤 5/5] 服务验证和配置文件生成
echo ==========================================

REM 验证服务状态
echo [INFO] 验证服务状态...

REM 检查PostgreSQL
sc query postgresql-x64-14 | find "RUNNING" >nul
if not errorlevel 1 (
    echo [OK] PostgreSQL 服务运行正常
) else (
    echo [ERROR] PostgreSQL 服务未运行
)

REM 检查Redis
sc query Redis | find "RUNNING" >nul
if not errorlevel 1 (
    echo [OK] Redis 服务运行正常
) else (
    echo [ERROR] Redis 服务未运行
)

REM 创建Windows原生配置文件
echo [INFO] 生成配置文件...
cd /d "%PROJECT_DIR%\.."

REM 生成.env.native配置文件
(
echo # ==================== TradeMaster Windows原生环境配置 ====================
echo # Windows原生服务配置，使用标准端口
echo.
echo # ==================== 基础应用配置 ====================
echo APP_NAME=TradeMaster Web Backend
echo APP_VERSION=1.0.0
echo DEBUG=true
echo LOG_LEVEL=INFO
echo ENVIRONMENT=development
echo.
echo # ==================== 服务器配置 ====================
echo SERVER_HOST=0.0.0.0
echo SERVER_PORT=8000
echo API_V1_STR=/api/v1
echo.
echo # ==================== PostgreSQL 数据库配置 ^(Windows原生^) ====================
echo # 使用Windows原生PostgreSQL服务
echo DATABASE_URL=postgresql+asyncpg://trademaster:TradeMaster2024!@localhost:5432/trademaster_web
echo DB_HOST=localhost
echo DB_PORT=5432
echo DB_USER=trademaster
echo DB_PASSWORD=TradeMaster2024!
echo DB_NAME=trademaster_web
echo.
echo # 数据库连接池配置
echo DB_POOL_SIZE=15
echo DB_MAX_OVERFLOW=25
echo DB_POOL_TIMEOUT=30
echo DB_POOL_RECYCLE=3600
echo DB_ECHO=false
echo.
echo # ==================== Redis 缓存配置 ^(Windows原生^) ====================
echo # 使用Windows原生Redis服务
echo REDIS_URL=redis://:TradeMaster2024!@localhost:6379/0
echo REDIS_HOST=localhost
echo REDIS_PORT=6379
echo REDIS_DB=0
echo REDIS_PASSWORD=TradeMaster2024!
echo REDIS_SSL=false
echo.
echo # Redis连接池配置
echo REDIS_MAX_CONNECTIONS=25
echo REDIS_CONNECTION_TIMEOUT=10
echo REDIS_SOCKET_TIMEOUT=10
echo.
echo # 缓存策略配置
echo CACHE_DEFAULT_EXPIRE=3600
echo CACHE_PREFIX=trademaster:native:
echo CACHE_ENABLED=true
echo.
echo # ==================== JWT 安全配置 ====================
echo SECRET_KEY=native_development_secret_key_change_in_production_very_long_and_secure
echo ALGORITHM=HS256
echo ACCESS_TOKEN_EXPIRE_MINUTES=60
echo REFRESH_TOKEN_EXPIRE_DAYS=7
echo.
echo # ==================== CORS 配置 ====================
echo BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://127.0.0.1:3000","http://127.0.0.1:3001"]
echo CORS_ALLOW_CREDENTIALS=true
echo.
echo # ==================== Celery 异步任务配置 ^(Windows原生^) ====================
echo CELERY_BROKER_URL=redis://:TradeMaster2024!@localhost:6379/2
echo CELERY_RESULT_BACKEND=redis://:TradeMaster2024!@localhost:6379/3
echo CELERY_TASK_SERIALIZER=json
echo CELERY_RESULT_SERIALIZER=json
echo.
echo # ==================== TradeMaster 集成配置 ====================
echo TRADEMASTER_API_URL=http://localhost:8080
echo TRADEMASTER_API_TIMEOUT=300
echo TRADEMASTER_API_RETRY_ATTEMPTS=3
echo.
echo # ==================== 开发调试配置 ====================
echo AUTO_RELOAD=true
echo SHOW_ERROR_DETAILS=true
echo ENABLE_API_DOCS=true
echo ENABLE_SWAGGER_UI=true
echo ENABLE_REDOC=true
echo.
echo # ==================== Windows原生特定配置 ====================
echo WINDOWS_NATIVE_DEPLOYMENT=true
echo POSTGRESQL_SERVICE_NAME=postgresql-x64-14
echo REDIS_SERVICE_NAME=Redis
echo.
echo # 服务管理配置
echo AUTO_START_SERVICES=true
echo SERVICE_STARTUP_TIMEOUT=30
echo.
echo # ==================== 文件路径配置 ====================
echo UPLOAD_DIR=uploads
echo DATA_DIR=data  
echo MODEL_DIR=models
echo LOG_DIR=logs
echo MAX_UPLOAD_SIZE=104857600
echo.
echo # ==================== 监控配置 ====================
echo ENABLE_METRICS=true
echo METRICS_PORT=9090
echo HEALTH_CHECK_ENABLED=true
echo SENTRY_ENABLED=false
) > backend\.env.native

echo [OK] 配置文件生成: backend\.env.native

echo.
echo ==========================================
echo     🎉 Windows原生数据库服务安装完成
echo ==========================================
echo.
echo  📊 服务状态:
echo     PostgreSQL: localhost:5432 ^(原生服务^)
echo     Redis:      localhost:6379 ^(原生服务^)
echo.
echo  🔧 Windows服务管理:
echo     PostgreSQL服务名: postgresql-x64-14
echo     Redis服务名:      Redis
echo.
echo  💡 管理命令:
echo     启动PostgreSQL: net start postgresql-x64-14
echo     停止PostgreSQL: net stop postgresql-x64-14
echo     启动Redis:      net start Redis  
echo     停止Redis:      net stop Redis
echo.
echo  📝 配置文件: backend\.env.native
echo  🔑 数据库凭据: trademaster / TradeMaster2024!
echo.
echo  ✅ 原生数据库服务已就绪，可以启动后端应用
echo.

REM 设置服务自启动
echo [INFO] 配置服务自启动...
sc config postgresql-x64-14 start= auto >nul 2>&1
sc config Redis start= auto >nul 2>&1
echo [OK] 服务自启动配置完成

echo.
echo ==========================================
echo     📋 Windows 服务状态
echo ==========================================
sc query postgresql-x64-14
echo.
sc query Redis

echo.
echo [SUCCESS] Windows原生数据库服务配置完成！
echo [INFO] 请使用 .env.native 配置启动后端应用
pause