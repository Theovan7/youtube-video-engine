#!/usr/bin/env python3
"""Test NCA without any filters."""

import requests
import json
from services.airtable_service import AirtableService

airtable = AirtableService()

def test_without_filter():
    """Test combining without any filter."""
    print("Testing NCA Combine WITHOUT Filters")
    print("=" * 80)
    
    # Get a segment
    segments_table = airtable.segments_table
    segment = segments_table.get('reci0gT2LhNaIaFtp')
    
    video_url = segment['fields']['Video'][0]['url']
    voiceover_url = segment['fields']['Voiceover'][0]['url']
    
    print(f"\nVideo URL: {video_url[:100]}...")
    print(f"Voiceover URL: {voiceover_url[:100]}...")
    
    url = "https://no-code-architect-app-gpxhq.ondigitalocean.app/v1/ffmpeg/compose"
    headers = {
        "x-api-key": "K2_JVFN!csh&i1248",
        "Content-Type": "application/json"
    }
    
    # Simple payload without filters
    payload = {
        "inputs": [
            {"file_url": video_url},
            {"file_url": voiceover_url}
        ],
        "outputs": [{
            "filename": "test_no_filter_combined.mp4",
            "options": [
                {"option": "-map", "argument": "0:v"},
                {"option": "-map", "argument": "1:a"},
                {"option": "-c:v", "argument": "copy"},
                {"option": "-c:a", "argument": "copy"},
                {"option": "-shortest"}
            ]
        }],
        "global_options": [
            {"option": "-y"}
        ],
        "webhook_url": "https://youtube-video-engine.fly.dev/webhook/nca/test",
        "id": "test_no_filter"
    }
    
    print("\nPayload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code in [200, 202]:
            result = response.json()
            print(f"✓ Success - Job ID: {result.get('job_id')}")
            print(f"Full response: {json.dumps(result, indent=2)}")
            return result.get('job_id')
        else:
            print(f"✗ Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    return None

if __name__ == "__main__":
    job_id = test_without_filter()
    
    if job_id:
        print(f"\n\nJob created successfully: {job_id}")
        print("Check webhook logs or use job status endpoint to monitor progress.")