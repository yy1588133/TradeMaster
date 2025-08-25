"""
Test basic backend API health
"""
import requests
import json

def test_basic_api():
    """Test basic API endpoints"""
    base_url = "http://localhost:8001"
    
    print("Testing Basic API Endpoints")
    print("="*50)
    
    # Test root endpoint
    try:
        print("1. Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}")
    except requests.exceptions.Timeout:
        print("   ERROR: Root endpoint timeout")
    except requests.exceptions.ConnectionError:
        print("   ERROR: Cannot connect to server")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test health endpoint (if exists)
    try:
        print("\n2. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}")
    except requests.exceptions.Timeout:
        print("   ERROR: Health endpoint timeout")
    except Exception as e:
        print(f"   INFO: Health endpoint not found or error: {e}")
    
    # Test API docs
    try:
        print("\n3. Testing API docs...")
        response = requests.get(f"{base_url}/api/v1/docs", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   API docs accessible: {'Yes' if response.status_code == 200 else 'No'}")
    except requests.exceptions.Timeout:
        print("   ERROR: API docs timeout")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test simple API endpoint
    try:
        print("\n4. Testing simple API endpoint...")
        response = requests.get(f"{base_url}/api/v1/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}")
    except requests.exceptions.Timeout:
        print("   ERROR: API endpoint timeout")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    test_basic_api()