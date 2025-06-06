#!/usr/bin/env python3
"""Test the process-script endpoint with a real Airtable video ID."""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get a real video ID from Airtable
airtable_api_key = os.getenv('AIRTABLE_API_KEY')
airtable_base_id = os.getenv('AIRTABLE_BASE_ID')

# First, let's create a test video record
headers = {
    'Authorization': f'Bearer {airtable_api_key}',
    'Content-Type': 'application/json'
}

# Create a test video
video_data = {
    "fields": {
        "Description": "OpenAI Test Video",
        "Video Script": "This is the first line of my test script.\nThis is the second line with some emotion!\nAnd here's the dramatic conclusion."
    }
}

print("Creating test video in Airtable...")
response = requests.post(
    f'https://api.airtable.com/v0/{airtable_base_id}/Videos',
    headers=headers,
    json=video_data
)

if response.status_code == 200:
    video_record = response.json()
    video_id = video_record['id']
    print(f"Created video with ID: {video_id}")
    
    # Now test the process-script endpoint
    print("\nTesting process-script endpoint...")
    test_data = {
        "record_id": video_id
    }
    
    response2 = requests.post(
        "https://youtube-video-engine.fly.dev/api/v2/process-script",
        json=test_data
    )
    
    print(f"Status Code: {response2.status_code}")
    print(f"Response: {json.dumps(response2.json(), indent=2)}")
    
    # Check if segments were created with markup
    if response2.status_code == 201:
        segments = response2.json().get('segments', [])
        if segments:
            print(f"\nCreated {len(segments)} segments")
            for i, segment in enumerate(segments[:3]):  # Show first 3 segments
                print(f"\nSegment {i+1}:")
                print(f"  Original: {segment.get('text', '')}")
                print(f"  Marked up: {segment.get('marked_text', segment.get('text', ''))}")
    
    # Clean up - delete the test video
    print(f"\nCleaning up - deleting test video {video_id}")
    requests.delete(
        f'https://api.airtable.com/v0/{airtable_base_id}/Videos/{video_id}',
        headers=headers
    )
else:
    print(f"Failed to create test video: {response.status_code}")
    print(response.text)