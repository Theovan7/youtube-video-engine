#!/usr/bin/env python3
"""
Debug script to test webhook payload structure
"""

import json
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/debug/goapi', methods=['POST'])
def debug_goapi_webhook():
    """Debug endpoint to see raw webhook payload."""
    try:
        # Get all data about the request
        raw_data = request.get_data()
        json_data = request.get_json()
        headers = dict(request.headers)
        args = dict(request.args)
        
        logger.info("=== GoAPI Webhook Debug ===")
        logger.info(f"Headers: {json.dumps(headers, indent=2)}")
        logger.info(f"Query Args: {json.dumps(args, indent=2)}")
        logger.info(f"Raw Data: {raw_data}")
        logger.info(f"JSON Data: {json.dumps(json_data, indent=2) if json_data else 'None'}")
        
        # Check for status field
        if json_data:
            status = json_data.get('status')
            logger.info(f"Status field: {status}")
        
        return jsonify({
            'received': True,
            'headers': headers,
            'args': args,
            'json': json_data,
            'raw': str(raw_data)
        })
        
    except Exception as e:
        logger.error(f"Error in debug webhook: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8081, debug=True)
