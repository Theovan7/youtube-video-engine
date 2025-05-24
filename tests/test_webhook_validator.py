"""Tests for webhook signature validation."""

import pytest
import json
import hmac
import hashlib
from unittest.mock import Mock, patch
from flask import Flask, request

from utils.webhook_validator import WebhookValidator, webhook_validation_required


class TestWebhookValidator:
    """Test webhook signature validation."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = Mock()
        
        # Configure test settings
        self.config.WEBHOOK_VALIDATION_ELEVENLABS_ENABLED = True
        self.config.WEBHOOK_SECRET_ELEVENLABS = 'test-secret-elevenlabs'
        
        self.config.WEBHOOK_VALIDATION_NCA_ENABLED = True
        self.config.WEBHOOK_SECRET_NCA = 'test-secret-nca'
        
        self.config.WEBHOOK_VALIDATION_GOAPI_ENABLED = False
        self.config.WEBHOOK_SECRET_GOAPI = 'test-secret-goapi'
        
        self.validator = WebhookValidator(self.config)
    
    def test_validate_signature_sha256(self):
        """Test SHA256 signature validation."""
        payload = b'{"test": "data"}'
        secret = 'test-secret-elevenlabs'
        
        # Calculate expected signature
        expected = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Should validate correct signature
        assert self.validator.validate_signature('elevenlabs', payload, expected) is True
        
        # Should reject incorrect signature
        assert self.validator.validate_signature('elevenlabs', payload, 'wrong-signature') is False
    
    def test_validate_signature_disabled_service(self):
        """Test validation when service is disabled."""
        # GoAPI is disabled in our test config
        assert self.validator.validate_signature('goapi', b'test', 'any-signature') is True
    
    def test_validate_signature_unknown_service(self):
        """Test validation with unknown service."""
        assert self.validator.validate_signature('unknown', b'test', 'signature') is False
    
    def test_validate_signature_no_secret(self):
        """Test validation when no secret is configured."""
        self.config.WEBHOOK_SECRET_ELEVENLABS = ''
        validator = WebhookValidator(self.config)
        assert validator.validate_signature('elevenlabs', b'test', 'signature') is False
    
    def test_get_signature_header(self):
        """Test getting signature header name."""
        assert self.validator.get_signature_header('elevenlabs') == 'X-ElevenLabs-Signature'
        assert self.validator.get_signature_header('nca-toolkit') == 'X-NCA-Signature'
        assert self.validator.get_signature_header('goapi') == 'X-GoAPI-Signature'
        assert self.validator.get_signature_header('unknown') is None
    
    def test_validate_request(self):
        """Test request validation."""
        app = Flask(__name__)
        
        with app.test_request_context(
            method='POST',
            data=b'{"test": "data"}',
            headers={'X-ElevenLabs-Signature': 'invalid'}
        ):
            is_valid, error = self.validator.validate_request('elevenlabs')
            assert is_valid is False
            assert error == 'Invalid signature'
        
        # Test with correct signature
        payload = b'{"test": "data"}'
        secret = 'test-secret-elevenlabs'
        correct_sig = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        with app.test_request_context(
            method='POST',
            data=payload,
            headers={'X-ElevenLabs-Signature': correct_sig}
        ):
            is_valid, error = self.validator.validate_request('elevenlabs')
            assert is_valid is True
            assert error is None
    
    def test_validate_request_missing_header(self):
        """Test request validation with missing header."""
        app = Flask(__name__)
        
        with app.test_request_context(
            method='POST',
            data=b'{"test": "data"}'
        ):
            is_valid, error = self.validator.validate_request('elevenlabs')
            assert is_valid is False
            assert 'Missing signature header' in error
    
    def test_validate_request_disabled_service(self):
        """Test request validation for disabled service."""
        app = Flask(__name__)
        
        with app.test_request_context(
            method='POST',
            data=b'{"test": "data"}'
        ):
            # GoAPI is disabled, should pass validation
            is_valid, error = self.validator.validate_request('goapi')
            assert is_valid is True
            assert error is None


class TestWebhookValidationDecorator:
    """Test webhook validation decorator."""
    
    def test_decorator_with_valid_signature(self):
        """Test decorator allows valid signatures."""
        app = Flask(__name__)
        
        # Mock config
        mock_config = Mock()
        mock_config.WEBHOOK_VALIDATION_ELEVENLABS_ENABLED = True
        mock_config.WEBHOOK_SECRET_ELEVENLABS = 'test-secret'
        mock_config.WEBHOOK_VALIDATION_NCA_ENABLED = False
        mock_config.WEBHOOK_SECRET_NCA = ''
        mock_config.WEBHOOK_VALIDATION_GOAPI_ENABLED = False
        mock_config.WEBHOOK_SECRET_GOAPI = ''
        
        with patch('utils.webhook_validator.get_config') as mock_get_config:
            mock_get_config.return_value = lambda: mock_config
            
            @webhook_validation_required('elevenlabs')
            def test_endpoint():
                return {'status': 'success'}, 200
            
            # Calculate correct signature
            payload = b'{"test": "data"}'
            secret = 'test-secret'
            correct_sig = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            with app.test_request_context(
                method='POST',
                data=payload,
                headers={'X-ElevenLabs-Signature': correct_sig}
            ):
                response, status_code = test_endpoint()
                assert status_code == 200
                assert response['status'] == 'success'
    
    def test_decorator_with_invalid_signature(self):
        """Test decorator rejects invalid signatures."""
        app = Flask(__name__)
        
        # Mock config
        mock_config = Mock()
        mock_config.WEBHOOK_VALIDATION_ELEVENLABS_ENABLED = True
        mock_config.WEBHOOK_SECRET_ELEVENLABS = 'test-secret'
        mock_config.WEBHOOK_VALIDATION_NCA_ENABLED = False
        mock_config.WEBHOOK_SECRET_NCA = ''
        mock_config.WEBHOOK_VALIDATION_GOAPI_ENABLED = False
        mock_config.WEBHOOK_SECRET_GOAPI = ''
        
        with patch('utils.webhook_validator.get_config') as mock_get_config:
            mock_get_config.return_value = lambda: mock_config
            
            @webhook_validation_required('elevenlabs')
            def test_endpoint():
                return {'status': 'success'}, 200
            
            with app.test_request_context(
                method='POST',
                data=b'{"test": "data"}',
                headers={'X-ElevenLabs-Signature': 'invalid-signature'}
            ):
                response = test_endpoint()
                # Response is a JSON response object
                data = response.get_json()
                assert response.status_code == 401
                assert data['status'] == 'error'
                assert 'Invalid webhook signature' in data['message']
    
    def test_decorator_with_disabled_validation(self):
        """Test decorator allows requests when validation is disabled."""
        app = Flask(__name__)
        
        # Mock config with disabled validation
        mock_config = Mock()
        mock_config.WEBHOOK_VALIDATION_ELEVENLABS_ENABLED = False
        mock_config.WEBHOOK_SECRET_ELEVENLABS = ''
        mock_config.WEBHOOK_VALIDATION_NCA_ENABLED = False
        mock_config.WEBHOOK_SECRET_NCA = ''
        mock_config.WEBHOOK_VALIDATION_GOAPI_ENABLED = False
        mock_config.WEBHOOK_SECRET_GOAPI = ''
        
        with patch('utils.webhook_validator.get_config') as mock_get_config:
            mock_get_config.return_value = lambda: mock_config
            
            @webhook_validation_required('elevenlabs')
            def test_endpoint():
                return {'status': 'success'}, 200
            
            with app.test_request_context(
                method='POST',
                data=b'{"test": "data"}'
                # No signature header
            ):
                response, status_code = test_endpoint()
                assert status_code == 200
                assert response['status'] == 'success'
