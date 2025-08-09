"""
Application settings and configuration
"""
import os
from typing import List


class Settings:
    """Application configuration settings"""
    
    # Database
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'returns_management')
    
    # CORS
    CORS_ORIGINS: List[str] = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # API
    API_PREFIX: str = "/api"
    
    # Application
    APP_NAME: str = "Returns Management SaaS API"
    APP_VERSION: str = "1.0.0"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    # Return Rules
    DEFAULT_RETURN_WINDOW_DAYS: int = 30
    
    # Debug
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'


settings = Settings()