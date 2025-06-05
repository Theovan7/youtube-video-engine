#!/usr/bin/env python3
"""
Check the status of a specific job in Airtable.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.airtable_service import AirtableService

def check_job_status(job_id):
    """Check the status of a specific job."""
    
    airtable = AirtableService()
    
    try:
        # Get the job record
        job = airtable.get_job(job_id)
        
        print(f"📋 Job Status for {job_id}:")
        print(f"   Status: {job['fields'].get('Status', 'N/A')}")
        print(f"   External Task ID: {job['fields'].get('External Task ID', 'N/A')}")
        print(f"   Created: {job['fields'].get('Created Time', 'N/A')}")
        print(f"   Updated: {job['fields'].get('Last Modified Time', 'N/A')}")
        
        # Check if there's a video URL
        video_url = job['fields'].get('Video URL')
        if video_url:
            print(f"   Video URL: {video_url}")
        else:
            print(f"   Video URL: Not generated yet")
        
        # Check error field
        error = job['fields'].get('Error')
        if error:
            print(f"   Error: {error}")
        
        # Get the associated segment
        segment_ids = job['fields'].get('Segment ID', [])
        if segment_ids:
            segment_id = segment_ids[0]
            segment = airtable.get_segment(segment_id)
            print(f"\n📝 Associated Segment {segment_id}:")
            print(f"   Text: {segment['fields'].get('SRT Text', 'N/A')[:100]}...")
            
            # Check if segment has video URL
            segment_video = segment['fields'].get('Video URL')
            if segment_video:
                print(f"   Segment Video URL: {segment_video}")
            else:
                print(f"   Segment Video URL: Not updated yet")
        
        return job
        
    except Exception as e:
        print(f"❌ Error checking job status: {e}")
        return None

if __name__ == "__main__":
    # Check the job we just created
    job_id = "recYughPfNurpuJek"
    check_job_status(job_id)
