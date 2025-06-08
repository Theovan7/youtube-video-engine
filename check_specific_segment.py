#!/usr/bin/env python3
"""Check specific segment for combined video results and voiceover URL."""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
SEGMENTS_TABLE = os.getenv('AIRTABLE_SEGMENTS_TABLE', 'Segments')
JOBS_TABLE = os.getenv('AIRTABLE_JOBS_TABLE', 'Jobs')

def check_segment(segment_id):
    """Get detailed information about a specific segment."""
    
    url = f"https://api.airtable.com/v0/{BASE_ID}/{SEGMENTS_TABLE}/{segment_id}"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        fields = data.get('fields', {})
        
        print("=" * 80)
        print(f"SEGMENT DETAILS: {segment_id}")
        print("=" * 80)
        
        # Show all fields first
        print("\n--- ALL FIELDS IN RECORD ---")
        for field_name, field_value in sorted(fields.items()):
            if isinstance(field_value, list) and field_value and isinstance(field_value[0], dict):
                print(f"{field_name}: [Attachment - {len(field_value)} file(s)]")
            elif isinstance(field_value, str) and len(field_value) > 100:
                print(f"{field_name}: {field_value[:100]}...")
            else:
                print(f"{field_name}: {field_value}")
        
        # Basic information
        print(f"\n--- BASIC INFORMATION ---")
        print(f"Text: {fields.get('SRT Text', 'N/A')}")
        print(f"Duration: {fields.get('Duration', 'N/A')} seconds")
        print(f"Status: {fields.get('Status', 'N/A')}")
        print(f"Created: {fields.get('Created', 'N/A')}")
        
        # Video files
        print("\n--- VIDEO FILES ---")
        
        # Original video
        video_files = fields.get('Video', [])
        if video_files:
            print("\nOriginal Video:")
            for video in video_files:
                print(f"  Filename: {video.get('filename', 'N/A')}")
                print(f"  Size: {video.get('size', 0) / 1024 / 1024:.2f} MB")
                print(f"  Type: {video.get('type', 'N/A')}")
                print(f"  URL: {video.get('url', 'N/A')}")
        else:
            print("\nNo original video found")
        
        # Voiceover
        voiceover_files = fields.get('Voiceover', [])
        voiceover_url = fields.get('Voiceover URL', '')
        
        print("\n--- VOICEOVER INFORMATION ---")
        
        # Check for Voiceover URL field
        if voiceover_url:
            print(f"\n✅ Voiceover URL field populated: {voiceover_url}")
        else:
            print(f"\n❌ Voiceover URL field is empty or not present")
        
        # Check for Voiceover file attachments
        if voiceover_files:
            print("\nVoiceover files:")
            for voice in voiceover_files:
                print(f"  Filename: {voice.get('filename', 'N/A')}")
                print(f"  Size: {voice.get('size', 0) / 1024:.2f} KB")
                print(f"  Type: {voice.get('type', 'N/A')}")
                print(f"  URL: {voice.get('url', 'N/A')}")
        else:
            print("\nNo voiceover file attachments found")
        
        # Combined video
        combined_files = fields.get('Voiceover + Video', [])
        if combined_files:
            print("\n✅ COMBINED VIDEO RESULT:")
            for combined in combined_files:
                print(f"  Filename: {combined.get('filename', 'N/A')}")
                print(f"  Size: {combined.get('size', 0) / 1024 / 1024:.2f} MB")
                print(f"  Type: {combined.get('type', 'N/A')}")
                print(f"  URL: {combined.get('url', 'N/A')}")
                
                # Size comparison
                if video_files and combined_files:
                    original_size = video_files[0].get('size', 0)
                    combined_size = combined_files[0].get('size', 0)
                    size_ratio = (combined_size / original_size * 100) if original_size > 0 else 0
                    print(f"\n  Size comparison:")
                    print(f"    Original: {original_size / 1024 / 1024:.2f} MB")
                    print(f"    Combined: {combined_size / 1024 / 1024:.2f} MB")
                    print(f"    Ratio: {size_ratio:.1f}% of original")
        else:
            print("\n❌ No combined video found")
        
        # Check for related jobs
        print("\n--- RELATED JOBS ---")
        
        # Search for jobs related to this segment
        jobs_url = f"https://api.airtable.com/v0/{BASE_ID}/{JOBS_TABLE}"
        params = {
            'filterByFormula': f"SEARCH('{segment_id}', {{Related Segment}})",
            'maxRecords': 10
        }
        
        jobs_response = requests.get(jobs_url, headers=headers, params=params)
        if jobs_response.status_code == 200:
            jobs_data = jobs_response.json()
            jobs = jobs_data.get('records', [])
            
            if jobs:
                print(f"\nFound {len(jobs)} related job(s):")
                for job in jobs:
                    job_fields = job.get('fields', {})
                    print(f"\n  Job ID: {job.get('id')}")
                    print(f"    Type: {job_fields.get('Type', 'N/A')}")
                    print(f"    Status: {job_fields.get('Status', 'N/A')}")
                    print(f"    External ID: {job_fields.get('External Job ID', 'N/A')}")
                    
                    # Show error if any
                    error = job_fields.get('Error Details', '')
                    if error:
                        print(f"    Error: {error[:100]}...")
            else:
                print("\nNo related jobs found")
        
        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS:")
        print("=" * 80)
        
        if combined_files:
            print("\n✅ Combined video exists")
            print("\nDURATION HANDLING:")
            print("- Expected duration: Matches voiceover duration")
            print("- If video was shorter: Last frame held (tpad filter)")
            print("- If video was longer: Trimmed to audio length")
            print("\nTo verify duration:")
            print("1. Download the combined video URL above")
            print("2. Check duration with ffprobe or media player")
            print(f"3. Should match segment duration: {fields.get('Duration', 'N/A')} seconds")
        else:
            print("\n❌ No combined video found")
            print("\nPossible reasons:")
            print("1. Combination process not yet run")
            print("2. Process failed - check related jobs")
            print("3. Missing original video or voiceover")
            
            if not video_files:
                print("\n⚠️  Missing original video - upload required")
            if not voiceover_files:
                print("\n⚠️  Missing voiceover - generation required")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching segment from Airtable: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Check if segment ID is provided as command line argument
    if len(sys.argv) > 1:
        segment_id = sys.argv[1]
    else:
        # Default to the record you want to check
        segment_id = "recjDBBDr7h8KwnTU"
    
    print(f"Checking segment: {segment_id}")
    check_segment(segment_id)