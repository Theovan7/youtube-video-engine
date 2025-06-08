#!/usr/bin/env python3
"""
Check the status of record recphkqVVvJEwM19c
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

def check_segment_and_jobs(segment_id):
    """Check segment and all related jobs."""
    base_id = os.getenv('AIRTABLE_BASE_ID')
    headers = get_airtable_headers()
    
    # Get segment details
    logger.info(f"Checking segment: {segment_id}")
    url = f"https://api.airtable.com/v0/{base_id}/Segments/{segment_id}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            segment = response.json()
            fields = segment.get('fields', {})
            
            logger.info("\nSegment Details:")
            logger.info(f"  Status: {fields.get('Status', 'Unknown')}")
            logger.info(f"  Has Video: {'Yes' if fields.get('Video') else 'No'}")
            logger.info(f"  Has Voiceover: {'Yes' if fields.get('Voiceover') else 'No'}")
            logger.info(f"  Has Combined: {'Yes' if fields.get('Combined') else 'No'}")
            logger.info(f"  Created: {segment.get('createdTime', 'Unknown')}")
            
            # Check video URL if exists
            if fields.get('Video'):
                video_url = fields['Video'][0]['url']
                logger.info(f"\n  Video URL: {video_url}")
                
                # Try to access the video
                try:
                    head_response = requests.head(video_url, timeout=5)
                    if head_response.status_code == 200:
                        logger.info("  ✅ Video URL is accessible")
                    else:
                        logger.error(f"  ❌ Video URL returned status: {head_response.status_code}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to access video URL: {e}")
            
            # Check voiceover URL if exists
            if fields.get('Voiceover'):
                voiceover_url = fields['Voiceover'][0]['url']
                logger.info(f"\n  Voiceover URL: {voiceover_url}")
                
                # Try to access the voiceover
                try:
                    head_response = requests.head(voiceover_url, timeout=5)
                    if head_response.status_code == 200:
                        logger.info("  ✅ Voiceover URL is accessible")
                    else:
                        logger.error(f"  ❌ Voiceover URL returned status: {head_response.status_code}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to access voiceover URL: {e}")
                    
        else:
            logger.error(f"Failed to get segment: {response.status_code}")
            return
    except Exception as e:
        logger.error(f"Error checking segment: {e}")
        return
    
    # Check for related jobs
    logger.info("\n" + "="*60)
    logger.info("Checking for related jobs...")
    
    jobs_url = f"https://api.airtable.com/v0/{base_id}/Jobs"
    params = {
        'filterByFormula': f"OR({{Related Segment}} = '{segment_id}', SEARCH('{segment_id}', {{Request Payload}}))"
    }
    
    try:
        response = requests.get(jobs_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('records', [])
            
            logger.info(f"Found {len(jobs)} related jobs")
            
            for job in jobs:
                job_fields = job.get('fields', {})
                logger.info(f"\nJob ID: {job['id']}")
                logger.info(f"  Type: {job_fields.get('Type', 'Unknown')}")
                logger.info(f"  Status: {job_fields.get('Status', 'Unknown')}")
                logger.info(f"  External ID: {job_fields.get('External Job ID', 'None')}")
                logger.info(f"  Created: {job.get('createdTime', 'Unknown')}")
                
                if job_fields.get('Error Details'):
                    logger.error(f"  Error: {job_fields.get('Error Details')}")
                    
        else:
            logger.error(f"Failed to get jobs: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error checking jobs: {e}")

def main():
    segment_id = "recphkqVVvJEwM19c"
    
    logger.info("="*60)
    logger.info(f"CHECKING RECORD: {segment_id}")
    logger.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    check_segment_and_jobs(segment_id)

if __name__ == "__main__":
    main()