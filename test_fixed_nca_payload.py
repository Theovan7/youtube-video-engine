#!/usr/bin/env python3
"""
Test the fixed NCA Toolkit payload structure.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_fixed_nca_payload():
    """Test the fixed NCA payload structure."""
    
    print("🔧 TESTING FIXED NCA TOOLKIT PAYLOAD STRUCTURE")
    print("=" * 55)
    
    # Get API credentials
    api_key = os.getenv('NCA_API_KEY')
    base_url = os.getenv('NCA_BASE_URL', 'https://no-code-architect-app-gpxhq.ondigitalocean.app')
    
    if not api_key:
        print("❌ ERROR: NCA_API_KEY not found in environment variables")
        return False
    
    print(f"🔧 Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '[REDACTED]'}")
    print()
    
    # Test URLs (using placeholder URLs for structure testing)
    video_url = "https://example.com/test_video.mp4"
    audio_url = "https://example.com/test_audio.mp3"
    
    # FIXED payload structure based on NCA documentation
    fixed_payload = {
        'inputs': [
            {'file_url': video_url},  # Video input as object with file_url
            {'file_url': audio_url}   # Audio input as object with file_url
        ],
        'outputs': [{
            'options': [  # Options must be in array format
                {'option': '-c:v', 'argument': 'libx264'},
                {'option': '-c:a', 'argument': 'aac'},
                {'option': '-preset', 'argument': 'medium'},
                {'option': '-crf', 'argument': 23}
            ]
        }],
        'global_options': [
            {'option': '-y'}  # Overwrite output files without asking
        ],
        'webhook_url': 'https://example.com/webhook',
        'id': 'test-payload-structure'
    }
    
    print("📦 FIXED PAYLOAD STRUCTURE:")
    print("-" * 30)
    print(json.dumps(fixed_payload, indent=2))
    print()
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    url = f"{base_url}/v1/ffmpeg/compose"
    
    print("🚀 MAKING REQUEST TO NCA:")
    print("-" * 25)
    print(f"   URL: {url}")
    print(f"   Method: POST")
    print()
    
    try:
        response = requests.post(
            url,
            json=fixed_payload,
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print("Response:")
            print(json.dumps(response_data, indent=2))
        except:
            print("Response (text):")
            print(response.text[:500])
        
        print()
        
        if response.status_code == 200:
            print("✅ SUCCESS! Fixed payload structure accepted")
            return True
        elif response.status_code == 202:
            print("✅ SUCCESS! Request accepted for processing")
            return True
        elif response.status_code == 400:
            print("❌ BAD REQUEST - Still payload validation issues")
            return False
        else:
            print(f"⚠️  Status {response.status_code} - Check response for details")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    success = test_fixed_nca_payload()
    
    print()
    print("🏁 TEST SUMMARY:")
    print("=" * 15)
    
    if success:
        print("✅ NCA PAYLOAD STRUCTURE FIX: SUCCESSFUL")
        print("✅ The corrected payload structure is working")
        print("✅ Ready to deploy the fixed NCA service")
    else:
        print("❌ NCA PAYLOAD STRUCTURE FIX: STILL ISSUES")
        print("❌ May need further payload structure adjustments")
    
    sys.exit(0 if success else 1)
