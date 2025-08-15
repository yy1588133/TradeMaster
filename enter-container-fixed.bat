@echo off
chcp 65001 >nul
echo ==================================================
echo         TradeMaster Docker Container Shell
echo ==================================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running or not installed. Please start Docker Desktop.
    pause
    exit /b 1
)

REM Check if container is running
docker ps | findstr trademaster-container >nul
if errorlevel 1 (
    echo [ERROR] Container 'trademaster-container' is not running.
    echo [INFO] Please run start-container.bat first to start the container.
    pause
    exit /b 1
)

echo [INFO] Entering TradeMaster container...
echo [INFO] Current working directory: /home/TradeMaster
echo [INFO] Web service running on: http://localhost:8080
echo.
echo Common commands:
echo   - python3 -c "import trademaster; print('TradeMaster available')"
echo   - ls /home/TradeMaster  : View project files
echo   - curl http://localhost:8080/api/TradeMaster/healthcheck : Test API
echo   - exit : Exit container
echo.
echo Connecting to container...
echo ================================================

REM Enter container bash shell
docker exec -it trademaster-container bash

echo.
echo [INFO] Exited container.
pause