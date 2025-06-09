#!/usr/bin/env python3
"""Test NCA with minimal payload."""

import requests
import json
import time

# Test with the simplest possible payload
def test_minimal_payload():
    """Test with minimal FFmpeg compose payload."""
    print("Testing NCA FFmpeg Compose with Minimal Payload")
    print("=" * 80)
    
    url = "https://no-code-architect-app-gpxhq.ondigitalocean.app/v1/ffmpeg/compose"
    headers = {
        "x-api-key": "K2_JVFN!csh&i1248",
        "Content-Type": "application/json"
    }
    
    # Start with the absolute minimum payload
    payloads = [
        {
            "name": "Test 1: Empty payload",
            "data": {}
        },
        {
            "name": "Test 2: Just inputs",
            "data": {
                "inputs": [
                    {"file_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"}
                ]
            }
        },
        {
            "name": "Test 3: Input + Output (no options)",
            "data": {
                "inputs": [
                    {"file_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"}
                ],
                "outputs": [
                    {
                        "filename": "test_output.mp4"
                    }
                ]
            }
        },
        {
            "name": "Test 4: Input + Output with basic options",
            "data": {
                "inputs": [
                    {"file_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"}
                ],
                "outputs": [
                    {
                        "filename": "test_output.mp4",
                        "options": [
                            {"option": "-c", "argument": "copy"}
                        ]
                    }
                ]
            }
        },
        {
            "name": "Test 5: With webhook URL",
            "data": {
                "inputs": [
                    {"file_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"}
                ],
                "outputs": [
                    {
                        "filename": "test_output.mp4",
                        "options": [
                            {"option": "-c", "argument": "copy"}
                        ]
                    }
                ],
                "webhook_url": "https://webhook.site/test"
            }
        }
    ]
    
    for test in payloads:
        print(f"\n{test['name']}:")
        print(f"Payload: {json.dumps(test['data'], indent=2)}")
        
        start_time = time.time()
        try:
            response = requests.post(url, json=test['data'], headers=headers, timeout=30)
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed:.2f}s")
            
            if response.status_code == 200 or response.status_code == 202:
                print(f"✓ Success: {response.text[:200]}")
            else:
                print(f"✗ Error: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            print(f"✗ Timeout after {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Exception after {elapsed:.2f}s: {e}")
        
        time.sleep(2)  # Small delay between tests

if __name__ == "__main__":
    test_minimal_payload()