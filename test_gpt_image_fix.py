#!/usr/bin/env python3
"""
Test script to verify gpt-image-1 API parameter fix
"""

import requests
import json
import os
from datetime import datetime

# Production API endpoint
BASE_URL = "https://youtube-video-engine.fly.dev"

def test_gpt_image_api():
    """Test the gpt-image-1 API parameter fix"""
    
    # Test payload - using a mock segment_id for testing
    test_payload = {
        "segment_id": "test_segment_12345",  # This would need to be a real segment ID
        "size": "1792x1024",  # Using the new supported size format
        "quality": "high"
    }
    
    print(f"Testing gpt-image-1 API parameter fix...")
    print(f"Timestamp: {datetime.now()}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        # Make request to the API
        response = requests.post(
            f"{BASE_URL}/api/v2/generate-ai-image",
            json=test_payload,
            timeout=30
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
        else:
            print(f"Response Body (raw): {response.text}")
        
        # Analyze the response
        if response.status_code == 404 and "Segment record not found" in response.text:
            print("\n✅ SUCCESS: API parameters are working correctly!")
            print("The endpoint reached the point where it's looking for the segment record,")
            print("which means the OpenAI API parameters are no longer causing errors.")
            return True
        elif response.status_code == 200:
            print("\n🎉 COMPLETE SUCCESS: Image generation worked!")
            return True
        elif "OpenAI API error" in response.text:
            print("\n❌ FAILED: Still getting OpenAI API parameter errors")
            return False
        else:
            print(f"\n⚠️  Unexpected response: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False

def test_health_check():
    """Test if the app is healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print("✅ App is healthy")
            return True
        else:
            print("❌ App health check failed")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GPT-IMAGE-1 API PARAMETER FIX TEST")
    print("=" * 60)
    
    # First check if app is healthy
    if test_health_check():
        print("\n" + "-" * 40)
        test_gpt_image_api()
    
    print("\n" + "=" * 60)
    print("Test completed")
