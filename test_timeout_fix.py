#!/usr/bin/env python3
"""Test script to verify the timeout fix for AI image generation.

This script tests the generate AI image endpoint with the increased timeout.
"""

import sys
import json
import requests
import time
from datetime import datetime


def test_timeout_fix(segment_id, base_url='http://localhost:5000'):
    """Test the generate AI image endpoint with timeout monitoring."""
    
    endpoint = f"{base_url}/api/v2/generate-ai-image"
    
    payload = {
        'segment_id': segment_id,
        'size': '1792x1008'  # Default YouTube size
    }
    
    print(f"{'='*60}")
    print(f"Testing AI Image Generation Timeout Fix")
    print(f"Segment ID: {segment_id}")
    print(f"Endpoint: {endpoint}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        print("🎨 Starting AI image generation request...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Monitor request time
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minutes client timeout (longer than server 240s)
        )
        
        end_time = time.time()
        request_duration = end_time - start_time
        
        print(f"\n⏱️  Request completed in {request_duration:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Response:")
            print(json.dumps(data, indent=2))
            
            if 'image_urls' in data:
                print(f"\n🖼️  Generated {data.get('image_count', 0)} images:")
                for i, url in enumerate(data['image_urls'], 1):
                    print(f"  {i}. {url}")
                    
            print(f"\n📊 Performance Metrics:")
            print(f"  - Request Duration: {request_duration:.2f}s")
            print(f"  - Model: {data.get('model', 'unknown')}")
            print(f"  - Output Format: {data.get('output_format', 'unknown')}")
            
        elif response.status_code == 500:
            print("❌ ERROR 500 - Server Error")
            try:
                error_data = response.json()
                print("Error Response:")
                print(json.dumps(error_data, indent=2))
                
                # Check if it's still a timeout error
                if 'timeout' in json.dumps(error_data).lower():
                    print("\n🔍 Analysis: Still getting timeout despite increased timeout")
                    print("   This suggests:")
                    print("   1. OpenAI API is taking longer than 240 seconds")
                    print("   2. Need to increase timeout further OR")
                    print("   3. Implement async processing")
                else:
                    print("\n🔍 Analysis: Different error - not timeout related")
                    
            except:
                print("Raw error response:")
                print(response.text)
                
        else:
            print(f"❌ HTTP Error {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
        
    except requests.exceptions.Timeout:
        end_time = time.time()
        request_duration = end_time - start_time
        print(f"❌ CLIENT TIMEOUT after {request_duration:.2f} seconds")
        print("   This means the client gave up waiting")
        print("   The server might still be processing the request")
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not connect to server")
        print("   Is the app running on the specified URL?")
        
    except Exception as e:
        end_time = time.time()
        request_duration = end_time - start_time
        print(f"❌ UNEXPECTED ERROR after {request_duration:.2f} seconds")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
    
    print(f"\n{'='*60}")
    print("Test completed!")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_timeout_fix.py [segment_id] [optional_base_url]")
        print("\nExample: python test_timeout_fix.py recxGRBRi1Qe9sLDn")
        print("         python test_timeout_fix.py recxGRBRi1Qe9sLDn http://localhost:5000")
        print("\nNote: Make sure:")
        print("1. The app is running (python app.py)")
        print("2. OPENAI_API_KEY is set in .env file")
        print("3. The segment exists in Airtable with an 'AI Image Prompt' field")
        sys.exit(1)
    
    segment_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:5000'
    
    test_timeout_fix(segment_id, base_url)


if __name__ == '__main__':
    main()
