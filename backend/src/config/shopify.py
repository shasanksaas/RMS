"""
Shopify OAuth and API configuration
"""
import os
from typing import Optional

class ShopifyConfig:
    """Shopify configuration settings"""
    
    # OAuth Credentials
    CLIENT_ID = "81e556a66ac6d28a54e1ed972a3c43ad"
    CLIENT_SECRET = "d23f49ea8d18e93a8a26c2c04dba826c"
    
    # OAuth URLs
    AUTHORIZE_URL = "https://{shop}.myshopify.com/admin/oauth/authorize"
    TOKEN_URL = "https://{shop}.myshopify.com/admin/oauth/access_token"
    
    # Required Scopes for Returns Management
    SCOPES = [
        "read_orders",
        "write_orders", 
        "read_products",
        "read_customers",
        "read_inventory",
        "read_fulfillments",
        "write_fulfillments",
        "read_returns",
        "write_returns",
        "read_refunds",
        "write_refunds",
        "read_locations",
        "read_shipping"
    ]
    
    # API Configuration
    API_VERSION = "2024-01"  # Latest stable version
    
    @classmethod
    def get_authorization_url(cls, shop: str, redirect_uri: str, state: str) -> str:
        """Generate Shopify OAuth authorization URL"""
        scopes = ",".join(cls.SCOPES)
        return (
            f"https://{shop}.myshopify.com/admin/oauth/authorize"
            f"?client_id={cls.CLIENT_ID}"
            f"&scope={scopes}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
        )
    
    @classmethod
    def get_api_url(cls, shop: str, endpoint: str) -> str:
        """Get Shopify API URL for endpoint"""
        return f"https://{shop}.myshopify.com/admin/api/{cls.API_VERSION}/{endpoint}"
    
    @classmethod
    def is_valid_shop_domain(cls, shop: str) -> bool:
        """Validate shop domain format"""
        if not shop:
            return False
        
        # Remove .myshopify.com if present
        shop = shop.replace('.myshopify.com', '')
        
        # Check if valid shop name (alphanumeric and hyphens only)
        if not shop.replace('-', '').isalnum():
            return False
            
        return True
    
    @classmethod
    def normalize_shop_domain(cls, shop: str) -> str:
        """Normalize shop domain to just the shop name"""
        if not shop:
            return ""
            
        # Remove protocol if present
        shop = shop.replace('https://', '').replace('http://', '')
        
        # Remove .myshopify.com if present
        shop = shop.replace('.myshopify.com', '')
        
        return shop.lower()

# Environment-based configuration
OFFLINE_MODE = os.environ.get('OFFLINE_MODE', 'false').lower() == 'true'
MOCK_DATA_PATH = "/app/mock_data"