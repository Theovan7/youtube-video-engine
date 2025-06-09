#!/usr/bin/env python3
"""Test NCA with our files but simpler operation."""

import requests
import json
import time
from services.airtable_service import AirtableService

airtable = AirtableService()

def test_simple_combine():
    """Test with our actual files but simpler FFmpeg operation."""
    print("Testing NCA with Actual Files - Simple Combine")
    print("=" * 80)
    
    # Get a segment with files
    segments_table = airtable.segments_table
    segment = segments_table.get('reci0gT2LhNaIaFtp')
    
    video_url = segment['fields']['Video'][0]['url']
    voiceover_url = segment['fields']['Voiceover'][0]['url']
    
    print(f"\nVideo URL: {video_url[:100]}...")
    print(f"Voiceover URL: {voiceover_url[:100]}...")
    
    url = "https://no-code-architect-app-gpxhq.ondigitalocean.app/v1/ffmpeg/compose"
    headers = {
        "x-api-key": "K2_JVFN!csh&i1248",
        "Content-Type": "application/json"
    }
    
    # Test different approaches
    tests = [
        {
            "name": "Test 1: Simple copy without filters",
            "payload": {
                "inputs": [
                    {"file_url": video_url},
                    {"file_url": voiceover_url}
                ],
                "outputs": [{
                    "filename": "test_simple_copy.mp4",
                    "options": [
                        {"option": "-map", "argument": "0:v"},
                        {"option": "-map", "argument": "1:a"},
                        {"option": "-c", "argument": "copy"}
                    ]
                }],
                "webhook_url": "https://youtube-video-engine.fly.dev/webhook/nca/test",
                "id": "test_simple_copy"
            }
        },
        {
            "name": "Test 2: With shortest flag",
            "payload": {
                "inputs": [
                    {"file_url": video_url},
                    {"file_url": voiceover_url}
                ],
                "outputs": [{
                    "filename": "test_with_shortest.mp4",
                    "options": [
                        {"option": "-map", "argument": "0:v"},
                        {"option": "-map", "argument": "1:a"},
                        {"option": "-c:v", "argument": "copy"},
                        {"option": "-c:a", "argument": "copy"},
                        {"option": "-shortest"}
                    ]
                }],
                "webhook_url": "https://youtube-video-engine.fly.dev/webhook/nca/test",
                "id": "test_with_shortest"
            }
        },
        {
            "name": "Test 3: With simple filter",
            "payload": {
                "inputs": [
                    {"file_url": video_url},
                    {"file_url": voiceover_url}
                ],
                "filters": [
                    {"filter": "[0:v]copy[v]"}
                ],
                "outputs": [{
                    "filename": "test_simple_filter.mp4",
                    "options": [
                        {"option": "-map", "argument": "[v]"},
                        {"option": "-map", "argument": "1:a"},
                        {"option": "-c:v", "argument": "libx264"},
                        {"option": "-c:a", "argument": "copy"}
                    ]
                }],
                "webhook_url": "https://youtube-video-engine.fly.dev/webhook/nca/test",
                "id": "test_simple_filter"
            }
        }
    ]
    
    for test in tests:
        print(f"\n{test['name']}:")
        print(f"Payload size: {len(json.dumps(test['payload']))} bytes")
        
        start_time = time.time()
        try:
            response = requests.post(url, json=test['payload'], headers=headers, timeout=65)
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed:.2f}s")
            
            if response.status_code in [200, 202]:
                result = response.json()
                print(f"✓ Success - Job ID: {result.get('job_id')}")
                if response.status_code == 200:
                    print(f"Result: {json.dumps(result.get('response', {}), indent=2)[:200]}")
            else:
                print(f"✗ Error: {response.text[:500]}")
                
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            print(f"✗ Timeout after {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Exception after {elapsed:.2f}s: {e}")
        
        print("-" * 40)
        time.sleep(3)  # Delay between tests

if __name__ == "__main__":
    test_simple_combine()