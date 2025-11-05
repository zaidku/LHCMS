import requests
import json

def test_endpoints():
    base_url = "http://127.0.0.1:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health endpoint status: {response.status_code}")
        print(f"Health response: {response.json()}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test API documentation
    try:
        response = requests.get(f"{base_url}/docs/")
        print(f"Docs endpoint status: {response.status_code}")
        print("Docs endpoint is accessible")
    except Exception as e:
        print(f"Docs endpoint error: {e}")
    
    # Test API swagger.json
    try:
        response = requests.get(f"{base_url}/api/v1/swagger.json")
        print(f"Swagger JSON status: {response.status_code}")
        if response.status_code == 200:
            print("API definition is available")
    except Exception as e:
        print(f"Swagger JSON error: {e}")

if __name__ == "__main__":
    test_endpoints()