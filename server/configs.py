"""Flask application configuration"""
from decouple import config
import os

# Development configuration (default)
DB_HOST = config('DB_HOST')  # Must be set in environment
DB_USER = config('DB_USER')  # Must be set in environment
DB_PASSWORD = config('DB_PASSWORD')  # Must be set in environment
DB_NAME = config('DB_NAME')  # Must be set in environment

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_DB = config('REDIS_DB', default=0, cast=int)

SECRET_KEY = config('SECRET_KEY')  # Must be set in environment
CORS_ORIGINS = config('CORS_ORIGINS', default='http://localhost:5000').split(',')

REPO_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repos')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

CACHE_DEFAULT_TIMEOUT = 300
CACHE_TYPE = 'redis'

LOG_LEVEL = config('LOG_LEVEL', default='INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(os.path.dirname(__file__), 'server.log')

class Config:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
    CORS_ORIGINS = CORS_ORIGINS
    REPO_BASE = REPO_BASE
    MAX_FILE_SIZE = MAX_FILE_SIZE
    DEFAULT_PAGE_SIZE = DEFAULT_PAGE_SIZE
    MAX_PAGE_SIZE = MAX_PAGE_SIZE
    CACHE_DEFAULT_TIMEOUT = CACHE_DEFAULT_TIMEOUT
    CACHE_TYPE = CACHE_TYPE
    LOG_LEVEL = LOG_LEVEL
    LOG_FORMAT = LOG_FORMAT
    LOG_FILE = LOG_FILE
    DEBUG = False
    DEVELOPMENT = False

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DEVELOPMENT = True

# Development settings
DEBUG = True
DEVELOPMENT = True

