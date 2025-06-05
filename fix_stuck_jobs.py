#!/usr/bin/env python3
"""
Fix stuck NCA jobs that completed but webhook failed due to missing 'id' field.
This script will update the Airtable records based on successful NCA job outputs.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.airtable_service import AirtableService
from utils.logger import setup_logging

# Setup logging
logger = setup_logging()

def fix_concatenate_job():
    """Fix the stuck concatenate job rec7LlI0v8nSvMoeF"""
    airtable = AirtableService()
    
    job_id = "rec7LlI0v8nSvMoeF"
    video_id = "rectTH9JqTfgkvih4"
    output_url = "https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket/bb60e8fc-fdc1-42dd-a9d3-8170fa723a1d.mp4"
    
    try:
        # Update job to completed
        airtable.update_job(job_id, {
            'Status': 'completed',
            'Response Payload': f'{{"output_url": "{output_url}"}}',
            'Notes': 'Fixed manually - webhook failed due to missing id field'
        })
        logger.info(f"Updated job {job_id} to completed")
        
        # Update video with combined segments video
        airtable.update_video(video_id, {
            'Combined Segments Video': [{'url': output_url}]
        })
        logger.info(f"Updated video {video_id} with combined segments video")
        
        return True
    except Exception as e:
        logger.error(f"Failed to fix concatenate job: {e}")
        return False

def fix_add_music_job():
    """Fix the stuck add_music job rec0uIkbCTb3XLLtB"""
    airtable = AirtableService()
    
    job_id = "rec0uIkbCTb3XLLtB"
    video_id = "rectTH9JqTfgkvih4"
    output_url = "https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket/182f3d54-5757-450f-b6d7-b69c028f9be3_output_0.mp4"
    
    try:
        # Update job to completed
        airtable.update_job(job_id, {
            'Status': 'completed',
            'Response Payload': f'{{"output_url": "{output_url}"}}',
            'Notes': 'Fixed manually - webhook failed due to missing id field'
        })
        logger.info(f"Updated job {job_id} to completed")
        
        # Update video with final video + music
        airtable.update_video(video_id, {
            'Video + Music': [{'url': output_url}]
        })
        logger.info(f"Updated video {video_id} with video + music")
        
        return True
    except Exception as e:
        logger.error(f"Failed to fix add_music job: {e}")
        return False

def main():
    """Main function to fix stuck jobs"""
    logger.info("Starting to fix stuck jobs...")
    
    # Fix concatenate job
    if fix_concatenate_job():
        logger.info("✅ Successfully fixed concatenate job")
    else:
        logger.error("❌ Failed to fix concatenate job")
    
    # Fix add music job
    if fix_add_music_job():
        logger.info("✅ Successfully fixed add_music job")
    else:
        logger.error("❌ Failed to fix add_music job")
    
    logger.info("Done fixing stuck jobs")

if __name__ == "__main__":
    main()