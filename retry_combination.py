#!/usr/bin/env python3
"""
Retry the combination job for segment reci0gT2LhNaIaFtp
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

def retry_combination(segment_id):
    """Retry the combination by calling the API endpoint."""
    api_url = "https://youtube-video-engine.fly.dev/api/v2/combine-segment-media"
    
    payload = {
        "record_id": segment_id
    }
    
    logger.info(f"Retrying combination for segment: {segment_id}")
    logger.info(f"API URL: {api_url}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code in [200, 202]:
            data = response.json()
            logger.info("✅ Combination job created successfully!")
            logger.info(f"Job ID: {data.get('job_id')}")
            logger.info(f"Status: {data.get('status')}")
            return True
        else:
            logger.error(f"Failed to create combination job: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error calling API: {e}")
        return False

def check_segment_status(segment_id):
    """Check current segment status."""
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    url = f"https://api.airtable.com/v0/{base_id}/Segments/{segment_id}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            fields = data.get('fields', {})
            
            logger.info("\nSegment Status:")
            logger.info(f"  Status: {fields.get('Status')}")
            logger.info(f"  Has Video: {'Yes' if fields.get('Video') else 'No'}")
            logger.info(f"  Has Voiceover: {'Yes' if fields.get('Voiceover') else 'No'}")
            logger.info(f"  Has Combined: {'Yes' if fields.get('Combined') else 'No'}")
            
            return fields
    except Exception as e:
        logger.error(f"Failed to check segment: {e}")
    
    return None

def main():
    segment_id = "reci0gT2LhNaIaFtp"
    
    logger.info("="*60)
    logger.info("RETRYING COMBINATION JOB")
    logger.info("="*60)
    
    # Check current status
    logger.info("Checking current segment status...")
    segment_fields = check_segment_status(segment_id)
    
    if segment_fields:
        if segment_fields.get('Combined'):
            logger.info("✅ Segment already has combined video!")
            return
        
        if not segment_fields.get('Video') or not segment_fields.get('Voiceover'):
            logger.error("❌ Segment missing required files for combination")
            return
    
    # Retry combination
    logger.info("\nRetrying combination...")
    if retry_combination(segment_id):
        logger.info("\n✅ New combination job created successfully!")
        logger.info("Monitor the logs for webhook delivery")
    else:
        logger.error("\n❌ Failed to create new combination job")

if __name__ == "__main__":
    main()