#!/usr/bin/env python3
"""
Test voiceover generation in production
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://youtube-video-engine.fly.dev"
TEST_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice from ElevenLabs

def test_voiceover_generation(segment_id):
    """Test voiceover generation for a specific segment"""
    print(f"\n{'='*60}")
    print(f"  Testing Voiceover Generation for Segment: {segment_id}")
    print(f"{'='*60}\n")
    
    payload = {
        "segment_id": segment_id,
        "voice_id": TEST_VOICE_ID,
        "stability": 0.5,
        "similarity_boost": 0.5
    }
    
    try:
        print("Sending voiceover generation request...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/generate-voiceover",
            json=payload,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 202:
            data = response.json()
            print(f"\nResponse Body: {json.dumps(data, indent=2)}")
            
            if data.get("job_id"):
                print(f"\n✅ Voiceover generation initiated!")
                print(f"Job ID: {data.get('job_id')}")
                return True, data.get('job_id')
            else:
                print(f"\n❌ Voiceover generation failed: No job ID returned")
                return False, None
        else:
            print(f"\n❌ Request failed with status: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            # Try to parse error response
            try:
                error_data = response.json()
                print(f"\nError details: {json.dumps(error_data, indent=2)}")
            except:
                pass
                
            return False, None
            
    except Exception as e:
        print(f"\n❌ Error testing voiceover generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def check_job_status(job_id):
    """Check status of a job"""
    print(f"\nChecking job status for: {job_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Job Status: {json.dumps(data, indent=2)}")
            return data.get('status', 'unknown')
        else:
            print(f"Failed to get job status: {response.text}")
            return 'error'
            
    except Exception as e:
        print(f"Error checking job status: {str(e)}")
        return 'error'

def main():
    """Run voiceover generation test"""
    
    if len(sys.argv) > 1:
        segment_id = sys.argv[1]
        print(f"Using provided segment ID: {segment_id}")
    else:
        # Use default segment ID from recent test
        segment_id = "rectSkl0041whl76Y"
        print(f"Using default segment ID: {segment_id}")
        print("You can provide a custom segment ID as an argument")
    
    print(f"\n🚀 Starting Voiceover Generation Test")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test voiceover generation
    success, job_id = test_voiceover_generation(segment_id)
    
    if success and job_id:
        print("\n⏳ Waiting 5 seconds before checking job status...")
        time.sleep(5)
        
        # Check job status
        status = check_job_status(job_id)
        print(f"\nFinal Job Status: {status}")
        
        if status == 'completed':
            print("\n✅ Voiceover generation completed successfully!")
        elif status == 'processing':
            print("\n⏳ Voiceover is still processing. Check job status later.")
        else:
            print(f"\n⚠️ Job status: {status}")
    
    print("\n" + "="*60)
    print("Test Summary:")
    print(f"Voiceover Generation: {'PASSED' if success else 'FAILED'}")
    print("="*60)

if __name__ == "__main__":
    main()
