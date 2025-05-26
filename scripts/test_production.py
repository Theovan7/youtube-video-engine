#!/usr/bin/env python3
"""
Production Testing Script for YouTube Video Engine
Tests the deployed application endpoints
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "https://youtube-video-engine.fly.dev"
TEST_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice from ElevenLabs

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test the health check endpoint"""
    print_header("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Check if all services are connected
            if data.get("status") == "healthy":
                print("\n✅ All services are connected!")
            else:
                print("\n⚠️  Some services may not be connected properly")
                
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing health check: {str(e)}")
        return False

def test_script_processing():
    """Test the script processing endpoint"""
    print_header("Testing Script Processing")
    
    test_script = """
    Welcome to our video about artificial intelligence.
    
    AI is transforming the way we live and work. From smart assistants to self-driving cars, 
    AI is everywhere around us.
    
    Machine learning algorithms can now recognize images, understand speech, and even generate 
    creative content like music and art.
    
    The future of AI holds incredible possibilities, but also important challenges we need to 
    address together.
    
    Thank you for watching this brief introduction to AI.
    """
    
    payload = {
        "script_text": test_script,
        "video_name": "Test Video " + datetime.now().strftime("%Y%m%d_%H%M%S"),
        "target_segment_duration": 30
    }
    
    try:
        print("Sending script for processing...")
        response = requests.post(
            f"{BASE_URL}/api/v1/process-script",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:  # 201 Created is the expected status
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # API doesn't return 'success' field, check for video_id instead
            if data.get("video_id"):
                print(f"\n✅ Script processed successfully!")
                print(f"Video ID: {data.get('video_id')}")
                print(f"Segments created: {data.get('total_segments', 0)}")
                return True, data.get('video_id')
            else:
                print(f"\n❌ Script processing failed: No video ID returned")
                return False, None
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing script processing: {str(e)}")
        return False, None

def test_job_status(job_id):
    """Test the job status endpoint"""
    print_header(f"Testing Job Status for ID: {job_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # API doesn't return 'success' field, check for job_id instead
            if data.get("job_id"):
                print(f"\n✅ Job status retrieved successfully!")
                print(f"Job Type: {data.get('type')}")
                print(f"Job Status: {data.get('status')}")
                return True
            else:
                print(f"\n❌ Failed to get job status: No job ID returned")
                return False
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing job status: {str(e)}")
        return False

def test_voiceover_generation(segment_id):
    """Test the voiceover generation endpoint"""
    print_header(f"Testing Voiceover Generation for Segment: {segment_id}")
    
    payload = {
        "segment_id": segment_id,
        "voice_id": TEST_VOICE_ID,
        "stability": 0.5,
        "similarity_boost": 0.5
    }
    
    try:
        print("Requesting voiceover generation...")
        response = requests.post(
            f"{BASE_URL}/api/v1/generate-voiceover",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 202:  # 202 Accepted for async processing
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # API doesn't return 'success' field, check for job_id instead
            if data.get("job_id"):
                print(f"\n✅ Voiceover generation initiated!")
                print(f"Job ID: {data.get('job_id')}")
                return True, data.get('job_id')
            else:
                print(f"\n❌ Voiceover generation failed: No job ID returned")
                return False, None
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing voiceover generation: {str(e)}")
        return False, None

def main():
    """Run all production tests"""
    print("\n🚀 Starting YouTube Video Engine Production Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Health Check
    health_ok = test_health_check()
    if not health_ok:
        print("\n⚠️  Health check failed. Some tests may not work properly.")
    
    # Test 2: Script Processing
    script_ok, video_id = test_script_processing()
    if not script_ok:
        print("\n⚠️  Script processing failed. Skipping dependent tests.")
        return
    
    # Give Airtable a moment to process
    print("\nWaiting 2 seconds for Airtable to process...")
    time.sleep(2)
    
    # Test 3: Job Status (if we have a job ID)
    # Note: We'd need to get a job ID from one of the operations
    
    # Test 4: Voiceover Generation (would need a segment ID)
    # This would require querying Airtable to get the segment IDs
    
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    print(f"✅ Health Check: {'PASSED' if health_ok else 'FAILED'}")
    print(f"✅ Script Processing: {'PASSED' if script_ok else 'FAILED'}")
    print("\n📝 Note: Full production testing requires:")
    print("   - Airtable access to retrieve segment IDs")
    print("   - Webhook endpoints to be registered")
    print("   - External services to be fully configured")
    
    print("\n✨ Basic production tests completed!")

if __name__ == "__main__":
    main()
