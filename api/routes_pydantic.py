"""API routes using Pydantic models for validation."""

import logging
import uuid
from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pydantic import ValidationError

from config import get_config
from services.airtable_service import AirtableService
from services.script_processor import ScriptProcessor
from services.elevenlabs_service import ElevenLabsService
from services.nca_service import NCAService
from services.goapi_service import GoAPIService
from utils.logger import APILogger

# Import Pydantic models
from models.api.requests import (
    ProcessScriptRequest,
    GenerateVoiceoverRequest,
    CombineSegmentMediaRequest,
    CombineAllSegmentsRequest,
    GenerateAndAddMusicRequest
)
from models.api.responses import (
    ProcessScriptResponse,
    GenerateVoiceoverResponse,
    CombineMediaResponse,
    JobCreatedResponse,
    StatusResponse,
    ErrorResponse,
    SegmentInfo
)

logger = logging.getLogger(__name__)
api_logger = APILogger()

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize services
airtable = AirtableService()
script_processor = ScriptProcessor()
config = get_config()()


def validate_request(model_class, data):
    """Validate request data using Pydantic model."""
    try:
        return model_class(**data)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = '.'.join(str(x) for x in error['loc'])
            error_details.append({
                'field': field,
                'message': error['msg'],
                'type': error['type']
            })
        raise ValueError(error_details)


@api_bp.route('/status', methods=['GET'])
def status():
    """Simple status endpoint."""
    response = StatusResponse(
        status='ok',
        message='YouTube Video Engine API is running'
    )
    return jsonify(response.dict())


@api_bp.route('/process-script', methods=['POST'])
@limiter.limit("10 per minute")
def process_script():
    """Process a script into timed segments."""
    try:
        # Validate input using Pydantic
        data = validate_request(ProcessScriptRequest, request.json or {})
    except ValueError as err:
        error_response = ErrorResponse(error='Validation error', details=err)
        return jsonify(error_response.dict()), 400
    
    try:
        # Create video record
        video = airtable.create_video(
            name=data.video_name,
            script=data.script_text,
            music_prompt=data.music_prompt
        )
        video_id = video['id']
        
        # Process script into segments
        segments = script_processor.process_script(
            data.script_text,
            data.target_segment_duration
        )
        
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
        segment_records = airtable.create_segments(video_id, segment_data)
        
        # Update video status
        airtable.update_video_status(video_id, 'segments_created')
        
        # Build response
        segment_infos = []
        for i, record in enumerate(segment_records):
            fields = record['fields']
            segment_infos.append(SegmentInfo(
                id=record['id'],
                order=fields.get('SRT Segment ID', i+1),
                text=fields.get('SRT Text', ''),
                duration=fields.get('End Time', 0) - fields.get('Start Time', 0)
            ))
        
        response = ProcessScriptResponse(
            video_id=video_id,
            video_name=data.video_name,
            total_segments=len(segment_records),
            estimated_duration=sum(s.estimated_duration for s in segments),
            status='segments_created',
            segments=segment_infos
        )
        
        return jsonify(response.dict()), 201
        
    except Exception as e:
        logger.error(f"Error processing script: {e}")
        if 'video_id' in locals():
            airtable.update_video_status(video_id, 'failed', str(e))
        error_response = ErrorResponse(error='Failed to process script', details=str(e))
        return jsonify(error_response.dict()), 500


@api_bp.route('/generate-voiceover', methods=['POST'])
@limiter.limit("20 per minute")
def generate_voiceover():
    """Generate voiceover for a segment."""
    try:
        # Validate input using Pydantic
        data = validate_request(GenerateVoiceoverRequest, request.json or {})
    except ValueError as err:
        error_response = ErrorResponse(error='Validation error', details=err)
        return jsonify(error_response.dict()), 400
    
    try:
        # Initialize ElevenLabs service
        elevenlabs = ElevenLabsService()
        
        # Get segment from Airtable
        segment = airtable.get_segment(data.segment_id)
        if not segment:
            error_response = ErrorResponse(error='Segment not found')
            return jsonify(error_response.dict()), 404
        
        text = segment['fields'].get('SRT Text', '')
        if not text:
            error_response = ErrorResponse(error='Segment has no text')
            return jsonify(error_response.dict()), 400
        
        # Generate voiceover synchronously
        result = elevenlabs.generate_voice_sync(
            text=text,
            voice_id=data.voice_id,
            stability=data.stability,
            similarity_boost=data.similarity_boost,
            style_exaggeration=data.style_exaggeration,
            use_speaker_boost=data.use_speaker_boost
        )
        
        # Upload to S3
        nca = NCAService()
        filename = f"voiceover_{data.segment_id}_{uuid.uuid4()}.mp3"
        s3_url = nca.upload_to_s3(result['audio_data'], filename, 'audio/mpeg')
        
        # Update segment with voiceover URL
        update_fields = {
            'Voiceover': [{'url': s3_url}],
            'Status': 'voiceover_ready'
        }
        airtable.update_segment(data.segment_id, update_fields)
        
        # Build response
        response = GenerateVoiceoverResponse(
            segment_id=data.segment_id,
            status='completed',
            audio_url=s3_url,
            duration=0.0,  # Would need to calculate from audio data
            file_size_bytes=len(result['audio_data']),
            voice_id=data.voice_id
        )
        
        api_logger.log_api_response('elevenlabs', 'generate_voiceover', 200, response.dict())
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Error generating voiceover: {e}")
        error_response = ErrorResponse(error='Failed to generate voiceover', details=str(e))
        return jsonify(error_response.dict()), 500


@api_bp.route('/combine-segment-media', methods=['POST'])
@limiter.limit("10 per minute")
def combine_segment_media():
    """Combine video and voiceover for a segment."""
    try:
        # Validate input using Pydantic
        data = validate_request(CombineSegmentMediaRequest, request.json or {})
    except ValueError as err:
        error_response = ErrorResponse(error='Validation error', details=err)
        return jsonify(error_response.dict()), 400
    
    try:
        # Get segment
        segment = airtable.get_segment(data.segment_id)
        if not segment:
            error_response = ErrorResponse(error='Segment not found')
            return jsonify(error_response.dict()), 404
        
        fields = segment['fields']
        
        # Check for required media
        voiceover_urls = fields.get('Voiceover', [])
        video_urls = fields.get('Video', [])
        
        if not voiceover_urls:
            error_response = ErrorResponse(error='Segment has no voiceover')
            return jsonify(error_response.dict()), 400
        
        if not video_urls:
            error_response = ErrorResponse(error='Segment has no video')
            return jsonify(error_response.dict()), 400
        
        # Create job record
        job_data = {
            'segment_id': data.segment_id,
            'voiceover_url': voiceover_urls[0]['url'],
            'video_url': video_urls[0]['url']
        }
        
        job_record = airtable.create_job(
            job_type='combine_media',
            service='NCA',
            request_payload=job_data,
            related_segments=[data.segment_id]
        )
        job_id = job_record['id']
        
        # Submit to NCA
        nca = NCAService()
        webhook_url = f"{config.BASE_URL}/webhooks/nca-toolkit?job_id={job_id}&operation=combine"
        
        result = nca.compose_media(
            video_url=video_urls[0]['url'],
            audio_url=voiceover_urls[0]['url'],
            webhook_url=webhook_url
        )
        
        # Update job with external ID
        if result.get('job_id'):
            airtable.update_job(job_id, {'External Job ID': result['job_id']})
        
        # Build response
        response = JobCreatedResponse(
            status='processing',
            message='Media combination job submitted',
            job_id=job_id,
            external_job_id=result.get('job_id')
        )
        
        return jsonify(response.dict()), 202
        
    except Exception as e:
        logger.error(f"Error combining media: {e}")
        if 'job_id' in locals():
            airtable.update_job(job_id, {'Status': 'failed', 'Error Details': str(e)})
        error_response = ErrorResponse(error='Failed to combine media', details=str(e))
        return jsonify(error_response.dict()), 500


@api_bp.route('/combine-all-segments', methods=['POST'])
@limiter.limit("5 per minute")
def combine_all_segments():
    """Combine all segments into final video."""
    try:
        # Validate input using Pydantic
        data = validate_request(CombineAllSegmentsRequest, request.json or {})
    except ValueError as err:
        error_response = ErrorResponse(error='Validation error', details=err)
        return jsonify(error_response.dict()), 400
    
    try:
        # Get video and its segments
        video = airtable.get_video(data.video_id)
        if not video:
            error_response = ErrorResponse(error='Video not found')
            return jsonify(error_response.dict()), 404
        
        # Get all segments with combined media
        segments = airtable.get_video_segments(data.video_id)
        combined_segments = [s for s in segments if s['fields'].get('Voiceover + Video')]
        
        if not combined_segments:
            error_response = ErrorResponse(error='No segments with combined media found')
            return jsonify(error_response.dict()), 400
        
        # Sort segments by order
        combined_segments.sort(key=lambda s: s['fields'].get('SRT Segment ID', 0))
        
        # Extract video URLs
        video_urls = []
        for segment in combined_segments:
            combined_media = segment['fields'].get('Voiceover + Video', [])
            if combined_media:
                video_urls.append(combined_media[0]['url'])
        
        # Create job
        job_data = {
            'video_id': data.video_id,
            'video_urls': video_urls,
            'segment_count': len(video_urls)
        }
        
        job_record = airtable.create_job(
            job_type='concatenate_videos',
            service='NCA',
            request_payload=job_data,
            related_videos=[data.video_id]
        )
        job_id = job_record['id']
        
        # Submit to NCA
        nca = NCAService()
        webhook_url = f"{config.BASE_URL}/webhooks/nca-toolkit?job_id={job_id}&operation=concatenate"
        
        result = nca.concatenate_videos(
            video_urls=video_urls,
            webhook_url=webhook_url
        )
        
        # Update job with external ID
        if result.get('job_id'):
            airtable.update_job(job_id, {'External Job ID': result['job_id']})
        
        # Build response
        response = JobCreatedResponse(
            status='processing',
            message=f'Concatenating {len(video_urls)} segments',
            job_id=job_id,
            external_job_id=result.get('job_id')
        )
        
        return jsonify(response.dict()), 202
        
    except Exception as e:
        logger.error(f"Error combining segments: {e}")
        if 'job_id' in locals():
            airtable.update_job(job_id, {'Status': 'failed', 'Error Details': str(e)})
        error_response = ErrorResponse(error='Failed to combine segments', details=str(e))
        return jsonify(error_response.dict()), 500


@api_bp.route('/generate-and-add-music', methods=['POST'])
@limiter.limit("5 per minute")
def generate_and_add_music():
    """Generate and add background music to video."""
    try:
        # Validate input using Pydantic
        data = validate_request(GenerateAndAddMusicRequest, request.json or {})
    except ValueError as err:
        error_response = ErrorResponse(error='Validation error', details=err)
        return jsonify(error_response.dict()), 400
    
    try:
        # Get video
        video = airtable.get_video(data.video_id)
        if not video:
            error_response = ErrorResponse(error='Video not found')
            return jsonify(error_response.dict()), 404
        
        # Check for production video
        production_video = video['fields'].get('Production Video', [])
        if not production_video:
            error_response = ErrorResponse(error='Video has no production video')
            return jsonify(error_response.dict()), 400
        
        # Create job
        job_data = {
            'video_id': data.video_id,
            'music_prompt': data.music_prompt,
            'duration': data.duration
        }
        
        job_record = airtable.create_job(
            job_type='generate_music',
            service='GoAPI',
            request_payload=job_data,
            related_videos=[data.video_id]
        )
        job_id = job_record['id']
        
        # Submit to GoAPI
        goapi = GoAPIService()
        webhook_url = f"{config.BASE_URL}/webhooks/goapi?job_id={job_id}&operation=music"
        
        result = goapi.generate_music(
            prompt=data.music_prompt,
            duration=data.duration,
            webhook_url=webhook_url
        )
        
        # Update job with task ID
        if result.get('task_id'):
            airtable.update_job(job_id, {'External Job ID': result['task_id']})
        
        # Build response
        response = JobCreatedResponse(
            status='processing',
            message='Music generation job submitted',
            job_id=job_id,
            external_job_id=result.get('task_id')
        )
        
        return jsonify(response.dict()), 202
        
    except Exception as e:
        logger.error(f"Error generating music: {e}")
        if 'job_id' in locals():
            airtable.update_job(job_id, {'Status': 'failed', 'Error Details': str(e)})
        error_response = ErrorResponse(error='Failed to generate music', details=str(e))
        return jsonify(error_response.dict()), 500