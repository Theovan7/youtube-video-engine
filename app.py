"""Main application entry point for YouTube Video Engine."""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import get_config
from api.routes import api_bp
from api.webhooks import webhooks_bp
from utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Create and configure the Flask application."""
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_obj = get_config(config_name)()
    app.config.from_object(config_obj)
    
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
    app.register_blueprint(webhooks_bp, url_prefix='/webhooks')
    
    # Health check endpoint
    @app.route('/health')
    @limiter.exempt
    def health_check():
        """Comprehensive health check endpoint."""
        health_status = {
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': os.popen('date').read().strip(),
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