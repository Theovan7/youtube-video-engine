#!/usr/bin/env python3
"""
Test webhook logging endpoint to debug NCA webhook delivery issues.
This creates a simple logging endpoint that captures ALL webhook attempts.
"""

import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('webhook_debug.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.before_request
def log_all_requests():
    """Log ALL incoming requests for debugging."""
    logger.info("="*60)
    logger.info(f"REQUEST RECEIVED: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Query Args: {dict(request.args)}")
    
    # Try to get body data
    try:
        if request.content_type and 'json' in request.content_type:
            data = request.get_json(silent=True)
            logger.info(f"JSON Body: {json.dumps(data, indent=2) if data else 'None'}")
        else:
            data = request.get_data(as_text=True)
            logger.info(f"Raw Body: {data[:1000]}")  # First 1000 chars
    except Exception as e:
        logger.error(f"Error reading body: {e}")
    
    logger.info("="*60)

@app.route('/webhooks/nca-toolkit', methods=['GET', 'POST', 'PUT'])
def nca_webhook_debug():
    """Debug endpoint that accepts any method and logs everything."""
    response = {
        'status': 'logged',
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'url': request.url,
        'args': dict(request.args)
    }
    
    # Try to get the body
    try:
        if request.is_json:
            response['body'] = request.get_json()
        else:
            response['body'] = request.get_data(as_text=True)
    except:
        response['body'] = 'Could not read body'
    
    logger.info(f"RESPONSE: {json.dumps(response, indent=2)}")
    
    return jsonify(response), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/', methods=['GET', 'POST', 'PUT'])
def catch_all():
    """Catch all other requests for debugging."""
    logger.warning(f"Unmatched route: {request.method} {request.url}")
    return jsonify({
        'status': 'logged',
        'message': 'Request logged but no matching route',
        'url': request.url
    }), 200

if __name__ == '__main__':
    print("Starting webhook debug server on port 5001...")
    print("Logs will be written to webhook_debug.log")
    print("Test with: curl http://localhost:5001/webhooks/nca-toolkit?job_id=test123")
    app.run(host='0.0.0.0', port=5001, debug=True)