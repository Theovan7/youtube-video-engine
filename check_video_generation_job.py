#!/usr/bin/env python3
"""
Check the status of a specific video generation job that appears to be stuck.
Job External ID: f9021949-23de-4e0d-90d4-d1e810172cff
Started at: 2:35pm on 6/6/2025
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.goapi_service import GoAPIService
from services.airtable_service import AirtableService
from utils.logger import setup_logging

# Setup logging
logger = setup_logging()

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
    
    try:
        goapi = GoAPIService()
        
        # Get current status from GoAPI
        status_data = goapi.get_video_status(task_id)
        
        logger.info(f"GoAPI Response: {json.dumps(status_data, indent=2)}")
        
        # Extract relevant information
        status = status_data.get('status', 'unknown')
        progress = status_data.get('progress', 0)
        output = status_data.get('output')
        error = status_data.get('error')
        
        return {
            'status': status,
            'progress': progress,
            'output': output,
            'error': error,
            'raw_response': status_data
        }
        
    except Exception as e:
        logger.error(f"Failed to check GoAPI status: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'raw_response': None
        }

def find_airtable_job(external_job_id):
    """Find the job in Airtable by external job ID."""
    logger.info(f"Searching for job in Airtable with External Job ID: {external_job_id}")
    
    try:
        airtable = AirtableService()
        
        # Search for the job
        filter_formula = f"{{External Job ID}} = '{external_job_id}'"
        jobs = airtable.get_jobs(filter_formula)
        
        if jobs:
            job = jobs[0]
            logger.info(f"Found job in Airtable: {job['id']}")
            logger.info(f"Job details: {json.dumps(job['fields'], indent=2)}")
            return job
        else:
            logger.warning("Job not found in Airtable")
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
    # According to benchmarks, video generation typically takes less than 10 minutes
    # But let's check against a more conservative 30-minute threshold
    max_duration = 30 * 60  # 30 minutes in seconds
    
    if duration_seconds > max_duration:
        logger.warning(f"⚠️  Job has been running for {duration_str}, which exceeds typical duration!")
    
    # Get GoAPI status
    goapi_status = check_goapi_status(task_id)
    
    logger.info(f"\nGoAPI Status: {goapi_status['status']}")
    if goapi_status.get('progress'):
        logger.info(f"Progress: {goapi_status['progress']}%")
    
    if goapi_status.get('output'):
        logger.info(f"Output URL: {goapi_status['output']}")
    
    if goapi_status.get('error'):
        logger.error(f"Error: {goapi_status['error']}")
    
    # Airtable status
    if airtable_job:
        airtable_status = airtable_job['fields'].get('Status', 'unknown')
        logger.info(f"\nAirtable Status: {airtable_status}")
        
        # Check for status mismatch
        if goapi_status['status'] != airtable_status:
            logger.warning(f"⚠️  Status mismatch! GoAPI: {goapi_status['status']}, Airtable: {airtable_status}")
    
    # Determine if job is stuck
    logger.info("\n" + "-"*60)
    logger.info("DIAGNOSIS:")
    
    if goapi_status['status'] == 'completed' and goapi_status.get('output'):
        logger.info("✅ Job appears to be completed successfully in GoAPI")
        logger.info("   - Video is ready at: " + goapi_status['output'])
        if airtable_job and airtable_job['fields'].get('Status') != 'completed':
            logger.warning("   - BUT Airtable status is not updated!")
            logger.warning("   - Webhook may have failed to deliver")
    elif goapi_status['status'] == 'failed':
        logger.error("❌ Job failed in GoAPI")
        if goapi_status.get('error'):
            logger.error(f"   - Error details: {goapi_status['error']}")
    elif goapi_status['status'] == 'processing' and duration_seconds > max_duration:
        logger.warning("⚠️  Job appears to be stuck in processing state")
        logger.warning(f"   - Has been processing for {duration_str}")
        logger.warning("   - This exceeds typical video generation time")
        logger.warning("   - Consider cancelling and retrying the job")
    elif goapi_status['status'] == 'processing':
        logger.info("🔄 Job is still processing (within normal time range)")
        if goapi_status.get('progress'):
            logger.info(f"   - Progress: {goapi_status['progress']}%")
    else:
        logger.warning(f"❓ Unknown status: {goapi_status['status']}")
    
    return goapi_status

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