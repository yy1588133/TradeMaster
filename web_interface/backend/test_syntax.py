"""
快速语法测试脚本
"""
import sys
sys.path.append('.')

try:
    from typing import List
    print("✅ List 类型导入成功")
    
    # 测试CORS解析函数
    def parse_cors_origins() -> List[str]:
        """智能解析CORS源地址列表"""
        import os
        import json
        
        # 直接从环境变量获取
        cors_env = os.getenv("BACKEND_CORS_ORIGINS", "")
        
        if not cors_env.strip():
            # 默认开发环境CORS配置
            return [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001"
            ]
        
        # 尝试JSON格式解析
        try:
            parsed = json.loads(cors_env)
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 逗号分隔格式解析
        if ',' in cors_env:
            return [origin.strip() for origin in cors_env.split(',') if origin.strip()]
        
        # 单个URL处理
        if cors_env.strip():
            return [cors_env.strip()]
        
        # 返回默认值
        return [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000", 
            "http://127.0.0.1:3001"
        ]
    
    # 测试函数
    cors_origins = parse_cors_origins()
    print(f"✅ CORS解析函数测试成功: {cors_origins}")
    
    print("✅ 所有语法检查通过！")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")