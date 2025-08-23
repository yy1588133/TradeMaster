"""
简化版后端主应用 - 包含完整的API端点用于测试
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time

# 创建FastAPI应用
app = FastAPI(
    title="TradeMaster Web Interface (Testing)",
    version="1.0.0-dev", 
    description="完整API端点测试版本 - 无需数据库",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100", "http://localhost:3000", "http://127.0.0.1:3100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "TradeMaster Web Interface Backend (Simple Version)", "status": "running"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.0.0-dev"}

@app.get("/api/v1/health")
async def api_health_check():
    """API健康检查"""
    return {"status": "healthy", "api_version": "v1"}

@app.post("/api/v1/auth/login")
async def login():
    """模拟登录 - 返回完整的登录响应格式"""
    return {
        "user": {
            "id": 1,
            "uuid": "demo-uuid-123",
            "username": "demo_user",
            "email": "demo@example.com",
            "full_name": "Demo User",
            "role": "user",
            "is_active": True,
            "is_verified": True,
            "created_at": "2023-01-01T00:00:00Z",
            "last_login_at": datetime.now().isoformat() + "Z",
            "login_count": 1
        },
        "tokens": {
            "access_token": "demo_access_token_12345",
            "refresh_token": "demo_refresh_token_67890", 
            "token_type": "bearer",
            "expires_in": 1800  # 30 minutes
        },
        "message": "登录成功"
    }

@app.post("/api/v1/auth/register")
async def register():
    """模拟注册 - 返回用户信息"""
    return {
        "id": 2,
        "uuid": "new-user-uuid-456", 
        "username": "new_user",
        "email": "new_user@example.com",
        "full_name": "New User",
        "role": "user",
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.now().isoformat() + "Z",
        "last_login_at": None,
        "login_count": 0
    }

@app.get("/api/v1/auth/me")
async def get_current_user():
    """获取当前用户信息"""
    return {
        "id": "1",
        "username": "demo_user",
        "email": "demo@example.com",
        "role": "admin"
    }

@app.get("/api/v1/strategies")
async def get_strategies():
    """获取策略列表"""
    return {
        "items": [
            {
                "id": "1",
                "name": "Demo Strategy",
                "description": "示例策略",
                "strategy_type": "algorithmic_trading",
                "status": "active"
            }
        ],
        "total": 1
    }

@app.get("/api/v1/data/datasets")
async def get_datasets():
    """获取数据集列表"""
    return {
        "items": [
            {
                "id": "1",
                "name": "Demo Dataset",
                "description": "示例数据集",
                "data_type": "csv",
                "size": 1024
            }
        ],
        "total": 1
    }

# ==================== 完整认证API ====================

@app.post("/api/v1/auth/logout")
async def logout():
    """用户退出"""
    return {"message": "退出成功"}

@app.post("/api/v1/auth/refresh")
async def refresh_token():
    """刷新令牌"""
    return {
        "access_token": "refreshed_token_" + str(int(time.time())),
        "refresh_token": "refresh_token_" + str(int(time.time())),
        "token_type": "bearer",
        "expires_in": 3600
    }

@app.post("/api/v1/auth/change-password")
async def change_password():
    """修改密码"""
    return {"message": "密码修改成功"}

@app.post("/api/v1/auth/forgot-password")
async def forgot_password():
    """忘记密码"""
    return {"message": "密码重置邮件已发送"}

@app.post("/api/v1/auth/reset-password")
async def reset_password():
    """重置密码"""
    return {"message": "密码重置成功"}

@app.post("/api/v1/auth/verify-token")
async def verify_token():
    """验证令牌"""
    return {
        "valid": True,
        "user": {"id": "1", "username": "demo_user", "role": "admin"}
    }

# ==================== 策略管理API ====================

@app.post("/api/v1/strategies")
async def create_strategy():
    """创建策略"""
    return {
        "id": "strategy_" + str(int(time.time())),
        "name": "New Strategy",
        "description": "新创建的策略",
        "strategy_type": "algorithmic_trading",
        "status": "draft",
        "created_at": datetime.now().isoformat()
    }

@app.get("/api/v1/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """获取单个策略"""
    return {
        "id": strategy_id,
        "name": "Demo Strategy",
        "description": "示例策略详情",
        "strategy_type": "algorithmic_trading",
        "status": "active",
        "config": {"symbol": "BTC-USDT", "timeframe": "1d"},
        "created_at": "2025-01-01T00:00:00",
        "updated_at": datetime.now().isoformat()
    }

@app.put("/api/v1/strategies/{strategy_id}")
async def update_strategy(strategy_id: str):
    """更新策略"""
    return {
        "id": strategy_id,
        "name": "Updated Strategy",
        "description": "更新后的策略",
        "status": "active",
        "updated_at": datetime.now().isoformat()
    }

@app.delete("/api/v1/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略"""
    return {"message": f"策略 {strategy_id} 删除成功"}

@app.post("/api/v1/strategies/{strategy_id}/backtest")
async def backtest_strategy(strategy_id: str):
    """策略回测"""
    return {
        "task_id": f"backtest_{strategy_id}_{int(time.time())}",
        "status": "started",
        "message": "回测任务已启动"
    }

@app.post("/api/v1/strategies/{strategy_id}/start")
async def start_strategy(strategy_id: str):
    """启动策略"""
    return {
        "id": strategy_id,
        "status": "running",
        "message": "策略已启动"
    }

@app.post("/api/v1/strategies/{strategy_id}/stop")
async def stop_strategy(strategy_id: str):
    """停止策略"""
    return {
        "id": strategy_id,
        "status": "stopped",
        "message": "策略已停止"
    }

# ==================== 数据管理API ====================

@app.post("/api/v1/data/upload")
async def upload_data():
    """上传数据"""
    return {
        "id": "upload_" + str(int(time.time())),
        "filename": "demo_data.csv",
        "size": 2048,
        "message": "数据上传成功"
    }

@app.get("/api/v1/data/{dataset_id}")
async def get_dataset(dataset_id: str):
    """获取数据集详情"""
    return {
        "id": dataset_id,
        "name": "Demo Dataset",
        "description": "示例数据集详情",
        "data_type": "csv",
        "size": 1024,
        "rows": 1000,
        "columns": 10,
        "created_at": "2025-01-01T00:00:00"
    }

@app.put("/api/v1/data/{dataset_id}")
async def update_dataset(dataset_id: str):
    """更新数据集"""
    return {
        "id": dataset_id,
        "name": "Updated Dataset",
        "description": "更新后的数据集",
        "updated_at": datetime.now().isoformat()
    }

@app.delete("/api/v1/data/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """删除数据集"""
    return {"message": f"数据集 {dataset_id} 删除成功"}

# ==================== 训练任务API ====================

@app.get("/api/v1/training")
async def get_training_jobs():
    """获取训练任务列表"""
    return {
        "items": [
            {
                "id": "training_1",
                "name": "Demo Training Job",
                "status": "running",
                "progress": 75,
                "created_at": "2025-01-01T00:00:00"
            }
        ],
        "total": 1
    }

@app.post("/api/v1/training")
async def create_training_job():
    """创建训练任务"""
    return {
        "id": "training_" + str(int(time.time())),
        "name": "New Training Job",
        "status": "pending",
        "message": "训练任务创建成功"
    }

@app.get("/api/v1/training/{job_id}")
async def get_training_job(job_id: str):
    """获取训练任务详情"""
    return {
        "id": job_id,
        "name": "Demo Training Job",
        "status": "running",
        "progress": 75,
        "metrics": {"loss": 0.25, "accuracy": 0.85},
        "created_at": "2025-01-01T00:00:00"
    }

@app.post("/api/v1/training/{job_id}/start")
async def start_training_job(job_id: str):
    """启动训练任务"""
    return {
        "id": job_id,
        "status": "running",
        "message": "训练任务已启动"
    }

@app.post("/api/v1/training/{job_id}/stop")
async def stop_training_job(job_id: str):
    """停止训练任务"""
    return {
        "id": job_id,
        "status": "stopped",
        "message": "训练任务已停止"
    }

@app.get("/api/v1/training/{job_id}/logs")
async def get_training_logs(job_id: str):
    """获取训练日志"""
    return {
        "logs": [
            f"[{datetime.now().strftime('%H:%M:%S')}] Training started for job {job_id}",
            f"[{datetime.now().strftime('%H:%M:%S')}] Epoch 1/10 completed",
            f"[{datetime.now().strftime('%H:%M:%S')}] Current loss: 0.25"
        ]
    }

# ==================== 分析评估API ====================

@app.post("/api/v1/analysis/backtest")
async def run_backtest():
    """运行回测分析"""
    return {
        "task_id": "backtest_" + str(int(time.time())),
        "status": "started",
        "message": "回测分析已启动"
    }

@app.get("/api/v1/analysis/backtest/{task_id}")
async def get_backtest_results(task_id: str):
    """获取回测结果"""
    return {
        "task_id": task_id,
        "status": "completed",
        "results": {
            "total_return": 15.6,
            "sharpe_ratio": 1.23,
            "max_drawdown": -8.5,
            "win_rate": 0.65
        }
    }

@app.get("/api/v1/analysis/backtests")
async def list_backtests():
    """获取回测列表"""
    return {
        "items": [
            {
                "id": "backtest_1",
                "strategy_name": "Demo Strategy",
                "status": "completed",
                "created_at": "2025-01-01T00:00:00"
            }
        ],
        "total": 1
    }

@app.post("/api/v1/analysis/performance")
async def run_performance_analysis():
    """运行性能分析"""
    return {
        "task_id": "performance_" + str(int(time.time())),
        "status": "started",
        "message": "性能分析已启动"
    }

@app.get("/api/v1/analysis/performance/{task_id}")
async def get_performance_results(task_id: str):
    """获取性能分析结果"""
    return {
        "task_id": task_id,
        "status": "completed",
        "metrics": {
            "annual_return": 12.5,
            "volatility": 18.3,
            "sharpe_ratio": 1.23,
            "sortino_ratio": 1.45
        }
    }

@app.post("/api/v1/analysis/risk")
async def run_risk_analysis():
    """运行风险分析"""
    return {
        "task_id": "risk_" + str(int(time.time())),
        "status": "started",
        "message": "风险分析已启动"
    }

@app.get("/api/v1/analysis/risk/{task_id}")
async def get_risk_results(task_id: str):
    """获取风险分析结果"""
    return {
        "task_id": task_id,
        "status": "completed",
        "risk_metrics": {
            "var_95": -2.5,
            "cvar_95": -3.8,
            "max_drawdown": -8.5,
            "beta": 1.15
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)