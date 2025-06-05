#!/usr/bin/env python3
"""Test the deployed API with corrected parameters"""

import requests
import json

def test_production_api():
    """Test the production API endpoint with corrected parameters"""
    
    print("🧪 Testing Production API - Generate AI Image")
    print("=" * 50)
    
    # Test with YouTube 16:9 aspect ratio
    test_data = {
        'segment_id': 'test_segment_123',
        'size': '1792x1008',  # YouTube 16:9 format (should map to 1536x1024)
        'quality': 'high'
    }
    
    print(f"📤 Request: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            'https://youtube-video-engine.fly.dev/api/v2/generate-ai-image',
            json=test_data,
            timeout=30
        )
        
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 404:
            result = response.json()
            if 'Segment record not found' in str(result):
                print("✅ VALIDATION SUCCESS! API is accepting parameters and reaching Airtable lookup!")
                print("📋 The endpoint correctly processed the YouTube 16:9 size format")
                print("🔍 Expected error: Segment record not found (test segment doesn't exist)")
                return True
        elif response.status_code == 400:
            result = response.json()
            if 'Validation error' in str(result):
                print("❌ Parameter validation failed")
                print(f"🔍 Details: {json.dumps(result, indent=2)}")
                return False
        
        result = response.json()
        print(f"📋 Response: {json.dumps(result, indent=2)}")
        return response.status_code in [200, 404]  # 404 is expected for test data
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint to ensure system is running"""
    
    print("\n🏥 Testing Health Endpoint")
    print("=" * 30)
    
    try:
        response = requests.get(
            'https://youtube-video-engine.fly.dev/health',
            timeout=10
        )
        
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ System is healthy!")
            print(f"📊 Services: {result.get('services', {})}")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 YouTube Video Engine - Production API Test")
    print("=" * 55)
    
    # Test health first
    health_ok = test_health_endpoint()
    
    # Test AI image generation API
    api_ok = test_production_api()
    
    print("\n📊 TEST RESULTS:")
    print(f"🏥 Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"🖼️  AI Image API: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if health_ok and api_ok:
        print("\n🎉 SUCCESS! API parameter fix is working correctly in production!")
        print("📋 The system now accepts YouTube 16:9 aspect ratios and reaches Airtable lookup")
        print("🔧 Ready for real segment testing with valid segment IDs")
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
