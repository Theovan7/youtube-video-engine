#!/usr/bin/env python3
"""
Trigger combine operations for stuck segments.
"""

import requests
import json
from services.airtable_service import AirtableService

airtable = AirtableService()

# The stuck segment IDs
stuck_segments = [
    'recTuqCj6GN2ajsxp',
    'reci0gT2LhNaIaFtp',
    'recjDBBDr7h8KwnTU',
    'recmXnXCm5tFVAlFo',
    'recphkqVVvJEwM19c'
]

def trigger_combine_jobs():
    """Trigger combine operations for stuck segments."""
    print("Triggering combine operations for stuck segments...")
    print("=" * 80)
    
    api_url = "https://youtube-video-engine.fly.dev/api/v2/combine-segment-media"
    
    success_count = 0
    
    for segment_id in stuck_segments:
        print(f"\nProcessing segment: {segment_id}")
        
        try:
            # Call the combine API
            response = requests.post(
                api_url,
                json={"record_id": segment_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code in [200, 202]:
                result = response.json()
                print(f"  ✓ Success!")
                print(f"    Job ID: {result.get('job_id')}")
                print(f"    External ID: {result.get('external_job_id')}")
                print(f"    Status: {result.get('status')}")
                success_count += 1
            else:
                print(f"  ✗ Failed: {response.status_code}")
                print(f"    Response: {response.text}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n\nSummary: {success_count}/{len(stuck_segments)} segments processed successfully")
    
    if success_count > 0:
        print("\nThe combine jobs have been created. The polling system should pick them up within 2-5 minutes.")
        print("You can manually trigger a check with:")
        print("  curl -X POST https://youtube-video-engine.fly.dev/api/v2/check-stuck-jobs")

if __name__ == "__main__":
    trigger_combine_jobs()