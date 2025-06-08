#!/usr/bin/env python3
"""
Check the status of the combination job for segment reci0gT2LhNaIaFtp
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

def check_nca_job_status(job_id):
    """Check NCA job status."""
    api_key = os.getenv('NCA_API_KEY')
    base_url = os.getenv('NCA_BASE_URL', 'https://api.ncatoolkit.com')
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    url = f"{base_url}/v1/jobs/{job_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get NCA job status: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error checking NCA job: {e}")
        return None

def get_job_from_airtable(job_id):
    """Get job details from Airtable."""
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_JOBS_TABLE', 'Jobs')
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{job_id}"
    headers = get_airtable_headers()
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to get job from Airtable: {response.status_code}")
        return None

def get_segment_status(segment_id):
    """Get segment details from Airtable."""
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_SEGMENTS_TABLE', 'Segments')
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{segment_id}"
    headers = get_airtable_headers()
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to get segment: {response.status_code}")
        return None

def main():
    # Job details from the logs
    airtable_job_id = "recSuCamTeC8nwje9"
    nca_job_id = "3d9d23eb-4a2f-4136-82a8-3ebc090ae96f"
    segment_id = "reci0gT2LhNaIaFtp"
    
    logger.info(f"Checking combination job status")
    logger.info(f"Airtable Job ID: {airtable_job_id}")
    logger.info(f"NCA Job ID: {nca_job_id}")
    logger.info(f"Segment ID: {segment_id}")
    logger.info("="*60)
    
    # Check Airtable job
    job = get_job_from_airtable(airtable_job_id)
    if job:
        fields = job.get('fields', {})
        logger.info(f"\nAirtable Job Status: {fields.get('Status', 'Unknown')}")
        logger.info(f"Type: {fields.get('Type', 'Unknown')}")
        logger.info(f"Created: {job.get('createdTime', 'Unknown')}")
        
        if fields.get('Error Details'):
            logger.error(f"Error: {fields.get('Error Details')}")
    
    # Check NCA job status
    logger.info(f"\nChecking NCA job status...")
    nca_status = check_nca_job_status(nca_job_id)
    if nca_status:
        logger.info(f"NCA Status: {nca_status.get('status', 'Unknown')}")
        if nca_status.get('progress'):
            logger.info(f"Progress: {nca_status.get('progress')}%")
        if nca_status.get('output_url'):
            logger.info(f"Output URL: {nca_status.get('output_url')}")
        if nca_status.get('error'):
            logger.error(f"NCA Error: {nca_status.get('error')}")
    
    # Check segment status
    logger.info(f"\nChecking segment status...")
    segment = get_segment_status(segment_id)
    if segment:
        fields = segment.get('fields', {})
        logger.info(f"Segment Status: {fields.get('Status', 'Unknown')}")
        logger.info(f"Has Combined Video: {'Yes' if fields.get('Combined') else 'No'}")
        
        if fields.get('Combined'):
            logger.info("✅ Segment has been successfully combined!")
        else:
            logger.info("⏳ Waiting for combination to complete...")
    
    logger.info("\n" + "="*60)
    logger.info("SUMMARY:")
    
    # Determine overall status
    if nca_status and nca_status.get('status') == 'completed' and nca_status.get('output_url'):
        logger.info("✅ NCA job completed successfully!")
        logger.info(f"   Output: {nca_status['output_url']}")
        if segment and not segment.get('fields', {}).get('Combined'):
            logger.warning("⚠️  But segment not updated yet - webhook may be delayed")
    elif nca_status and nca_status.get('status') == 'processing':
        logger.info("🔄 Job is still processing...")
        if nca_status.get('progress'):
            logger.info(f"   Progress: {nca_status.get('progress')}%")
    elif nca_status and nca_status.get('status') == 'failed':
        logger.error("❌ Job failed!")
    else:
        logger.warning("❓ Unable to determine job status")

if __name__ == "__main__":
    main()