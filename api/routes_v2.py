"""API v2 routes for YouTube Video Engine - Webhook-based architecture."""

import logging
from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError

from services.airtable_service import AirtableService
from services.script_processor import ScriptProcessor

logger = logging.getLogger(__name__)

# Create v2 blueprint for webhook-based architecture
api_v2_bp = Blueprint('api_v2', __name__)

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize services
airtable = AirtableService()
script_processor = ScriptProcessor()


class ProcessScriptWebhookSchema(Schema):
    """Schema for webhook-based process script request."""
    record_id = fields.String(required=True)


@api_v2_bp.route('/process-script', methods=['POST'])
@limiter.limit("10 per minute")
def process_script_webhook():
    """Process a script into timed segments using webhook architecture."""
    try:
        # Validate input
        schema = ProcessScriptWebhookSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Fetch video record from Airtable
        video = airtable.get_video(data['record_id'])
        if not video:
            return jsonify({'error': 'Video record not found'}), 404
        
        # Get ONLY the Video Script field
        script_text = video['fields'].get('Video Script')
        if not script_text:
            return jsonify({'error': 'Video Script field is empty'}), 400
        
        # Process script into segments using newline-based segmentation
        segments = script_processor.process_script_by_newlines(script_text)
        
        # Convert segments to Airtable format
        segment_data = []
        for segment in segments:
            segment_dict = segment.to_dict()
            segment_data.append({
                'text': segment_dict['text'],
                'start_time': segment_dict['start_time'],
                'end_time': segment_dict['end_time']
            })
        
        # Create segment records
        segment_records = airtable.create_segments(data['record_id'], segment_data)
        
        # Note: NOT updating any status fields or other video fields as per requirements
        
        return jsonify({
            'video_id': data['record_id'],
            'total_segments': len(segment_records),
            'estimated_duration': sum(s.estimated_duration for s in segments),
            'segments': [
                {
                    'id': record['id'],
                    'order': record['fields'].get('SRT Segment ID', i+1),
                    'text': record['fields'].get('SRT Text', ''),
                    'duration': record['fields'].get('End Time', 0) - record['fields'].get('Start Time', 0)
                }
                for i, record in enumerate(segment_records)
            ]
        }), 201
        
    except Exception as e:
        logger.error(f"Error processing script: {e}")
        return jsonify({'error': 'Failed to process script', 'details': str(e)}), 500


@api_v2_bp.route('/status', methods=['GET'])
def status_v2():
    """Simple status endpoint for v2 API."""
    return jsonify({
        'status': 'ok',
        'version': 'v2',
        'architecture': 'webhook-based',
        'message': 'YouTube Video Engine API v2 is running'
    })
