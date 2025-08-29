@echo off
chcp 65001 >nul
echo 测试PostgreSQL数据库连接...

echo.
echo === 测试1: 检查PostgreSQL服务状态 ===
sc query postgresql-x64-14

echo.
echo === 测试2: 检查端口是否监听 ===
netstat -ano | findstr ":5432"

echo.
echo === 测试3: 尝试连接数据库 ===
echo 尝试使用用户trademaster连接...

timeout /t 2 /nobreak >nul
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U trademaster -d trademaster_web -c "SELECT current_user, current_database();" 2>nul
if errorlevel 1 (
    echo 连接失败，可能的原因：
    echo 1. 用户trademaster不存在
    echo 2. 数据库trademaster_web不存在  
    echo 3. 密码不正确
    echo 4. 权限问题
) else (
    echo 连接成功！
)

echo.
echo === 测试4: 使用postgres用户检查 ===
"C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -d postgres -c "SELECT usename FROM pg_user;" 2>nul
if errorlevel 1 (
    echo 无法连接到PostgreSQL，请检查服务状态
) else (
    echo PostgreSQL服务正常，用户列表见上方
)

echo.
echo 测试完成。
pause