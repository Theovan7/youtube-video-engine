#!/usr/bin/env python3
"""
Simple test for script processing endpoint
"""

import requests
import json

BASE_URL = "https://youtube-video-engine.fly.dev"

# Test script processing
test_data = {
    "video_name": "Simple Test Video",
    "script_text": "This is a test script. It will be split into segments automatically.",
    "music_prompt": "calm background music"
}

print("Testing script processing endpoint...")
print(f"POST {BASE_URL}/api/v1/process-script")
print(f"Data: {json.dumps(test_data, indent=2)}")

response = requests.post(
    f"{BASE_URL}/api/v1/process-script",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    print("\nSuccess! Video and segments created:")
    print(f"Video ID: {result.get('video_id')}")
    print(f"Segments: {len(result.get('segments', []))}")
