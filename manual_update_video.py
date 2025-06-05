#!/usr/bin/env python3
"""
Manual update script to add the generated video to Airtable segment.
This is needed because webhooks to localhost don't work from external services.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.airtable_service import AirtableService

def update_segment_with_video():
    """Update the segment with the generated video URL."""
    
    # Video details from the GoAPI response
    segment_id = "recxGRBRi1Qe9sLDn"
    video_url = "https://storage.theapi.app/videos/280466557533844.mp4"
    job_id = "recS3bE7bF2xZHW6D"
    
    # Initialize Airtable service
    airtable = AirtableService()
    
    try:
        # Update segment with video URL (without changing status)
        print(f"Updating segment {segment_id} with video URL...")
        airtable.update_segment(segment_id, {
            'Video': [{'url': video_url}]
        })
        print("✅ Segment updated successfully with video!")
        
        # Try to complete the job record
        try:
            print(f"Completing job {job_id}...")
            airtable.complete_job(job_id, {'video_url': video_url})
            print("✅ Job completed successfully!")
        except Exception as e:
            print(f"⚠️  Could not update job (might not exist or have different schema): {e}")
        
        # Fetch and display the updated segment
        segment = airtable.get_segment(segment_id)
        print(f"\n📹 Updated Segment Details:")
        print(f"   ID: {segment['id']}")
        print(f"   Text: {segment['fields'].get('SRT Text', 'N/A')[:50]}...")
        print(f"   Video URLs: {len(segment['fields'].get('Video', []))} video(s)")
        if 'Video' in segment['fields'] and segment['fields']['Video']:
            print(f"   Latest Video: {segment['fields']['Video'][0]['url']}")
        
    except Exception as e:
        print(f"❌ Error updating segment: {e}")
        return False
    
    return True

if __name__ == "__main__":
    update_segment_with_video()
