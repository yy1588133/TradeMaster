#!/usr/bin/env python3
"""
TradeMaster 后端启动脚本
设置正确的环境变量并启动FastAPI服务
"""
import os
import sys

# 设置 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['PYTHONPATH'] = '.'

# 检测并使用虚拟环境
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv')
if os.path.exists(venv_path):
    os.environ['VIRTUAL_ENV'] = venv_path
    print(f"Using virtual environment: {venv_path}")
else:
    os.environ['VIRTUAL_ENV'] = os.path.dirname(os.path.abspath(__file__))
    print("Virtual environment not found, using system Python")

# 启动服务
if __name__ == "__main__":
    import uvicorn
    print("Starting TradeMaster Backend Service...")
    print("Virtual Environment:", os.environ.get('VIRTUAL_ENV'))
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)