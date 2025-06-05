#!/usr/bin/env python3
"""Manual test script for the generate AI image endpoint.

Usage:
    python test_generate_ai_image_manual.py [segment_id]
    
Example:
    python test_generate_ai_image_manual.py rec123ABC
"""

import sys
import json
import requests
from datetime import datetime


def test_generate_ai_image(segment_id, base_url='http://localhost:5000'):
    """Test the generate AI image endpoint."""
    
    endpoint = f"{base_url}/api/v2/generate-ai-image"
    
    # Test different parameter combinations
    test_cases = [
        {
            'name': 'Default parameters',
            'payload': {
                'segment_id': segment_id
            }
        },
        {
            'name': 'Square image with medium quality',
            'payload': {
                'segment_id': segment_id,
                'size': '1024x1024',
                'quality': 'medium'
            }
        },
        {
            'name': 'Landscape image with high quality',
            'payload': {
                'segment_id': segment_id,
                'size': '1536x1024',
                'quality': 'high'
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print(f"Payload: {json.dumps(test['payload'], indent=2)}")
        print(f"{'='*60}")
        
        try:
            # Make the request
            response = requests.post(
                endpoint,
                json=test['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=300  # 5 minutes timeout to match increased API timeout (was 180)
            )
            
            # Print response
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("Success! Response:")
                print(json.dumps(data, indent=2))
                
                if 'image_url' in data:
                    print(f"\nGenerated image URL: {data['image_url']}")
            else:
                print("Error Response:")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    print(response.text)
            
        except requests.exceptions.Timeout:
            print("ERROR: Request timed out after 3 minutes")
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to server. Is the app running?")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
        
        print("\nPress Enter to continue to next test...")
        input()


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_generate_ai_image_manual.py [segment_id]")
        print("\nExample: python test_generate_ai_image_manual.py recXYZ123")
        print("\nNote: Make sure:")
        print("1. The app is running (python app.py)")
        print("2. OPENAI_API_KEY is set in .env file")
        print("3. The segment exists in Airtable with an 'AI Image Prompt' field")
        sys.exit(1)
    
    segment_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:5000'
    
    print(f"Testing generate AI image endpoint")
    print(f"Segment ID: {segment_id}")
    print(f"Base URL: {base_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    test_generate_ai_image(segment_id, base_url)
    
    print("\n✅ All tests completed!")


if __name__ == '__main__':
    main()
