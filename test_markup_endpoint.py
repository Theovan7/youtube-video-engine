#!/usr/bin/env python3
"""Test the markup generation endpoint."""

import requests
import json

# Test endpoint
url = "https://youtube-video-engine.fly.dev/api/v2/test-markup"

# Test data
test_data = {
    "text": "This is a test segment that needs markup.",
    "previous": "This was the previous segment.",
    "following": "This will be the next segment."
}

# Make request
print("Testing markup generation endpoint...")
response = requests.post(url, json=test_data)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Also test process-script to see if OpenAI is working
print("\n\nTesting process-script endpoint...")
test_script_data = {
    "video_id": "recTest123",  # This will fail but we want to see if OpenAI initializes
    "script": "This is line one.\nThis is line two.\nThis is line three."
}

response2 = requests.post("https://youtube-video-engine.fly.dev/api/v2/process-script", json=test_script_data)
print(f"Status Code: {response2.status_code}")
print(f"Response: {json.dumps(response2.json(), indent=2)}")