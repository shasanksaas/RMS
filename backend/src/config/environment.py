"""
Environment Configuration Service
Automatically detects APP_URL, API credentials, and other environment-specific settings
"""
import os
import json
import aiohttp
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class EnvironmentConfig:
    """
    Centralized configuration service that automatically detects environment settings
    """
    
    def __init__(self):
        self._config = {}
        self._app_url = None
        self._shopify_credentials = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize configuration on startup"""
        if self._initialized:
            return
            
        # Detect APP_URL
        self._app_url = await self._detect_app_url()
        
        # Load Shopify credentials
        self._shopify_credentials = await self._load_shopify_credentials()
        
        # Load additional config if available
        await self._load_optional_config()
        
        self._initialized = True
        
        # Log configuration for debugging
        self._log_configuration()
    
    async def _detect_app_url(self) -> str:
        """
        Automatically detect the APP_URL from various sources
        Priority order:
        1. APP_URL environment variable (if set)
        2. RENDER_EXTERNAL_URL (Render.com)
        3. VERCEL_URL (Vercel)
        4. RAILWAY_STATIC_URL (Railway)
        5. PORT + hostname detection
        6. Fallback to localhost
        """
        
        # 1. Check explicit APP_URL
        app_url = os.environ.get('APP_URL')
        if app_url:
            print(f"✅ Using explicit APP_URL: {app_url}")
            return app_url.rstrip('/')
        
        # 2. Check Render.com
        render_url = os.environ.get('RENDER_EXTERNAL_URL')
        if render_url:
            print(f"✅ Detected Render deployment: {render_url}")
            return render_url.rstrip('/')
        
        # 3. Check Vercel
        vercel_url = os.environ.get('VERCEL_URL')
        if vercel_url:
            full_url = f"https://{vercel_url}" if not vercel_url.startswith('http') else vercel_url
            print(f"✅ Detected Vercel deployment: {full_url}")
            return full_url.rstrip('/')
        
        # 4. Check Railway
        railway_url = os.environ.get('RAILWAY_STATIC_URL')
        if railway_url:
            print(f"✅ Detected Railway deployment: {railway_url}")
            return railway_url.rstrip('/')
        
        # 5. Check for Emergent preview environment
        emergent_preview = os.environ.get('preview_endpoint')
        if emergent_preview:
            print(f"✅ Detected Emergent preview: {emergent_preview}")
            return emergent_preview.rstrip('/')
        
        # 6. Check legacy Emergent variable
        emergent_url = os.environ.get('EMERGENT_PREVIEW_URL')
        if emergent_url:
            print(f"✅ Detected Emergent preview (legacy): {emergent_url}")
            return emergent_url.rstrip('/')
        
        # 7. Try to detect from common environment patterns
        port = os.environ.get('PORT', '8001')
        host = os.environ.get('HOST', 'localhost')
        
        # Check if we're in a cloud environment
        if any(env_var in os.environ for env_var in ['DYNO', 'KUBERNETES_SERVICE_HOST', 'GOOGLE_CLOUD_PROJECT']):
            # Try to get external hostname
            try:
                # For Google Cloud Run, Railway, etc.
                if 'GOOGLE_CLOUD_PROJECT' in os.environ:
                    service_name = os.environ.get('K_SERVICE', 'app')
                    region = os.environ.get('GOOGLE_CLOUD_REGION', 'us-central1')
                    project = os.environ.get('GOOGLE_CLOUD_PROJECT')
                    detected_url = f"https://{service_name}-{project}.{region}.run.app"
                    print(f"✅ Detected Google Cloud Run: {detected_url}")
                    return detected_url
            except Exception:
                pass
        
        # 7. Fallback based on current environment
        if host == 'localhost' or host == '127.0.0.1':
            fallback_url = f"http://localhost:{port}"
        else:
            # Assume HTTPS for production environments
            fallback_url = f"https://{host}" if port in ['80', '443'] else f"https://{host}:{port}"
        
        print(f"⚠️ Using fallback APP_URL: {fallback_url}")
        return fallback_url
    
    async def _load_shopify_credentials(self) -> Dict[str, str]:
        """
        Load Shopify API credentials from environment variables
        """
        credentials = {}
        
        # Required credentials
        api_key = os.environ.get('SHOPIFY_API_KEY')
        api_secret = os.environ.get('SHOPIFY_API_SECRET')
        
        if not api_key or not api_secret:
            print("⚠️ SHOPIFY_API_KEY or SHOPIFY_API_SECRET not found in environment")
            print("   Set these environment variables for Shopify integration to work")
        
        credentials.update({
            'api_key': api_key or '',
            'api_secret': api_secret or '',
            'api_version': os.environ.get('SHOPIFY_API_VERSION', '2025-07'),
            'scopes': os.environ.get('SHOPIFY_SCOPES', 'read_orders,read_fulfillments,read_products,read_customers,read_returns,write_returns')
        })
        
        return credentials
    
    async def _load_optional_config(self):
        """
        Load optional configuration from external sources (S3, HTTP endpoint, etc.)
        """
        config_url = os.environ.get('CONFIG_URL')
        if not config_url:
            return
        
        try:
            print(f"📥 Loading configuration from: {config_url}")
            
            if config_url.startswith('http'):
                # Load from HTTP endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.get(config_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            remote_config = await response.json()
                            self._merge_config(remote_config)
                            print("✅ Remote configuration loaded successfully")
                        else:
                            print(f"⚠️ Failed to load remote config: HTTP {response.status}")
            
            elif config_url.startswith('s3://'):
                # Load from S3 (would need boto3)
                print("⚠️ S3 configuration loading not implemented yet")
            
            elif os.path.exists(config_url):
                # Load from local file
                with open(config_url, 'r') as f:
                    local_config = json.load(f)
                    self._merge_config(local_config)
                    print("✅ Local configuration file loaded")
                    
        except Exception as e:
            print(f"⚠️ Failed to load optional configuration: {e}")
    
    def _merge_config(self, remote_config: Dict[str, Any]):
        """Merge remote configuration with environment variables (env takes precedence)"""
        for key, value in remote_config.items():
            env_key = key.upper()
            if env_key not in os.environ:
                os.environ[env_key] = str(value)
                print(f"📝 Set {env_key} from remote config")
    
    def _log_configuration(self):
        """Log current configuration for debugging"""
        print("\n" + "=" * 50)
        print("🔧 ENVIRONMENT CONFIGURATION")
        print("=" * 50)
        print(f"APP_URL: {self._app_url}")
        print(f"Redirect URI: {self.get_oauth_redirect_uri()}")
        print(f"Shopify API Key: {self._shopify_credentials.get('api_key', 'NOT_SET')[:10]}...")
        print(f"Shopify API Version: {self._shopify_credentials.get('api_version')}")
        print(f"Shopify Scopes: {self._shopify_credentials.get('scopes')}")
        print("=" * 50 + "\n")
    
    def get_app_url(self) -> str:
        """Get the detected APP_URL"""
        return self._app_url
    
    def get_oauth_redirect_uri(self) -> str:
        """Get the OAuth redirect URI built from APP_URL"""
        return f"{self._app_url}/api/auth/shopify/callback"
    
    def get_shopify_credentials(self) -> Dict[str, str]:
        """Get Shopify API credentials"""
        return self._shopify_credentials.copy()
    
    def get_shopify_api_key(self) -> Optional[str]:
        """Get Shopify API key"""
        return self._shopify_credentials.get('api_key')
    
    def get_shopify_api_secret(self) -> Optional[str]:
        """Get Shopify API secret"""
        return self._shopify_credentials.get('api_secret')
    
    def get_shopify_scopes(self) -> str:
        """Get Shopify OAuth scopes"""
        return self._shopify_credentials.get('scopes', 'read_orders,read_fulfillments,read_products,read_customers,read_returns,write_returns')
    
    def get_shopify_api_version(self) -> str:
        """Get Shopify API version"""
        return self._shopify_credentials.get('api_version', '2025-07')
    
    def update_app_url_from_request(self, request_host: str, request_scheme: str = 'https'):
        """
        Update APP_URL from request context if not already set
        This is useful for dynamic environments where the URL can't be detected at startup
        """
        if not self._app_url or 'localhost' in self._app_url:
            detected_url = f"{request_scheme}://{request_host}"
            print(f"🔄 Updating APP_URL from request: {detected_url}")
            self._app_url = detected_url
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return not ('localhost' in self._app_url or '127.0.0.1' in self._app_url)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for health checks"""
        return {
            'app_url': self._app_url,
            'redirect_uri': self.get_oauth_redirect_uri(),
            'shopify_configured': bool(self.get_shopify_api_key() and self.get_shopify_api_secret()),
            'environment': 'production' if self.is_production() else 'development',
            'initialized': self._initialized
        }


# Global configuration instance
env_config = EnvironmentConfig()