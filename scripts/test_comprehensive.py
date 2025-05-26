#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for YouTube Video Engine
Tests the complete video production pipeline
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://youtube-video-engine.fly.dev"
TEST_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice from ElevenLabs

# Test data
TEST_SCRIPT = """
Welcome to our comprehensive test of the YouTube Video Engine.

This is segment one, where we introduce the concept of automated video production.

In segment two, we explore how AI is revolutionizing content creation.

Finally, in segment three, we conclude with the future possibilities.

Thank you for watching this test video.
"""

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_status(success, message):
    """Print status with emoji"""
    emoji = "✅" if success else "❌"
    print(f"{emoji} {message}")

def test_health_check():
    """Test the health check endpoint"""
    print_header("1. Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        data = response.json()
        
        all_healthy = all(status == "connected" for status in data.get("services", {}).values())
        print_status(all_healthy, f"System Status: {data.get('status', 'unknown')}")
        
        for service, status in data.get("services", {}).items():
            print_status(status == "connected", f"{service}: {status}")
        
        return all_healthy
    except Exception as e:
        print_status(False, f"Health check failed: {str(e)}")
        return False

def test_script_processing():
    """Test script processing"""
    print_header("2. Script Processing")
    
    payload = {
        "script_text": TEST_SCRIPT,
        "video_name": f"E2E Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "target_segment_duration": 30
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/process-script", json=payload, timeout=30)
        
        if response.status_code == 201:
            data = response.json()
            video_id = data.get("video_id")
            segments = data.get("segments", [])
            
            print_status(True, f"Script processed - Video ID: {video_id}")
            print(f"   Segments created: {len(segments)}")
            
            return True, video_id, segments
        else:
            print_status(False, f"Script processing failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False, None, []
            
    except Exception as e:
        print_status(False, f"Script processing error: {str(e)}")
        return False, None, []

def test_voiceover_generation(segment_id, segment_text):
    """Test voiceover generation for a segment"""
    print(f"\n   Testing voiceover for segment: {segment_id}")
    print(f"   Text preview: {segment_text[:50]}...")
    
    payload = {
        "segment_id": segment_id,
        "voice_id": TEST_VOICE_ID,
        "stability": 0.5,
        "similarity_boost": 0.5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/generate-voiceover", json=payload, timeout=30)
        
        if response.status_code == 202:
            data = response.json()
            job_id = data.get("job_id")
            print_status(True, f"Voiceover job created: {job_id}")
            return True, job_id
        else:
            print_status(False, f"Voiceover generation failed: {response.status_code}")
            return False, None
            
    except Exception as e:
        print_status(False, f"Voiceover generation error: {str(e)}")
        return False, None

def wait_for_job(job_id, max_wait=60):
    """Wait for a job to complete"""
    print(f"\n   Waiting for job {job_id} to complete...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "completed":
                    print_status(True, f"Job completed successfully")
                    return True
                elif status == "failed":
                    print_status(False, f"Job failed: {data.get('error')}")
                    return False
                else:
                    print(f"   Status: {status} (waiting...)")
                    time.sleep(5)
            else:
                print_status(False, f"Failed to get job status: {response.status_code}")
                return False
                
        except Exception as e:
            print_status(False, f"Error checking job status: {str(e)}")
            return False
    
    print_status(False, f"Job timed out after {max_wait} seconds")
    return False

def test_segment_combination(segment_id):
    """Test combining segment media"""
    print(f"\n   Testing segment combination for: {segment_id}")
    
    payload = {
        "segment_id": segment_id,
        "background_video_url": "https://example.com/test-background.mp4"  # Would need real URL
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/combine-segment-media", json=payload, timeout=30)
        
        if response.status_code in [200, 202]:
            data = response.json()
            job_id = data.get("job_id")
            print_status(True, f"Segment combination job created: {job_id}")
            return True, job_id
        else:
            print_status(False, f"Segment combination failed: {response.status_code}")
            print(f"      Note: This may require a valid background video URL")
            return False, None
            
    except Exception as e:
        print_status(False, f"Segment combination error: {str(e)}")
        return False, None

def test_video_assembly(video_id):
    """Test final video assembly"""
    print_header("5. Video Assembly")
    
    payload = {
        "video_id": video_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/combine-all-segments", json=payload, timeout=30)
        
        if response.status_code in [200, 202]:
            data = response.json()
            job_id = data.get("job_id")
            print_status(True, f"Video assembly job created: {job_id}")
            return True, job_id
        else:
            print_status(False, f"Video assembly failed: {response.status_code}")
            print(f"   Note: This requires all segments to have completed media")
            return False, None
            
    except Exception as e:
        print_status(False, f"Video assembly error: {str(e)}")
        return False, None

def test_music_generation(video_id):
    """Test music generation"""
    print_header("6. Music Generation")
    
    payload = {
        "video_id": video_id,
        "music_prompt": "Upbeat corporate background music",
        "duration": 60
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/generate-and-add-music", json=payload, timeout=30)
        
        if response.status_code in [200, 202]:
            data = response.json()
            job_id = data.get("job_id")
            print_status(True, f"Music generation job created: {job_id}")
            return True, job_id
        else:
            print_status(False, f"Music generation failed: {response.status_code}")
            print(f"   Note: This requires a completed video")
            return False, None
            
    except Exception as e:
        print_status(False, f"Music generation error: {str(e)}")
        return False, None

def main():
    """Run comprehensive end-to-end test"""
    print("\n🚀 YouTube Video Engine - Comprehensive End-to-End Test")
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    
    # Track results
    results = {
        "health_check": False,
        "script_processing": False,
        "voiceover_generation": False,
        "segment_combination": False,
        "video_assembly": False,
        "music_generation": False
    }
    
    # 1. Health Check
    results["health_check"] = test_health_check()
    if not results["health_check"]:
        print("\n⚠️  Health check failed. Some services may not work properly.")
    
    # 2. Script Processing
    script_ok, video_id, segments = test_script_processing()
    results["script_processing"] = script_ok
    
    if not script_ok:
        print("\n⚠️  Script processing failed. Cannot continue with pipeline.")
        print_summary(results)
        return
    
    # Wait for Airtable
    print("\n⏳ Waiting for Airtable to sync...")
    time.sleep(3)
    
    # 3. Voiceover Generation
    print_header("3. Voiceover Generation")
    
    voiceover_jobs = []
    all_voiceovers_ok = True
    
    for segment in segments[:2]:  # Test first 2 segments only
        vo_ok, job_id = test_voiceover_generation(segment["id"], segment["text"])
        if vo_ok and job_id:
            voiceover_jobs.append(job_id)
        else:
            all_voiceovers_ok = False
    
    results["voiceover_generation"] = all_voiceovers_ok
    
    # Wait for voiceover jobs
    if voiceover_jobs:
        print("\n⏳ Waiting for voiceover jobs to complete...")
        for job_id in voiceover_jobs:
            wait_for_job(job_id, max_wait=30)
    
    # 4. Segment Combination (would need real background videos)
    print_header("4. Segment Combination")
    print("⚠️  Skipping - requires valid background video URLs")
    
    # 5. Video Assembly
    # test_video_assembly(video_id)
    print_header("5. Video Assembly")
    print("⚠️  Skipping - requires completed segment media")
    
    # 6. Music Generation
    # test_music_generation(video_id)
    print_header("6. Music Generation")
    print("⚠️  Skipping - requires completed video")
    
    # Summary
    print_summary(results)

def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")
    
    for test, passed in results.items():
        test_name = test.replace("_", " ").title()
        print_status(passed, test_name)
    
    passed_count = sum(1 for passed in results.values() if passed)
    total_count = len(results)
    
    print(f"\nPassed: {passed_count}/{total_count} tests")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
    elif passed_count >= total_count * 0.5:
        print("\n⚠️  Some tests failed. Check the logs above.")
    else:
        print("\n❌ Most tests failed. Please check service configurations.")

if __name__ == "__main__":
    main()
