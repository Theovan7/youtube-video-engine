#!/usr/bin/env python3
"""
Test script to verify the corrected GoAPI payload structure actually works.
This script makes a real API call to GoAPI with the corrected payload structure.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_corrected_goapi_payload():
    """Test the corrected payload structure with a real GoAPI request."""
    
    print("🎬 TESTING CORRECTED GOAPI PAYLOAD WITH REAL REQUEST")
    print("=" * 60)
    
    # Get API credentials
    api_key = os.getenv('GOAPI_API_KEY')
    base_url = os.getenv('GOAPI_BASE_URL', 'https://api.goapi.ai')
    
    if not api_key:
        print("❌ ERROR: GOAPI_API_KEY not found in environment variables")
        print("   Please ensure your .env file contains GOAPI_API_KEY=your_key_here")
        return False
    
    print(f"🔧 Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '[REDACTED]'}")
    print()
    
    # Test image URL (using a publicly accessible test image)
    test_image_url = "https://via.placeholder.com/1024x1024/FF5733/FFFFFF?text=TEST+IMAGE"
    
    print(f"📸 Test Image URL: {test_image_url}")
    print()
    
    # Build the CORRECTED payload structure
    corrected_payload = {
        "model": "kling",
        "task_type": "video_generation",
        "input": {  # ✅ KEY FIX: 'input' wrapper
            "prompt": "animate the video with gentle movement",
            "cfg_scale": 0.5,
            "duration": 5,  # Short duration for testing
            "aspect_ratio": "1:1",  # Square for testing
            "version": "1.6",  # ✅ FIXED: Inside 'input'
            "mode": "std",     # ✅ FIXED: Inside 'input'
            "image_url": test_image_url,
            "effect": "expansion",  # ✅ FIXED: Inside 'input'
            "camera_control": {
                "type": "simple",
                "config": {  # ✅ KEY FIX: 'config' wrapper for camera params
                    "horizontal": 0,
                    "vertical": 1,  # Gentle vertical movement
                    "pan": 0,
                    "tilt": 0,
                    "roll": 0,
                    "zoom": 0
                }
            }
        },
        "config": {  # ✅ KEY FIX: 'config' section
            "service_mode": "public"
            # Note: No webhook for this test
        }
    }
    
    print("📦 CORRECTED PAYLOAD STRUCTURE:")
    print("=" * 40)
    print(json.dumps(corrected_payload, indent=2))
    print()
    
    # Set up request headers
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'YouTube-Video-Engine-PayloadTest/1.0'
    }
    
    # Make the request
    url = f"{base_url}/api/v1/task"
    
    print("🚀 MAKING REQUEST TO GOAPI:")
    print("=" * 30)
    print(f"   URL: {url}")
    print(f"   Method: POST")
    print(f"   Headers: {list(headers.keys())}")
    print()
    
    try:
        print("📡 Sending request...")
        response = requests.post(
            url,
            json=corrected_payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📥 Response received!")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print()
        
        # Parse response
        try:
            response_data = response.json()
            print("📄 Response Body (JSON):")
            print(json.dumps(response_data, indent=2))
        except json.JSONDecodeError:
            print("📄 Response Body (Text):")
            print(response.text[:1000])
            if len(response.text) > 1000:
                print(f"... (truncated, full length: {len(response.text)} chars)")
        
        print()
        
        # Analyze results
        print("🔍 RESULT ANALYSIS:")
        print("=" * 20)
        
        if response.status_code == 200:
            print("✅ SUCCESS! Request accepted by GoAPI")
            try:
                result = response.json()
                if 'id' in result or 'task_id' in result:
                    task_id = result.get('id') or result.get('task_id')
                    print(f"✅ Task Created: {task_id}")
                    print("✅ The corrected payload structure is working!")
                    return True
                else:
                    print("⚠️  Request accepted but no task ID returned")
                    print("   Response structure may be different than expected")
                    return True
            except:
                print("✅ Request accepted (200 status) - payload structure is correct!")
                return True
                
        elif response.status_code == 400:
            print("❌ BAD REQUEST (400) - Payload validation failed")
            print("   This suggests the payload structure may still have issues")
            print("   OR there may be other validation problems (API key, image URL, etc.)")
            return False
            
        elif response.status_code == 401:
            print("❌ UNAUTHORIZED (401) - API key authentication failed")
            print("   Check your GOAPI_API_KEY in the .env file")
            return False
            
        elif response.status_code == 403:
            print("❌ FORBIDDEN (403) - Access denied")
            print("   Your API key may not have video generation permissions")
            return False
            
        elif response.status_code == 429:
            print("⚠️  RATE LIMITED (429) - Too many requests")
            print("   Wait a moment and try again")
            return False
            
        elif 500 <= response.status_code < 600:
            print(f"❌ SERVER ERROR ({response.status_code}) - GoAPI internal error")
            print("   The payload structure is likely correct, but GoAPI is having issues")
            return False
            
        else:
            print(f"⚠️  UNEXPECTED STATUS ({response.status_code})")
            print("   Review the response for more information")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ REQUEST TIMEOUT")
        print("   The request took too long to complete")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR")
        print("   Could not connect to GoAPI")
        print("   Check your internet connection and the base URL")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 GOAPI CORRECTED PAYLOAD STRUCTURE TEST")
    print("=" * 50)
    print()
    
    success = test_corrected_goapi_payload()
    
    print()
    print("🏁 TEST SUMMARY:")
    print("=" * 15)
    
    if success:
        print("✅ PAYLOAD STRUCTURE FIX: SUCCESSFUL")
        print("✅ GoAPI accepted the corrected payload structure")
        print("✅ Video generation should now work properly")
        print()
        print("🎬 NEXT STEPS:")
        print("   1. The corrected payload structure is confirmed working")
        print("   2. Deploy the updated goapi_service.py to production")
        print("   3. Test end-to-end video generation workflow")
        
    else:
        print("❌ PAYLOAD STRUCTURE TEST: FAILED")
        print("❌ There may still be issues with the payload structure")
        print("   OR other configuration problems (API key, permissions, etc.)")
        print()
        print("🔧 TROUBLESHOOTING:")
        print("   1. Verify GOAPI_API_KEY is correct in .env file")
        print("   2. Check API key permissions for video generation")
        print("   3. Review GoAPI documentation for any recent changes")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
