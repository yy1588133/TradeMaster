"""
测试登录API功能的脚本
"""
import requests
import json

def test_login_api():
    """测试登录API"""
    # 后端API地址 (根据启动脚本，应该是8001端口)
    base_url = "http://localhost:8001/api/v1"
    login_url = f"{base_url}/auth/login"
    
    print("Testing TradeMaster Login API")
    print("="*50)
    
    # 测试管理员用户登录
    test_cases = [
        {
            "name": "Admin User",
            "username": "admin",
            "password": "admin123",
            "remember_me": False
        },
        {
            "name": "Demo User", 
            "username": "demo",
            "password": "demo123",
            "remember_me": False
        },
        {
            "name": "Invalid User",
            "username": "invalid",
            "password": "wrong123",
            "remember_me": False
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting {test_case['name']}:")
        print(f"  Username: {test_case['username']}")
        
        try:
            response = requests.post(
                login_url,
                json={
                    "username": test_case["username"],
                    "password": test_case["password"],
                    "remember_me": test_case["remember_me"]
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Success: Login successful")
                print(f"  User ID: {data.get('user', {}).get('id', 'N/A')}")
                print(f"  Access Token: {data.get('tokens', {}).get('access_token', 'N/A')[:50]}...")
            else:
                print(f"  Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  Detail: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"  Response: {response.text[:200]}")
                    
        except requests.exceptions.ConnectionError:
            print(f"  Error: Cannot connect to {login_url}")
            print("  Make sure the backend server is running on port 8001")
            break
        except requests.exceptions.Timeout:
            print(f"  Error: Request timeout")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_login_api()