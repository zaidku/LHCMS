#!/usr/bin/env python3
"""
Test script for UMS-CMS integration
Tests the authentication flow between User Management Service and Case Management Service
"""

import requests
import json
import sys
from typing import Optional, Dict, Any

# Service URLs
UMS_BASE_URL = "http://localhost:5000/api"
CMS_BASE_URL = "http://localhost:5001/api/v1"

class IntegrationTester:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user_data = None
        
    def test_ums_health(self) -> bool:
        """Test UMS health endpoint"""
        try:
            response = requests.get(f"http://localhost:5000/health", timeout=5)
            if response.status_code == 200:
                print("✅ UMS is running and healthy")
                return True
            else:
                print(f"❌ UMS health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to UMS - make sure it's running on port 5000")
            return False
        except Exception as e:
            print(f"❌ UMS health check error: {e}")
            return False
    
    def test_cms_health(self) -> bool:
        """Test CMS health endpoint"""
        try:
            response = requests.get(f"http://localhost:5001/health", timeout=5)
            if response.status_code == 200:
                print("✅ CMS is running and healthy")
                return True
            else:
                print(f"❌ CMS health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to CMS - make sure it's running on port 5001")
            return False
        except Exception as e:
            print(f"❌ CMS health check error: {e}")
            return False
    
    def test_ums_login(self, username: str = "admin", password: str = "admin123") -> bool:
        """Test UMS login and token generation"""
        try:
            url = f"{UMS_BASE_URL}/auth/login"
            data = {
                "username": username,
                "password": password
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                self.refresh_token = result.get('refresh_token')
                self.user_data = result.get('user')
                
                print("✅ UMS login successful")
                print(f"   User: {self.user_data.get('username')} ({self.user_data.get('email')})")
                
                if 'labs' in self.user_data:
                    print(f"   Labs: {len(self.user_data['labs'])} lab(s)")
                    for lab in self.user_data['labs']:
                        print(f"     - {lab.get('lab_name')} (ID: {lab.get('lab_id')}, Role: {lab.get('role')})")
                
                return True
            else:
                print(f"❌ UMS login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ UMS login error: {e}")
            return False
    
    def test_ums_token_verification(self) -> bool:
        """Test UMS token verification"""
        if not self.access_token:
            print("❌ No access token available for verification")
            return False
            
        try:
            url = f"{UMS_BASE_URL}/auth/me"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_info = response.json()
                print("✅ UMS token verification successful")
                print(f"   Verified user: {user_info.get('username')}")
                return True
            else:
                print(f"❌ UMS token verification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ UMS token verification error: {e}")
            return False
    
    def test_cms_with_ums_token(self) -> bool:
        """Test CMS endpoints using UMS token"""
        if not self.access_token:
            print("❌ No access token available for CMS testing")
            return False
            
        try:
            # Test CMS cases endpoint with UMS token
            url = f"{CMS_BASE_URL}/cases/"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                cases_data = response.json()
                print("✅ CMS authentication with UMS token successful")
                print(f"   Retrieved {len(cases_data.get('cases', []))} case(s)")
                return True
            elif response.status_code == 401:
                print("❌ CMS rejected UMS token (authentication failed)")
                print(f"   Response: {response.text}")
                return False
            elif response.status_code == 403:
                print("❌ CMS access forbidden (lab access issue)")
                print(f"   Response: {response.text}")
                return False
            else:
                print(f"❌ CMS request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ CMS integration test error: {e}")
            return False
    
    def test_cms_case_creation(self) -> bool:
        """Test creating a case through CMS"""
        if not self.access_token:
            print("❌ No access token available for case creation")
            return False
            
        try:
            url = f"{CMS_BASE_URL}/cases/"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            case_data = {
                "doctor_id": "DOC001",
                "product_id": "PROD001",
                "case_name": "Test Crown Case",
                "description": "Integration test case",
                "case_type": "fixed_prosthetic",
                "patient_info": {
                    "patient_id": "PAT001",
                    "age": 35,
                    "gender": "male"
                },
                "fixed_prosthetic": {
                    "type": "crown",
                    "material": "zirconia",
                    "tooth_numbers": [14],
                    "shade": {
                        "shade_system": "vita_classical",
                        "shade_value": "A2"
                    }
                }
            }
            
            response = requests.post(url, json=case_data, headers=headers, timeout=10)
            
            if response.status_code == 201:
                created_case = response.json()
                print("✅ CMS case creation successful")
                print(f"   Created case ID: {created_case.get('id')}")
                print(f"   Case name: {created_case.get('case_name')}")
                return True
            else:
                print(f"❌ CMS case creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ CMS case creation error: {e}")
            return False
    
    def run_full_integration_test(self, username: str = "admin", password: str = "admin123"):
        """Run complete integration test suite"""
        print("🚀 Starting UMS-CMS Integration Test")
        print("=" * 50)
        
        # Test service health
        print("\n1. Testing Service Health:")
        ums_healthy = self.test_ums_health()
        cms_healthy = self.test_cms_health()
        
        if not ums_healthy or not cms_healthy:
            print("\n❌ Service health checks failed. Cannot continue integration test.")
            return False
        
        # Test UMS authentication
        print("\n2. Testing UMS Authentication:")
        login_success = self.test_ums_login(username, password)
        
        if not login_success:
            print("\n❌ UMS authentication failed. Cannot continue integration test.")
            print("   Make sure UMS has a user with the provided credentials.")
            return False
        
        # Test UMS token verification
        print("\n3. Testing UMS Token Verification:")
        token_valid = self.test_ums_token_verification()
        
        if not token_valid:
            print("\n❌ UMS token verification failed.")
            return False
        
        # Test CMS with UMS token
        print("\n4. Testing CMS with UMS Token:")
        cms_auth_success = self.test_cms_with_ums_token()
        
        if not cms_auth_success:
            print("\n❌ CMS-UMS integration failed.")
            return False
        
        # Test case creation
        print("\n5. Testing CMS Case Creation:")
        case_creation_success = self.test_cms_case_creation()
        
        print("\n" + "=" * 50)
        if ums_healthy and cms_healthy and login_success and token_valid and cms_auth_success:
            print("🎉 Integration Test PASSED!")
            print("   UMS and CMS are properly integrated and communicating.")
            return True
        else:
            print("❌ Integration Test FAILED!")
            print("   Check the error messages above for details.")
            return False

def main():
    """Main function to run integration tests"""
    tester = IntegrationTester()
    
    # Check if custom credentials provided
    username = "admin"
    password = "admin123"
    
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
        print(f"Using provided credentials: {username}")
    else:
        print(f"Using default credentials: {username}")
        print("Usage: python integration_test.py [username] [password]")
    
    # Run the test
    success = tester.run_full_integration_test(username, password)
    
    if success:
        print("\n✅ All tests passed! UMS-CMS integration is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Integration tests failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()