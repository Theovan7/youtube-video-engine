#!/usr/bin/env python3
"""Manual test script for Generate Video endpoint."""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"  # Change to production URL when testing deployed version
# BASE_URL = "https://youtube-video-engine.fly.dev"

def test_generate_video():
    """Test the Generate Video endpoint."""
    print("🎬 Testing Generate Video Endpoint")
    print("=" * 50)
    
    # Test data - replace with actual segment ID from your Airtable
    test_payload = {
        "segment_id": "recXXXXXXXXXXXXXX",  # Replace with actual segment ID that has 'Upscale Image'
        "duration_override": 5,  # Optional: 5 or 10 seconds
        "aspect_ratio": "16:9",  # Optional: '1:1', '16:9', 'auto'
        "quality": "standard"  # Optional: 'standard', 'high'
    }
    
    print(f"🔧 Request URL: {BASE_URL}/api/v2/generate-video")
    print(f"📝 Request Payload:")
    print(json.dumps(test_payload, indent=2))
    print()
    
    try:
        # Make the request
        print("📤 Sending request...")
        response = requests.post(
            f"{BASE_URL}/api/v2/generate-video",
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📈 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 202:
            # Success - processing started
            result = response.json()
            print("✅ SUCCESS: Video generation started!")
            print("📋 Response Data:")
            print(json.dumps(result, indent=2))
            
            # Extract job ID for status checking
            job_id = result.get('job_id')
            if job_id:
                print(f"\n🔍 You can check job status with:")
                print(f"GET {BASE_URL}/api/v1/jobs/{job_id}")
                
                # Optionally check status
                print("\n⏳ Checking initial job status...")
                status_response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print("📊 Job Status:")
                    print(json.dumps(status_data, indent=2))
                
        elif response.status_code == 400:
            # Validation error
            error_data = response.json()
            print("❌ VALIDATION ERROR:")
            print(json.dumps(error_data, indent=2))
            
        elif response.status_code == 404:
            # Segment not found
            error_data = response.json()
            print("❌ SEGMENT NOT FOUND:")
            print(json.dumps(error_data, indent=2))
            print("\nℹ️  Make sure the segment_id exists and has an 'Upscale Image' field")
            
        elif response.status_code == 500:
            # Server error
            error_data = response.json()
            print("❌ SERVER ERROR:")
            print(json.dumps(error_data, indent=2))
            
        else:
            # Other error
            print(f"❌ UNEXPECTED RESPONSE: {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Make sure the server is running")
        print(f"   Tried to connect to: {BASE_URL}")
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT ERROR: Request took too long")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def test_endpoint_schema():
    """Test the endpoint with invalid data to check schema validation."""
    print("\n🧪 Testing Schema Validation")
    print("=" * 50)
    
    # Test cases for validation
    test_cases = [
        {
            "name": "Missing segment_id",
            "payload": {"duration_override": 5}
        },
        {
            "name": "Invalid duration_override",
            "payload": {"segment_id": "recXXXXXXXXXXXXXX", "duration_override": 15}
        },
        {
            "name": "Invalid aspect_ratio",
            "payload": {"segment_id": "recXXXXXXXXXXXXXX", "aspect_ratio": "4:3"}
        },
        {
            "name": "Invalid quality",
            "payload": {"segment_id": "recXXXXXXXXXXXXXX", "quality": "ultra"}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/v2/generate-video",
                json=test_case['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 400:
                print("✅ Validation working correctly")
                error_data = response.json()
                print(f"   Error: {error_data.get('error')}")
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print(f"🚀 Generate Video Endpoint Test")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test the main functionality
    test_generate_video()
    
    # Test schema validation
    test_endpoint_schema()
    
    print(f"\n✨ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📝 Instructions for real testing:")
    print("1. Replace 'recXXXXXXXXXXXXXX' with actual segment ID from Airtable")
    print("2. Make sure the segment has an 'Upscale Image' field with an image")
    print("3. Check that GoAPI credentials are configured")
    print("4. Monitor the webhook for completion status")
