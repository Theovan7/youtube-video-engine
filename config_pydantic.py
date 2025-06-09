"""
Pydantic-based configuration management for YouTube Video Engine.
"""

import os
import logging
from typing import Optional, Literal, List
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with Pydantic validation."""
    
    # Flask Configuration
    secret_key: str = Field(default='dev-secret-key-change-in-production', env='SECRET_KEY')
    debug: bool = Field(default=False, env='FLASK_DEBUG')
    testing: bool = Field(default=False)
    flask_env: str = Field(default='development', env='FLASK_ENV')
    
    # Airtable Configuration
    airtable_api_key: str = Field(..., env='AIRTABLE_API_KEY')
    airtable_base_id: str = Field(..., env='AIRTABLE_BASE_ID')
    
    # NCA Toolkit Configuration
    nca_api_key: str = Field(default='K2_JVFN!csh&i1248', env='NCA_API_KEY')
    nca_base_url: str = Field(
        default='https://no-code-architect-app-gpxhq.ondigitalocean.app',
        env='NCA_BASE_URL'
    )
    nca_s3_bucket_name: str = Field(default='phi-bucket', env='NCA_S3_BUCKET_NAME')
    nca_s3_endpoint_url: Optional[str] = Field(None, env='NCA_S3_ENDPOINT_URL')
    nca_s3_access_key: Optional[str] = Field(None, env='NCA_S3_ACCESS_KEY')
    nca_s3_secret_key: Optional[str] = Field(None, env='NCA_S3_SECRET_KEY')
    nca_s3_region: str = Field(default='nyc3', env='NCA_S3_REGION')
    
    # Local backup configuration
    local_backup_path: str = Field(default='./local_backups', env='LOCAL_BACKUP_PATH')
    
    # Remote backup configuration
    local_receiver_url: Optional[str] = Field(None, env='LOCAL_RECEIVER_URL')
    local_upload_secret: Optional[str] = Field(None, env='LOCAL_UPLOAD_SECRET')
    
    # ElevenLabs Configuration
    elevenlabs_api_key: str = Field(..., env='ELEVENLABS_API_KEY')
    elevenlabs_base_url: str = Field(default='https://api.elevenlabs.io/v1')
    
    # GoAPI Configuration
    goapi_api_key: str = Field(..., env='GOAPI_API_KEY')
    goapi_base_url: str = Field(default='https://api.goapi.ai', env='GOAPI_BASE_URL')
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    openai_base_url: str = Field(default='https://api.openai.com/v1')
    
    # Application Configuration
    webhook_base_url: str = Field(default='http://localhost:5000', env='WEBHOOK_BASE_URL')
    
    # Job Polling Configuration
    polling_enabled: bool = Field(default=True, env='POLLING_ENABLED')
    polling_interval_minutes: int = Field(default=2, ge=1, env='POLLING_INTERVAL_MINUTES')
    polling_max_age_hours: int = Field(default=24, ge=1, env='POLLING_MAX_AGE_HOURS')
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = Field(
        default='INFO', env='LOG_LEVEL'
    )
    
    # Rate Limiting Configuration
    ratelimit_storage_url: str = Field(default='memory://', env='RATELIMIT_STORAGE_URL')
    ratelimit_default: str = Field(default='100 per hour', env='RATELIMIT_DEFAULT')
    
    # Default Values
    default_segment_duration: int = Field(default=30, ge=10, le=300)
    max_processing_time: int = Field(default=300, ge=60, le=3600)
    
    # Table Names (constants)
    videos_table: Literal['Videos'] = 'Videos'
    segments_table: Literal['Segments'] = 'Segments'
    voices_table: Literal['Voices'] = 'Voices'
    jobs_table: Literal['Jobs'] = 'Jobs'
    webhook_events_table: Literal['Webhook Events'] = 'Webhook Events'
    
    # Job Types (constants)
    job_type_voiceover: Literal['voiceover'] = 'voiceover'
    job_type_combine: Literal['combine'] = 'combine'
    job_type_concatenate: Literal['concatenate'] = 'concatenate'
    job_type_music: Literal['music'] = 'music'
    job_type_final: Literal['final'] = 'final'
    job_type_ai_image: Literal['ai_image'] = 'ai_image'
    job_type_video: Literal['video_generation'] = 'video_generation'
    
    # Status Values (constants)
    status_pending: Literal['pending'] = 'pending'
    status_processing: Literal['processing'] = 'processing'
    status_completed: Literal['completed'] = 'completed'
    status_failed: Literal['failed'] = 'failed'
    
    # Webhook Validation Configuration
    webhook_validation_elevenlabs_enabled: bool = Field(
        default=False, env='WEBHOOK_VALIDATION_ELEVENLABS_ENABLED'
    )
    webhook_secret_elevenlabs: str = Field(default='', env='WEBHOOK_SECRET_ELEVENLABS')
    
    webhook_validation_nca_enabled: bool = Field(
        default=False, env='WEBHOOK_VALIDATION_NCA_ENABLED'
    )
    webhook_secret_nca: str = Field(default='', env='WEBHOOK_SECRET_NCA')
    
    webhook_validation_goapi_enabled: bool = Field(
        default=False, env='WEBHOOK_VALIDATION_GOAPI_ENABLED'
    )
    webhook_secret_goapi: str = Field(default='', env='WEBHOOK_SECRET_GOAPI')
    
    # Monitoring and Error Tracking
    sentry_dsn: Optional[str] = Field(None, env='SENTRY_DSN')
    sentry_environment: str = Field(default='development', env='SENTRY_ENVIRONMENT')
    sentry_release: str = Field(default='1.0.0', env='SENTRY_RELEASE')
    
    # Slack Notifications
    slack_webhook_url: Optional[str] = Field(None, env='SLACK_WEBHOOK_URL')
    
    # Metrics Collection
    enable_metrics: bool = Field(default=True, env='ENABLE_METRICS')
    metrics_retention_hours: int = Field(default=24, ge=1, env='METRICS_RETENTION_HOURS')
    
    @field_validator('debug', 'testing', 'polling_enabled', 'webhook_validation_elevenlabs_enabled',
                     'webhook_validation_nca_enabled', 'webhook_validation_goapi_enabled',
                     'enable_metrics', mode='before')
    @classmethod
    def parse_bool(cls, v):
        """Parse boolean from string."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    @field_validator('webhook_base_url')
    @classmethod
    def ensure_no_trailing_slash(cls, v):
        """Remove trailing slash from webhook URL."""
        return str(v).rstrip('/')
    
    @model_validator(mode='after')
    def validate_webhook_secrets(self):
        """Validate webhook secrets are provided when validation is enabled."""
        if self.webhook_validation_elevenlabs_enabled and not self.webhook_secret_elevenlabs:
            raise ValueError('webhook_secret_elevenlabs is required when webhook_validation_elevenlabs_enabled is True')
        
        if self.webhook_validation_nca_enabled and not self.webhook_secret_nca:
            raise ValueError('webhook_secret_nca is required when webhook_validation_nca_enabled is True')
        
        if self.webhook_validation_goapi_enabled and not self.webhook_secret_goapi:
            raise ValueError('webhook_secret_goapi is required when webhook_validation_goapi_enabled is True')
        
        return self
    
    @model_validator(mode='after')
    def validate_backup_config(self):
        """Validate backup configuration."""
        if self.local_receiver_url and not self.local_upload_secret:
            raise ValueError('local_upload_secret is required when local_receiver_url is set')
        return self
    
    def init_sentry(self):
        """Initialize Sentry error tracking."""
        if self.sentry_dsn:
            sentry_logging = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
            
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                integrations=[
                    FlaskIntegration(transaction_style='endpoint'),
                    sentry_logging,
                ],
                environment=self.sentry_environment,
                release=self.sentry_release,
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                before_send=self._filter_sentry_events,
            )
            
            print(f"✅ Sentry initialized for environment: {self.sentry_environment}")
        else:
            print("⚠️ Sentry DSN not configured - error tracking disabled")
    
    @staticmethod
    def _filter_sentry_events(event, hint):
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
    
    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8',
        'case_sensitive': False,
        'extra': 'ignore',  # Ignore extra env vars
    }


class DevelopmentSettings(Settings):
    """Development-specific settings."""
    debug: bool = True
    flask_env: str = 'development'
    

class TestingSettings(Settings):
    """Testing-specific settings."""
    testing: bool = True
    debug: bool = True
    flask_env: str = 'testing'
    
    # Override with test values
    airtable_api_key: str = 'test-api-key'
    airtable_base_id: str = 'test-base-id'
    nca_api_key: str = 'test-nca-key'
    elevenlabs_api_key: str = 'test-elevenlabs-key'
    goapi_api_key: str = 'test-goapi-key'
    openai_api_key: str = 'test-openai-key'


class ProductionSettings(Settings):
    """Production-specific settings."""
    debug: bool = False
    testing: bool = False
    flask_env: str = 'production'
    log_level: str = 'INFO'
    
    # Override webhook URL for production
    webhook_base_url: str = Field(
        default='https://youtube-video-engine.fly.dev',
        env='WEBHOOK_BASE_URL'
    )


# Configuration factory
def get_settings(env: Optional[str] = None) -> Settings:
    """Get settings based on environment."""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    settings_map = {
        'development': DevelopmentSettings,
        'testing': TestingSettings,
        'production': ProductionSettings,
    }
    
    settings_class = settings_map.get(env, Settings)
    return settings_class()


# Backwards compatibility
def get_config(env=None):
    """Get configuration (backwards compatible)."""
    return get_settings(env)


# Create a singleton instance
settings = get_settings()