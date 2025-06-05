"""Logging configuration for YouTube Video Engine."""

import logging
import sys
from pythonjsonlogger import jsonlogger
from config import get_config


def setup_logging():
    """Set up logging configuration."""
    config = get_config()()
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Create formatter
    if config.DEBUG:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # JSON format for production
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
            rename_fields={'asctime': '@timestamp', 'levelname': 'severity'}
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


class APILogger:
    """Logger for API requests and responses."""
    
    def __init__(self):
        self.logger = logging.getLogger('youtube_video_engine')
    
    def log_api_request(self, service, endpoint, payload):
        """Log API request details."""
        self.logger.info({
            'type': 'api_request',
            'service': service,
            'endpoint': endpoint,
            'payload': payload
        })
    
    def log_api_response(self, service, endpoint, status_code, response):
        """Log API response details."""
        self.logger.info({
            'type': 'api_response',
            'service': service,
            'endpoint': endpoint,
            'status_code': status_code,
            'response': response
        })
    
    def log_webhook(self, service, payload):
        """Log webhook received."""
        self.logger.info({
            'type': 'webhook_received',
            'service': service,
            'payload': payload
        })
    
    def log_error(self, service, error, context=None):
        """Log error details."""
        self.logger.error({
            'type': 'error',
            'service': service,
            'error': str(error),
            'error_type': type(error).__name__,
            'context': context
        })
    
    def log_job_status(self, job_id, status, details=None):
        """Log job status change."""
        self.logger.info({
            'type': 'job_status',
            'job_id': job_id,
            'status': status,
            'details': details
        })