#!/usr/bin/env python3
"""
Test script to debug NCA Toolkit payload structure issues.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_nca_payload():
    """Test NCA Toolkit API to understand exact payload requirements."""
    
    print("🔧 TESTING NCA TOOLKIT PAYLOAD STRUCTURE")
    print("=" * 50)
    
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
    
    # Test different payload structures to find the correct one
    test_payloads = [
        {
            "name": "Current Structure (from code)",
            "payload": {
                'inputs': [video_url, audio_url],  # Direct URL strings
                'filename': 'test_output.mp4',
                'outputs': [{
                    'video_codec': 'libx264',
                    'audio_codec': 'aac',
                    'video_preset': 'medium',
                    'video_crf': 23
                }]
            }
        },
        {
            "name": "Alternative Structure 1 - Simple outputs",
            "payload": {
                'inputs': [video_url, audio_url],
                'filename': 'test_output.mp4',
                'outputs': ['mp4']  # Simple format array
            }
        },
        {
            "name": "Alternative Structure 2 - Single output object",
            "payload": {
                'inputs': [video_url, audio_url],
                'filename': 'test_output.mp4',
                'output': {
                    'format': 'mp4',
                    'video_codec': 'libx264',
                    'audio_codec': 'aac'
                }
            }
        },
        {
            "name": "Alternative Structure 3 - No codec details",
            "payload": {
                'inputs': [video_url, audio_url],
                'filename': 'test_output.mp4',
                'outputs': [{}]  # Empty output config
            }
        }
    ]
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    url = f"{base_url}/v1/ffmpeg/compose"
    
    for i, test in enumerate(test_payloads, 1):
        print(f"🧪 TEST {i}: {test['name']}")
        print("-" * 30)
        print("Payload:")
        print(json.dumps(test['payload'], indent=2))
        print()
        
        try:
            response = requests.post(
                url,
                json=test['payload'],
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
                print(f"✅ SUCCESS with {test['name']}")
                return True
            elif response.status_code == 400:
                print(f"❌ BAD REQUEST - Payload validation failed")
            else:
                print(f"⚠️  Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("=" * 50)
        print()
    
    return False

if __name__ == '__main__':
    success = test_nca_payload()
    sys.exit(0 if success else 1)
