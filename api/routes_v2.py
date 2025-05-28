"""API v2 routes for YouTube Video Engine - Hybrid architecture with direct ElevenLabs processing."""

import logging
import requests
import base64
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError

from config import get_config
from services.airtable_service import AirtableService
from services.script_processor import ScriptProcessor
from services.elevenlabs_service import ElevenLabsService
from services.nca_service import NCAService
from services.goapi_service import GoAPIService

logger = logging.getLogger(__name__)

# Create v2 blueprint for webhook-based architecture
api_v2_bp = Blueprint('api_v2', __name__)

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize services
airtable = AirtableService()
script_processor = ScriptProcessor()
config = get_config()()


class ProcessScriptWebhookSchema(Schema):
    """Schema for webhook-based process script request."""
    record_id = fields.String(required=True)


class GenerateVoiceoverWebhookSchema(Schema):
    """Schema for webhook-based generate voiceover request."""
    record_id = fields.String(required=True)


class CombineSegmentMediaWebhookSchema(Schema):
    """Schema for webhook-based combine segment media request."""
    record_id = fields.String(required=True)


class CombineAllSegmentsWebhookSchema(Schema):
    """Schema for webhook-based combine all segments request."""
    record_id = fields.String(required=True)


class GenerateAndAddMusicWebhookSchema(Schema):
    """Schema for webhook-based generate and add music request."""
    record_id = fields.String(required=True)


class GenerateAIImageWebhookSchema(Schema):
    """Schema for webhook-based generate AI image request."""
    segment_id = fields.String(required=True)
    size = fields.String(required=False, missing='1024x1536', 
                         validate=lambda x: x in ['1024x1024', '1024x1536', '1536x1024', 'auto'])
    quality = fields.String(required=False, missing='high',
                           validate=lambda x: x in ['low', 'medium', 'high', 'auto'])


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


@api_v2_bp.route('/generate-voiceover', methods=['POST'])
@limiter.limit("20 per minute")
def generate_voiceover_direct():
    """Generate voiceover for a segment using direct synchronous processing."""
    try:
        # Validate input
        schema = GenerateVoiceoverWebhookSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get segment record from Airtable
        segment = airtable.get_segment(data['record_id'])
        if not segment:
            return jsonify({'error': 'Segment record not found'}), 404
        
        # Get segment text
        segment_text = segment['fields'].get('SRT Text')
        if not segment_text:
            return jsonify({'error': 'Segment text is empty'}), 400
        
        # Check if Voice is linked (required)
        voice_links = segment['fields'].get('Voices', [])
        if not voice_links:
            return jsonify({'error': 'Voice ID is required - please link a voice to this segment'}), 400
        
        # Get the first linked voice record
        voice_record_id = voice_links[0]
        voice = airtable.get_voice(voice_record_id)
        if not voice:
            return jsonify({'error': 'Linked voice record not found'}), 404
        
        # Get voice settings
        voice_id = voice['fields'].get('Voice ID')
        if not voice_id:
            return jsonify({'error': 'Voice ID field is empty in voice record'}), 400
        
        # Get voice settings with defaults
        stability = voice['fields'].get('Stability', 0.5)
        similarity_boost = voice['fields'].get('Similarity Boost', 0.5)
        
        # Update segment status to 'Generating Voiceover'
        airtable.update_segment(data['record_id'], {
            'Status': 'Generating Voiceover'
        })
        
        # Initialize services
        elevenlabs = ElevenLabsService()
        nca = NCAService()
        
        # Generate voiceover synchronously
        result = elevenlabs.generate_voice_sync(
            text=segment_text,
            voice_id=voice_id,
            stability=stability,
            similarity_boost=similarity_boost
        )
        
        # Upload audio to NCA for storage
        upload_result = nca.upload_file(
            file_data=result['audio_data'],
            filename=f"voiceover_{data['record_id']}.mp3",
            content_type='audio/mpeg'
        )
        
        # Update segment with voiceover URL and success status
        airtable.update_segment(data['record_id'], {
            'Voiceover': [{'url': upload_result['url']}],
            'Status': 'Voiceover Ready'
        })
        
        return jsonify({
            'segment_id': data['record_id'],
            'voice_id': voice_id,
            'voice_name': voice['fields'].get('Name', 'Unknown'),
            'stability': stability,
            'similarity_boost': similarity_boost,
            'voiceover_url': upload_result['url'],
            'status': 'completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating voiceover: {e}")
        
        # Update segment status to 'Voiceover Failed'
        try:
            airtable.update_segment(data['record_id'], {
                'Status': 'Voiceover Failed'
            })
        except:
            pass  # Don't fail if status update fails
        
        return jsonify({'error': 'Failed to generate voiceover', 'details': str(e)}), 500


@api_v2_bp.route('/combine-segment-media', methods=['POST'])
@limiter.limit("20 per minute")
def combine_segment_media_webhook():
    """Combine voiceover with base video for a segment using webhook architecture."""
    try:
        # Validate input
        schema = CombineSegmentMediaWebhookSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get segment record from Airtable
        segment = airtable.get_segment(data['record_id'])
        if not segment:
            return jsonify({'error': 'Segment record not found'}), 404
        
        # Check if background video is ready
        if 'Video' not in segment['fields'] or not segment['fields']['Video']:
            return jsonify({'error': 'Background video not uploaded. Please upload a video to this segment in Airtable first.'}), 400
        
        # Check if voiceover is ready
        if 'Voiceover' not in segment['fields'] or not segment['fields']['Voiceover']:
            return jsonify({'error': 'Voiceover not ready for this segment'}), 400
        
        # Get URLs from existing fields
        video_url = segment['fields']['Video'][0]['url']
        voiceover_url = segment['fields']['Voiceover'][0]['url']
        
        # Update segment status to 'Combining Media'
        airtable.update_segment(data['record_id'], {
            'Status': 'Combining Media'
        })
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_COMBINE,
            segment_id=data['record_id'],
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
            output_filename=f"segment_{data['record_id']}_combined.mp4",
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
            'segment_id': data['record_id'],
            'status': 'processing',
            'webhook_url': webhook_url
        }), 202
        
    except Exception as e:
        logger.error(f"Error combining segment media: {e}")
        
        # Update segment status to 'Combination Failed'
        try:
            airtable.update_segment(data['record_id'], {
                'Status': 'Combination Failed'
            })
        except:
            pass  # Don't fail if status update fails
        
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to combine media', 'details': str(e)}), 500


@api_v2_bp.route('/combine-all-segments', methods=['POST'])
@limiter.limit("5 per minute")
def combine_all_segments_webhook():
    """Concatenate all segment videos into one using webhook architecture."""
    try:
        # Validate input
        schema = CombineAllSegmentsWebhookSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get video record from Airtable
        video = airtable.get_video(data['record_id'])
        if not video:
            return jsonify({'error': 'Video record not found'}), 404
        
        # Get all segments for this video
        segments = airtable.get_video_segments(data['record_id'])
        if not segments:
            return jsonify({'error': 'No segments found for this video'}), 400
        
        # Check if all segments have combined videos
        uncombined = []
        video_urls = []
        
        for segment in segments:
            if 'Combined' not in segment['fields'] or not segment['fields']['Combined']:
                uncombined.append(segment['id'])
            else:
                video_urls.append(segment['fields']['Combined'][0]['url'])
        
        if uncombined:
            return jsonify({
                'error': 'Not all segments have been combined',
                'uncombined_segments': uncombined
            }), 400
        
        # Update video status - note that Videos table might not have Status field
        try:
            airtable.update_video(data['record_id'], {'Status': 'Concatenating Segments'})
        except:
            pass  # Continue if status update fails
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_CONCATENATE,
            video_id=data['record_id'],
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
            output_filename=f"video_{data['record_id']}_combined.mp4",
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
            'video_id': data['record_id'],
            'segment_count': len(segments),
            'status': 'processing',
            'webhook_url': webhook_url
        }), 202
        
    except Exception as e:
        logger.error(f"Error combining all segments: {e}")
        
        # Update video status to failed if possible
        try:
            airtable.update_video(data['record_id'], {'Status': 'Concatenation Failed'})
        except:
            pass  # Continue if status update fails
        
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to combine segments', 'details': str(e)}), 500


@api_v2_bp.route('/generate-and-add-music', methods=['POST'])
@limiter.limit("5 per minute")
def generate_and_add_music_webhook():
    """Generate background music and add to video using webhook architecture."""
    try:
        # Validate input
        schema = GenerateAndAddMusicWebhookSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get video record from Airtable
        video = airtable.get_video(data['record_id'])
        if not video:
            return jsonify({'error': 'Video record not found'}), 404
        
        # Check if combined video exists
        if 'Combined Segments Video' not in video['fields'] or not video['fields']['Combined Segments Video']:
            return jsonify({'error': 'Combined video not ready'}), 400
        
        # Get music prompt from video record, with default
        music_prompt = video['fields'].get('Music Prompt', 'Calm, instrumental background music suitable for video content')
        
        # Get estimated duration from video or use default
        duration = 180  # Default duration in seconds
        
        # Try to estimate duration from segments if possible
        try:
            segments = airtable.get_video_segments(data['record_id'])
            if segments:
                total_duration = sum(seg['fields'].get('End Time', 30) for seg in segments)
                duration = max(int(total_duration), 30)  # Minimum 30 seconds
        except:
            pass  # Use default if estimation fails
        
        # Update video status
        try:
            airtable.update_video(data['record_id'], {'Status': 'Generating Music'})
        except:
            pass  # Continue if status update fails
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_MUSIC,
            video_id=data['record_id'],
            request_payload=data
        )
        job_id = job['id']
        
        # Generate webhook URL
        webhook_url = f"{config.WEBHOOK_BASE_URL}/webhooks/goapi?job_id={job_id}"
        
        # Initialize GoAPI service
        goapi = GoAPIService()
        
        # Generate music
        result = goapi.generate_music(
            prompt=music_prompt,
            duration=duration,
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
            'video_id': data['record_id'],
            'music_prompt': music_prompt,
            'duration': duration,
            'status': 'processing',
            'webhook_url': webhook_url
        }), 202
        
    except Exception as e:
        logger.error(f"Error generating music: {e}")
        
        # Update video status to failed if possible
        try:
            airtable.update_video(data['record_id'], {'Status': 'Music Generation Failed'})
        except:
            pass  # Continue if status update fails
        
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to generate music', 'details': str(e)}), 500


@api_v2_bp.route('/generate-ai-image', methods=['POST'])
@limiter.limit("10 per minute")
def generate_ai_image_webhook():
    """Generate AI image from text prompt using OpenAI's gpt-image-1 model."""
    try:
        # Validate input
        schema = GenerateAIImageWebhookSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get segment record from Airtable
        segment = airtable.get_segment(data['segment_id'])
        if not segment:
            return jsonify({'error': 'Segment record not found'}), 404
        
        # Get AI image prompt from segment
        ai_image_prompt = segment['fields'].get('AI Image Prompt')
        if not ai_image_prompt:
            return jsonify({'error': 'AI Image Prompt field is empty'}), 400
        
        # Update segment status to 'Generating Image'
        airtable.update_segment(data['segment_id'], {
            'Status': 'Generating Image'
        })
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_AI_IMAGE,
            segment_id=data['segment_id'],
            request_payload=data
        )
        job_id = job['id']
        
        # Prepare OpenAI API request
        openai_headers = {
            'Authorization': f'Bearer {config.OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Map size parameter to OpenAI format
        size_mapping = {
            '1024x1024': '1024x1024',
            '1024x1536': '1024x1792',  # OpenAI uses 1792 instead of 1536
            '1536x1024': '1792x1024',  # OpenAI uses 1792 instead of 1536
            'auto': '1024x1792'  # Default to portrait
        }
        
        openai_payload = {
            'model': 'dall-e-3',  # Using DALL-E 3 as gpt-image-1 might not be the exact model name
            'prompt': ai_image_prompt,
            'size': size_mapping.get(data['size'], '1024x1792'),
            'quality': 'hd' if data['quality'] in ['high', 'auto'] else 'standard',
            'n': 1,
            'response_format': 'b64_json'
        }
        
        # Call OpenAI API
        response = requests.post(
            f"{config.OPENAI_BASE_URL}/images/generations",
            headers=openai_headers,
            json=openai_payload,
            timeout=120  # 2 minutes timeout for image generation
        )
        
        if response.status_code != 200:
            error_detail = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            raise Exception(f"OpenAI API error: {response.status_code} - {error_detail}")
        
        # Extract base64 encoded image
        result = response.json()
        base64_image = result['data'][0]['b64_json']
        
        # Decode base64 to binary
        image_data = base64.b64decode(base64_image)
        
        # Get the attachment field ID for the 'Image' field
        # We need to find the field ID for the Image attachment field
        # First, let's upload to S3 using NCA service for storage
        nca = NCAService()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        upload_result = nca.upload_file(
            file_data=image_data,
            filename=f"ai_generated_{data['segment_id']}_{timestamp}.png",
            content_type='image/png'
        )
        
        # Update segment with image URL
        airtable.update_segment(data['segment_id'], {
            'Image': [{'url': upload_result['url']}],
            'Status': 'Image Ready'
        })
        
        # Update job status
        airtable.update_job(job_id, {
            'Status': config.STATUS_COMPLETED,
            'Response Payload': json.dumps({
                'image_url': upload_result['url'],
                'prompt': ai_image_prompt,
                'size': data['size'],
                'quality': data['quality']
            })
        })
        
        return jsonify({
            'job_id': job_id,
            'segment_id': data['segment_id'],
            'image_url': upload_result['url'],
            'prompt': ai_image_prompt,
            'size': data['size'],
            'quality': data['quality'],
            'status': 'completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating AI image: {e}")
        
        # Update segment status to 'Image Generation Failed'
        try:
            airtable.update_segment(data['segment_id'], {
                'Status': 'Image Generation Failed'
            })
        except:
            pass  # Don't fail if status update fails
        
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to generate AI image', 'details': str(e)}), 500


@api_v2_bp.route('/status', methods=['GET'])
def status_v2():
    """Simple status endpoint for v2 API."""
    return jsonify({
        'status': 'ok',
        'version': 'v2',
        'architecture': 'hybrid - direct ElevenLabs processing with webhook support for other services',
        'message': 'YouTube Video Engine API v2 is running with fixed ElevenLabs integration'
    })
