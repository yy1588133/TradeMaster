@echo off
echo ==================================================
echo         TradeMaster Docker Container Starter
echo ==================================================
echo.

:: 检查Docker是否运行
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未运行或未安装。请启动Docker Desktop。
    pause
    exit /b 1
)

:: 停止并删除现有容器（如果存在）
echo [INFO] 停止现有容器...
docker stop trademaster-container >nul 2>&1
docker rm trademaster-container >nul 2>&1

:: 启动新容器
echo [INFO] 启动TradeMaster容器...
docker run -d ^
    --name trademaster-container ^
    -p 8080:8080 ^
    -p 8888:8888 ^
    -p 5001:5000 ^
    -v "%CD%\data:/app/data" ^
    -v "%CD%:/workspace" ^
    --restart unless-stopped ^
    trademaster:latest tail -f /dev/null

if errorlevel 1 (
    echo [ERROR] 容器启动失败！
    pause
    exit /b 1
)

:: 等待容器启动
echo [INFO] 等待容器启动...
timeout /t 3 /nobreak >nul

:: 检查容器状态
docker ps | findstr trademaster-container >nul
if errorlevel 1 (
    echo [ERROR] 容器未正常运行！
    pause
    exit /b 1
)

echo [SUCCESS] TradeMaster容器启动成功！
echo.
echo 容器信息:
echo   - 容器名称: trademaster-container
echo   - Web服务端口: http://localhost:8080
echo   - Jupyter端口: http://localhost:8888
echo   - API端口: http://localhost:5001
echo.
echo 使用以下脚本管理容器:
echo   - enter-container.bat : 进入容器
echo   - stop-container.bat  : 停止容器
echo.
pause