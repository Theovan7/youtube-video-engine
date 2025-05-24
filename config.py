"""Configuration management for YouTube Video Engine."""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Required environment variables
    REQUIRED_VARS = [
        'AIRTABLE_API_KEY',
        'AIRTABLE_BASE_ID',
        'NCA_API_KEY',
        'ELEVENLABS_API_KEY',
        'GOAPI_API_KEY'
    ]
    
    def __init__(self):
        """Initialize configuration and validate environment."""
        self.validate_environment()
    
    def validate_environment(self):
        """Validate that all required environment variables are set."""
        missing = []
        for var in self.REQUIRED_VARS:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # Airtable Configuration
    AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
    AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
    
    # NCA Toolkit Configuration
    NCA_API_KEY = os.getenv('NCA_API_KEY', 'K2_JVFN!csh&i1248')
    NCA_BASE_URL = os.getenv('NCA_BASE_URL', 'https://no-code-architect-app-gpxhq.ondigitalocean.app')
    NCA_S3_BUCKET_NAME = os.getenv('NCA_S3_BUCKET_NAME', 'phi-bucket')
    NCA_S3_ENDPOINT_URL = os.getenv('NCA_S3_ENDPOINT_URL')
    NCA_S3_ACCESS_KEY = os.getenv('NCA_S3_ACCESS_KEY')
    NCA_S3_SECRET_KEY = os.getenv('NCA_S3_SECRET_KEY')
    NCA_S3_REGION = os.getenv('NCA_S3_REGION', 'nyc3')
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    ELEVENLABS_BASE_URL = 'https://api.elevenlabs.io/v1'
    
    # GoAPI Configuration
    GOAPI_API_KEY = os.getenv('GOAPI_API_KEY')
    GOAPI_BASE_URL = 'https://api.goapi.ai/v1'
    
    # Application Configuration
    WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'http://localhost:5000')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per hour')
    
    # Default Values
    DEFAULT_SEGMENT_DURATION = 30  # seconds
    MAX_PROCESSING_TIME = 300  # seconds (5 minutes)
    
    # Airtable Table Names
    VIDEOS_TABLE = 'Videos'
    SEGMENTS_TABLE = 'Segments'
    JOBS_TABLE = 'Jobs'
    WEBHOOK_EVENTS_TABLE = 'Webhook Events'
    
    # Job Types
    JOB_TYPE_VOICEOVER = 'voiceover'
    JOB_TYPE_COMBINE = 'combine'
    JOB_TYPE_CONCATENATE = 'concatenate'
    JOB_TYPE_MUSIC = 'music'
    JOB_TYPE_FINAL = 'final'
    
    # Status Values
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    # Webhook Validation Configuration
    # ElevenLabs webhook validation
    WEBHOOK_VALIDATION_ELEVENLABS_ENABLED = os.getenv('WEBHOOK_VALIDATION_ELEVENLABS_ENABLED', 'False').lower() == 'true'
    WEBHOOK_SECRET_ELEVENLABS = os.getenv('WEBHOOK_SECRET_ELEVENLABS', '')
    
    # NCA Toolkit webhook validation
    WEBHOOK_VALIDATION_NCA_ENABLED = os.getenv('WEBHOOK_VALIDATION_NCA_ENABLED', 'False').lower() == 'true'
    WEBHOOK_SECRET_NCA = os.getenv('WEBHOOK_SECRET_NCA', '')
    
    # GoAPI webhook validation
    WEBHOOK_VALIDATION_GOAPI_ENABLED = os.getenv('WEBHOOK_VALIDATION_GOAPI_ENABLED', 'False').lower() == 'true'
    WEBHOOK_SECRET_GOAPI = os.getenv('WEBHOOK_SECRET_GOAPI', '')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    
    # Override with test values
    AIRTABLE_API_KEY = 'test-api-key'
    AIRTABLE_BASE_ID = 'test-base-id'
    NCA_API_KEY = 'test-nca-key'
    ELEVENLABS_API_KEY = 'test-elevenlabs-key'
    GOAPI_API_KEY = 'test-goapi-key'
    
    # Skip validation for testing
    def validate_environment(self):
        pass


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    LOG_LEVEL = 'WARNING'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment."""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])