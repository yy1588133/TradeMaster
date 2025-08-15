@echo off
setlocal enabledelayedexpansion

:menu
cls
echo ==================================================
echo         TradeMaster Docker Container Manager
echo ==================================================
echo.
echo 选择操作:
echo   1. 启动容器
echo   2. 停止容器
echo   3. 进入容器
echo   4. 查看容器状态
echo   5. 查看容器日志
echo   6. 重启容器
echo   7. 删除容器数据（危险操作）
echo   8. 退出
echo.
set /p choice="请输入选项(1-8): "

if "%choice%"=="1" goto start_container
if "%choice%"=="2" goto stop_container
if "%choice%"=="3" goto enter_container
if "%choice%"=="4" goto status_container
if "%choice%"=="5" goto logs_container
if "%choice%"=="6" goto restart_container
if "%choice%"=="7" goto cleanup_container
if "%choice%"=="8" goto exit
goto invalid_choice

:start_container
echo.
echo [INFO] 启动TradeMaster容器...
call start-container.bat
goto menu

:stop_container
echo.
echo [INFO] 停止TradeMaster容器...
call stop-container.bat
goto menu

:enter_container
echo.
echo [INFO] 进入TradeMaster容器...
call enter-container.bat
goto menu

:status_container
echo.
echo [INFO] 容器状态信息:
echo ================================================
docker ps -a | findstr trademaster-container
if errorlevel 1 (
    echo 容器不存在
) else (
    echo.
    echo 端口映射信息:
    docker port trademaster-container 2>nul
    echo.
    echo 数据卷信息:
    docker inspect trademaster-container --format="{{.Mounts}}" 2>nul
)
echo ================================================
pause
goto menu

:logs_container
echo.
echo [INFO] 容器日志 (最新50行):
echo ================================================
docker logs --tail 50 trademaster-container 2>nul
if errorlevel 1 (
    echo 无法获取日志，容器可能不存在或未运行
)
echo ================================================
pause
goto menu

:restart_container
echo.
echo [INFO] 重启容器...
docker restart trademaster-container 2>nul
if errorlevel 1 (
    echo [ERROR] 重启失败，容器可能不存在
) else (
    echo [SUCCESS] 容器重启成功
)
pause
goto menu

:cleanup_container
echo.
echo [WARNING] 这将删除容器和所有未保存的数据！
echo [WARNING] 挂载的数据卷不会被删除。
set /p confirm="确认删除吗? (y/N): "
if /i "%confirm%"=="y" (
    docker rm -f trademaster-container 2>nul
    echo [INFO] 容器已删除
) else (
    echo [INFO] 操作已取消
)
pause
goto menu

:invalid_choice
echo.
echo [ERROR] 无效选项，请重新选择
pause
goto menu

:exit
echo.
echo 感谢使用TradeMaster容器管理工具！
pause
exit /b 0