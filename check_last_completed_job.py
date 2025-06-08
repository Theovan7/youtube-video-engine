#!/usr/bin/env python3
"""Check the last completed job to verify the video/audio duration fix is working."""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
JOBS_TABLE = os.getenv('AIRTABLE_JOBS_TABLE', 'Jobs')
SEGMENTS_TABLE = os.getenv('AIRTABLE_SEGMENTS_TABLE', 'Segments')

def get_job_details(job_id):
    """Get details of a specific job."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{JOBS_TABLE}/{job_id}"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except:
        return None

def get_segment_details(segment_id):
    """Get details of a specific segment."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{SEGMENTS_TABLE}/{segment_id}"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except:
        return None

def check_last_completed_combine_job():
    """Find and check the last completed combine job."""
    
    # Get recent jobs
    url = f"https://api.airtable.com/v0/{BASE_ID}/{JOBS_TABLE}"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'maxRecords': 50,  # Get more records to find combine jobs
        'filterByFormula': "OR({Status}='completed', {Status}='Completed')"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        records = data.get('records', [])
        
        # Find combine jobs (the ones that would use our updated duration handling)
        combine_jobs = []
        for record in records:
            fields = record.get('fields', {})
            job_type = fields.get('Type', '')
            if job_type == 'combine':
                combine_jobs.append(record)
        
        if not combine_jobs:
            print("No completed 'combine' jobs found.")
            return
        
        # Get the most recent combine job
        latest_job = combine_jobs[0]
        fields = latest_job.get('fields', {})
        
        print("=" * 80)
        print("LAST COMPLETED COMBINE JOB ANALYSIS")
        print("=" * 80)
        
        print(f"\nJob ID: {latest_job.get('id')}")
        print(f"Type: {fields.get('Type')}")
        print(f"Status: {fields.get('Status')}")
        print(f"External Job ID: {fields.get('External Job ID', 'N/A')}")
        
        # Get related segment
        segment_ids = fields.get('Related Segment', [])
        if segment_ids:
            segment_id = segment_ids[0]
            print(f"\nRelated Segment: {segment_id}")
            
            # Get segment details
            segment = get_segment_details(segment_id)
            if segment:
                seg_fields = segment.get('fields', {})
                
                print("\nSEGMENT DETAILS:")
                print(f"  Text: {seg_fields.get('SRT Text', '')[:100]}...")
                print(f"  Duration: {seg_fields.get('Duration', 'N/A')} seconds")
                print(f"  Status: {seg_fields.get('Status', 'N/A')}")
                
                # Check if combined video exists
                combined_video = seg_fields.get('Voiceover + Video', [])
                if combined_video:
                    print(f"\n✅ Combined video created successfully!")
                    print(f"   URL: {combined_video[0].get('url', 'N/A')}")
                    
                    # Get video and voiceover info
                    video_files = seg_fields.get('Video', [])
                    voiceover_files = seg_fields.get('Voiceover', [])
                    
                    if video_files:
                        print(f"\nOriginal Video: {video_files[0].get('filename', 'N/A')}")
                    if voiceover_files:
                        print(f"Voiceover: {voiceover_files[0].get('filename', 'N/A')}")
                    
                    print("\n📊 DURATION HANDLING TEST:")
                    print("To verify the fix is working:")
                    print("1. Download the combined video")
                    print("2. Check its duration matches the voiceover duration")
                    print("3. If video was shorter: Last frame should be held")
                    print("4. If video was longer: Should be trimmed to audio length")
                    
                else:
                    print("\n❌ No combined video found in segment")
        
        # Check response payload for more details
        response_payload = fields.get('Response Payload', '')
        if response_payload:
            print("\n" + "-" * 40)
            print("JOB RESPONSE PAYLOAD:")
            try:
                import json
                payload_data = json.loads(response_payload)
                if 'output' in payload_data:
                    output = payload_data['output']
                    print(f"Output URL: {output.get('url', 'N/A')}")
                    print(f"Output Size: {output.get('size', 'N/A')} bytes")
            except:
                print("Could not parse response payload")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        print("=" * 80)
        print("\nTo fully verify the duration fix:")
        print("1. Create a test with video shorter than audio (should see last frame held)")
        print("2. Create a test with video longer than audio (should be trimmed)")
        print("3. Use ffprobe or similar tool to check output durations")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching jobs from Airtable: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    check_last_completed_combine_job()