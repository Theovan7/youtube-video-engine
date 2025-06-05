"""Webhook handlers for external services."""

import logging
import json
import requests
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request

from config import get_config
from services.airtable_service import AirtableService
from services.nca_service import NCAService
from utils.logger import APILogger
from utils.webhook_validator import webhook_validation_required

logger = logging.getLogger(__name__)
api_logger = APILogger()

# Create blueprint
webhooks_bp = Blueprint('webhooks', __name__)

# Initialize services
airtable = AirtableService()
config = get_config()()


@webhooks_bp.route('/test', methods=['POST'])
def test_webhook():
    """Test webhook endpoint."""
    payload = request.get_json()
    logger.info(f"Test webhook received: {payload}")
    
    return jsonify({
        'status': 'ok',
        'message': 'Webhook received'
    })


@webhooks_bp.route('/elevenlabs', methods=['POST'])
def elevenlabs_webhook_deprecated():
    """DEPRECATED: ElevenLabs TTS API does not support webhooks.
    
    This endpoint is kept for backward compatibility but will never receive callbacks.
    Use the synchronous /api/v2/generate-voiceover endpoint instead.
    """
    logger.warning("ElevenLabs webhook endpoint called - this should not happen as ElevenLabs TTS doesn't support webhooks")
    return jsonify({
        'status': 'deprecated',
        'message': 'ElevenLabs TTS API does not support webhooks. Use synchronous processing instead.',
        'correct_endpoint': '/api/v2/generate-voiceover'
    }), 410  # 410 Gone


@webhooks_bp.route('/nca-toolkit', methods=['POST'])
@webhook_validation_required('nca-toolkit')
def nca_toolkit_webhook():
    """Handle NCA Toolkit media processing callbacks."""
    try:
        # Get webhook data
        payload = request.get_json()
        job_id = request.args.get('job_id')
        operation = request.args.get('operation')
        
        # Log webhook receipt
        api_logger.log_webhook('nca-toolkit', payload)
        
        # Create webhook event record
        event = airtable.create_webhook_event(
            service='NCA Toolkit',
            endpoint='/webhooks/nca-toolkit',
            payload=payload,
            related_job_id=job_id
        )
        event_id = event['id']
        
        try:
            # Get job record
            if not job_id:
                raise ValueError("Job ID not provided in webhook URL")
            
            job = airtable.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Process based on operation type
            if payload.get('status') == 'completed':
                output_url = payload.get('output_url')
                if not output_url:
                    raise ValueError("No output URL in webhook payload")
                
                if operation == 'combine':
                    # Handle segment combination - get segment ID with fallback
                    segment_id = None
                    
                    # Try to get from Segments field (correct field name)
                    if 'Segments' in job['fields'] and job['fields']['Segments']:
                        segment_id = job['fields']['Segments'][0]
                    else:
                        # Fallback: Extract from Request Payload
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            segment_id = payload_data.get('record_id') or payload_data.get('segment_id')
                        except Exception as e:
                            logger.error(f"Failed to parse Request Payload for segment ID: {e}")
                            segment_id = None
                    
                    if not segment_id:
                        raise ValueError("No segment ID found in job")
                    
                    # Update segment with combined video
                    airtable.update_segment(segment_id, {
                        'Combined': [{'url': output_url}],
                        'Status': 'combined'
                    })
                    
                    logger.info(f"Successfully combined media for segment {segment_id}")
                    
                elif operation == 'concatenate':
                    # Handle video concatenation - get video ID with fallback
                    video_id = None
                    
                    # Try to get from Related Video field (if it exists)
                    if 'Related Video' in job['fields'] and job['fields']['Related Video']:
                        video_id = job['fields']['Related Video'][0]
                    else:
                        # Fallback: Extract from Request Payload
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            video_id = payload_data.get('record_id') or payload_data.get('video_id')
                        except Exception as e:
                            logger.error(f"Failed to parse Request Payload for video ID: {e}")
                            video_id = None
                    
                    if not video_id:
                        raise ValueError("No video ID found in job")
                    
                    # Update video with combined segments video
                    airtable.update_video(video_id, {
                        'Combined Segments Video': [{'url': output_url}],
                        'Status': 'segments_combined'
                    })
                    
                    logger.info(f"Successfully concatenated segments for video {video_id}")
                    
                elif operation == 'add_music':
                    # Handle music addition - get video ID with fallback
                    video_id = None
                    
                    # Try to get from Related Video field (if it exists)
                    if 'Related Video' in job['fields'] and job['fields']['Related Video']:
                        video_id = job['fields']['Related Video'][0]
                    else:
                        # Fallback: Extract from Request Payload
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            video_id = payload_data.get('record_id') or payload_data.get('video_id')
                        except Exception as e:
                            logger.error(f"Failed to parse Request Payload for video ID: {e}")
                            video_id = None
                    
                    if not video_id:
                        raise ValueError("No video ID found in job")
                    
                    # Update video with final video
                    airtable.update_video(video_id, {
                        'Final Video': [{'url': output_url}],
                        'Status': 'completed'
                    })
                    
                    logger.info(f"Successfully added music to video {video_id}")
                
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                # Complete job
                airtable.complete_job(job_id, {'output_url': output_url})
                
                # Mark webhook as processed
                airtable.mark_webhook_processed(event_id, success=True)
                
                return jsonify({'status': 'success'}), 200
                
            elif payload.get('status') == 'failed':
                # Handle failure
                error_message = payload.get('error', 'Unknown error')
                
                # Update entity status based on operation
                if operation == 'combine':
                    # Get segment ID with fallback for failure handling
                    segment_id = None
                    if 'Segments' in job['fields'] and job['fields']['Segments']:
                        segment_id = job['fields']['Segments'][0]
                    else:
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            segment_id = payload_data.get('record_id') or payload_data.get('segment_id')
                        except:
                            segment_id = None
                    
                    if segment_id:
                        airtable.update_segment(segment_id, {'Status': 'combination_failed'})
                elif operation in ['concatenate', 'add_music']:
                    # Get video ID with fallback for failure handling
                    video_id = None
                    if 'Related Video' in job['fields'] and job['fields']['Related Video']:
                        video_id = job['fields']['Related Video'][0]
                    else:
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            video_id = payload_data.get('record_id') or payload_data.get('video_id')
                        except:
                            video_id = None
                    
                    if video_id:
                        status = 'concatenation_failed' if operation == 'concatenate' else 'music_addition_failed'
                        airtable.update_video_status(video_id, status, error_message)
                
                # Fail job
                airtable.fail_job(job_id, error_message)
                
                # Mark webhook as processed
                airtable.mark_webhook_processed(event_id, success=False)
                
                logger.error(f"NCA Toolkit operation {operation} failed: {error_message}")
                
                return jsonify({'status': 'failed', 'error': error_message}), 200
            
            else:
                raise ValueError(f"Unknown status: {payload.get('status')}")
                
        except Exception as e:
            # Log error and update webhook event
            logger.error(f"Error processing NCA Toolkit webhook: {e}")
            airtable.mark_webhook_processed(event_id, success=False)
            
            # Try to fail the job if we have a job_id
            if job_id:
                try:
                    airtable.fail_job(job_id, str(e))
                except:
                    pass
            
            return jsonify({'status': 'error', 'message': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Critical error in NCA Toolkit webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@webhooks_bp.route('/goapi', methods=['POST'])
@webhook_validation_required('goapi')
def goapi_webhook():
    """Handle GoAPI music generation callbacks."""
    try:
        # Get webhook data
        payload = request.get_json()
        job_id = request.args.get('job_id')
        
        # Enhanced logging for debugging
        logger.info(f"GoAPI webhook received - Job ID: {job_id}")
        logger.info(f"Payload type: {type(payload)}")
        logger.info(f"Payload: {json.dumps(payload, indent=2) if payload else 'None'}")
        
        # Log webhook receipt
        api_logger.log_webhook('goapi', payload)
        
        # Handle empty payload
        if not payload:
            logger.error("GoAPI webhook received with empty payload")
            return jsonify({'status': 'error', 'message': 'Empty payload'}), 400
        
        # Create webhook event record
        event = airtable.create_webhook_event(
            service='GoAPI',
            endpoint='/webhooks/goapi',
            payload=payload,
            related_job_id=job_id
        )
        event_id = event['id']
        
        try:
            # Get job record
            if not job_id:
                raise ValueError("Job ID not provided in webhook URL")
            
            job = airtable.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Get job type to determine processing
            job_type = job['fields'].get('Job Type')
            operation = request.args.get('operation', 'music')  # Default to music for backward compatibility
            
            # Process webhook based on job type or operation
            # GoAPI might send the complete task result, check for that first
            task_status = None
            
            # Check if this is a complete task result (has 'task_id' and 'status' at root)
            if 'task_id' in payload and 'status' in payload:
                task_status = payload.get('status')
            # Otherwise check for status in the payload
            elif 'status' in payload:
                task_status = payload.get('status')
            else:
                # Log the payload structure for debugging
                logger.warning(f"Unexpected GoAPI webhook payload structure: {json.dumps(payload, indent=2)}")
                raise ValueError("Missing status field in webhook payload")
            
            if task_status == 'completed':
                if job_type == config.JOB_TYPE_VIDEO or operation == 'video':
                    # Handle video generation completion
                    video_data = payload.get('output', {})
                    video_url = video_data.get('video_url') or video_data.get('url')
                    
                    if not video_url:
                        raise ValueError("No video URL in webhook payload")
                    
                    # Get segment ID from job
                    segment_id = None
                    if 'Segments' in job['fields'] and job['fields']['Segments']:
                        segment_id = job['fields']['Segments'][0]
                    else:
                        # Fallback: Extract from Request Payload
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            segment_id = payload_data.get('segment_id')
                        except Exception as e:
                            logger.error(f"Failed to parse Request Payload for segment ID: {e}")
                            segment_id = None
                    
                    if not segment_id:
                        raise ValueError("No segment ID found in job")
                    
                    # Update segment with generated video
                    airtable.update_segment(segment_id, {
                        'Video': [{'url': video_url}],
                        'Status': 'Video Ready'
                    })
                    
                    # Complete job
                    airtable.complete_job(job_id, {'video_url': video_url})
                    
                    # Mark webhook as processed
                    airtable.mark_webhook_processed(event_id, success=True)
                    
                    logger.info(f"Successfully generated video for segment {segment_id}")
                    
                    return jsonify({
                        'status': 'success',
                        'segment_id': segment_id,
                        'video_url': video_url
                    }), 200
                
                else:
                    # Handle music generation completion (existing logic)
                    # Get video ID from job with fallback
                    video_id = None
                    
                    # Try to get from Related Video field (if it exists)
                    if 'Related Video' in job['fields'] and job['fields']['Related Video']:
                        video_id = job['fields']['Related Video'][0]
                    else:
                        # Fallback: Extract from Request Payload
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            video_id = payload_data.get('record_id') or payload_data.get('video_id')
                        except Exception as e:
                            logger.error(f"Failed to parse Request Payload for video ID: {e}")
                            video_id = None
                    
                    if not video_id:
                        raise ValueError("No video ID found in job")
                
                    # Get music URL from payload
                    music_data = payload.get('output', {})
                    music_url = music_data.get('audio_url') or music_data.get('url')
                
                if not music_url:
                    raise ValueError("No music URL in webhook payload")
                
                # Update video with music URL
                airtable.update_video(video_id, {
                    'Music': [{'url': music_url}],
                    'Status': 'adding_music'
                })
                
                # Get combined video URL
                video = airtable.get_video(video_id)
                combined_video_url = video['fields'].get('Combined Segments Video', [{}])[0].get('url')
                
                if not combined_video_url:
                    raise ValueError("No combined video URL found")
                
                # Create new job for adding music
                music_job = airtable.create_job(
                    job_type=config.JOB_TYPE_FINAL,
                    video_id=video_id,
                    request_payload={'operation': 'add_music'}
                )
                music_job_id = music_job['id']
                
                # Generate webhook URL
                webhook_url = f"{config.WEBHOOK_BASE_URL}/webhooks/nca-toolkit?job_id={music_job_id}&operation=add_music"
                
                # Request adding music to video
                nca = NCAService()
                add_music_result = nca.add_background_music(
                    video_url=combined_video_url,
                    music_url=music_url,
                    output_filename=f"video_{video_id}_final.mp4",
                    volume_ratio=0.2,
                    webhook_url=webhook_url
                )
                
                # Update music job with external ID
                if 'job_id' in add_music_result:
                    airtable.update_job(music_job_id, {
                        'External Job ID': add_music_result['job_id'],
                        'Webhook URL': webhook_url,
                        'Status': config.STATUS_PROCESSING
                    })
                
                # Complete original music generation job
                airtable.complete_job(job_id, {'music_url': music_url})
                
                # Mark webhook as processed
                airtable.mark_webhook_processed(event_id, success=True)
                
                logger.info(f"Successfully generated music for video {video_id}")
                
                return jsonify({
                    'status': 'success',
                    'video_id': video_id,
                    'music_job_id': music_job_id
                }), 200
                
            elif payload.get('status') == 'failed':
                # Get job type to determine failure handling
                job_type = job['fields'].get('Job Type')
                operation = request.args.get('operation', 'music')
                
                if job_type == config.JOB_TYPE_VIDEO or operation == 'video':
                    # Handle video generation failure
                    # Get segment ID for failure handling
                    segment_id = None
                    if 'Segments' in job['fields'] and job['fields']['Segments']:
                        segment_id = job['fields']['Segments'][0]
                    else:
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            segment_id = payload_data.get('segment_id')
                        except:
                            segment_id = None
                    
                    error_message = payload.get('error', {}).get('message', 'Unknown error')
                    
                    # Update segment status if we have segment_id
                    if segment_id:
                        airtable.update_segment(segment_id, {'Status': 'Video Generation Failed'})
                    
                    # Fail job
                    airtable.fail_job(job_id, error_message)
                    
                    # Mark webhook as processed
                    airtable.mark_webhook_processed(event_id, success=False)
                    
                    logger.error(f"Video generation failed for segment {segment_id}: {error_message}")
                    
                    return jsonify({'status': 'failed', 'error': error_message}), 200
                
                else:
                    # Handle music generation failure (existing logic)
                    # Get video ID with fallback for failure handling
                    video_id = None
                    
                    # Try to get from Related Video field (if it exists)
                    if 'Related Video' in job['fields'] and job['fields']['Related Video']:
                        video_id = job['fields']['Related Video'][0]
                    else:
                        # Fallback: Extract from Request Payload
                        request_payload = job['fields'].get('Request Payload', '{}')
                        try:
                            import ast
                            payload_data = ast.literal_eval(request_payload)
                            video_id = payload_data.get('record_id') or payload_data.get('video_id')
                        except:
                            video_id = None
                    
                    error_message = payload.get('error', {}).get('message', 'Unknown error')
                
                # Update video status if we have video_id
                if video_id:
                    airtable.update_video_status(video_id, 'music_generation_failed', error_message)
                
                # Fail job
                airtable.fail_job(job_id, error_message)
                
                # Mark webhook as processed
                airtable.mark_webhook_processed(event_id, success=False)
                
                logger.error(f"Music generation failed for video {video_id}: {error_message}")
                
                return jsonify({'status': 'failed', 'error': error_message}), 200
            
            else:
                raise ValueError(f"Unknown status: {payload.get('status')}")
                
        except Exception as e:
            # Log error and update webhook event
            logger.error(f"Error processing GoAPI webhook: {e}")
            airtable.mark_webhook_processed(event_id, success=False)
            
            # Try to fail the job if we have a job_id
            if job_id:
                try:
                    airtable.fail_job(job_id, str(e))
                except:
                    pass
            
            return jsonify({'status': 'error', 'message': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Critical error in GoAPI webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
