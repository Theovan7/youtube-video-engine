"""Webhook signature validation utilities."""

import hashlib
import hmac
import logging
import json
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


class WebhookValidator:
    """Validates webhook signatures from external services."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        
        # Configure service-specific settings
        self.service_configs = {
            'elevenlabs': {
                'enabled': config.WEBHOOK_VALIDATION_ELEVENLABS_ENABLED,
                'secret': config.WEBHOOK_SECRET_ELEVENLABS,
                'header': 'X-ElevenLabs-Signature',
                'algorithm': 'sha256',
                'prefix': ''  # Some services prefix the signature
            },
            'nca-toolkit': {
                'enabled': config.WEBHOOK_VALIDATION_NCA_ENABLED,
                'secret': config.WEBHOOK_SECRET_NCA,
                'header': 'X-NCA-Signature',
                'algorithm': 'sha256',
                'prefix': ''
            },
            'goapi': {
                'enabled': config.WEBHOOK_VALIDATION_GOAPI_ENABLED,
                'secret': config.WEBHOOK_SECRET_GOAPI,
                'header': 'X-GoAPI-Signature',
                'algorithm': 'sha256',
                'prefix': ''
            }
        }
    
    def validate_signature(self, service, payload, signature):
        """Validate webhook signature for a specific service.
        
        Args:
            service: Service name (elevenlabs, nca-toolkit, goapi)
            payload: Request payload (bytes or string)
            signature: Signature from request header
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            service_config = self.service_configs.get(service)
            if not service_config:
                logger.error(f"Unknown service for webhook validation: {service}")
                return False
            
            # Skip validation if not enabled
            if not service_config['enabled']:
                logger.debug(f"Webhook validation disabled for {service}")
                return True
            
            # Get secret
            secret = service_config['secret']
            if not secret:
                logger.error(f"No webhook secret configured for {service}")
                return False
            
            # Ensure payload is bytes
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            
            # Calculate expected signature
            algorithm = service_config['algorithm']
            if algorithm == 'sha256':
                expected = hmac.new(
                    secret.encode('utf-8'),
                    payload,
                    hashlib.sha256
                ).hexdigest()
            elif algorithm == 'sha1':
                expected = hmac.new(
                    secret.encode('utf-8'),
                    payload,
                    hashlib.sha1
                ).hexdigest()
            else:
                logger.error(f"Unknown algorithm for {service}: {algorithm}")
                return False
            
            # Add prefix if configured
            prefix = service_config['prefix']
            if prefix:
                expected = f"{prefix}{expected}"
            
            # Compare signatures
            is_valid = hmac.compare_digest(signature, expected)
            
            if not is_valid:
                logger.warning(f"Invalid webhook signature for {service}")
                logger.debug(f"Expected: {expected}, Got: {signature}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating webhook signature for {service}: {e}")
            return False
    
    def get_signature_header(self, service):
        """Get the signature header name for a service."""
        service_config = self.service_configs.get(service)
        if service_config:
            return service_config['header']
        return None
    
    def validate_request(self, service):
        """Validate the current Flask request for a service.
        
        Args:
            service: Service name
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            service_config = self.service_configs.get(service)
            if not service_config:
                return False, f"Unknown service: {service}"
            
            # Skip if not enabled
            if not service_config['enabled']:
                return True, None
            
            # Get signature from header
            header_name = service_config['header']
            signature = request.headers.get(header_name)
            
            if not signature:
                return False, f"Missing signature header: {header_name}"
            
            # Get raw payload
            payload = request.get_data()
            
            # Validate
            if self.validate_signature(service, payload, signature):
                return True, None
            else:
                return False, "Invalid signature"
                
        except Exception as e:
            logger.error(f"Error validating request for {service}: {e}")
            return False, str(e)


def webhook_validation_required(service):
    """Decorator to require webhook validation for an endpoint.
    
    Args:
        service: Service name for validation
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Import here to avoid circular imports
            from config import get_config
            
            # Get validator
            config = get_config()()
            validator = WebhookValidator(config)
            
            # Validate request
            is_valid, error_message = validator.validate_request(service)
            
            if not is_valid:
                logger.warning(f"Webhook validation failed for {service}: {error_message}")
                return jsonify({
                    'status': 'error',
                    'message': 'Unauthorized: Invalid webhook signature',
                    'error': error_message
                }), 401
            
            # Continue to the actual handler
            return f(*args, **kwargs)
            
        return decorated_function
    return decorator
