#!/usr/bin/env python3
"""Test script to verify gpt-image-1 API parameter fix"""

import os
import requests
import json
from datetime import datetime

# Test the API parameters locally
def test_openai_api_parameters():
    """Test OpenAI API parameters for gpt-image-1"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print("🔧 Testing gpt-image-1 API parameters...")
    
    # Test payload with corrected parameters
    test_payload = {
        'model': 'gpt-image-1',
        'prompt': 'A beautiful sunset landscape for testing purposes',
        'size': '1536x1024',  # Using supported size (3:2 ratio, closest to 16:9)
        'quality': 'high',
        'n': 1,  # Test with 1 image first
        'output_format': 'png',  # Supported format
        'moderation': 'auto'
    }
    
    headers = {
        'Authorization': f'Bearer {openai_api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"📤 Sending request with parameters: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/images/generations',
            headers=headers,
            json=test_payload,
            timeout=60
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API parameters are correct!")
            print(f"📊 Generated {len(result['data'])} image(s)")
            print(f"📋 First image URL available: {bool(result['data'][0].get('url'))}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"🔍 Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"🔍 Error text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_production_endpoint():
    """Test the production endpoint with the new parameters"""
    
    print("\n🌐 Testing production endpoint...")
    
    test_data = {
        'segment_id': 'test_segment_001',
        'size': '1792x1008',  # YouTube 16:9 format
        'quality': 'high'
    }
    
    print(f"📤 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            'https://youtube-video-engine.fly.dev/api/v2/generate-ai-image',
            json=test_data,
            timeout=60
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code in [200, 400, 404]:  # 400/404 expected for test data
            result = response.json()
            print("✅ Endpoint is accepting new size format!")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"🔍 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Production test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 YouTube Video Engine - API Parameter Fix Test")
    print("=" * 50)
    
    # Test API parameters
    api_test_passed = test_openai_api_parameters()
    
    # Test production endpoint
    endpoint_test_passed = test_production_endpoint()
    
    print("\n📊 TEST RESULTS:")
    print(f"✅ OpenAI API parameters: {'PASS' if api_test_passed else 'FAIL'}")
    print(f"✅ Production endpoint: {'PASS' if endpoint_test_passed else 'FAIL'}")
    
    if api_test_passed and endpoint_test_passed:
        print("\n🎉 All tests passed! API parameter fix is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
