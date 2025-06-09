#!/usr/bin/env python3
"""
Direct test of combine-segment-media without framework
"""

import requests
import json
import time
from services.airtable_service import AirtableService

def test_combine_direct():
    """Test combine API directly"""
    print("Direct Test of Combine-Segment-Media")
    print("=" * 80)
    
    airtable = AirtableService()
    base_url = 'https://youtube-video-engine.fly.dev'
    
    stuck_segments = [
        'recTuqCj6GN2ajsxp',
        'recmXnXCm5tFVAlFo', 
        'recphkqVVvJEwM19c'
    ]
    
    for segment_id in stuck_segments:
        print(f"\n\nTesting segment: {segment_id}")
        print("-" * 40)
        
        # Make direct API call
        url = f"{base_url}/api/v2/combine-segment-media"
        payload = {"record_id": segment_id}
        headers = {"Content-Type": "application/json"}
        
        print(f"POST {url}")
        print(f"Payload: {json.dumps(payload)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"\nStatus Code: {response.status_code}")
            
            # Get response data
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if response.status_code == 200:
                    # Synchronous success
                    print("\n✓ Synchronous processing succeeded!")
                    if 'output_url' in data:
                        print(f"✓ Output URL: {data['output_url']}")
                        
                        # Check segment status
                        segment = airtable.get_segment(segment_id)
                        status = segment['fields'].get('Status', 'Unknown')
                        has_combined = 'Voiceover + Video' in segment['fields']
                        print(f"\nSegment Status: {status}")
                        print(f"Has Combined Video: {has_combined}")
                        
                elif response.status_code == 202:
                    # Async processing
                    print("\n→ Async processing started")
                    job_id = data.get('job_id')
                    print(f"  Job ID: {job_id}")
                    
                    # Wait and check
                    print("  Waiting 15 seconds...")
                    time.sleep(15)
                    
                    # Check segment again
                    segment = airtable.get_segment(segment_id)
                    status = segment['fields'].get('Status', 'Unknown')
                    has_combined = 'Voiceover + Video' in segment['fields']
                    print(f"\n  Segment Status: {status}")
                    print(f"  Has Combined Video: {has_combined}")
                    
                else:
                    print(f"\n✗ Error response: {response.status_code}")
                    
            except Exception as e:
                print(f"\nCould not parse JSON response: {e}")
                print(f"Raw response: {response.text[:500]}")
                
        except requests.exceptions.Timeout:
            print("\n✗ Request timed out after 30 seconds")
        except Exception as e:
            print(f"\n✗ Request failed: {e}")
    
    # Final check of all segments
    print("\n\n" + "=" * 80)
    print("FINAL STATUS CHECK")
    print("=" * 80)
    
    for segment_id in stuck_segments:
        segment = airtable.get_segment(segment_id)
        status = segment['fields'].get('Status', 'Unknown')
        has_combined = 'Voiceover + Video' in segment['fields']
        
        print(f"\n{segment_id}:")
        print(f"  Status: {status}")
        print(f"  Has Combined Video: {'✓' if has_combined else '✗'}")
        
        if has_combined:
            url = segment['fields']['Voiceover + Video'][0]['url']
            print(f"  URL: {url[:100]}...")

if __name__ == "__main__":
    test_combine_direct()