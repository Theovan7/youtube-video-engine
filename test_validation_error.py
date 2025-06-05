#!/usr/bin/env python3
"""Test script to reproduce the validation error from Airtable script."""

import requests
import json

def test_validation_error():
    """Test the exact API call that's failing from Airtable."""
    
    # This is the exact payload being sent from Airtable
    payload = {
        "record_id": "recxGRBRi1Qe9sLDn"
    }
    
    # API endpoint from Airtable script
    api_url = "https://youtube-video-engine.fly.dev/api/v2/generate-video"
    
    print("🧪 Testing validation error...")
    print(f"📡 URL: {api_url}")
    print(f"📄 Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            api_url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")
        print()
        
        try:
            response_data = response.json()
            print(f"📋 Response Data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📋 Response Text: {response.text}")
            
        # Analyze the error
        if response.status_code == 400:
            print("\n🔍 ANALYSIS:")
            print("✅ Confirmed: This is a validation error (400 status)")
            if 'error' in response_data:
                print(f"❌ Error Message: {response_data['error']}")
                if 'details' in response_data:
                    print(f"📄 Error Details: {response_data['details']}")
                    
    except Exception as e:
        print(f"❌ Network error: {e}")

if __name__ == "__main__":
    test_validation_error()
