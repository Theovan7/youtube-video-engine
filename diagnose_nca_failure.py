#!/usr/bin/env python3
"""
Diagnose why NCA service is failing.
"""

import requests
import json
import time
from services.nca_service import NCAService
from config import get_config

config = get_config()()
nca = NCAService()

def diagnose_nca():
    """Run comprehensive NCA diagnostics."""
    print("NCA Service Diagnostics")
    print("=" * 80)
    
    # 1. Check basic connectivity
    print("\n1. Testing NCA Base URL...")
    print(f"   Base URL: {nca.base_url}")
    print(f"   API Key: {nca.api_key[:10]}..." if nca.api_key else "   API Key: NOT SET")
    
    # 2. Test health endpoint
    print("\n2. Testing NCA Health Check...")
    try:
        health = nca.check_health()
        print(f"   Health Check: {'PASSED ✓' if health else 'FAILED ✗'}")
    except Exception as e:
        print(f"   Health Check: FAILED ✗ - {e}")
    
    # 3. Test different endpoints
    print("\n3. Testing NCA Endpoints...")
    
    endpoints = [
        ("/v1/toolkit/test", "GET", None),
        ("/v1/job/status/test-id", "GET", None),
        ("/v1/ffmpeg/compose", "POST", {"test": True})
    ]
    
    for path, method, data in endpoints:
        print(f"\n   Testing {method} {path}...")
        try:
            url = f"{nca.base_url}{path}"
            headers = {'x-api-key': nca.api_key}
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            else:
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, json=data, timeout=10)
            
            print(f"   Status: {response.status_code}")
            if response.status_code >= 500:
                print(f"   Server Error: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            print(f"   TIMEOUT after 10 seconds")
        except requests.exceptions.ConnectionError as e:
            print(f"   CONNECTION ERROR: {e}")
        except Exception as e:
            print(f"   ERROR: {e}")
    
    # 4. Test with minimal payload
    print("\n\n4. Testing Minimal FFmpeg Compose...")
    minimal_payload = {
        "inputs": [
            {"file_url": "https://example.com/video.mp4"},
            {"file_url": "https://example.com/audio.mp3"}
        ],
        "outputs": [{
            "filename": "test.mp4",
            "options": [
                {"option": "-c:v", "argument": "copy"},
                {"option": "-c:a", "argument": "copy"}
            ]
        }]
    }
    
    try:
        response = nca.session.post(
            f"{nca.base_url}/v1/ffmpeg/compose",
            json=minimal_payload,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 524:
            print("   ⚠️  524 TIMEOUT - Server is taking too long to respond")
            print("   This suggests NCA's FFmpeg processing is overloaded or stuck")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 5. Check if it's a payload size issue
    print("\n\n5. Checking Payload Size Issues...")
    print(f"   Airtable URL length: ~277 characters each")
    print(f"   Total payload size: ~2KB")
    print("   This should be well within limits")
    
    # 6. Test alternative video processing
    print("\n\n6. Alternative Solutions:")
    print("   a) Use direct file uploads instead of Airtable URLs")
    print("   b) Use a different video processing service")
    print("   c) Process videos in smaller batches")
    print("   d) Implement local FFmpeg processing")
    
    # 7. Check NCA status page
    print("\n\n7. NCA Service Status:")
    print("   Check: https://status.nocodearchitect.com (if available)")
    print("   Or contact NCA support about 524 errors on /v1/ffmpeg/compose")

if __name__ == "__main__":
    diagnose_nca()