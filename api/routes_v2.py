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


class AddMusicToVideoWebhookSchema(Schema):
    """Schema for webhook-based add music to video request."""
    record_id = fields.String(required=True)


class GenerateAIImageWebhookSchema(Schema):
    """Schema for webhook-based generate AI image request."""
    segment_id = fields.String(required=True)
    size = fields.String(required=False, missing='1792x1008', 
                         validate=lambda x: x in ['1920x1080', '1792x1008', '1024x576', 'auto'])
    # Note: quality parameter removed - gpt-image-1 produces high-fidelity output by default


class GenerateVideoWebhookSchema(Schema):
    """Schema for webhook-based generate video request."""
    segment_id = fields.String(required=True)
    duration_override = fields.Integer(required=False, missing=None,
                                     validate=lambda x: x in [5, 10] if x is not None else True)
    aspect_ratio = fields.String(required=False, missing='16:9',
                                validate=lambda x: x in ['1:1', '16:9', 'auto'])
    quality = fields.String(required=False, missing='standard',
                           validate=lambda x: x in ['standard', 'high'])


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
        
        # Process segments with ElevenLabs markup
        marked_segments = script_processor.process_segments_with_markup(segments)
        
        # Convert segments to Airtable format
        segment_data = []
        for segment in marked_segments:
            segment_data.append({
                'text': segment['text'],  # This is the marked-up text
                'original_text': segment['original_text'],  # This is the original text
                'start_time': segment['start_time'],
                'end_time': segment['end_time']
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
        similarity_boost = voice['fields'].get('Similarity Boost', 0.5) # Fetch from voice record
        speed_value = segment['fields'].get('Speed (from Voices)', 1.0) # Fetch speed, default to 1.0
        style_exaggeration_value = voice['fields'].get('Style Exaggeration', 0.0) # Fetch style exaggeration, default to 0.0
        use_speaker_boost_value = voice['fields'].get('Speaker Boost (from Voices)', True) # Fetch speaker boost, default to True
        
        # Ensure speed is a float and within valid range for ElevenLabs (0.7-1.2)
        # Airtable lookup fields (like 'Speed (from Voices)') often return as a list.
        if isinstance(speed_value, list):
            if len(speed_value) > 0:
                try:
                    speed = float(speed_value[0])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid speed value in list '{speed_value[0]}' for segment {data['record_id']}. Defaulting to 1.0.")
                    speed = 1.0
            else: # Empty list
                logger.warning(f"Empty speed value list for segment {data['record_id']}. Defaulting to 1.0.")
                speed = 1.0
        elif isinstance(speed_value, (float, int)):
            speed = float(speed_value)
        else: # Try to convert if it's a string or other type that might be valid
            try:
                speed = float(speed_value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid speed value '{speed_value}' (type: {type(speed_value)}) for segment {data['record_id']}. Defaulting to 1.0.")
                speed = 1.0
        
        # Clamp speed to ElevenLabs valid range [0.7, 1.2]
        if speed < 0.7:
            logger.warning(f"Speed {speed} for segment {data['record_id']} is below 0.7. Clamping to 0.7.")
            speed = 0.7
        elif speed > 1.2:
            logger.warning(f"Speed {speed} for segment {data['record_id']} is above 1.2. Clamping to 1.2.")
            speed = 1.2

        # Ensure style_exaggeration is a float and within valid range [0.0, 1.0]
        if isinstance(style_exaggeration_value, list):
            if len(style_exaggeration_value) > 0:
                try:
                    style_exaggeration = float(style_exaggeration_value[0])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid style_exaggeration value in list '{style_exaggeration_value[0]}' for voice {voice_record_id}. Defaulting to 0.0.")
                    style_exaggeration = 0.0
            else: # Empty list
                logger.warning(f"Empty style_exaggeration value list for voice {voice_record_id}. Defaulting to 0.0.")
                style_exaggeration = 0.0
        elif isinstance(style_exaggeration_value, (float, int)):
            style_exaggeration = float(style_exaggeration_value)
        else: # Try to convert if it's a string or other type that might be valid
            try:
                style_exaggeration = float(style_exaggeration_value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid style_exaggeration value '{style_exaggeration_value}' (type: {type(style_exaggeration_value)}) for voice {voice_record_id}. Defaulting to 0.0.")
                style_exaggeration = 0.0

        # Clamp style_exaggeration to [0.0, 1.0]
        if style_exaggeration < 0.0:
            logger.warning(f"Style Exaggeration {style_exaggeration} for voice {voice_record_id} is below 0.0. Clamping to 0.0.")
            style_exaggeration = 0.0
        elif style_exaggeration > 1.0:
            logger.warning(f"Style Exaggeration {style_exaggeration} for voice {voice_record_id} is above 1.0. Clamping to 1.0.")
            style_exaggeration = 1.0


        # Ensure use_speaker_boost is a boolean
        if not isinstance(use_speaker_boost_value, bool):
            logger.warning(f"Invalid 'Speaker Boost (from Voices)' value '{use_speaker_boost_value}' (type: {type(use_speaker_boost_value)}) for voice {voice_record_id}. Defaulting to True.")
            use_speaker_boost = True # Default to True if not a valid boolean
        else:
            use_speaker_boost = use_speaker_boost_value
        
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
            similarity_boost=similarity_boost,
            speed=speed,
            style_exaggeration=style_exaggeration,
            use_speaker_boost=use_speaker_boost
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
            webhook_url=webhook_url,
            custom_id=job_id
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
    logger.info("combine_all_segments_webhook endpoint hit")
    try:
        # Validate input
        schema = CombineAllSegmentsWebhookSchema()
        data = schema.load(request.json)
        logger.info(f"Request data validated. Record ID: {data.get('record_id')}")
    except ValidationError as err:
        logger.error(f"Validation error in combine_all_segments_webhook: {err.messages}")
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    record_id = data['record_id'] # Use a variable for clarity

    try:
        # Get video record from Airtable
        logger.info(f"Fetching video record for ID: {record_id}")
        video = airtable.get_video(record_id)
        if not video:
            logger.warning(f"Video record not found for ID: {record_id}")
            return jsonify({'error': 'Video record not found'}), 404
        logger.info(f"Video record found: {video.get('id') if video else 'None'}")
        
        # Get all segments for this video
        logger.info(f"Fetching segments for video ID: {record_id}")
        segments = airtable.get_video_segments(record_id)
        logger.info(f"Found {len(segments) if segments else 0} segments for video ID: {record_id}")
        
        if not segments:
            logger.warning(f"No segments returned by airtable.get_video_segments for video ID: {record_id}")
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
        
        # Update video status - note that Videos table might not have Status field
        # try:
        #     airtable.update_video(record_id, {'Status': 'Concatenating Segments'})
        # except:
        #     pass  # Continue if status update fails
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_CONCATENATE,
            video_id=record_id,
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
            output_filename=f"video_{record_id}_combined.mp4",
            webhook_url=webhook_url,
            custom_id=job_id
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
            'video_id': record_id,
            'segment_count': len(segments),
            'status': 'processing',
            'webhook_url': webhook_url
        }), 202
        
    except Exception as e:
        logger.error(f"Error combining all segments: {e}")
        
        # Update video status to failed if possible
        # try:
        #     airtable.update_video(record_id, {'Status': 'Concatenation Failed'})
        # except:
        #     pass  # Continue if status update fails
        
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to combine segments', 'details': str(e)}), 500


@api_v2_bp.route('/generate-and-add-music', methods=['POST'])
@limiter.limit("5 per minute")
def generate_and_add_music_webhook():
    """Generate background music using GoAPI based on a prompt from Airtable."""
    try:
        # Validate input
        schema = GenerateAndAddMusicWebhookSchema()
        data = schema.load(request.json)
        record_id = data['record_id']
    except ValidationError as err:
        logger.warning(f"Validation error for /generate-and-add-music: {err.messages}")
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    job_id = None  # Initialize job_id for error handling
    try:
        # Fetch video record from Airtable
        video = airtable.get_video(record_id)
        if not video:
            logger.warning(f"Video record {record_id} not found for music generation.")
            return jsonify({'error': f'Video record {record_id} not found'}), 404
        
        # Get music prompt from video record - this is mandatory
        music_prompt = video['fields'].get('Music Prompt')
        if not music_prompt or not music_prompt.strip():
            logger.warning(f"Music Prompt field is empty for video record {record_id}.")
            try:
                airtable.update_video(record_id, {'Status': 'Music Gen Error - No Prompt'})
            except Exception as e_airtable:
                logger.error(f"Failed to update Airtable status for no prompt on {record_id}: {e_airtable}")
            return jsonify({'error': 'Music Prompt field is empty in Airtable record. Please provide a prompt.'}), 400
        
        logger.info(f"Initiating music generation for video record {record_id} with prompt: '{music_prompt}'")

        # Update video status to 'Generating Music'
        try:
            airtable.update_video(record_id, {'Status': 'Generating Music'})
        except Exception as e_airtable:
            logger.error(f"Failed to update Airtable status to 'Generating Music' for {record_id}: {e_airtable}")
            # Continue, but log the error
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_MUSIC, # Ensure JOB_TYPE_MUSIC is defined in config
            video_id=record_id,
            request_payload=data
        )
        job_id = job['id']
        logger.info(f"Created Airtable job {job_id} for music generation, video {record_id}.")
        
        # Construct the webhook URL for GoAPI callback
        webhook_url_for_goapi = f"{config.WEBHOOK_BASE_URL}/webhooks/goapi?job_id={job_id}&operation=generate_music_only&target_id={record_id}"
        logger.info(f"Constructed GoAPI webhook URL: {webhook_url_for_goapi}")

        # Initialize GoAPI service
        goapi_service = GoAPIService() # GoAPIService should be imported at the top of the file
        
        # Call GoAPI to generate music
        logger.info(f"Calling GoAPIService.generate_music for job {job_id} with prompt: '{music_prompt}'")
        goapi_result = goapi_service.generate_music(
            music_prompt=music_prompt, # Correct parameter name
            webhook_url=webhook_url_for_goapi
        )
        
        external_task_id = goapi_result.get('id') # GoAPI usually returns task ID in 'id' field
        
        if not external_task_id:
            error_detail = f"GoAPI did not return an external task ID for job {job_id}. Response: {goapi_result}"
            logger.error(error_detail)
            airtable.fail_job(job_id, "GoAPI did not return task ID", status_override='GoAPI Error - No Task ID')
            airtable.update_video(record_id, {'Status': 'Music Gen Error - GoAPI No Task ID'})
            return jsonify({'error': 'Failed to initiate music generation with GoAPI - no task ID returned', 'details': str(goapi_result)}), 500

        logger.info(f"GoAPI music generation initiated. External Task ID: {external_task_id} for job {job_id}")

        # Update job record with external task ID and processing status
        airtable.update_job(job_id, {
            'External Job ID': external_task_id,
            'Webhook URL': webhook_url_for_goapi, # Store the webhook URL we sent to GoAPI
            'Status': config.STATUS_PROCESSING
        })
        
        return jsonify({
            'job_id': job_id,
            'video_id': record_id,
            'music_prompt': music_prompt,
            'status': config.STATUS_PROCESSING,
            'message': 'Music generation initiated with GoAPI. Waiting for webhook callback.',
            'webhook_url_sent_to_goapi': webhook_url_for_goapi,
            'external_task_id': external_task_id
        }), 202
        
    except Exception as e:
        logger.error(f"Error in generate_and_add_music_webhook for record {record_id}, job {job_id if job_id else 'N/A'}: {e}", exc_info=True)
        error_message = str(e)
        try:
            airtable.update_video(record_id, {'Status': 'Music Generation Failed - System Error'})
        except Exception as airtable_err:
            logger.error(f"Failed to update video status to 'Music Generation Failed' for record {record_id}: {airtable_err}")
            
        if job_id:
            try:
                airtable.fail_job(job_id, error_message, status_override='Music Gen Error - System')
            except Exception as airtable_job_err:
                 logger.error(f"Failed to update job status to failed for job {job_id}: {airtable_job_err}")
        return jsonify({'error': 'Failed to generate music due to an internal error', 'details': error_message}), 500


@api_v2_bp.route('/add-music-to-video', methods=['POST'])
@limiter.limit("10 per minute") # Adjust limit as needed
def add_music_to_video_webhook():
    """Add generated music to a combined video using webhook architecture."""
    data = {}
    video_record_id = None
    job_id = None
    try:
        # Validate input
        schema = AddMusicToVideoWebhookSchema()
        data = schema.load(request.json)
        video_record_id = data['record_id']
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get video record from Airtable
        video = airtable.get_video(video_record_id)
        if not video:
            return jsonify({'error': f'Video record {video_record_id} not found'}), 404
        
        # --- Get Music URL ---
        music_attachments = video['fields'].get('Music') # Your 'Music' field
        if not music_attachments or not isinstance(music_attachments, list) or not music_attachments[0].get('url'):
            logger.error(f"Music URL not found or invalid in 'Music' field for video {video_record_id}.")
            return jsonify({'error': "Music file URL not found in 'Music' field. Ensure music is generated first."}), 400
        music_url = music_attachments[0]['url']
        
        # --- Get Combined Video URL ---
        # Assuming your field for the video (without music yet) is 'Combined Segments Video'
        # This is the field that the 'combine_all_segments_webhook' populates.
        combined_video_attachments = video['fields'].get('Combined Segments Video') 
        if not combined_video_attachments or not isinstance(combined_video_attachments, list) or not combined_video_attachments[0].get('url'):
            logger.error(f"Combined video URL not found or invalid in 'Combined Segments Video' field for video {video_record_id}.")
            return jsonify({'error': "Combined video URL not found in 'Combined Segments Video' field."}), 400
        combined_video_url = combined_video_attachments[0]['url']

        logger.info(f"Attempting to add music ({music_url}) to video ({combined_video_url}) for record {video_record_id}")

        # Video status updates are handled by the job record or later webhook processing.

        # Create a new job record for this operation
        job = airtable.create_job(
            job_type='add_music_to_video', # Or use a config constant e.g., config.JOB_TYPE_ADD_MUSIC_TO_VIDEO
            video_id=video_record_id,
            request_payload=data # Store the initial request
        )
        job_id = job['id']
        
        # Generate webhook URL for NCA Toolkit callback
        # This will use the existing 'add_music' operation handler in nca_toolkit_webhook
        nca_webhook_url = f"{config.WEBHOOK_BASE_URL}/webhooks/nca-toolkit?job_id={job_id}&operation=add_music"
        
        # Initialize NCA Service
        nca = NCAService()
        
        # Call NCA to add background music
        output_filename = f"video_with_music_{video_record_id}.mp4"

        add_music_result = nca.add_background_music(
            video_url=combined_video_url,
            music_url=music_url,
            output_filename=output_filename,
            # volume_ratio=0.2, # Example, adjust as needed or make configurable in Airtable
            webhook_url=nca_webhook_url,
            custom_id=job_id  # Pass the Airtable job ID to ensure it's returned in webhook
        )
        
        airtable.update_job(job_id, {
            'External Job ID': add_music_result.get('job_id', add_music_result.get('id')), 
            'Webhook URL': nca_webhook_url,
            'Status': config.STATUS_PROCESSING,
            'Notes': f"NCA job initiated to add music. Output: {output_filename}"
        })
        
        return jsonify({
            'job_id': job_id,
            'video_id': video_record_id,
            'status': 'processing_add_music',
            'message': 'Job created to add music to video. Waiting for NCA callback.',
            'nca_webhook_url': nca_webhook_url,
            'nca_job_details': add_music_result 
        }), 202
        
    except Exception as e:
        logger.error(f"Error in /add-music-to-video for record {data.get('record_id', 'unknown')}: {e}")
        if job_id:
            try:
                airtable.fail_job(job_id, str(e))
            except Exception as e_fail_job:
                logger.error(f"Additionally, failed to mark job {job_id} as failed: {e_fail_job}")
        # Video status updates are handled by the job record or later webhook processing.

        return jsonify({'error': 'Failed to initiate adding music to video', 'details': str(e)}), 500


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
            # Generate the prompt automatically
            logger.info(f"AI Image Prompt is empty for segment {data['segment_id']}, generating automatically")
            
            try:
                # Get the parent video record for full script
                video_ids = segment['fields'].get('Videos')
                if not video_ids:
                    return jsonify({'error': 'No parent video linked to segment'}), 400
                
                video = airtable.get_video(video_ids[0])  # Video ID is a list
                full_script = video['fields'].get('Video Script')
                if not full_script:
                    return jsonify({'error': 'Parent video has no script'}), 400
                
                # Get theme description if available
                theme_ids = segment['fields'].get('Image Theme')
                theme_description = None
                if theme_ids:
                    try:
                        theme = airtable.get_record('Image Themes', theme_ids[0])
                        theme_description = theme['fields'].get('Theme Description')
                    except Exception as e:
                        logger.warning(f"Failed to fetch Image Theme: {e}")
                        # Continue without theme description
                
                # Get segment text
                segment_text = segment['fields'].get('Original SRT Text', '')
                if not segment_text:
                    return jsonify({'error': 'Segment has no Original SRT Text'}), 400
                
                # Initialize OpenAI service and generate prompt
                from services.openai_service import OpenAIService
                openai_service = OpenAIService()
                ai_image_prompt = openai_service.generate_ai_image_prompt(
                    segment_text=segment_text,
                    full_video_script=full_script,
                    theme_description=theme_description
                )
                
                # Update segment with generated prompt
                airtable.update_segment(data['segment_id'], {
                    'AI Image Prompt': ai_image_prompt
                })
                
                logger.info(f"Generated AI image prompt for segment {data['segment_id']}: {ai_image_prompt[:100]}...")
                
            except Exception as e:
                logger.error(f"Failed to generate AI image prompt: {e}")
                return jsonify({'error': 'Failed to generate AI image prompt', 'details': str(e)}), 500
        
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
        
        # Map size parameter to OpenAI format - Using only supported gpt-image-1 sizes
        size_mapping = {
            '1920x1080': '1536x1024',  # YouTube Full HD 16:9 → closest supported landscape size
            '1792x1008': '1536x1024',  # YouTube optimized 16:9 → closest supported landscape size  
            '1024x576': '1536x1024',   # YouTube mobile 16:9 → closest supported landscape size
            'auto': 'auto'             # Use OpenAI's auto sizing
        }
        
        openai_payload = {
            'model': 'gpt-image-1',  # Using new gpt-image-1 model (NOT DALL-E 3!)
            'prompt': ai_image_prompt,
            'size': size_mapping.get(data['size'], '1536x1024'),
            # Note: gpt-image-1 does NOT support quality parameter - produces high-fidelity by default
            'n': 4,  # Generate 4 images like Midjourney
            'output_format': 'png',  # gpt-image-1 supports 'png', 'webp', 'jpeg'
            'moderation': 'auto'  # gpt-image-1 requires moderation parameter
        }
        
        # Call OpenAI API
        response = requests.post(
            f"{config.OPENAI_BASE_URL}/images/generations",
            headers=openai_headers,
            json=openai_payload,
            timeout=600  # 10 minutes timeout for 4-image generation (increased from 240s)
        )
        
        if response.status_code != 200:
            error_detail = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            raise Exception(f"OpenAI API error: {response.status_code} - {error_detail}")
        
        # Extract all 4 base64 encoded images from gpt-image-1 response
        result = response.json()
        image_data_list = result['data']  # This will be an array of 4 images
        
        # Process all 4 images
        uploaded_images = []
        nca = NCAService()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for i, image_data in enumerate(image_data_list):
            # gpt-image-1 returns base64-encoded data in 'b64_json' field (not URLs)
            if 'b64_json' in image_data:
                # Base64 encoded response from gpt-image-1
                image_binary = base64.b64decode(image_data['b64_json'])
            else:
                # Fallback error handling
                raise Exception(f"Expected 'b64_json' field in gpt-image-1 response, got: {list(image_data.keys())}")
            
            # Upload each image to S3 using NCA service
            upload_result = nca.upload_file(
                file_data=image_binary,
                filename=f"ai_generated_{data['segment_id']}_{timestamp}_{i+1}.png",
                content_type='image/png'
            )
            
            uploaded_images.append({'url': upload_result['url']})
        
        # Update segment with ALL 4 image URLs
        airtable.update_segment(data['segment_id'], {
            'Image': uploaded_images,  # Upload all 4 images to attachment field
            'Status': 'Image Ready'
        })
        
        # Update job status
        airtable.update_job(job_id, {
            'Status': config.STATUS_COMPLETED,
            'Response Payload': json.dumps({
                'image_urls': [img['url'] for img in uploaded_images],  # All 4 image URLs
                'image_count': len(uploaded_images),
                'prompt': ai_image_prompt,
                'size': data['size'],
                'model': 'gpt-image-1',
                'output_format': 'png'
            })
        })
        
        return jsonify({
            'job_id': job_id,
            'segment_id': data['segment_id'],
            'image_urls': [img['url'] for img in uploaded_images],  # All 4 image URLs
            'image_count': len(uploaded_images),
            'prompt': ai_image_prompt,
            'size': data['size'],
            'model': 'gpt-image-1',
            'output_format': 'png',
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


@api_v2_bp.route('/generate-video', methods=['POST'])
@limiter.limit("5 per minute")
def generate_video_webhook():
    """Generate video from image using Kling AI via GoAPI."""
    try:
        # Validate input
        schema = GenerateVideoWebhookSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400
    
    try:
        # Get segment record from Airtable
        segment = airtable.get_segment(data['segment_id'])
        if not segment:
            return jsonify({'error': 'Segment record not found'}), 404
        
        # Get upscale image from segment
        upscale_images = segment['fields'].get('Upscale Image')
        if not upscale_images:
            return jsonify({'error': 'Upscale Image field is empty - please generate and upscale an image first'}), 400
        
        # Get the first upscale image URL
        image_url = upscale_images[0]['url']

        video_style = segment['fields'].get('Video Style', 'Kling Video') # Default to Kling Video
        # Fetch video_id for webhook context (assuming 'Video' is the link field name)
        video_link_field_name = getattr(config, 'AIRTABLE_SEGMENTS_VIDEO_LINK_FIELD', 'Video')
        video_record_ids = segment['fields'].get(video_link_field_name, [])
        video_id = video_record_ids[0] if video_record_ids else None

        if not video_id:
            logger.warning(f"Segment {data['segment_id']} is not linked to a Video record. video_id will be None for webhook context.")

        # Update segment status to 'Generating Video'
        airtable.update_segment(data['segment_id'], {
            'Status': 'Generating Video'
        })
        
        # Create job record
        job = airtable.create_job(
            job_type=config.JOB_TYPE_VIDEO, # Consider making this more specific for Zoom vs Kling if needed
            segment_id=data['segment_id'],
            video_id=video_id, # Store video_id for context
            request_payload=data
        )
        job_id = job['id']

        if video_style == 'Zoom':
            # --- Parameters for smooth zoom, based on new documentation ---
            OUTPUT_W, OUTPUT_H = 1920, 1080
            FPS = 60  # Increased from 25 to 60 for ultra-smooth zoom animation
            MAX_ZOOM = 1.15  # Reduced from 1.2 to 1.15 for more gradual zoom effect
            INITIAL_SCALE_FACTOR = 3 # Increased from 2 to 3 for better quality during zoom

            actual_segment_duration = segment['fields'].get('Duration')
            if not actual_segment_duration or actual_segment_duration <= 0:
                error_msg = "Segment 'Duration' is missing or invalid for Zoom video style."
                logger.error(f"{error_msg} Segment ID: {data['segment_id']}")
                airtable.fail_job(job_id, error_msg)
                airtable.update_segment(data['segment_id'], {'Status': 'Video Generation Failed'})
                return jsonify({'error': error_msg}), 400

            # Add 20% to the duration for zoom videos to ensure smooth transitions
            zoom_duration = actual_segment_duration * 1.2
            logger.info(f"Zoom video for segment {data['segment_id']}: Original duration={actual_segment_duration}s, Extended duration={zoom_duration}s (+20%)")
            
            total_frames = int(zoom_duration * FPS)
            if total_frames < 1: # Ensure at least 1 frame
                total_frames = 1
            
            zoom_increment = (MAX_ZOOM - 1.0) / total_frames if total_frames > 0 else 0.0

            input_image_filename = "source_image.jpg"
            nca_inputs_payload = [
                {
                    'file_url': image_url,
                    'filename': input_image_filename,
                    'options': [
                        {'option': '-loop', 'argument': "1"},
                        {'option': '-framerate', 'argument': str(FPS)}
                    ]
                }
            ]

            initial_scale_width = OUTPUT_W * INITIAL_SCALE_FACTOR
            zoom_filter_string = (
                f"scale={initial_scale_width}:-1,"
                f"zoompan=z='min(zoom+{zoom_increment:.6f},{MAX_ZOOM})':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={total_frames}:s={OUTPUT_W}x{OUTPUT_H}:fps={FPS}"
            )
            nca_filters_payload = [
                {"filter": zoom_filter_string}
            ]

            output_filename_zoom = f"zoom_{data['segment_id']}_{job_id}.mp4"
            nca_outputs_payload = [
                {
                    'options': [
                        {"option": "-t", "argument": str(zoom_duration)},
                        {"option": "-c:v", "argument": "libx264"},
                        {"option": "-preset", "argument": "slow"},
                        {"option": "-crf", "argument": "23"},
                        {"option": "-pix_fmt", "argument": "yuv420p"},
                        {"option": "-an"},
                        {"option": "-movflags", "argument": "+faststart"}
                    ]
                }
            ]

            nca_compose_payload = {
                "inputs": nca_inputs_payload,
                "filters": nca_filters_payload,
                "outputs": nca_outputs_payload,
                "output_filename": output_filename_zoom
            }
            
            nca_webhook_params = f"job_id={job_id}&operation=image_zoom&target_id={data['segment_id']}"
            if video_id:
                nca_webhook_params += f"&video_id={video_id}"
            webhook_url_nca = f"{config.WEBHOOK_BASE_URL}/webhooks/nca-toolkit?{nca_webhook_params}"

            nca = NCAService()
            
            try:
                # Call the new method in NCAService, passing the structured payload components
                nca_response = nca.invoke_ffmpeg_compose_job(
                    inputs_payload=nca_inputs_payload,
                    outputs_payload=nca_outputs_payload,
                    filters_payload=nca_filters_payload,
                    # global_options_payload can be added if needed, currently not defined for this style
                    webhook_url=webhook_url_nca,
                    custom_id=job_id
                )
                
                external_nca_job_id = nca_response.get('job_id')
                airtable.update_job(job_id, {
                    'External Job ID': external_nca_job_id,
                    'Webhook URL': webhook_url_nca,
                    'Status': config.STATUS_PROCESSING,
                    'Notes': f"NCA Zoom video (smooth) generation initiated. NCA Job ID: {external_nca_job_id}"
                })
                
                return jsonify({
                    'job_id': job_id,
                    'segment_id': data['segment_id'],
                    'video_style': 'Zoom (smooth)',
                    'image_url_processed': image_url,
                    'original_duration_seconds': actual_segment_duration,
                    'extended_duration_seconds': zoom_duration,
                    'status': 'processing',
                    'external_nca_job_id': external_nca_job_id,
                    'webhook_url_sent_to_nca': webhook_url_nca,
                    'nca_payload_sent': nca_compose_payload # For debugging
                }), 202

            except requests.exceptions.HTTPError as e_http_nca:
                nca_response_text = e_http_nca.response.text if e_http_nca.response is not None else "No response body from NCA."
                error_msg_nca = f"NCA Zoom submission failed with HTTPError: {str(e_http_nca)}. NCA Response: {nca_response_text}"
                logger.error(f"Error submitting Zoom video job to NCA for segment {data['segment_id']}: {e_http_nca}. NCA Response: {nca_response_text}")
                airtable.fail_job(job_id, error_msg_nca) # This will now include NCA's response
                airtable.update_segment(data['segment_id'], {'Status': 'Video Generation Failed'})
                status_code = e_http_nca.response.status_code if e_http_nca.response is not None else 500
                return jsonify({'error': 'Failed to submit Zoom video job to NCA', 'details': error_msg_nca}), status_code
            except Exception as e_nca: # Catch other exceptions
                error_msg_nca = f"NCA Zoom submission failed with general error: {str(e_nca)}"
                logger.error(f"Error submitting Zoom video job to NCA for segment {data['segment_id']}: {e_nca}")
                airtable.fail_job(job_id, error_msg_nca)
                airtable.update_segment(data['segment_id'], {'Status': 'Video Generation Failed'})
                return jsonify({'error': 'Failed to submit Zoom video job to NCA', 'details': str(e_nca)}), 500
        
        else: # Default to Kling Video (or any other style not 'Zoom')
            if data['duration_override']:
                kling_duration = data['duration_override']
            else:
                segment_actual_duration = segment['fields'].get('Duration', 0)
                kling_duration = 5 if segment_actual_duration < 5 else 10
            
            goapi_webhook_params = f"job_id={job_id}&operation=video"
            if video_id:
                goapi_webhook_params += f"&video_id={video_id}"
            webhook_url_goapi = f"{config.WEBHOOK_BASE_URL}/webhooks/goapi?{goapi_webhook_params}"
            
            goapi = GoAPIService()
            result_goapi = goapi.generate_video(
                image_url=image_url,
                duration=kling_duration,
                aspect_ratio=data['aspect_ratio'],
                quality=data['quality'],
                webhook_url=webhook_url_goapi
            )
            
            external_goapi_job_id = result_goapi.get('id', result_goapi.get('task_id'))
            airtable.update_job(job_id, {
                'External Job ID': external_goapi_job_id,
                'Webhook URL': webhook_url_goapi,
                'Status': config.STATUS_PROCESSING,
                'Notes': f"Kling video generation initiated. GoAPI Task ID: {external_goapi_job_id}"
            })
            
            return jsonify({
                'job_id': job_id,
                'segment_id': data['segment_id'],
                'video_style': 'Kling Video (default)',
                'image_url': image_url,
                'duration_sent_to_kling': kling_duration,
                'aspect_ratio': data['aspect_ratio'],
                'quality': data['quality'],
                'status': 'processing',
                'webhook_url_sent_to_goapi': webhook_url_goapi,
                'external_goapi_task_id': external_goapi_job_id
            }), 202
        
    except Exception as e:
        logger.error(f"Error generating video: {e}")
        
        # Update segment status to 'Video Generation Failed'
        try:
            airtable.update_segment(data['segment_id'], {
                'Status': 'Video Generation Failed'
            })
        except:
            pass  # Don't fail if status update fails
        
        if 'job_id' in locals():
            airtable.fail_job(job_id, str(e))
        return jsonify({'error': 'Failed to generate video', 'details': str(e)}), 500


@api_v2_bp.route('/status', methods=['GET'])
def status_v2():
    """Simple status endpoint for v2 API."""
    return jsonify({
        'status': 'ok',
        'version': 'v2',
        'architecture': 'hybrid - direct ElevenLabs processing with webhook support for other services',
        'message': 'YouTube Video Engine API v2 is running with fixed ElevenLabs integration'
    })
