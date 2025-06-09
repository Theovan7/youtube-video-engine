#!/usr/bin/env python3
"""
Test NCA combine directly to see if it's working.
"""

from services.nca_service import NCAService
from services.airtable_service import AirtableService
import json

# Initialize services
nca = NCAService()
airtable = AirtableService()

def test_nca_combine():
    """Test NCA combine with a simple example."""
    print("Testing NCA Combine Functionality...")
    print("=" * 80)
    
    # First, let's check if NCA is healthy
    print("\n1. Checking NCA health...")
    if nca.check_health():
        print("   ✓ NCA service is healthy")
    else:
        print("   ✗ NCA service health check failed")
        return
    
    # Get one of the stuck segments to test with
    segment_id = 'reci0gT2LhNaIaFtp'
    
    print(f"\n2. Getting segment {segment_id}...")
    try:
        segment = airtable.get_segment(segment_id)
        if not segment:
            print("   ✗ Segment not found")
            return
            
        fields = segment['fields']
        
        # Get URLs
        video_urls = fields.get('Video', [])
        voiceover_urls = fields.get('Voiceover', [])
        
        if not video_urls or not voiceover_urls:
            print("   ✗ Segment missing video or voiceover")
            return
            
        video_url = video_urls[0]['url']
        voiceover_url = voiceover_urls[0]['url']
        
        print(f"   ✓ Found video URL: {video_url[:60]}...")
        print(f"   ✓ Found voiceover URL: {voiceover_url[:60]}...")
        
    except Exception as e:
        print(f"   ✗ Error getting segment: {e}")
        return
    
    # Test combine without webhook first
    print("\n3. Testing NCA combine (without webhook)...")
    try:
        result = nca.combine_audio_video(
            video_url=video_url,
            audio_url=voiceover_url,
            output_filename=f"test_segment_{segment_id}_combined.mp4",
            webhook_url=None,  # No webhook for this test
            custom_id=f"test_{segment_id}"
        )
        
        print(f"   Result: {json.dumps(result, indent=2)}")
        
        if 'job_id' in result:
            external_id = result['job_id']
            print(f"\n   ✓ NCA job created: {external_id}")
            
            # Check if job exists
            print("\n4. Verifying job exists in NCA...")
            try:
                status = nca.get_job_status(external_id)
                print(f"   Job status: {json.dumps(status, indent=2)}")
            except Exception as e:
                print(f"   ✗ Error checking job status: {e}")
        else:
            print(f"   ✗ No job_id in result!")
            
    except Exception as e:
        print(f"   ✗ Error calling combine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nca_combine()