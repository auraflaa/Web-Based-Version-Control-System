"""Configuration module for the Flask application."""
from decouple import config
import os

class Config:
    """Base configuration."""
    DB_HOST = config('DB_HOST', default='localhost')
    DB_USER = config('DB_USER', default='root')
    DB_PASSWORD = config('DB_PASSWORD')
    DB_NAME = config('DB_NAME', default='codehub')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    REDIS_HOST = config('REDIS_HOST', default='localhost')
    REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
    REDIS_DB = config('REDIS_DB', default=0, cast=int)
    
    SECRET_KEY = config('SECRET_KEY', default='your-secret-key-here')
    CORS_ORIGINS = config('CORS_ORIGINS', default='http://localhost:5000').split(',')
    
    REPO_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repos')
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100
    
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_TYPE = 'redis'
    
    LOG_LEVEL = config('LOG_LEVEL', default='INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'server.log')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DEVELOPMENT = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DEVELOPMENT = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Make configuration classes available at package level
__all__ = ['Config', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig']