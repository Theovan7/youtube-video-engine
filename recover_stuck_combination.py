#!/usr/bin/env python3
"""
Recover stuck combination job by manually checking NCA status and updating Airtable.
"""

import os
import json
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
import time

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

def check_nca_job_directly(job_id):
    """Try different approaches to check NCA job status."""
    api_key = os.getenv('NCA_API_KEY')
    base_url = os.getenv('NCA_BASE_URL', 'https://api.ncatoolkit.com')
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Try different endpoints
    endpoints = [
        f"/v1/jobs/{job_id}",
        f"/v1/job/{job_id}",
        f"/v1/ffmpeg/jobs/{job_id}",
        f"/v1/ffmpeg/job/{job_id}",
        f"/v1/status/{job_id}"
    ]
    
    for endpoint in endpoints:
        url = base_url + endpoint
        logger.info(f"Trying: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            logger.info(f"Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Success! Data: {json.dumps(data, indent=2)}")
                return data
            elif response.status_code != 404:
                logger.warning(f"Got {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error: {e}")
    
    return None

def simulate_webhook(job_id, segment_id, output_url):
    """Simulate the webhook that should have been received."""
    logger.info("Simulating webhook delivery...")
    
    # Prepare webhook payload similar to what NCA would send
    webhook_data = {
        "id": job_id,
        "job_id": job_id,
        "status": "completed",
        "output_url": output_url,
        "webhook_simulated": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Call the webhook endpoint
    webhook_url = f"https://youtube-video-engine.fly.dev/webhooks/nca-toolkit?job_id={job_id}&operation=combine"
    
    try:
        response = requests.post(webhook_url, json=webhook_data, timeout=30)
        logger.info(f"Webhook response: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to deliver webhook: {e}")
        return False

def update_manually(airtable_job_id, segment_id, output_url):
    """Manually update Airtable records."""
    base_id = os.getenv('AIRTABLE_BASE_ID')
    headers = get_airtable_headers()
    
    # Update job status
    job_url = f"https://api.airtable.com/v0/{base_id}/Jobs/{airtable_job_id}"
    job_update = {
        "fields": {
            "Status": "completed",
            "Response Payload": json.dumps({
                "output_url": output_url,
                "completed_at": datetime.utcnow().isoformat(),
                "manual_recovery": True
            })
        }
    }
    
    response = requests.patch(job_url, headers=headers, json=job_update)
    if response.status_code == 200:
        logger.info("✅ Job updated successfully")
    else:
        logger.error(f"Failed to update job: {response.status_code}")
    
    # Update segment with combined video
    segment_url = f"https://api.airtable.com/v0/{base_id}/Segments/{segment_id}"
    segment_update = {
        "fields": {
            "Status": "completed",
            "Combined": [{"url": output_url}]
        }
    }
    
    response = requests.patch(segment_url, headers=headers, json=segment_update)
    if response.status_code == 200:
        logger.info("✅ Segment updated successfully")
    else:
        logger.error(f"Failed to update segment: {response.status_code}")

def main():
    # Known details
    airtable_job_id = "recSuCamTeC8nwje9"
    nca_job_id = "3d9d23eb-4a2f-4136-82a8-3ebc090ae96f"
    segment_id = "reci0gT2LhNaIaFtp"
    output_filename = "segment_reci0gT2LhNaIaFtp_combined.mp4"
    
    logger.info("="*60)
    logger.info("RECOVERING STUCK COMBINATION JOB")
    logger.info("="*60)
    logger.info(f"Airtable Job: {airtable_job_id}")
    logger.info(f"NCA Job: {nca_job_id}")
    logger.info(f"Segment: {segment_id}")
    
    # Step 1: Try to check NCA job status
    logger.info("\nStep 1: Checking NCA job status...")
    nca_status = check_nca_job_directly(nca_job_id)
    
    if nca_status and nca_status.get('status') == 'completed' and nca_status.get('output_url'):
        output_url = nca_status['output_url']
        logger.info(f"✅ Job is completed! Output: {output_url}")
        
        # Step 2: Try webhook delivery first
        logger.info("\nStep 2: Attempting webhook delivery...")
        if simulate_webhook(airtable_job_id, segment_id, output_url):
            logger.info("✅ Webhook delivered successfully")
        else:
            # Step 3: Manual update as fallback
            logger.info("\nStep 3: Manually updating records...")
            update_manually(airtable_job_id, segment_id, output_url)
    
    elif nca_status:
        logger.warning(f"Job status: {nca_status.get('status', 'unknown')}")
        if nca_status.get('error'):
            logger.error(f"Job error: {nca_status.get('error')}")
    else:
        # Try to construct the likely output URL
        logger.warning("Could not check NCA status - constructing likely output URL")
        
        # NCA typically uses a pattern for output URLs
        # This is a guess based on common patterns
        bucket_name = "nca-toolkit-outputs"  # Common bucket name
        likely_url = f"https://s3.amazonaws.com/{bucket_name}/{output_filename}"
        
        logger.info(f"Attempting recovery with likely URL: {likely_url}")
        
        # Check if URL is accessible
        try:
            response = requests.head(likely_url, timeout=5)
            if response.status_code == 200:
                logger.info("✅ URL is accessible!")
                update_manually(airtable_job_id, segment_id, likely_url)
            else:
                logger.error(f"URL not accessible: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to check URL: {e}")
    
    logger.info("\n" + "="*60)
    logger.info("Recovery process completed")

if __name__ == "__main__":
    main()