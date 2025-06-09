#!/usr/bin/env python3
"""Test NCA with different tpad filter configurations."""

import requests
import json
import time
from services.airtable_service import AirtableService

airtable = AirtableService()

def test_tpad_variations():
    """Test different tpad filter configurations."""
    print("Testing NCA tpad Filter Variations")
    print("=" * 80)
    
    # Get a segment with files
    segments_table = airtable.segments_table
    segment = segments_table.get('reci0gT2LhNaIaFtp')
    
    video_url = segment['fields']['Video'][0]['url']
    voiceover_url = segment['fields']['Voiceover'][0]['url']
    
    url = "https://no-code-architect-app-gpxhq.ondigitalocean.app/v1/ffmpeg/compose"
    headers = {
        "x-api-key": "K2_JVFN!csh&i1248",
        "Content-Type": "application/json"
    }
    
    # Test different tpad configurations
    tests = [
        {
            "name": "Test 1: tpad with smaller stop_duration",
            "filter": "[0:v]tpad=stop_mode=clone:stop_duration=30[v]"
        },
        {
            "name": "Test 2: tpad without stop_duration",
            "filter": "[0:v]tpad=stop_mode=clone[v]"
        },
        {
            "name": "Test 3: Using loop filter instead",
            "filter": "[0:v]loop=loop=-1:size=1:start=0[v]"
        },
        {
            "name": "Test 4: Using setpts to slow down",
            "filter": "[0:v]setpts=2*PTS[v]"
        },
        {
            "name": "Test 5: No filter, rely on -shortest",
            "filter": None
        }
    ]
    
    for test in tests:
        print(f"\n{test['name']}:")
        
        payload = {
            "inputs": [
                {"file_url": video_url},
                {"file_url": voiceover_url}
            ],
            "outputs": [{
                "filename": f"test_{test['name'].replace(' ', '_').lower()}.mp4",
                "options": [
                    {"option": "-map", "argument": "[v]" if test['filter'] else "0:v"},
                    {"option": "-map", "argument": "1:a"},
                    {"option": "-c:v", "argument": "libx264"},
                    {"option": "-c:a", "argument": "copy"},
                    {"option": "-shortest"}
                ]
            }],
            "webhook_url": "https://youtube-video-engine.fly.dev/webhook/nca/test",
            "id": f"test_{int(time.time())}"
        }
        
        if test['filter']:
            payload['filters'] = [{"filter": test['filter']}]
            print(f"Filter: {test['filter']}")
        else:
            print("No filter")
        
        # Add global options
        payload['global_options'] = [{"option": "-y"}]
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=65)
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed:.2f}s")
            
            if response.status_code in [200, 202]:
                result = response.json()
                print(f"✓ Success - Job ID: {result.get('job_id')}")
            else:
                print(f"✗ Error: {response.text[:500]}")
                
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            print(f"✗ Timeout after {elapsed:.2f}s")
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            print(f"✗ HTTP Error after {elapsed:.2f}s: {e}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Exception after {elapsed:.2f}s: {e}")
        
        print("-" * 40)
        time.sleep(3)

if __name__ == "__main__":
    test_tpad_variations()