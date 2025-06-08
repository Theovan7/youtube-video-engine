#!/usr/bin/env python3
"""
Check the status of a specific video generation job that appears to be stuck.
Job External ID: f9021949-23de-4e0d-90d4-d1e810172cff
Started at: 2:35pm on 6/6/2025
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_job_duration(start_time_str):
    """Calculate how long the job has been running."""
    # Parse the start time (assuming today 6/6/2025 at 2:35pm)
    start_time = datetime(2025, 6, 6, 14, 35, 0)  # 2:35pm
    current_time = datetime.now()
    
    duration = current_time - start_time
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    
    return f"{hours} hours {minutes} minutes", duration.total_seconds()

def check_goapi_status(task_id):
    """Check the current status with GoAPI."""
    logger.info(f"Checking GoAPI status for task: {task_id}")
    
    # Get API credentials
    api_key = os.getenv('GOAPI_API_KEY')
    base_url = os.getenv('GOAPI_BASE_URL', 'https://api.goapi.ai')
    
    if not api_key:
        logger.error("GOAPI_API_KEY not found in environment")
        return None
    
    try:
        # Make request to GoAPI
        url = f"{base_url}/api/v1/task/{task_id}"
        headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Making request to: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Parse response - handle nested structure
            if result.get('code') == 200 and result.get('data'):
                return result['data']
            else:
                return result
        else:
            logger.error(f"GoAPI request failed with status: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to check GoAPI status: {e}")
        return None

def find_airtable_job(external_job_id):
    """Find the job in Airtable by external job ID."""
    logger.info(f"Searching for job in Airtable with External Job ID: {external_job_id}")
    
    # Get Airtable credentials
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key or not base_id:
        logger.error("Airtable credentials not found in environment")
        return None
    
    try:
        # Search for the job
        url = f"https://api.airtable.com/v0/{base_id}/Jobs"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        params = {
            'filterByFormula': f"{{External Job ID}} = '{external_job_id}'"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            
            if records:
                job = records[0]
                logger.info(f"Found job in Airtable: {job['id']}")
                logger.info(f"Job fields: {json.dumps(job['fields'], indent=2)}")
                return job
            else:
                logger.warning("Job not found in Airtable")
                return None
        else:
            logger.error(f"Airtable request failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to search Airtable: {e}")
        return None

def analyze_job_status(task_id, airtable_job):
    """Analyze the job status and determine if it's stuck."""
    logger.info("\n" + "="*60)
    logger.info("ANALYZING VIDEO GENERATION JOB")
    logger.info("="*60)
    
    # Calculate duration
    duration_str, duration_seconds = check_job_duration("2:35pm")
    logger.info(f"\nJob Duration: {duration_str}")
    
    # Check if duration exceeds typical video generation time
    max_duration = 30 * 60  # 30 minutes in seconds
    
    if duration_seconds > max_duration:
        logger.warning(f"⚠️  Job has been running for {duration_str}, which exceeds typical duration!")
    
    # Get GoAPI status
    goapi_data = check_goapi_status(task_id)
    
    if not goapi_data:
        logger.error("Failed to get GoAPI status")
        return None
    
    status = goapi_data.get('status', 'unknown')
    progress = goapi_data.get('progress', 0)
    output = goapi_data.get('output')
    error = goapi_data.get('error')
    
    logger.info(f"\nGoAPI Status: {status}")
    if progress:
        logger.info(f"Progress: {progress}%")
    
    if output:
        logger.info(f"Output URL: {output}")
    
    if error:
        logger.error(f"Error: {error}")
    
    # Airtable status
    if airtable_job:
        airtable_status = airtable_job['fields'].get('Status', 'unknown')
        logger.info(f"\nAirtable Status: {airtable_status}")
        
        # Check for status mismatch
        if status != airtable_status:
            logger.warning(f"⚠️  Status mismatch! GoAPI: {status}, Airtable: {airtable_status}")
    
    # Determine if job is stuck
    logger.info("\n" + "-"*60)
    logger.info("DIAGNOSIS:")
    
    if status == 'completed' and output:
        logger.info("✅ Job appears to be completed successfully in GoAPI")
        logger.info("   - Video is ready at: " + output)
        if airtable_job and airtable_job['fields'].get('Status') != 'completed':
            logger.warning("   - BUT Airtable status is not updated!")
            logger.warning("   - Webhook may have failed to deliver")
    elif status == 'failed':
        logger.error("❌ Job failed in GoAPI")
        if error:
            logger.error(f"   - Error details: {error}")
    elif status == 'processing' and duration_seconds > max_duration:
        logger.warning("⚠️  Job appears to be stuck in processing state")
        logger.warning(f"   - Has been processing for {duration_str}")
        logger.warning("   - This exceeds typical video generation time")
        logger.warning("   - Consider cancelling and retrying the job")
    elif status == 'processing':
        logger.info("🔄 Job is still processing (within normal time range)")
        if progress:
            logger.info(f"   - Progress: {progress}%")
    else:
        logger.warning(f"❓ Unknown status: {status}")
    
    return {
        'status': status,
        'progress': progress,
        'output': output,
        'error': error,
        'raw_data': goapi_data
    }

def main():
    """Main function to check the video generation job."""
    task_id = "f9021949-23de-4e0d-90d4-d1e810172cff"
    
    logger.info(f"Checking video generation job: {task_id}")
    logger.info(f"Job started at: 2:35pm on 6/6/2025")
    logger.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find job in Airtable
    airtable_job = find_airtable_job(task_id)
    
    # Analyze job status
    status = analyze_job_status(task_id, airtable_job)
    
    if not status:
        logger.error("Unable to analyze job status")
        return
    
    # Provide recommendations
    logger.info("\n" + "="*60)
    logger.info("RECOMMENDATIONS:")
    logger.info("="*60)
    
    if status['status'] == 'completed' and status.get('output'):
        logger.info("1. Job is complete - update Airtable if needed")
        logger.info("2. Download video from: " + status['output'])
        if airtable_job:
            logger.info(f"3. Update job {airtable_job['id']} status to 'completed'")
            logger.info(f"4. Update related segment with video URL")
    elif status['status'] == 'processing':
        duration_str, duration_seconds = check_job_duration("2:35pm")
        if duration_seconds > 1800:  # 30 minutes
            logger.info("1. Job has been processing for too long")
            logger.info("2. Consider cancelling the job if possible")
            logger.info("3. Retry video generation with a new job")
        else:
            logger.info("1. Job is still processing - wait a bit longer")
            logger.info("2. Check again in 5-10 minutes")
    elif status['status'] == 'failed':
        logger.info("1. Job failed - check error details")
        logger.info("2. Retry video generation with adjusted parameters")
        logger.info("3. Consider using a different video quality setting")

if __name__ == "__main__":
    main()