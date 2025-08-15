@echo off
echo ==================================================
echo         TradeMaster Docker Container Shell
echo ==================================================
echo.

:: 检查Docker是否运行
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未运行或未安装。请启动Docker Desktop。
    pause
    exit /b 1
)

:: 检查容器是否运行
docker ps | findstr trademaster-container >nul
if errorlevel 1 (
    echo [ERROR] 容器 'trademaster-container' 未运行。
    echo [INFO] 请先运行 start-container.bat 启动容器。
    pause
    exit /b 1
)

echo [INFO] 进入TradeMaster容器...
echo [INFO] 当前工作目录: /workspace (映射到本地项目目录)
echo [INFO] TradeMaster数据目录: /app/data
echo [INFO] Python虚拟环境已激活
echo.
echo 常用命令:
echo   - python3 -c "import trademaster; print('TradeMaster可用')"
echo   - ls /workspace  : 查看项目文件
echo   - ls /app/data   : 查看数据目录
echo   - exit           : 退出容器
echo.
echo 正在连接到容器...
echo ================================================

:: 进入容器bash shell
docker exec -it trademaster-container bash

echo.
echo [INFO] 已退出容器。
pause