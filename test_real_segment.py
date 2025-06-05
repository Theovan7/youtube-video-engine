#!/usr/bin/env python3
"""
Test the fixed NCA service with a real segment from troubleshooting notes.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add the project root to the path so we can import our services
sys.path.insert(0, '/Users/theovandermerwe/Dropbox/CODING2/ClaudeDesktop/ProjectHI/youtube_video_engine')

from services.nca_service import NCAService

# Load environment variables
load_dotenv()

def test_segment_combination():
    """Test combining media for segment recXwiLcbFPcIQxI7 from troubleshooting notes."""
    
    print("🎬 TESTING SEGMENT MEDIA COMBINATION")
    print("=" * 40)
    
    # From troubleshooting notes - segment recXwiLcbFPcIQxI7
    segment_id = "recXwiLcbFPcIQxI7"
    video_filename = "280489658322346.mp4"
    audio_filename = "20250528_015545_625a12e2_voiceover_recXwiLcbFPcIQxI7.mp3"
    
    # Construct URLs (these are from DigitalOcean Spaces based on the troubleshooting notes)
    spaces_base_url = "https://youtube-video-engine.nyc3.digitaloceanspaces.com"
    video_url = f"{spaces_base_url}/youtube-video-engine/videos/{video_filename}"
    audio_url = f"{spaces_base_url}/youtube-video-engine/voiceovers/{audio_filename}"
    
    print(f"📋 Test Details:")
    print(f"   Segment ID: {segment_id}")
    print(f"   Video URL: {video_url}")
    print(f"   Audio URL: {audio_url}")
    print()
    
    # Initialize NCA service
    try:
        nca_service = NCAService()
        print("✅ NCA Service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize NCA Service: {e}")
        return False
    
    # Test health check first
    print("🏥 Checking NCA health...")
    if not nca_service.check_health():
        print("❌ NCA health check failed")
        return False
    else:
        print("✅ NCA health check passed")
    
    print()
    print("🎬 Attempting to combine audio and video...")
    
    # Set up webhook URL for our app
    webhook_url = "https://youtube-video-engine.fly.dev/webhooks/nca"
    output_filename = f"combined_{segment_id}.mp4"
    
    try:
        # Call the fixed combine_audio_video method
        result = nca_service.combine_audio_video(
            video_url=video_url,
            audio_url=audio_url,
            output_filename=output_filename,
            webhook_url=webhook_url,
            custom_id=segment_id
        )
        
        print("✅ COMBINATION REQUEST SUCCESSFUL!")
        print(f"📋 Response:")
        print(f"   Status Code: {result.get('code', 'N/A')}")
        print(f"   Job ID: {result.get('job_id', 'N/A')}")
        print(f"   Message: {result.get('message', 'N/A')}")
        print(f"   Queue Length: {result.get('queue_length', 'N/A')}")
        
        if result.get('code') in [200, 202]:
            print("✅ SUCCESS! Media combination is processing")
            return True
        else:
            print(f"⚠️  Unexpected response code: {result.get('code')}")
            return False
            
    except Exception as e:
        print(f"❌ COMBINATION FAILED: {e}")
        return False


if __name__ == '__main__':
    success = test_segment_combination()
    
    print()
    print("🏁 TEST SUMMARY:")
    print("=" * 15)
    
    if success:
        print("✅ SEGMENT COMBINATION TEST: SUCCESSFUL")
        print("✅ NCA service is working with real segment data")
        print("✅ Ready to deploy the fix to production")
        print()
        print("🚀 NEXT STEPS:")
        print("   1. Deploy the fixed NCA service to production")
        print("   2. Test end-to-end workflow with Airtable")
        print("   3. Monitor processing results via webhook")
    else:
        print("❌ SEGMENT COMBINATION TEST: FAILED")
        print("❌ May need additional troubleshooting")
    
    sys.exit(0 if success else 1)
