#!/usr/bin/env python3
"""Test the process-script endpoint with markup generation."""

import requests
import json
import sys

# Test data
test_record_id = "recTest123"  # Replace with a real record ID if you have one
api_url = "https://youtube-video-engine.fly.dev/api/v2/process-script"

# Test payload
payload = {
    "record_id": test_record_id
}

print("Testing process-script endpoint with markup generation...")
print(f"URL: {api_url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("-" * 50)

try:
    response = requests.post(api_url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print("-" * 50)
    
    if response.status_code == 200 or response.status_code == 201:
        data = response.json()
        print("Success! Response:")
        print(json.dumps(data, indent=2))
        
        # Check if segments have markup
        if 'segments' in data and len(data['segments']) > 0:
            print("\nChecking first segment for markup...")
            first_segment = data['segments'][0]
            if 'text' in first_segment:
                print(f"Segment text: {first_segment['text']}")
                # Check for markup indicators
                if '<break' in first_segment['text'] or '...' in first_segment['text'] or any(c.isupper() for c in first_segment['text'] if c.isalpha()):
                    print("✓ Markup detected in segment!")
                else:
                    print("⚠ No obvious markup detected (may still be processed)")
    else:
        print("Error Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
except Exception as e:
    print(f"Error making request: {e}")
    sys.exit(1)