import requests
import logging
from flask import current_app
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class UMSClient:
    """Client for User Management Service (UMS) API integration."""
    
    def __init__(self):
        """Initialize UMS client with configuration from Flask app."""
        self.base_url = current_app.config.get('UMS_URL', 'http://localhost:5000')  # UMS runs on port 5000
        self.api_base = f"{self.base_url}/api"  # UMS API base path
        self.timeout = 30
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token with UMS and return user information.
        Uses UMS /api/auth/me endpoint to verify token and get user data.
        
        Args:
            token (str): JWT access token to verify
            
        Returns:
            Optional[Dict[str, Any]]: User information if token is valid, None otherwise
        """
        try:
            url = f"{self.api_base}/auth/me"  # UMS endpoint: GET /api/auth/me
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Token verified for user: {user_data.get('id')}")
                return user_data
            elif response.status_code == 401:
                logger.warning("Token verification failed: Invalid or expired token")
                return None
            else:
                logger.error(f"UMS verification failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to UMS: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {str(e)}")
            return None
    
    def get_user_info(self, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed user information from UMS.
        Uses UMS /api/users/{id} endpoint.
        
        Args:
            user_id (str): User ID to fetch information for
            token (str): Valid JWT token for authentication
            
        Returns:
            Optional[Dict[str, Any]]: User information if successful, None otherwise
        """
        try:
            url = f"{self.api_base}/users/{user_id}"  # UMS endpoint: GET /api/users/{id}
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user info: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user info from UMS: {str(e)}")
            return None
    
    def get_user_lab_relation(self, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user's lab relationship information from UMS.
        Uses UMS /api/users/{id}/labs endpoint.
        
        Args:
            user_id (str): User ID to fetch lab relation for
            token (str): Valid JWT token for authentication
            
        Returns:
            Optional[Dict[str, Any]]: Lab relation information if successful, None otherwise
        """
        try:
            url = f"{self.api_base}/users/{user_id}/labs"  # UMS endpoint: GET /api/users/{id}/labs
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get lab relation: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching lab relation from UMS: {str(e)}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Refresh an expired JWT token using UMS /api/auth/refresh endpoint.
        
        Args:
            refresh_token (str): Refresh token
            
        Returns:
            Optional[Dict[str, str]]: New tokens if successful, None otherwise
        """
        try:
            url = f"{self.api_base}/auth/refresh"  # UMS endpoint: POST /api/auth/refresh
            headers = {
                'Authorization': f'Bearer {refresh_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
    
    def get_lab_info(self, lab_id: int, token: str) -> Optional[Dict[str, Any]]:
        """
        Get lab information from UMS.
        Uses UMS /api/labs/{id} endpoint.
        
        Args:
            lab_id (int): Lab ID to fetch information for
            token (str): Valid JWT token for authentication
            
        Returns:
            Optional[Dict[str, Any]]: Lab information if successful, None otherwise
        """
        try:
            url = f"{self.api_base}/labs/{lab_id}"  # UMS endpoint: GET /api/labs/{id}
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get lab info: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching lab info from UMS: {str(e)}")
            return None