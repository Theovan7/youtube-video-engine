#!/usr/bin/env python3
"""
Simple test to trigger video generation and monitor webhook handling.
"""

import requests
import time

def test_webhook_fix():
    """Test the improved webhook handler."""
    
    # Test segment ID (same one we manually fixed)
    segment_id = "recdRdKs6y9dyf609"
    
    # Production API endpoint
    api_url = "https://youtube-video-engine.fly.dev/api/v2/generate-video"
    
    print(f"🧪 Testing webhook fix with segment: {segment_id}")
    print(f"   API URL: {api_url}")
    
    # Make the API request
    try:
        payload = {"segment_id": segment_id}
        
        print(f"\n📡 Sending request...")
        response = requests.post(api_url, json=payload, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Video generation request successful!")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   External Task ID: {result.get('external_task_id')}")
            print(f"   Message: {result.get('message')}")
            
            print(f"\n📊 Monitor webhook processing:")
            print(f"   1. Check logs: fly logs -a youtube-video-engine")
            print(f"   2. Look for enhanced GoAPI webhook debugging output")
            print(f"   3. Verify Airtable record gets updated automatically")
            
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error making request: {e}")
        return False

if __name__ == "__main__":
    test_webhook_fix()
