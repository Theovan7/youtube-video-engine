"""Configuration management for YouTube Video Engine."""

import os
import logging
from typing import List
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

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
        'GOAPI_API_KEY',
        'OPENAI_API_KEY'
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
    
    # Local backup configuration
    LOCAL_BACKUP_PATH = os.getenv('LOCAL_BACKUP_PATH', './local_backups')
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    ELEVENLABS_BASE_URL = 'https://api.elevenlabs.io/v1'
    
    # GoAPI Configuration
    GOAPI_API_KEY = os.getenv('GOAPI_API_KEY')
    GOAPI_BASE_URL = os.getenv('GOAPI_BASE_URL', 'https://api.goapi.ai')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = 'https://api.openai.com/v1'
    
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
    VOICES_TABLE = 'Voices'
    JOBS_TABLE = 'Jobs'
    WEBHOOK_EVENTS_TABLE = 'Webhook Events'
    
    # Job Types
    JOB_TYPE_VOICEOVER = 'voiceover'
    JOB_TYPE_COMBINE = 'combine'
    JOB_TYPE_CONCATENATE = 'concatenate'
    JOB_TYPE_MUSIC = 'music'
    JOB_TYPE_FINAL = 'final'
    JOB_TYPE_AI_IMAGE = 'ai_image'
    JOB_TYPE_VIDEO = 'video_generation'
    
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
    
    # Monitoring and Error Tracking Configuration
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'development')
    SENTRY_RELEASE = os.getenv('SENTRY_RELEASE', '1.0.0')
    
    # Slack Notifications
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
    
    # Metrics Collection
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'True').lower() == 'true'
    METRICS_RETENTION_HOURS = int(os.getenv('METRICS_RETENTION_HOURS', '24'))
    
    @staticmethod
    def filter_sentry_events(event, hint):
        """Filter Sentry events to reduce noise."""
        # Don't send health check errors
        if 'health' in event.get('request', {}).get('url', ''):
            return None
            
        # Don't send 404 errors for static assets
        if event.get('response', {}).get('status_code') == 404:
            url = event.get('request', {}).get('url', '')
            if any(ext in url for ext in ['.css', '.js', '.ico', '.png', '.jpg']):
                return None
                
        return event
    
    @staticmethod
    def init_sentry(environment='development'):
        """Initialize Sentry error tracking."""
        sentry_dsn = os.getenv('SENTRY_DSN')
        
        if sentry_dsn:
            sentry_logging = LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FlaskIntegration(transaction_style='endpoint'),
                    sentry_logging,
                ],
                environment=environment,
                release=os.getenv('SENTRY_RELEASE', '1.0.0'),
                traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
                profiles_sample_rate=0.1,  # 10% for profiling
                before_send=Config.filter_sentry_events,
            )
            
            print(f"✅ Sentry initialized for environment: {environment}")
        else:
            print("⚠️ Sentry DSN not configured - error tracking disabled")


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
    OPENAI_API_KEY = 'test-openai-key'
    
    # Skip validation for testing
    def validate_environment(self):
        pass


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings - Use INFO for better debugging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Override webhook URL for production
    WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'https://youtube-video-engine.fly.dev')


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