import requests
import logging
from flask import current_app
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class LinksHubClient:
    """Client for LinksHub Core API integration."""
    
    def __init__(self):
        """Initialize LinksHub client with configuration from Flask app."""
        self.base_url = current_app.config.get('LINKSHUB_CORE_URL', 'https://core.linkstechnologies.io')
        self.timeout = 30
    
    def get_doctor_info(self, doctor_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get doctor information from LinksHub Core API.
        
        Args:
            doctor_id (str): Doctor ID to fetch information for
            token (str): Valid JWT token for authentication
            
        Returns:
            Optional[Dict[str, Any]]: Doctor information if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/doctors/{doctor_id}"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                doctor_data = response.json()
                logger.info(f"Retrieved doctor info for ID: {doctor_id}")
                return doctor_data
            elif response.status_code == 404:
                logger.warning(f"Doctor not found: {doctor_id}")
                return None
            else:
                logger.error(f"Failed to get doctor info: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching doctor info from LinksHub: {str(e)}")
            return None
    
    def get_product_info(self, product_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get product information from LinksHub Core API.
        
        Args:
            product_id (str): Product ID to fetch information for
            token (str): Valid JWT token for authentication
            
        Returns:
            Optional[Dict[str, Any]]: Product information if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/products/{product_id}"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                product_data = response.json()
                logger.info(f"Retrieved product info for ID: {product_id}")
                return product_data
            elif response.status_code == 404:
                logger.warning(f"Product not found: {product_id}")
                return None
            else:
                logger.error(f"Failed to get product info: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching product info from LinksHub: {str(e)}")
            return None
    
    def get_lab_products(self, lab_id: str, token: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all products available for a specific lab.
        
        Args:
            lab_id (str): Lab ID to fetch products for
            token (str): Valid JWT token for authentication
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of products if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/labs/{lab_id}/products"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                products_data = response.json()
                logger.info(f"Retrieved {len(products_data)} products for lab: {lab_id}")
                return products_data
            elif response.status_code == 404:
                logger.warning(f"Lab not found or no products available: {lab_id}")
                return []
            else:
                logger.error(f"Failed to get lab products: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching lab products from LinksHub: {str(e)}")
            return None
    
    def validate_doctor_lab_relation(self, doctor_id: str, lab_id: str, token: str) -> bool:
        """
        Validate if a doctor has a relationship with a specific lab.
        
        Args:
            doctor_id (str): Doctor ID to validate
            lab_id (str): Lab ID to validate against
            token (str): Valid JWT token for authentication
            
        Returns:
            bool: True if relation exists, False otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/doctors/{doctor_id}/labs/{lab_id}/relation"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                relation_data = response.json()
                is_valid = relation_data.get('is_active', False)
                logger.info(f"Doctor-lab relation validation: {doctor_id}-{lab_id} = {is_valid}")
                return is_valid
            else:
                logger.warning(f"Doctor-lab relation not found: {doctor_id}-{lab_id}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating doctor-lab relation: {str(e)}")
            return False
    
    def get_lab_info(self, lab_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get lab information from LinksHub Core API.
        
        Args:
            lab_id (str): Lab ID to fetch information for
            token (str): Valid JWT token for authentication
            
        Returns:
            Optional[Dict[str, Any]]: Lab information if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/labs/{lab_id}"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                lab_data = response.json()
                logger.info(f"Retrieved lab info for ID: {lab_id}")
                return lab_data
            elif response.status_code == 404:
                logger.warning(f"Lab not found: {lab_id}")
                return None
            else:
                logger.error(f"Failed to get lab info: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching lab info from LinksHub: {str(e)}")
            return None