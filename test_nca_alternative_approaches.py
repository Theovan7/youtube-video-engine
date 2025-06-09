#!/usr/bin/env python3
"""
Test alternative approaches to work around NCA failures.
"""

import json
import time
from services.nca_service import NCAService
from services.airtable_service import AirtableService

nca = NCAService()
airtable = AirtableService()

def test_alternative_approaches():
    """Test different approaches to see if any work."""
    print("Testing Alternative NCA Approaches")
    print("=" * 80)
    
    # Get a test segment
    segment_id = 'reci0gT2LhNaIaFtp'
    segment = airtable.get_segment(segment_id)
    video_url = segment['fields']['Video'][0]['url']
    audio_url = segment['fields']['Voiceover'][0]['url']
    
    # Test 1: Try with shorter filenames
    print("\n1. Testing with shorter output filename...")
    try:
        result = nca.combine_audio_video(
            video_url=video_url,
            audio_url=audio_url,
            output_filename="out.mp4",  # Very short filename
            webhook_url=None,
            custom_id="test1"
        )
        print(f"   Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"   Failed: {str(e)[:100]}")
    
    # Test 2: Try concatenate endpoint instead
    print("\n2. Testing concatenate endpoint (different operation)...")
    try:
        result = nca.concatenate_videos(
            video_urls=[video_url],  # Just one video
            output_filename="concat_test.mp4",
            webhook_url=None,
            custom_id="test2"
        )
        print(f"   Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"   Failed: {str(e)[:100]}")
    
    # Test 3: Check if it's specific to Airtable URLs
    print("\n3. Testing with public sample files...")
    try:
        # Use public sample files
        result = nca.combine_audio_video(
            video_url="https://www.w3schools.com/html/mov_bbb.mp4",
            audio_url="https://www.w3schools.com/html/horse.mp3",
            output_filename="sample_test.mp4",
            webhook_url=None,
            custom_id="test3"
        )
        print(f"   Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"   Failed: {str(e)[:100]}")
    
    # Test 4: Try with delay between requests
    print("\n4. Testing with delay (rate limiting check)...")
    time.sleep(5)  # Wait 5 seconds
    try:
        result = nca.combine_audio_video(
            video_url=video_url,
            audio_url=audio_url,
            output_filename="delayed_test.mp4",
            webhook_url=None,
            custom_id="test4"
        )
        print(f"   Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"   Failed: {str(e)[:100]}")
    
    # Test 5: Check recently successful jobs
    print("\n5. Checking if ANY recent NCA jobs succeeded...")
    try:
        # Get all jobs from last 24 hours
        jobs_table = airtable.jobs_table
        all_jobs = jobs_table.all()
        
        successful_nca_jobs = 0
        recent_jobs = 0
        
        for job in all_jobs:
            fields = job.get('fields', {})
            if fields.get('External Job ID'):
                recent_jobs += 1
                if fields.get('Status') == 'completed':
                    successful_nca_jobs += 1
                    print(f"\n   Success: Job {job['id']} completed")
                    print(f"   External ID: {fields['External Job ID']}")
                    print(f"   Type: {fields.get('Job Type')}")
                    break  # Just show one example
        
        print(f"\n   Summary: {successful_nca_jobs}/{recent_jobs} NCA jobs succeeded")
        
    except Exception as e:
        print(f"   Error checking jobs: {e}")

if __name__ == "__main__":
    test_alternative_approaches()