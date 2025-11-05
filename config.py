import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM') or 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # External API URLs
    UMS_URL = os.environ.get('UMS_URL') or 'http://localhost:5000'  # UMS runs on port 5000
    LINKSHUB_CORE_URL = os.environ.get('LINKSHUB_CORE_URL') or 'https://core.linkstechnologies.io'
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else ['*']
    
    # API Configuration
    API_VERSION = os.environ.get('API_VERSION') or 'v1'
    
    # Pagination
    DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', 20))
    MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', 100))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///case_service_dev.db'
    LOG_LEVEL = 'DEBUG'

class QAConfig(Config):
    """QA/Testing configuration."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///case_service_qa.db'
    LOG_LEVEL = 'INFO'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/case_service_prod'
    LOG_LEVEL = 'WARNING'
    
    # Enhanced security for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'qa': QAConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}