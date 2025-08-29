@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo    手动PostgreSQL数据库配置
echo ========================================

echo [步骤1] 停止PostgreSQL服务以便重新配置...
net stop postgresql-x64-14 >nul 2>&1

echo [步骤2] 启动PostgreSQL服务...
net start postgresql-x64-14
if errorlevel 1 (
    echo 错误：无法启动PostgreSQL服务
    pause
    exit /b 1
)

echo [步骤3] 等待服务完全启动...
timeout /t 10 /nobreak >nul

echo [步骤4] 设置postgres超级用户密码...
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -d postgres -c "ALTER USER postgres PASSWORD 'TradeMaster2024!';" >nul 2>&1
if errorlevel 1 (
    echo 警告：可能已设置过密码
) else (
    echo 成功：postgres用户密码已设置
)

echo [步骤5] 创建trademaster用户和数据库...
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -d postgres -c "DROP USER IF EXISTS trademaster;" >nul 2>&1
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -d postgres -c "DROP DATABASE IF EXISTS trademaster_web;" >nul 2>&1

echo CREATE USER trademaster WITH PASSWORD 'TradeMaster2024!'; > temp_setup.sql
echo CREATE DATABASE trademaster_web OWNER trademaster; >> temp_setup.sql
echo GRANT ALL PRIVILEGES ON DATABASE trademaster_web TO trademaster; >> temp_setup.sql
echo ALTER USER trademaster CREATEDB; >> temp_setup.sql

set PGPASSWORD=TradeMaster2024!
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -d postgres -f temp_setup.sql >nul 2>&1
if errorlevel 1 (
    echo 错误：数据库配置失败
    del temp_setup.sql >nul 2>&1
    pause
    exit /b 1
) else (
    echo 成功：trademaster用户和数据库已创建
)

del temp_setup.sql >nul 2>&1

echo [步骤6] 测试连接...
set PGPASSWORD=TradeMaster2024!
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U trademaster -d trademaster_web -c "SELECT current_user, current_database();" >nul 2>&1
if errorlevel 1 (
    echo 错误：连接测试失败
    pause
    exit /b 1
) else (
    echo 成功：连接测试通过
)

echo.
echo ========================================
echo    PostgreSQL 配置完成！
echo ========================================
echo 用户：trademaster
echo 密码：TradeMaster2024!
echo 数据库：trademaster_web
echo 端口：5432
echo ========================================

pause