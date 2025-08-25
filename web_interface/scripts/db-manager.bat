@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo      TradeMaster 数据库管理工具
echo ==========================================
echo.

REM 设置工作目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

echo [INFO] 项目目录: %PROJECT_DIR%

REM 读取当前数据库方案
set "DB_SCHEME_FILE=.db-scheme"
set "DB_SCHEME="

if exist "%DB_SCHEME_FILE%" (
    set /p DB_SCHEME=<%DB_SCHEME_FILE%
    echo [INFO] 当前数据库方案: !DB_SCHEME!
) else (
    echo [WARN] 未检测到数据库方案配置
    echo [INFO] 请先运行 quick-start.bat 选择数据库方案
    pause
    exit /b 1
)

:main_menu
echo.
echo ==========================================
echo         数据库管理菜单
echo ==========================================
echo.
echo  当前方案: !DB_SCHEME!
echo.
echo [1] 📊 查看数据库状态
echo [2] 🔄 重启数据库服务  
echo [3] 🛑 停止数据库服务
echo [4] 🚀 启动数据库服务
echo [5] 📋 查看数据库日志
echo [6] 🔧 数据库连接测试
echo [7] 💾 数据备份
echo [8] 📥 数据恢复
echo [9] 🧹 清理数据库数据
echo [0] 🔄 切换数据库方案
echo [Q] 退出
echo.
set /p menu_choice="请选择操作 (1-9/0/Q): "

if /i "!menu_choice!"=="1" goto :check_database_status
if /i "!menu_choice!"=="2" goto :restart_database
if /i "!menu_choice!"=="3" goto :stop_database
if /i "!menu_choice!"=="4" goto :start_database
if /i "!menu_choice!"=="5" goto :view_database_logs
if /i "!menu_choice!"=="6" goto :test_database_connection
if /i "!menu_choice!"=="7" goto :backup_database
if /i "!menu_choice!"=="8" goto :restore_database
if /i "!menu_choice!"=="9" goto :clean_database
if /i "!menu_choice!"=="0" goto :switch_database_scheme
if /i "!menu_choice!"=="Q" goto :exit

echo [ERROR] 无效选择，请重新选择
goto :main_menu

:check_database_status
echo.
echo ==========================================
echo [1] 查看数据库状态
echo ==========================================

if /i "!DB_SCHEME!"=="docker" (
    call :check_docker_status
) else if /i "!DB_SCHEME!"=="native" (
    call :check_native_status
) else (
    echo [ERROR] 未知的数据库方案: !DB_SCHEME!
)

pause
goto :main_menu

:restart_database
echo.
echo ==========================================
echo [2] 重启数据库服务
echo ==========================================

echo [WARN] 重启数据库服务将暂时中断连接，是否继续? (Y/N)
set /p confirm=
if /i not "!confirm!"=="Y" goto :main_menu

if /i "!DB_SCHEME!"=="docker" (
    call :restart_docker_database
) else if /i "!DB_SCHEME!"=="native" (
    call :restart_native_database
) else (
    echo [ERROR] 未知的数据库方案: !DB_SCHEME!
)

pause
goto :main_menu

:stop_database
echo.
echo ==========================================
echo [3] 停止数据库服务
echo ==========================================

echo [WARN] 停止数据库服务将中断所有连接，是否继续? (Y/N)
set /p confirm=
if /i not "!confirm!"=="Y" goto :main_menu

if /i "!DB_SCHEME!"=="docker" (
    call :stop_docker_database
) else if /i "!DB_SCHEME!"=="native" (
    call :stop_native_database
) else (
    echo [ERROR] 未知的数据库方案: !DB_SCHEME!
)

pause
goto :main_menu

:start_database
echo.
echo ==========================================
echo [4] 启动数据库服务
echo ==========================================

if /i "!DB_SCHEME!"=="docker" (
    call :start_docker_database
) else if /i "!DB_SCHEME!"=="native" (
    call :start_native_database
) else (
    echo [ERROR] 未知的数据库方案: !DB_SCHEME!
)

pause
goto :main_menu

:view_database_logs
echo.
echo ==========================================
echo [5] 查看数据库日志
echo ==========================================

if /i "!DB_SCHEME!"=="docker" (
    call :view_docker_logs
) else if /i "!DB_SCHEME!"=="native" (
    call :view_native_logs
) else (
    echo [ERROR] 未知的数据库方案: !DB_SCHEME!
)

pause
goto :main_menu

:test_database_connection
echo.
echo ==========================================
echo [6] 数据库连接测试
echo ==========================================

call :test_connection
pause
goto :main_menu

:backup_database
echo.
echo ==========================================
echo [7] 数据备份
echo ==========================================

echo [INFO] 开始数据库备份...

REM 创建备份目录
set "BACKUP_DIR=data\backups"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 生成备份文件名 (包含时间戳)
for /f "tokens=2 delims==." %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "MIN=%dt:~10,2%"
set "SS=%dt:~12,2%"
set "TIMESTAMP=%YYYY%-%MM%-%DD%_%HH%-%MIN%-%SS%"

if /i "!DB_SCHEME!"=="docker" (
    call :backup_docker_database
) else if /i "!DB_SCHEME!"=="native" (
    call :backup_native_database
) else (
    echo [ERROR] 未知的数据库方案: !DB_SCHEME!
)

pause
goto :main_menu

:restore_database
echo.
echo ==========================================
echo [8] 数据恢复
echo ==========================================

echo [WARN] 数据恢复将覆盖现有数据，请确保已备份重要数据
echo [WARN] 是否继续数据恢复? (Y/N)
set /p confirm=
if /i not "!confirm!"=="Y" goto :main_menu

REM 列出可用的备份文件
echo [INFO] 可用的备份文件:
dir /b "data\backups\*.sql" 2>nul
if errorlevel 1 (
    echo [ERROR] 未找到备份文件
    goto :main_menu
)

echo.
set /p backup_file="请输入备份文件名 (不含路径): "

if not exist "data\backups\%backup_file%" (
    echo [ERROR] 备份文件不存在: %backup_file%
    goto :main_menu
)

if /i "!DB_SCHEME!"=="docker" (
    call :restore_docker_database
) else if /i "!DB_SCHEME!"=="native" (
    call :restore_native_database
) else (
    echo [ERROR] 未知的数据库方案: !DB_SCHEME!
)

pause
goto :main_menu

:clean_database
echo.
echo ==========================================
echo [9] 清理数据库数据
echo ==========================================

echo [WARN] 此操作将删除所有数据库数据，无法恢复！
echo [WARN] 请确保已备份重要数据
echo [WARN] 是否继续清理数据库? (Y/N)
set /p confirm=
if /i not "!confirm!"=="Y" goto :main_menu

echo [WARN] 最后确认：真的要清理所有数据吗? 输入 "DELETE" 确认:
set /p final_confirm=
if not "!final_confirm!"=="DELETE" (
    echo [INFO] 操作已取消
    goto :main_menu
)

if /i "!DB_SCHEME!"=="docker" (
    call :clean_docker_database
) else if /i "!DB_SCHEME!"=="native" (
    call :clean_native_database
) else (
    echo [ERROR] 未知的数据库方案: !DB_SCHEME!
)

pause
goto :main_menu

:switch_database_scheme
echo.
echo ==========================================
echo [0] 切换数据库方案
echo ==========================================

echo [INFO] 当前方案: !DB_SCHEME!
echo.
echo 切换数据库方案需要:
echo 1. 停止当前数据库服务
echo 2. 备份现有数据 (推荐)
echo 3. 配置新方案的数据库服务
echo.
echo 是否继续切换? (Y/N)
set /p confirm=
if /i not "!confirm!"=="Y" goto :main_menu

REM 停止当前服务
echo [INFO] 停止当前数据库服务...
if /i "!DB_SCHEME!"=="docker" (
    call :stop_docker_database
) else if /i "!DB_SCHEME!"=="native" (
    call :stop_native_database
)

REM 删除方案选择文件，强制重新选择
if exist "%DB_SCHEME_FILE%" del "%DB_SCHEME_FILE%"

echo [INFO] 请重新运行 quick-start.bat 选择新的数据库方案
pause
goto :exit

:check_docker_status
echo [INFO] 检查Docker容器状态...
docker compose -f docker-compose.services.yml ps
echo.
echo [INFO] Docker容器资源使用情况:
docker stats --no-stream trademaster_postgresql trademaster_redis 2>nul
goto :eof

:check_native_status
echo [INFO] 检查Windows服务状态...
echo.
echo PostgreSQL服务状态:
sc query postgresql-x64-14
echo.
echo Redis服务状态:
sc query Redis
echo.
echo [INFO] 端口占用情况:
netstat -ano | findstr ":5432"
netstat -ano | findstr ":6379"
goto :eof

:restart_docker_database
echo [INFO] 重启Docker数据库服务...
docker compose -f docker-compose.services.yml restart
echo [OK] Docker数据库服务重启完成
goto :eof

:restart_native_database
echo [INFO] 重启PostgreSQL服务...
net stop postgresql-x64-14 >nul 2>&1
timeout /t 3 /nobreak >nul
net start postgresql-x64-14

echo [INFO] 重启Redis服务...
net stop Redis >nul 2>&1
timeout /t 2 /nobreak >nul
net start Redis

echo [OK] Windows原生数据库服务重启完成
goto :eof

:stop_docker_database
echo [INFO] 停止Docker数据库服务...
docker compose -f docker-compose.services.yml stop
echo [OK] Docker数据库服务已停止
goto :eof

:stop_native_database
echo [INFO] 停止PostgreSQL服务...
net stop postgresql-x64-14

echo [INFO] 停止Redis服务...
net stop Redis

echo [OK] Windows原生数据库服务已停止
goto :eof

:start_docker_database
echo [INFO] 启动Docker数据库服务...
docker compose -f docker-compose.services.yml up -d
echo [OK] Docker数据库服务已启动

REM 等待服务就绪
echo [INFO] 等待服务就绪...
timeout /t 15 /nobreak >nul
goto :eof

:start_native_database
echo [INFO] 启动PostgreSQL服务...
net start postgresql-x64-14

echo [INFO] 启动Redis服务...
net start Redis

echo [OK] Windows原生数据库服务已启动
goto :eof

:view_docker_logs
echo [INFO] Docker容器日志 (最近50行):
echo.
echo === PostgreSQL日志 ===
docker compose -f docker-compose.services.yml logs --tail=50 postgresql
echo.
echo === Redis日志 ===
docker compose -f docker-compose.services.yml logs --tail=50 redis
goto :eof

:view_native_logs
echo [INFO] Windows服务日志:
echo.
echo 请在事件查看器中查看数据库服务日志:
echo - 开始菜单 -> 事件查看器
echo - Windows日志 -> 应用程序
echo - 筛选PostgreSQL和Redis相关事件
echo.
echo 或使用PowerShell命令:
echo Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='postgresql*'}
goto :eof

:test_connection
echo [INFO] 测试数据库连接...
echo.

if /i "!DB_SCHEME!"=="docker" (
    set "PG_HOST=localhost"
    set "PG_PORT=15432"
    set "REDIS_HOST=localhost"  
    set "REDIS_PORT=16379"
) else (
    set "PG_HOST=localhost"
    set "PG_PORT=5432"
    set "REDIS_HOST=localhost"
    set "REDIS_PORT=6379"
)

echo [INFO] 测试PostgreSQL连接 (!PG_HOST!:!PG_PORT!)...
if /i "!DB_SCHEME!"=="docker" (
    docker exec trademaster_postgresql pg_isready -U trademaster -h localhost -p 5432
) else (
    "C:\Program Files\PostgreSQL\14\bin\pg_isready.exe" -h !PG_HOST! -p !PG_PORT! -U trademaster
)

if not errorlevel 1 (
    echo [OK] PostgreSQL连接正常
) else (
    echo [ERROR] PostgreSQL连接失败
)

echo.
echo [INFO] 测试Redis连接 (!REDIS_HOST!:!REDIS_PORT!)...
if /i "!DB_SCHEME!"=="docker" (
    docker exec trademaster_redis redis-cli ping
) else (
    redis-cli -h !REDIS_HOST! -p !REDIS_PORT! -a TradeMaster2024! ping
)

if not errorlevel 1 (
    echo [OK] Redis连接正常
) else (
    echo [ERROR] Redis连接失败
)

goto :eof

:backup_docker_database
echo [INFO] 备份Docker PostgreSQL数据库...
set "BACKUP_FILE=%BACKUP_DIR%\postgresql_backup_%TIMESTAMP%.sql"
docker exec trademaster_postgresql pg_dump -U trademaster -d trademaster_web > "%BACKUP_FILE%"

if not errorlevel 1 (
    echo [OK] PostgreSQL备份完成: %BACKUP_FILE%
) else (
    echo [ERROR] PostgreSQL备份失败
)

echo [INFO] 备份Docker Redis数据...
docker exec trademaster_redis redis-cli BGSAVE
if not errorlevel 1 (
    echo [OK] Redis备份已启动 (后台执行)
) else (
    echo [ERROR] Redis备份失败
)
goto :eof

:backup_native_database
echo [INFO] 备份Windows原生PostgreSQL数据库...
set "BACKUP_FILE=%BACKUP_DIR%\postgresql_backup_%TIMESTAMP%.sql"
"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U trademaster -h localhost -p 5432 -d trademaster_web > "%BACKUP_FILE%"

if not errorlevel 1 (
    echo [OK] PostgreSQL备份完成: %BACKUP_FILE%
) else (
    echo [ERROR] PostgreSQL备份失败
)

echo [INFO] 备份Windows原生Redis数据...
redis-cli -a TradeMaster2024! BGSAVE
if not errorlevel 1 (
    echo [OK] Redis备份已启动 (后台执行)
) else (
    echo [ERROR] Redis备份失败
)
goto :eof

:restore_docker_database
echo [INFO] 恢复Docker PostgreSQL数据库...
docker exec -i trademaster_postgresql psql -U trademaster -d trademaster_web < "data\backups\%backup_file%"

if not errorlevel 1 (
    echo [OK] PostgreSQL数据恢复完成
) else (
    echo [ERROR] PostgreSQL数据恢复失败
)
goto :eof

:restore_native_database
echo [INFO] 恢复Windows原生PostgreSQL数据库...
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U trademaster -h localhost -p 5432 -d trademaster_web < "data\backups\%backup_file%"

if not errorlevel 1 (
    echo [OK] PostgreSQL数据恢复完成
) else (
    echo [ERROR] PostgreSQL数据恢复失败
)
goto :eof

:clean_docker_database
echo [INFO] 清理Docker数据库数据...
docker compose -f docker-compose.services.yml down -v
docker compose -f docker-compose.services.yml up -d
echo [OK] Docker数据库已重置
goto :eof

:clean_native_database
echo [INFO] 清理Windows原生数据库数据...
net stop postgresql-x64-14
net stop Redis

echo [INFO] 删除PostgreSQL数据目录...
rmdir /s /q "C:\Program Files\PostgreSQL\14\data" 2>nul

echo [INFO] 重新初始化数据库...
"C:\Program Files\PostgreSQL\14\bin\initdb.exe" -D "C:\Program Files\PostgreSQL\14\data" -U postgres

net start postgresql-x64-14
net start Redis

echo [INFO] 重新创建数据库和用户...
call scripts\windows-native-setup.bat

echo [OK] Windows原生数据库已重置
goto :eof

:exit
echo.
echo [INFO] 感谢使用TradeMaster数据库管理工具
exit /b 0