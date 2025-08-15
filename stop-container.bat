@echo off
echo ==================================================
echo         TradeMaster Docker Container Stopper
echo ==================================================
echo.

:: 检查Docker是否运行
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未运行或未安装。请启动Docker Desktop。
    pause
    exit /b 1
)

:: 检查容器是否存在
docker ps -a | findstr trademaster-container >nul
if errorlevel 1 (
    echo [INFO] 容器 'trademaster-container' 不存在。
    pause
    exit /b 0
)

:: 停止容器
echo [INFO] 停止TradeMaster容器...
docker stop trademaster-container

if errorlevel 1 (
    echo [ERROR] 停止容器失败！
    pause
    exit /b 1
)

:: 删除容器
echo [INFO] 删除容器...
docker rm trademaster-container

if errorlevel 1 (
    echo [ERROR] 删除容器失败！
    pause
    exit /b 1
)

echo [SUCCESS] TradeMaster容器已成功停止并删除！
echo.
echo 如需重新启动容器，请运行 start-container.bat
echo.
pause