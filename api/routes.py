"""API routes for YouTube Video Engine."""

import logging
import uuid
from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, validate, ValidationError

from config import get_config
from services.airtable_service import AirtableService
from services.script_processor import ScriptProcessor
from services.elevenlabs_service import ElevenLabsService
from services.nca_service import NCAService
from services.goapi_service import GoAPIService
from utils.logger import APILogger

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


# Validation schemas
class ProcessScriptSchema(Schema):
    """Schema for process script request."""
    script_text = fields.String(required=True, validate=validate.Length(min=1))
    video_name = fields.String(missing='Untitled Video')
    target_segment_duration = fields.Integer(
        missing=30, 
        validate=validate.Range(min=10, max=300)
    )
    music_prompt = fields.String(missing=None)


class GenerateVoiceoverSchema(Schema):
    """Schema for generate voiceover request."""
    segment_id = fields.String(required=True)
    voice_id = fields.String(required=True)
    stability = fields.Float(missing=0.5, validate=validate.Range(min=0, max=1))
    similarity_boost = fields.Float(missing=0.5, validate=validate.Range(min=0, max=1))
    style_exaggeration = fields.Float(missing=0.0, validate=validate.Range(min=0, max=1))
    use_speaker_boost = fields.Boolean(missing=True)  # Default to True if not provided


class CombineSegmentMediaSchema(Schema):
    """Schema for combine segment media request."""
    segment_id = fields.String(required=True)


class CombineAllSegmentsSchema(Schema):
    """Schema for combine all segments request."""
    video_id = fields.String(required=True)


class GenerateAndAddMusicSchema(Schema):
    """Schema for generate and add music request."""
    video_id = fields.String(required=True)
    music_prompt = fields.String(
        missing='Calm, instrumental background music suitable for video content'
    )
    duration = fields.Integer(missing=180, validate=validate.Range(min=30, max=600))


@api_bp.route('/status', methods=['GET'])
def status():
    """Simple status endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'YouTube Video Engine API is running'
    })


@api_bp.route('/process-script', methods=['POST'])
@limiter.limit("10 per minute")
def process_script():
    """Process a script into timed segments."""
    try:
        # Validate input
        schema = ProcessScriptSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Create video record
        video = airtable.create_video(
            name=data['video_name'],
            script=data['script_text'],
            music_prompt=data.get('music_prompt')
        )
        video_id = video['id']
        
        # Process script into segments
        segments = script_processor.process_script(
            data['script_text'],
            data.get('target_segment_duration')
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
        
        return jsonify({
            'video_id': video_id,
            'video_name': data['video_name'],
            'total_segments': len(segment_records),
            'estimated_duration': sum(s.estimated_duration for s in segments),
            'status': 'segments_created',
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
        if 'video_id' in locals():
            airtable.update_video_status(video_id, 'failed', str(e))
        return jsonify({'error': 'Failed to process script', 'details': str(e)}), 500


@api_bp.route('/generate-voiceover', methods=['POST'])
@limiter.limit("20 per minute")
def generate_voiceover():
    """Generate voiceover for a segment."""
    try:
        # Validate input
        schema = GenerateVoiceoverSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get segment
        segment = airtable.get_segment(data['segment_id'])
        if not segment:
            return jsonify({'error': 'Segment not found'}), 404
        
        # Note: Status field doesn't exist in current Segments table schema
        # Skipping status update for segment
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_VOICEOVER,
            segment_id=data['segment_id'],
            request_payload=data
        )
        job_id = job['id']
        
        # Generate webhook URL
        webhook_url = f"{config.WEBHOOK_BASE_URL}/webhooks/elevenlabs?job_id={job_id}"
        
        # Initialize ElevenLabs service
        elevenlabs = ElevenLabsService()

        # Fetch speed from segment data, parse, and clamp
        segment_fields = segment.get('fields', {})
        speed_value = segment_fields.get('Speed (from Voices)', 1.0)

        if isinstance(speed_value, list):
            if len(speed_value) > 0:
                try:
                    speed = float(speed_value[0])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid speed value in list '{speed_value[0]}' for segment {data['segment_id']}. Defaulting to 1.0.")
                    speed = 1.0
            else: # Empty list
                logger.warning(f"Empty speed value list for segment {data['segment_id']}. Defaulting to 1.0.")
                speed = 1.0
        elif isinstance(speed_value, (float, int)):
            speed = float(speed_value)
        else: 
            try:
                speed = float(speed_value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid speed value '{speed_value}' (type: {type(speed_value)}) for segment {data['segment_id']}. Defaulting to 1.0.")
                speed = 1.0
        
        # Clamp speed to ElevenLabs valid range [0.7, 1.2]
        if speed < 0.7:
            logger.warning(f"Speed {speed} for segment {data['segment_id']} is below 0.7. Clamping to 0.7.")
            speed = 0.7
        elif speed > 1.2:
            logger.warning(f"Speed {speed} for segment {data['segment_id']} is above 1.2. Clamping to 1.2.")
            speed = 1.2

        # Get style_exaggeration from request data, parse, and clamp
        style_exaggeration_value = data.get('style_exaggeration', 0.0)
        try:
            style_exaggeration = float(style_exaggeration_value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid style_exaggeration value '{style_exaggeration_value}' (type: {type(style_exaggeration_value)}) for job {job_id}. Defaulting to 0.0.")
            style_exaggeration = 0.0

        # Clamp style_exaggeration to [0.0, 1.0]
        if style_exaggeration < 0.0:
            logger.warning(f"Style Exaggeration {style_exaggeration} for job {job_id} is below 0.0. Clamping to 0.0.")
            style_exaggeration = 0.0
        elif style_exaggeration > 1.0:
            logger.warning(f"Style Exaggeration {style_exaggeration} for job {job_id} is above 1.0. Clamping to 1.0.")
            style_exaggeration = 1.0


        # Get use_speaker_boost from request data
        use_speaker_boost_value = data.get('use_speaker_boost', True)
        if not isinstance(use_speaker_boost_value, bool):
            logger.warning(f"Invalid 'use_speaker_boost' value '{use_speaker_boost_value}' (type: {type(use_speaker_boost_value)}) for job {job_id}. Defaulting to True.")
            use_speaker_boost = True # Default to True if not a valid boolean
        else:
            use_speaker_boost = use_speaker_boost_value
        
        # Generate voiceover
        result = elevenlabs.generate_voice(
            text=segment['fields']['SRT Text'],  # Using SRT Text field
            voice_id=data['voice_id'],
            stability=data['stability'],
            similarity_boost=data['similarity_boost'],
            speed=speed,
            style_exaggeration=style_exaggeration,
            use_speaker_boost=use_speaker_boost,
            webhook_url=webhook_url
        )
        
        # Update job with external ID if available
        if 'job_id' in result:
            airtable.update_job(job_id, {
                'External Job ID': result['job_id'],
                'Webhook URL': webhook_url,
                'Status': config.STATUS_PROCESSING
            })
        
        return jsonify({
            'job_id': job_id,
            'segment_id': data['segment_id'],
            'status': 'processing',
            'webhook_url': webhook_url
        }), 202
        
    except Exception as e:
        logger.error(f"Error generating voiceover: {e}")
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to generate voiceover', 'details': str(e)}), 500


@api_bp.route('/combine-segment-media', methods=['POST'])
@limiter.limit("20 per minute")
def combine_segment_media():
    """Combine voiceover with base video for a segment."""
    try:
        # Validate input
        schema = CombineSegmentMediaSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get segment
        segment = airtable.get_segment(data['segment_id'])
        if not segment:
            return jsonify({'error': 'Segment not found'}), 404
        
        # Check if background video is ready
        if 'Video' not in segment['fields'] or not segment['fields']['Video']:
            return jsonify({'error': 'Background video not uploaded. Please upload a video to this segment in Airtable first.'}), 400
        
        # Check if voiceover is ready
        if 'Voiceover' not in segment['fields'] or not segment['fields']['Voiceover']:
            return jsonify({'error': 'Voiceover not ready for this segment'}), 400
        
        # Get URLs from existing fields
        video_url = segment['fields']['Video'][0]['url']
        voiceover_url = segment['fields']['Voiceover'][0]['url']
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_COMBINE,
            segment_id=data['segment_id'],
            request_payload=data
        )
        job_id = job['id']
        
        # Generate webhook URL
        webhook_url = f"{config.WEBHOOK_BASE_URL}/webhooks/nca-toolkit?job_id={job_id}&operation=combine"
        
        # Initialize NCA service
        nca = NCAService()
        
        # Combine media
        result = nca.combine_audio_video(
            video_url=video_url,
            audio_url=voiceover_url,
            output_filename=f"segment_{data['segment_id']}_combined.mp4",
            webhook_url=webhook_url
        )
        
        # Update job with external ID
        if 'job_id' in result:
            airtable.update_job(job_id, {
                'External Job ID': result['job_id'],
                'Webhook URL': webhook_url,
                'Status': config.STATUS_PROCESSING
            })
        
        return jsonify({
            'job_id': job_id,
            'segment_id': data['segment_id'],
            'status': 'processing',
            'webhook_url': webhook_url
        }), 202
        
    except Exception as e:
        logger.error(f"Error combining segment media: {e}")
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to combine media', 'details': str(e)}), 500


@api_bp.route('/combine-all-segments', methods=['POST'])
@limiter.limit("5 per minute")
def combine_all_segments():
    """Concatenate all segment videos into one."""
    try:
        # Validate input
        schema = CombineAllSegmentsSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get video
        video = airtable.get_video(data['video_id'])
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Get all segments
        segments = airtable.get_video_segments(data['video_id'])
        if not segments:
            return jsonify({'error': 'No segments found for this video'}), 400
        
        # Check if all segments have combined videos
        uncombined = []
        video_urls = []
        
        for segment in segments:
            if 'Voiceover + Video' not in segment['fields'] or not segment['fields']['Voiceover + Video']:
                uncombined.append(segment['id'])
            else:
                video_urls.append(segment['fields']['Voiceover + Video'][0]['url'])
        
        if uncombined:
            return jsonify({
                'error': 'Not all segments have been combined',
                'uncombined_segments': uncombined
            }), 400
        
        # Update video status
        airtable.update_video_status(data['video_id'], 'concatenating_segments')
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_CONCATENATE,
            video_id=data['video_id'],
            request_payload=data
        )
        job_id = job['id']
        
        # Generate webhook URL
        webhook_url = f"{config.WEBHOOK_BASE_URL}/webhooks/nca-toolkit?job_id={job_id}&operation=concatenate"
        
        # Initialize NCA service
        nca = NCAService()
        
        # Concatenate videos
        result = nca.concatenate_videos(
            video_urls=video_urls,
            output_filename=f"video_{data['video_id']}_combined.mp4",
            webhook_url=webhook_url
        )
        
        # Update job with external ID
        if 'job_id' in result:
            airtable.update_job(job_id, {
                'External Job ID': result['job_id'],
                'Webhook URL': webhook_url,
                'Status': config.STATUS_PROCESSING
            })
        
        return jsonify({
            'job_id': job_id,
            'video_id': data['video_id'],
            'segment_count': len(segments),
            'status': 'processing',
            'webhook_url': webhook_url
        }), 202
        
    except Exception as e:
        logger.error(f"Error combining all segments: {e}")
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to combine segments', 'details': str(e)}), 500


@api_bp.route('/generate-and-add-music', methods=['POST'])
@limiter.limit("5 per minute")
def generate_and_add_music():
    """Generate background music and add to video."""
    try:
        # Validate input
        schema = GenerateAndAddMusicSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get video
        video = airtable.get_video(data['video_id'])
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Check if combined video exists
        if 'Combined Segments Video' not in video['fields'] or not video['fields']['Combined Segments Video']:
            return jsonify({'error': 'Combined video not ready'}), 400
        
        # Update video with music prompt
        airtable.update_video(data['video_id'], {
            'Music Prompt': data['music_prompt'],
            'Status': 'generating_music'
        })
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_MUSIC,
            video_id=data['video_id'],
            request_payload=data
        )
        job_id = job['id']
        
        # Generate webhook URL
        webhook_url = f"{config.WEBHOOK_BASE_URL}/webhooks/goapi?job_id={job_id}"
        
        # Initialize GoAPI service
        goapi = GoAPIService()
        
        # Generate music
        result = goapi.generate_music(
            prompt=data['music_prompt'],
            duration=data['duration'],
            webhook_url=webhook_url
        )
        
        # Update job with external ID
        if 'id' in result:
            airtable.update_job(job_id, {
                'External Job ID': result['id'],
                'Webhook URL': webhook_url,
                'Status': config.STATUS_PROCESSING
            })
        
        return jsonify({
            'job_id': job_id,
            'video_id': data['video_id'],
            'status': 'processing',
            'webhook_url': webhook_url
        }), 202
        
    except Exception as e:
        logger.error(f"Error generating music: {e}")
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to generate music', 'details': str(e)}), 500


@api_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status."""
    try:
        # Get job from Airtable
        job = airtable.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        fields = job['fields']
        
        response = {
            'job_id': job_id,
            'type': fields.get('Type'),
            'status': fields.get('Status'),
            'created_at': job.get('createdTime'),
            'external_job_id': fields.get('External Job ID')
        }
        
        # Extract related entity info from Request Payload
        # (Related Video/Segment fields don't exist in current schema)
        if 'Request Payload' in fields:
            try:
                import ast
                payload = ast.literal_eval(fields['Request Payload'])
                if isinstance(payload, dict):
                    if 'video_id' in payload:
                        response['video_id'] = payload['video_id']
                        response['entity_type'] = 'video'
                    if 'segment_id' in payload:
                        response['segment_id'] = payload['segment_id']
                        response['entity_type'] = 'segment'
            except:
                pass  # Ignore parsing errors
        
        # Add error details if failed
        if fields.get('Status') == config.STATUS_FAILED:
            response['error'] = fields.get('Error Details')
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({'error': 'Failed to get job status', 'details': str(e)}), 500


@api_bp.route('/videos/<video_id>', methods=['GET'])
def get_video_details(video_id):
    """Get video details."""
    try:
        # Get video from Airtable
        video = airtable.get_video(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        fields = video['fields']
        
        response = {
            'video_id': video_id,
            'name': fields.get('Description'),  # Using Description field
            'status': fields.get('Status', 'unknown'),  # Status field doesn't exist in current schema
            'created_at': video.get('createdTime'),
            'script': fields.get('Video Script'),  # Using Video Script field
            'music_prompt': fields.get('Music Prompt'),
            'segment_count': fields.get('# Segments', len(fields.get('Segments', [])))
        }
        
        # Add video URLs if available
        if 'Combined Segments Video' in fields and fields['Combined Segments Video']:
            response['combined_video_url'] = fields['Combined Segments Video'][0]['url']
        
        if 'Final Video' in fields and fields['Final Video']:
            response['final_video_url'] = fields['Final Video'][0]['url']
        
        if 'Music' in fields and fields['Music']:
            response['music_url'] = fields['Music'][0]['url']
        
        # Add error details if failed
        if fields.get('Status') == config.STATUS_FAILED:
            response['error'] = fields.get('Error Details')
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting video details: {e}")
        return jsonify({'error': 'Failed to get video details', 'details': str(e)}), 500


@api_bp.route('/videos/<video_id>/segments', methods=['GET'])
def get_video_segments(video_id):
    """Get all segments for a video."""
    try:
        # Get segments from Airtable
        segments = airtable.get_video_segments(video_id)
        
        response = {
            'video_id': video_id,
            'segment_count': len(segments),
            'segments': []
        }
        
        for segment in segments:
            fields = segment['fields']
            segment_data = {
                'segment_id': segment['id'],
                'order': fields.get('SRT Segment ID'),  # Using SRT Segment ID
                'text': fields.get('SRT Text'),  # Using SRT Text
                'status': fields.get('Status', 'unknown'),  # Status field doesn't exist
                'start_time': fields.get('Start Time'),
                'end_time': fields.get('End Time'),
                'duration': fields.get('End Time', 0) - fields.get('Start Time', 0),
                # 'voice_id' field doesn't exist in current schema
            }
            
            # Add media URLs if available
            if 'Voiceover' in fields and fields['Voiceover']:
                segment_data['voiceover_url'] = fields['Voiceover'][0]['url']
            
            if 'Video' in fields and fields['Video']:
                segment_data['base_video_url'] = fields['Video'][0]['url']
            
            if 'Voiceover + Video' in fields and fields['Voiceover + Video']:
                segment_data['combined_url'] = fields['Voiceover + Video'][0]['url']
            
            response['segments'].append(segment_data)
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting video segments: {e}")
        return jsonify({'error': 'Failed to get video segments', 'details': str(e)}), 500
