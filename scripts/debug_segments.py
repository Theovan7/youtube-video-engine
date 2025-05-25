#!/usr/bin/env python3
"""
Debug script to check segments creation and retrieval
"""

import requests
import json

BASE_URL = "https://youtube-video-engine.fly.dev"

# Use one of the video IDs from the recent tests
video_id = "recBFkFyGWaGnLm99"

print(f"Checking segments for video: {video_id}")

# Get video details
response = requests.get(f"{BASE_URL}/api/v1/videos/{video_id}")
print(f"\nVideo details status: {response.status_code}")
if response.status_code == 200:
    print(f"Video details: {json.dumps(response.json(), indent=2)}")

# Get segments
response = requests.get(f"{BASE_URL}/api/v1/videos/{video_id}/segments")
print(f"\nSegments status: {response.status_code}")
print(f"Segments response: {response.text}")
