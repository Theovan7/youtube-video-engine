#!/usr/bin/env python3
"""
Check the status of record reci0gT2LhNaIaFtp and all related jobs/segments.
"""

import os
import json
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_airtable_headers():
    """Get Airtable API headers."""
    api_key = os.getenv('AIRTABLE_API_KEY')
    if not api_key:
        raise ValueError("AIRTABLE_API_KEY not found in environment")
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

def get_video_record(record_id):
    """Get the video record from Airtable."""
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_VIDEOS_TABLE', 'Videos')
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}"
    headers = get_airtable_headers()
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to get video record: {response.status_code} - {response.text}")
        return None

def get_segments(video_record_id):
    """Get all segments for a video."""
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_SEGMENTS_TABLE', 'Segments')
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = get_airtable_headers()
    params = {
        'filterByFormula': f"{{Video}} = '{video_record_id}'"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('records', [])
    else:
        logger.error(f"Failed to get segments: {response.status_code}")
        return []

def get_jobs_for_video(video_record_id):
    """Get all jobs related to a video."""
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_JOBS_TABLE', 'Jobs')
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = get_airtable_headers()
    params = {
        'filterByFormula': f"{{Related Video}} = '{video_record_id}'"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('records', [])
    else:
        logger.error(f"Failed to get jobs: {response.status_code}")
        return []

def check_external_job_status(external_job_id, job_type):
    """Check the status of an external job."""
    if job_type == 'goapi':
        # Check GoAPI status
        api_key = os.getenv('GOAPI_API_KEY')
        base_url = os.getenv('GOAPI_BASE_URL', 'https://api.goapi.ai')
        
        url = f"{base_url}/api/v1/task/{external_job_id}"
        headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and data.get('data'):
                    return data['data']
            return None
        except Exception as e:
            logger.error(f"Failed to check GoAPI status: {e}")
            return None
    
    return None

def analyze_video_status(record_id):
    """Analyze the complete status of a video and its processing."""
    logger.info(f"\n{'='*60}")
    logger.info(f"ANALYZING VIDEO RECORD: {record_id}")
    logger.info(f"{'='*60}")
    
    # Get video record
    video = get_video_record(record_id)
    if not video:
        logger.error("Failed to retrieve video record")
        return
    
    video_fields = video.get('fields', {})
    logger.info(f"\nVideo Name: {video_fields.get('Name', 'Unknown')}")
    logger.info(f"Video Status: {video_fields.get('Status', 'Unknown')}")
    logger.info(f"Created: {video.get('createdTime', 'Unknown')}")
    
    # Get segments
    segments = get_segments(record_id)
    logger.info(f"\nSegments: {len(segments)} found")
    
    segment_statuses = {}
    for i, segment in enumerate(segments):
        fields = segment.get('fields', {})
        segment_id = segment.get('id')
        order = fields.get('Order', i+1)
        status = fields.get('Status', 'Unknown')
        
        segment_statuses[order] = {
            'id': segment_id,
            'status': status,
            'has_voiceover': bool(fields.get('Voiceover')),
            'has_video': bool(fields.get('Base Video')),
            'has_combined': bool(fields.get('Combined'))
        }
        
        logger.info(f"  Segment {order}: Status={status}, "
                   f"Voiceover={'✓' if segment_statuses[order]['has_voiceover'] else '✗'}, "
                   f"Video={'✓' if segment_statuses[order]['has_video'] else '✗'}, "
                   f"Combined={'✓' if segment_statuses[order]['has_combined'] else '✗'}")
    
    # Get jobs
    jobs = get_jobs_for_video(record_id)
    logger.info(f"\nJobs: {len(jobs)} found")
    
    active_jobs = []
    for job in jobs:
        fields = job.get('fields', {})
        job_type = fields.get('Type', 'Unknown')
        status = fields.get('Status', 'Unknown')
        external_id = fields.get('External Job ID')
        created = job.get('createdTime', 'Unknown')
        
        logger.info(f"\nJob: {job_type}")
        logger.info(f"  Status: {status}")
        logger.info(f"  Created: {created}")
        logger.info(f"  External ID: {external_id}")
        
        # Check external status for active jobs
        if status in ['pending', 'processing'] and external_id:
            service = 'goapi' if job_type in ['generate_video', 'generate_ai_image'] else None
            if service:
                external_status = check_external_job_status(external_id, service)
                if external_status:
                    logger.info(f"  External Status: {external_status.get('status', 'Unknown')}")
                    if external_status.get('progress'):
                        logger.info(f"  Progress: {external_status.get('progress')}%")
                    if external_status.get('output'):
                        logger.info(f"  Output Ready: {external_status.get('output')}")
                    
                    active_jobs.append({
                        'job': job,
                        'external_status': external_status
                    })
    
    # Provide diagnosis
    logger.info(f"\n{'-'*60}")
    logger.info("DIAGNOSIS:")
    logger.info(f"{'-'*60}")
    
    # Check for stuck segments
    stuck_segments = []
    for order, seg_info in segment_statuses.items():
        if seg_info['status'] == 'processing':
            stuck_segments.append(order)
        elif seg_info['status'] == 'pending' and seg_info['has_voiceover'] and seg_info['has_video'] and not seg_info['has_combined']:
            logger.warning(f"Segment {order} has voiceover and video but no combined output - may need combination")
    
    if stuck_segments:
        logger.warning(f"⚠️  Found {len(stuck_segments)} segments stuck in processing: {stuck_segments}")
    
    # Check for completed external jobs not reflected in Airtable
    for job_info in active_jobs:
        job = job_info['job']
        external_status = job_info['external_status']
        
        if external_status.get('status') == 'completed' and external_status.get('output'):
            logger.warning(f"⚠️  Job {job['id']} is completed externally but not updated in Airtable!")
            logger.warning(f"    Output URL: {external_status['output']}")
    
    # Overall status
    if video_fields.get('Status') == 'completed':
        logger.info("✅ Video processing appears to be completed")
    elif stuck_segments or active_jobs:
        logger.warning("🔄 Video processing is in progress or stuck")
    else:
        logger.info("📋 Video is waiting to be processed")
    
    return {
        'video': video,
        'segments': segments,
        'jobs': jobs,
        'active_jobs': active_jobs,
        'stuck_segments': stuck_segments
    }

def main():
    """Main function."""
    record_id = "reci0gT2LhNaIaFtp"
    
    logger.info(f"Checking status for record: {record_id}")
    logger.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    result = analyze_video_status(record_id)
    
    if result and (result['stuck_segments'] or result['active_jobs']):
        logger.info(f"\n{'='*60}")
        logger.info("RECOMMENDED ACTIONS:")
        logger.info(f"{'='*60}")
        
        if result['stuck_segments']:
            logger.info("1. Check webhook delivery for stuck segments")
            logger.info("2. Manually update segment statuses if jobs are complete")
            logger.info("3. Retry combination for segments with both video and voiceover")
        
        if result['active_jobs']:
            logger.info("1. Check external job statuses")
            logger.info("2. Update Airtable records if jobs are complete")
            logger.info("3. Verify webhook endpoints are working correctly")

if __name__ == "__main__":
    main()