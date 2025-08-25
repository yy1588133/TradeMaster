@echo off
REM ========================================
REM CORS修复测试脚本
REM ========================================

echo [INFO] 正在重启Docker服务以应用CORS修复...

echo [STEP 1] 停止现有容器...
docker compose -f docker-compose.services.yml down

echo [STEP 2] 重新构建并启动服务...
docker compose -f docker-compose.services.yml up -d --build

echo [STEP 3] 等待服务启动...
timeout /t 10 >nul

echo [STEP 4] 检查服务状态...
docker compose -f docker-compose.services.yml ps

echo [STEP 5] 查看后端日志...
echo "--- 后端服务日志 (最近50行) ---"
docker compose logs --tail=50 backend

echo [STEP 6] 测试CORS预检请求...
curl -X OPTIONS -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: Content-Type" http://localhost:8000/api/v1/auth/register

echo.
echo [INFO] CORS修复测试完成。请查看上述输出以确认修复效果。
echo [INFO] 如果仍有问题，请检查：
echo         1. 前端配置: frontend/.env (端口8000)
echo         2. 后端配置: backend/.env (CORS源地址)
echo         3. Docker容器日志
echo.
pause