#!/usr/bin/env python3
"""Test with more dramatic script that should trigger markup."""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
airtable_api_key = os.getenv('AIRTABLE_API_KEY')
airtable_base_id = os.getenv('AIRTABLE_BASE_ID')

headers = {
    'Authorization': f'Bearer {airtable_api_key}',
    'Content-Type': 'application/json'
}

# Create a test video with dramatic script
video_data = {
    "fields": {
        "Description": "Dramatic Test Video for OpenAI Markup",
        "Video Script": """I can't believe what just happened...
NO! This is absolutely UNACCEPTABLE!
Wait, did you hear that? Something's coming...
She whispered softly: I'll never forget you
RUUUUUN! GET OUT OF THERE NOW!!!
The silence was deafening, then suddenly—
I... I don't know what to say anymore...
This is it. This is the moment everything changes."""
    }
}

print("Creating dramatic test video in Airtable...")
response = requests.post(
    f'https://api.airtable.com/v0/{airtable_base_id}/Videos',
    headers=headers,
    json=video_data
)

if response.status_code == 200:
    video_record = response.json()
    video_id = video_record['id']
    print(f"Created video with ID: {video_id}")
    
    # Process the script
    print("\nProcessing dramatic script...")
    test_data = {
        "record_id": video_id
    }
    
    response2 = requests.post(
        "https://youtube-video-engine.fly.dev/api/v2/process-script",
        json=test_data
    )
    
    print(f"Status Code: {response2.status_code}")
    
    if response2.status_code == 201:
        segments = response2.json().get('segments', [])
        print(f"\nCreated {len(segments)} segments")
        
        # Now fetch the segments directly from Airtable to see both fields
        print("\nFetching segment details from Airtable...")
        for segment in segments[:5]:  # Check first 5 segments
            seg_response = requests.get(
                f'https://api.airtable.com/v0/{airtable_base_id}/Segments/{segment["id"]}',
                headers=headers
            )
            
            if seg_response.status_code == 200:
                seg_data = seg_response.json()['fields']
                print(f"\nSegment {segment['order']}:")
                print(f"  Original: {seg_data.get('Original SRT Text', 'N/A')}")
                print(f"  Marked:   {seg_data.get('SRT Text', 'N/A')}")
                if seg_data.get('Original SRT Text') != seg_data.get('SRT Text'):
                    print("  ✅ Markup was applied!")
                else:
                    print("  ❌ No markup applied")
    else:
        print(f"Error: {response2.text}")
    
    # Clean up
    print(f"\nCleaning up - deleting test video {video_id}")
    requests.delete(
        f'https://api.airtable.com/v0/{airtable_base_id}/Videos/{video_id}',
        headers=headers
    )
else:
    print(f"Failed to create test video: {response.status_code}")
    print(response.text)