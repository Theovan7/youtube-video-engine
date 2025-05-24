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
@webhook_validation_required('elevenlabs')
def elevenlabs_webhook():
    """Handle ElevenLabs voice generation callbacks."""
    try:
        # Get webhook data
        payload = request.get_json()
        job_id = request.args.get('job_id')
        
        # Log webhook receipt
        api_logger.log_webhook('elevenlabs', payload)
        
        # Create webhook event record
        event = airtable.create_webhook_event(
            service='ElevenLabs',
            endpoint='/webhooks/elevenlabs',
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
            
            # Get segment ID from job
            segment_id = job['fields'].get('Related Segment', [None])[0]
            if not segment_id:
                raise ValueError("No segment ID found in job")
            
            # Process webhook based on status
            if payload.get('status') == 'completed':
                # Get audio URL from payload
                audio_url = payload.get('output', {}).get('url')
                if not audio_url:
                    raise ValueError("No audio URL in webhook payload")
                
                # Download audio file
                logger.info(f"Downloading audio from: {audio_url}")
                audio_response = requests.get(audio_url)
                audio_response.raise_for_status()
                
                # Upload to NCA for storage
                nca = NCAService()
                upload_result = nca.upload_file(
                    file_data=audio_response.content,
                    filename=f"voiceover_{segment_id}.mp3",
                    content_type='audio/mpeg'
                )
                
                # Update segment with voiceover
                airtable.update_segment(segment_id, {
                    'Voiceover': [{'url': upload_result['url']}],
                    'Status': 'voiceover_ready'
                })
                
                # Complete job
                airtable.complete_job(job_id, {'audio_url': upload_result['url']})
                
                # Mark webhook as processed
                airtable.mark_webhook_processed(event_id, success=True)
                
                logger.info(f"Successfully processed voiceover for segment {segment_id}")
                
                return jsonify({'status': 'success', 'segment_id': segment_id}), 200
                
            elif payload.get('status') == 'failed':
                # Handle failure
                error_message = payload.get('error', {}).get('message', 'Unknown error')
                
                # Update segment status
                airtable.update_segment(segment_id, {
                    'Status': 'voiceover_failed'
                })
                
                # Fail job
                airtable.fail_job(job_id, error_message)
                
                # Mark webhook as processed
                airtable.mark_webhook_processed(event_id, success=False)
                
                logger.error(f"Voiceover generation failed for segment {segment_id}: {error_message}")
                
                return jsonify({'status': 'failed', 'error': error_message}), 200
            
            else:
                # Unknown status
                raise ValueError(f"Unknown status: {payload.get('status')}")
                
        except Exception as e:
            # Log error and update webhook event
            logger.error(f"Error processing ElevenLabs webhook: {e}")
            airtable.mark_webhook_processed(event_id, success=False)
            
            # Try to fail the job if we have a job_id
            if job_id:
                try:
                    airtable.fail_job(job_id, str(e))
                except:
                    pass
            
            return jsonify({'status': 'error', 'message': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Critical error in ElevenLabs webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
                    # Handle segment combination
                    segment_id = job['fields'].get('Related Segment', [None])[0]
                    if not segment_id:
                        raise ValueError("No segment ID found in job")
                    
                    # Update segment with combined video
                    airtable.update_segment(segment_id, {
                        'Combined': [{'url': output_url}],
                        'Status': 'combined'
                    })
                    
                    logger.info(f"Successfully combined media for segment {segment_id}")
                    
                elif operation == 'concatenate':
                    # Handle video concatenation
                    video_id = job['fields'].get('Related Video', [None])[0]
                    if not video_id:
                        raise ValueError("No video ID found in job")
                    
                    # Update video with combined segments video
                    airtable.update_video(video_id, {
                        'Combined Segments Video': [{'url': output_url}],
                        'Status': 'segments_combined'
                    })
                    
                    logger.info(f"Successfully concatenated segments for video {video_id}")
                    
                elif operation == 'add_music':
                    # Handle music addition
                    video_id = job['fields'].get('Related Video', [None])[0]
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
                    segment_id = job['fields'].get('Related Segment', [None])[0]
                    if segment_id:
                        airtable.update_segment(segment_id, {'Status': 'combination_failed'})
                elif operation in ['concatenate', 'add_music']:
                    video_id = job['fields'].get('Related Video', [None])[0]
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
        
        # Log webhook receipt
        api_logger.log_webhook('goapi', payload)
        
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
            
            # Get video ID from job
            video_id = job['fields'].get('Related Video', [None])[0]
            if not video_id:
                raise ValueError("No video ID found in job")
            
            # Process webhook based on status
            if payload.get('status') == 'completed':
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
                # Handle failure
                error_message = payload.get('error', {}).get('message', 'Unknown error')
                
                # Update video status
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
