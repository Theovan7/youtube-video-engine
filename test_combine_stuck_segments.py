#!/usr/bin/env python3
"""
Test combine-segment-media for stuck segments using the testing framework
"""

import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from testing_environment.test_framework import VideoEngineTestFramework
from testing_environment.file_inspector import FileInspector
from services.airtable_service import AirtableService

def test_stuck_segments():
    """Test the combine operation for stuck segments"""
    print("Testing Combine-Segment-Media for Stuck Segments")
    print("=" * 80)
    
    # Initialize services
    airtable = AirtableService()
    framework = VideoEngineTestFramework('https://youtube-video-engine.fly.dev')
    inspector = FileInspector()
    
    # List of stuck segments
    stuck_segments = [
        'recTuqCj6GN2ajsxp',
        'recmXnXCm5tFVAlFo', 
        'recphkqVVvJEwM19c'
    ]
    
    results = []
    
    for segment_id in stuck_segments:
        print(f"\n\nTesting segment: {segment_id}")
        print("-" * 40)
        
        # Get segment data
        try:
            segment = airtable.get_segment(segment_id)
            if not segment:
                print(f"✗ Segment {segment_id} not found")
                continue
                
            # Check for required fields
            if 'Video' not in segment['fields'] or 'Voiceover' not in segment['fields']:
                print(f"✗ Segment {segment_id} missing Video or Voiceover")
                continue
                
            video_url = segment['fields']['Video'][0]['url']
            voiceover_url = segment['fields']['Voiceover'][0]['url']
            
            print(f"✓ Found video URL: {video_url[:100]}...")
            print(f"✓ Found voiceover URL: {voiceover_url[:100]}...")
            
            # Test the combine endpoint
            payload = {
                "record_id": segment_id
            }
            
            print("\n1. Testing API endpoint...")
            response = framework.test_endpoint(
                '/api/v2/combine-segment-media',
                method='POST',
                payload=payload
            )
            
            if response.get('status_code') == 200:
                print("✓ API returned synchronous success (200)")
                result_data = response.get('json', {})
                
                if 'output_url' in result_data:
                    print(f"✓ Output URL: {result_data['output_url']}")
                    
                    # Verify file exists
                    import requests
                    try:
                        r = requests.head(result_data['output_url'])
                        if r.status_code == 200:
                            print(f"✓ Output file exists (size: {r.headers.get('content-length', 'unknown')} bytes)")
                        else:
                            print(f"✗ Output file not accessible: {r.status_code}")
                    except:
                        print("✗ Could not verify output file")
                
                results.append({
                    'segment_id': segment_id,
                    'status': 'success',
                    'response': result_data
                })
                
            elif response.get('status_code') == 202:
                print("✓ API returned async processing (202)")
                job_id = response.get('json', {}).get('job_id')
                print(f"  Job ID: {job_id}")
                
                # Wait a bit for processing
                print("  Waiting 30 seconds for processing...")
                time.sleep(30)
                
                # Check if file appeared in local backups
                print("\n2. Checking local backups...")
                files = inspector.find_files_by_record(segment_id)
                video_files = [f for f in files if f['type'] == 'videos']
                
                if video_files:
                    latest = max(video_files, key=lambda x: x['created'])
                    print(f"✓ Found combined video in local backup:")
                    print(f"  File: {latest['filename']}")
                    print(f"  Size: {latest['size_formatted']}")
                    print(f"  Created: {latest['created']}")
                else:
                    print("✗ No combined video found in local backups")
                
                results.append({
                    'segment_id': segment_id,
                    'status': 'async',
                    'job_id': job_id,
                    'local_files': len(video_files)
                })
                
            else:
                print(f"✗ API returned error: {response.get('status_code')}")
                print(f"  Error: {response.get('json', {}).get('error', 'Unknown error')}")
                
                results.append({
                    'segment_id': segment_id,
                    'status': 'error',
                    'error': response.get('json', {})
                })
                
        except Exception as e:
            print(f"✗ Exception testing segment {segment_id}: {e}")
            results.append({
                'segment_id': segment_id,
                'status': 'exception',
                'error': str(e)
            })
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    success_count = len([r for r in results if r['status'] == 'success'])
    async_count = len([r for r in results if r['status'] == 'async'])
    error_count = len([r for r in results if r['status'] in ['error', 'exception']])
    
    print(f"Total segments tested: {len(results)}")
    print(f"  Successful (sync): {success_count}")
    print(f"  Processing (async): {async_count}")
    print(f"  Errors: {error_count}")
    
    print("\nDetailed Results:")
    for result in results:
        print(f"\n{result['segment_id']}:")
        print(f"  Status: {result['status']}")
        if result['status'] == 'success' and 'response' in result:
            print(f"  Output URL: {result['response'].get('output_url', 'N/A')}")
        elif result['status'] == 'async':
            print(f"  Job ID: {result.get('job_id', 'N/A')}")
            print(f"  Local files: {result.get('local_files', 0)}")
        elif result['status'] in ['error', 'exception']:
            print(f"  Error: {result.get('error', 'Unknown')}")
    
    # Export detailed report
    print("\n\nExporting detailed file report...")
    inspector.export_report()
    print("✓ Report saved to file_inspection_report_*.txt")
    
    return results

if __name__ == "__main__":
    # Ensure we're using the test port
    if 'PORT' not in os.environ:
        os.environ['PORT'] = '5001'
    
    print("Note: Make sure the API is running on port 5001:")
    print("  PORT=5001 python app.py\n")
    
    results = test_stuck_segments()