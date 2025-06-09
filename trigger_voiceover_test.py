#!/usr/bin/env python3
"""
Trigger a voiceover generation to test the remote backup system.
This script finds a segment that needs a voiceover and triggers generation.
"""

import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from services.airtable_service import AirtableService
from config import get_config

# Load environment variables
load_dotenv()

# Initialize services
airtable = AirtableService()
config = get_config()()

def find_segment_for_test():
    """Find a segment that has a voice but no voiceover."""
    print("🔍 Looking for a segment to test with...")
    
    # Get recent segments
    segments = airtable.base.table(config.SEGMENTS_TABLE).all(max_records=20)
    
    for seg in segments:
        fields = seg['fields']
        # Need: has voice, has text, no voiceover
        if (fields.get('Voices') and 
            fields.get('SRT Text') and 
            not fields.get('Voiceover URL')):
            return seg
    
    return None

def trigger_voiceover(segment_id):
    """Trigger voiceover generation for a segment."""
    api_url = os.getenv('API_URL', 'https://youtube-video-engine.fly.dev')
    webhook_secret = os.getenv('WEBHOOK_SECRET')
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    if webhook_secret:
        headers['X-Webhook-Secret'] = webhook_secret
    
    data = {
        'record_id': segment_id
    }
    
    print(f"\n📤 Triggering voiceover generation...")
    print(f"   Segment ID: {segment_id}")
    print(f"   API URL: {api_url}/api/v2/generate-voiceover")
    
    try:
        response = requests.post(
            f"{api_url}/api/v2/generate-voiceover",
            json=data,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Voiceover generated successfully!")
            print(f"   Audio URL: {result.get('audio_url', 'N/A')}")
            print(f"   Duration: {result.get('duration', 'N/A')}s")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def check_local_backup(segment_id, wait_time=5):
    """Check if the voiceover was backed up locally."""
    print(f"\n⏳ Waiting {wait_time} seconds for backup to complete...")
    time.sleep(wait_time)
    
    print("🔍 Checking local backup directory...")
    backup_dir = "./local_backups/youtube-video-engine/voiceovers/"
    
    if not os.path.exists(backup_dir):
        print(f"❌ Backup directory does not exist: {backup_dir}")
        return False
    
    # Look for files containing the segment ID
    files = [f for f in os.listdir(backup_dir) if segment_id in f]
    
    if files:
        print(f"✅ BACKUP SUCCESSFUL! Found {len(files)} file(s):")
        for f in files:
            file_path = os.path.join(backup_dir, f)
            size = os.path.getsize(file_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            print(f"   - {f} ({size:,} bytes) - {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    else:
        # Show recent files for context
        all_files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.mp3')], 
                          key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
                          reverse=True)
        
        print("❌ Backup file not found for this segment.")
        if all_files:
            print(f"\n📁 Most recent files in backup directory:")
            for f in all_files[:5]:
                file_path = os.path.join(backup_dir, f)
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"   - {f} - {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return False

def main():
    """Run the test."""
    print("🚀 YouTube Video Engine - Remote Backup Test")
    print("=" * 60)
    
    # Find a segment to test with
    segment = find_segment_for_test()
    
    if not segment:
        print("\n❌ No suitable segment found for testing.")
        print("   Need a segment with:")
        print("   - Voice assigned")
        print("   - SRT Text present")
        print("   - No voiceover generated yet")
        
        # Show some segments for context
        print("\n📋 Recent segments:")
        segments = airtable.base.table(config.SEGMENTS_TABLE).all(max_records=5)
        for seg in segments:
            fields = seg['fields']
            print(f"\n   ID: {seg['id']}")
            print(f"   Text: {fields.get('SRT Text', '')[:50]}...")
            print(f"   Has Voice: {'Yes' if fields.get('Voices') else 'No'}")
            print(f"   Has Voiceover: {'Yes' if fields.get('Voiceover URL') else 'No'}")
        
        return
    
    # Found a segment
    segment_id = segment['id']
    fields = segment['fields']
    text_preview = fields.get('SRT Text', '')[:100] + '...'
    
    print(f"\n✅ Found segment to test:")
    print(f"   ID: {segment_id}")
    print(f"   Text: {text_preview}")
    
    # Trigger voiceover
    if trigger_voiceover(segment_id):
        # Check backup
        if check_local_backup(segment_id):
            print("\n✨ Remote backup system is working correctly!")
        else:
            print("\n⚠️  Voiceover was generated but not backed up.")
            print("   Check that:")
            print("   1. Local receiver is running")
            print("   2. Ngrok tunnel is active")
            print("   3. Production has correct LOCAL_RECEIVER_URL")
    else:
        print("\n❌ Failed to generate voiceover")

if __name__ == "__main__":
    main()