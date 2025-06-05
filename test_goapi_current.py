#!/usr/bin/env python3
"""Test current GoAPI video generation endpoint to diagnose the error."""

import requests
import json
import os
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_goapi_video_generation():
    """Test GoAPI video generation with actual payload."""
    
    api_key = os.getenv('GOAPI_API_KEY')
    base_url = os.getenv('GOAPI_BASE_URL')
    
    print(f"🔧 Testing GoAPI Video Generation")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    print("=" * 80)
    
    # Test image URL from the failing segment
    test_image_url = "https://v5.airtableusercontent.com/v3/u/41/41/1748505600000/V8-5J9iorvnECRZqfLlSVw/0-HJEoTS0J06sXlyY-NsgliQyaYMyCgNVWoUXxm_xIic1YbBp_yhjZvDlmA9_nioaCP8K-hCkEW_502W8StPPArimVeAiQBEQQo_UaIxePV-79-mNS3dhr_vMzzxbAYnqhnmU8hWxjwxjdYXKb7N3I4WuNukJ3tO0NwN2D1FpdTVAQK4ze3KqM5LtxPapbTZEZIy4br3gb0yCuuSADnABGcIXqCv4cjmMhBZpWYTcgbl9RI9yQSO3-75uhOEfyks/Dp4rrzHZx3wF89He7W3JfG-1_Ukym1oMHgfnWY20Pcs"
    
    # Payload structure from troubleshooting notes
    payload = {
        'model': 'kling',
        'task_type': 'video_generation',
        'input': {
            'prompt': 'animate the video',
            'negative_prompt': '',
            'cfg_scale': 0.5,
            'duration': 5,
            'aspect_ratio': '16:9',
            'version': '1.6',
            'camera_control': {
                'type': 'simple',
                'config': {
                    'horizontal': 0,
                    'vertical': 2,
                    'pan': -10,
                    'tilt': 0,
                    'roll': 0,
                    'zoom': 0
                }
            },
            'mode': 'std',
            'image_url': test_image_url,
            'effect': 'expansion'
        },
        'config': {
            'service_mode': 'public'
        }
    }
    
    # Headers as per troubleshooting notes (X-API-Key, not Authorization)
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json',
        'User-Agent': 'YouTube-Video-Engine/1.0'
    }
    
    url = f"{base_url}/api/v1/task"
    
    print(f"🚀 Making request to: {url}")
    print(f"📋 Headers: {json.dumps({k: v[:20] + '...' if k == 'X-API-Key' else v for k, v in headers.items()}, indent=2)}")
    print(f"📦 Payload preview: {json.dumps({**payload, 'input': {**payload['input'], 'image_url': 'REDACTED'}}, indent=2)}")
    print("=" * 80)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body:")
        
        # Try to parse as JSON
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
            
            # Check for task_id or id in response
            if response_json.get('task_id') or response_json.get('id'):
                task_id = response_json.get('task_id') or response_json.get('id')
                print(f"\n✅ SUCCESS: Got task ID: {task_id}")
            else:
                print(f"\n❌ ERROR: No task_id or id in response")
                print(f"   Available keys: {list(response_json.keys())}")
                
        except json.JSONDecodeError:
            print(f"   Raw text: {response.text}")
            print(f"\n❌ ERROR: Response is not valid JSON")
            
    except requests.exceptions.RequestException as e:
        print(f"\n💥 Request failed: {e}")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    
    print("\n" + "=" * 80)
    print(f"📅 Test completed at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    test_goapi_video_generation()
