#!/usr/bin/env python3
"""
Recovery script for stuck voiceover segments.
Resets failed segments and re-processes them using the synchronous API.
"""

import os
import sys
import requests
import time
from pyairtable import Table
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = 'app1XR6KcYA8GleJd'
SEGMENTS_TABLE = 'Segments'
API_BASE_URL = os.getenv('API_BASE_URL', 'https://youtube-video-engine.fly.dev')

# Initialize Airtable
segments_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, SEGMENTS_TABLE)


def find_stuck_segments():
    """Find all segments stuck in voiceover generation."""
    print("Finding stuck segments...")
    
    # Get all segments with voiceover-related status issues
    stuck_statuses = ['Generating Voiceover', 'Voiceover Failed', 'voiceover_failed']
    all_stuck = []
    
    for status in stuck_statuses:
        try:
            formula = f"{{Status}} = '{status}'"
            records = segments_table.all(formula=formula)
            all_stuck.extend(records)
            print(f"  Found {len(records)} segments with status '{status}'")
        except Exception as e:
            print(f"  Error searching for status '{status}': {e}")
    
    # Also find segments that should have voiceover but don't
    try:
        formula = "AND({Voiceover Go} = TRUE(), {Voiceover} = BLANK(), {SRT Text} != '')"
        missing_voiceover = segments_table.all(formula=formula)
        print(f"  Found {len(missing_voiceover)} segments marked for voiceover but missing audio")
        all_stuck.extend(missing_voiceover)
    except Exception as e:
        print(f"  Error searching for missing voiceovers: {e}")
    
    # Remove duplicates
    seen = set()
    unique_stuck = []
    for record in all_stuck:
        if record['id'] not in seen:
            seen.add(record['id'])
            unique_stuck.append(record)
    
    print(f"\nTotal unique stuck segments: {len(unique_stuck)}")
    return unique_stuck


def reset_segment_status(segment_id):
    """Reset a segment to 'Ready' status."""
    try:
        segments_table.update(segment_id, {'Status': 'Ready'})
        return True
    except Exception as e:
        print(f"  Error resetting segment {segment_id}: {e}")
        return False


def generate_voiceover(segment_id):
    """Call the synchronous voiceover API."""
    url = f"{API_BASE_URL}/api/v2/generate-voiceover"
    payload = {"record_id": segment_id}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


def process_stuck_segments(segments, auto_process=False):
    """Process stuck segments."""
    print(f"\n{'='*60}")
    print(f"Processing {len(segments)} stuck segments")
    print(f"{'='*60}\n")
    
    success_count = 0
    failure_count = 0
    
    for i, segment in enumerate(segments, 1):
        segment_id = segment['id']
        segment_text = segment['fields'].get('SRT Text', '')[:50] + '...'
        
        print(f"\n[{i}/{len(segments)}] Processing segment {segment_id}")
        print(f"  Text: {segment_text}")
        
        if not auto_process:
            response = input("  Process this segment? (y/n/q): ").lower()
            if response == 'q':
                print("\nQuitting...")
                break
            elif response != 'y':
                print("  Skipping...")
                continue
        
        # Reset status
        print("  Resetting status to 'Ready'...")
        if not reset_segment_status(segment_id):
            failure_count += 1
            continue
        
        # Generate voiceover
        print("  Generating voiceover...")
        result = generate_voiceover(segment_id)
        
        if 'error' in result:
            print(f"  ❌ Failed: {result['error']}")
            failure_count += 1
        else:
            print(f"  ✅ Success! Voiceover URL: {result.get('voiceover_url', 'N/A')}")
            success_count += 1
        
        # Rate limiting
        if auto_process and i < len(segments):
            time.sleep(1)  # 1 second between requests
    
    print(f"\n{'='*60}")
    print(f"Processing Complete:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {failure_count}")
    print(f"  ⏭️  Skipped: {len(segments) - success_count - failure_count}")
    print(f"{'='*60}\n")


def main():
    """Main function."""
    print("YouTube Video Engine - Voiceover Recovery Tool")
    print("=" * 60)
    
    # Check required environment variables
    if not AIRTABLE_API_KEY:
        print("ERROR: AIRTABLE_API_KEY not set in environment")
        sys.exit(1)
    
    # Find stuck segments
    stuck_segments = find_stuck_segments()
    
    if not stuck_segments:
        print("\n✅ No stuck segments found! All voiceovers are processing correctly.")
        return
    
    # Display stuck segments
    print("\nStuck segments found:")
    for i, segment in enumerate(stuck_segments[:10], 1):
        fields = segment['fields']
        print(f"\n{i}. ID: {segment['id']}")
        print(f"   Text: {fields.get('SRT Text', '')[:60]}...")
        print(f"   Status: {fields.get('Status', 'N/A')}")
        print(f"   Has Voiceover: {'Yes' if fields.get('Voiceover') else 'No'}")
    
    if len(stuck_segments) > 10:
        print(f"\n... and {len(stuck_segments) - 10} more segments")
    
    # Ask user how to proceed
    print("\nOptions:")
    print("1. Process all segments automatically")
    print("2. Process segments one by one with confirmation")
    print("3. Just reset status to 'Ready' (no voiceover generation)")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ")
    
    if choice == '1':
        print("\n⚠️  WARNING: This will process all segments automatically.")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            process_stuck_segments(stuck_segments, auto_process=True)
    elif choice == '2':
        process_stuck_segments(stuck_segments, auto_process=False)
    elif choice == '3':
        print("\nResetting all segments to 'Ready' status...")
        reset_count = 0
        for segment in stuck_segments:
            if reset_segment_status(segment['id']):
                reset_count += 1
        print(f"Reset {reset_count} segments to 'Ready' status")
    else:
        print("\nExiting...")


if __name__ == "__main__":
    main()
