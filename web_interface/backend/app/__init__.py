"""
TradeMaster Web Interface Backend Application

一个基于FastAPI的现代化Web后端，为TradeMaster提供统一的Web界面。
"""

__version__ = "1.0.0"
__author__ = "TradeMaster Team"
__email__ = "contact@trademaster.ai"

# 导出主要组件
from .main import app

__all__ = ["app"]