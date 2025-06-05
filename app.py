"""Main application entry point for YouTube Video Engine."""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import get_config, Config
from api.routes import api_bp
from api.routes_v2 import api_v2_bp
from api.webhooks import webhooks_bp
from utils.logger import setup_logging, APILogger
from flask_swagger_ui import get_swaggerui_blueprint
from utils.metrics import MetricsCollector
from datetime import datetime
import time

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)
api_logger = APILogger()  # Instantiate APILogger for use in this module

# Global metrics collector
metrics_collector = MetricsCollector()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_obj = get_config(config_name)()
    app.config.from_object(config_obj)
    
    # Initialize Sentry for error tracking
    Config.init_sentry(config_name or os.getenv('FLASK_ENV', 'development'))
    
    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config['RATELIMIT_STORAGE_URL'],
        default_limits=[app.config['RATELIMIT_DEFAULT']]
    )
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(api_v2_bp, url_prefix='/api/v2')
    app.register_blueprint(webhooks_bp, url_prefix='/webhooks')
    
    # Setup Swagger UI
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "YouTube Video Engine API",
            'deepLinking': True,
            'displayRequestDuration': True,
            'docExpansion': 'none',
            'defaultModelsExpandDepth': 1,
            'defaultModelExpandDepth': 1,
            'defaultModelRendering': 'example',
            'displayOperationId': False,
            'filter': True,
            'showExtensions': True,
            'showCommonExtensions': True,
            'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch']
        }
    )
    
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Metrics collection middleware
    @app.before_request
    def before_request():
        """Record request start time."""
        app.request_start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Record request metrics."""
        if hasattr(app, 'request_start_time'):
            response_time = time.time() - app.request_start_time
            success = response.status_code < 400
            
            if app.config.get('ENABLE_METRICS', True):
                metrics_collector.record_request(success, response_time)
        
        return response
    
    # Metrics endpoint
    @app.route('/metrics')
    @limiter.exempt
    def metrics():
        """Prometheus-style metrics endpoint."""
        return jsonify(metrics_collector.get_metrics_summary())
    
    # Test logging endpoint
    @app.route('/test-logging')
    @limiter.exempt
    def test_logging():
        """Test logging functionality for debugging."""
        logger.info("🟢 INFO level log test - this should appear in Fly.io logs")
        logger.warning("🟡 WARNING level log test - this should appear in Fly.io logs")
        logger.error("🔴 ERROR level log test - this should appear in Fly.io logs")
        
        # Also test the APILogger
        api_logger.log_api_request('test', 'test-logging', {'message': 'Testing API logging'})
        
        return jsonify({
            'status': 'logging_test_completed',
            'message': 'Check Fly.io logs for test messages',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    
    # Basic health check endpoint (for Fly.io)
    @app.route('/health/basic')
    @limiter.exempt
    def basic_health_check():
        """Fast basic health check endpoint for Fly.io monitoring."""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    
    # Comprehensive health check endpoint
    @app.route('/health')
    @limiter.exempt
    def health_check():
        """Comprehensive health check endpoint."""
        health_status = {
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'services': {}
        }
        
        # Check Airtable connection
        try:
            from services.airtable_service import AirtableService
            airtable = AirtableService()
            # Try to list tables (lightweight operation)
            airtable.base.schema().tables
            health_status['services']['airtable'] = 'connected'
        except Exception as e:
            health_status['services']['airtable'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check NCA Toolkit connection
        try:
            from services.nca_service import NCAService
            nca = NCAService()
            # Try to check service health
            if nca.check_health():
                health_status['services']['nca_toolkit'] = 'connected'
            else:
                health_status['services']['nca_toolkit'] = 'error'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['services']['nca_toolkit'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check ElevenLabs connection
        try:
            from services.elevenlabs_service import ElevenLabsService
            elevenlabs = ElevenLabsService()
            if elevenlabs.check_health():
                health_status['services']['elevenlabs'] = 'connected'
            else:
                health_status['services']['elevenlabs'] = 'error'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['services']['elevenlabs'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check GoAPI connection
        try:
            from services.goapi_service import GoAPIService
            goapi = GoAPIService()
            if goapi.check_health():
                health_status['services']['goapi'] = 'connected'
            else:
                health_status['services']['goapi'] = 'error'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['services']['goapi'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Return appropriate status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors."""
        return jsonify({
            'error': 'Bad Request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle rate limit errors."""
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors."""
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    # Log startup
    logger.info(f"YouTube Video Engine started with config: {config_name or 'default'}")
    
    return app


# Create the application
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])