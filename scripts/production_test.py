#!/usr/bin/env python3
"""
Production test script for YouTube Video Engine
Tests the complete video generation pipeline end-to-end
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "https://youtube-video-engine.fly.dev"
API_KEY = "test-api-key"  # You may need to update this with actual API key if required

# Test data
TEST_SCRIPT = """
Welcome to our quick demo of the YouTube Video Engine.
This powerful tool can transform your scripts into fully produced videos.
With AI-generated voiceovers, automatic scene detection, and background music.
Let's see how it works in just a few simple steps.
"""

MUSIC_PROMPT = "upbeat, motivational, tech demo, modern electronic"

def print_step(step_num, message):
    """Print a formatted step message"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {message}")
    print(f"{'='*60}")

def make_request(method, endpoint, data=None, headers=None):
    """Make an API request and handle response"""
    url = f"{BASE_URL}{endpoint}"
    if headers is None:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
    
    print(f"\n{method} {url}")
    if data:
        print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
            return response_data
        else:
            print(f"Error response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return None

def wait_for_job(job_id, max_attempts=30, delay=10):
    """Wait for a job to complete"""
    print(f"\nWaiting for job {job_id} to complete...")
    
    for attempt in range(max_attempts):
        result = make_request("GET", f"/api/v1/jobs/{job_id}")
        if result:
            status = result.get("status")
            print(f"Attempt {attempt + 1}: Job status = {status}")
            
            if status == "completed":
                print("Job completed successfully!")
                return result
            elif status == "failed":
                print(f"Job failed: {result.get('error')}")
                return None
        
        time.sleep(delay)
    
    print("Job timed out")
    return None

def run_production_test():
    """Run the complete production test"""
    print("\n" + "="*60)
    print("YouTube Video Engine - Production Test")
    print("="*60)
    
    # Step 1: Check health
    print_step(1, "Checking service health")
    health = make_request("GET", "/health")
    if not health or health.get("status") != "healthy":
        print("ERROR: Service is not healthy")
        return False
    print("✓ All services are healthy")
    
    # Step 2: Process script
    print_step(2, "Processing script to generate segments")
    script_data = {
        "video_name": f"Production Test - {time.strftime('%Y%m%d_%H%M%S')}",
        "script_text": TEST_SCRIPT,
        "music_prompt": MUSIC_PROMPT
    }
    
    result = make_request("POST", "/api/v1/process-script", script_data)
    if not result:
        print("ERROR: Failed to process script")
        return False
    
    video_id = result.get("video_id")
    segments = result.get("segments", [])
    print(f"✓ Script processed successfully")
    print(f"  Video ID: {video_id}")
    print(f"  Segments created: {len(segments)}")
    
    # Step 3: Generate voiceovers for each segment
    print_step(3, "Generating voiceovers for segments")
    voiceover_jobs = []
    
    for i, segment in enumerate(segments):
        segment_id = segment.get("id")
        print(f"\nGenerating voiceover for segment {i+1}/{len(segments)}")
        
        voiceover_data = {
            "segment_id": segment_id,
            "voice_id": "EXAVITQu4vr4xnSDxMaL"  # Default voice
        }
        
        result = make_request("POST", "/api/v1/generate-voiceover", voiceover_data)
        if result and result.get("job_id"):
            voiceover_jobs.append({
                "job_id": result["job_id"],
                "segment_id": segment_id
            })
            print(f"  Job created: {result['job_id']}")
        else:
            print(f"  ERROR: Failed to create voiceover job for segment {segment_id}")
    
    # Wait for voiceover jobs to complete
    print("\n✓ Waiting for all voiceover jobs to complete...")
    completed_jobs = 0
    for job_info in voiceover_jobs:
        result = wait_for_job(job_info["job_id"], max_attempts=20, delay=5)
        if result:
            completed_jobs += 1
    
    print(f"\n✓ Voiceover generation completed: {completed_jobs}/{len(voiceover_jobs)} successful")
    
    # Step 4: Combine segments
    print_step(4, "Combining video segments")
    combine_data = {"video_id": video_id}
    
    result = make_request("POST", "/api/v1/combine-all-segments", combine_data)
    if not result or not result.get("job_id"):
        print("ERROR: Failed to start segment combination")
        return False
    
    combine_job_id = result["job_id"]
    print(f"✓ Combination job created: {combine_job_id}")
    
    # Wait for combination to complete
    result = wait_for_job(combine_job_id)
    if not result:
        print("ERROR: Segment combination failed")
        return False
    
    print("✓ Segments combined successfully")
    
    # Step 5: Generate music
    print_step(5, "Generating background music")
    music_data = {"video_id": video_id}
    
    result = make_request("POST", "/api/v1/generate-music", music_data)
    if not result or not result.get("job_id"):
        print("ERROR: Failed to start music generation")
        return False
    
    music_job_id = result["job_id"]
    print(f"✓ Music generation job created: {music_job_id}")
    
    # Wait for music generation
    result = wait_for_job(music_job_id, max_attempts=30, delay=10)
    if not result:
        print("ERROR: Music generation failed")
        return False
    
    print("✓ Music generated successfully")
    
    # Step 6: Get final video status
    print_step(6, "Retrieving final video information")
    result = make_request("GET", f"/api/v1/videos/{video_id}")
    if result:
        print("\n✓ PRODUCTION TEST COMPLETED SUCCESSFULLY!")
        print(f"\nFinal Video Details:")
        print(f"  Video ID: {video_id}")
        print(f"  Name: {result.get('fields', {}).get('Description', 'N/A')}")
        print(f"  Segments: {result.get('fields', {}).get('# Segments', 'N/A')}")
        return True
    else:
        print("ERROR: Failed to retrieve final video information")
        return False

if __name__ == "__main__":
    success = run_production_test()
    sys.exit(0 if success else 1)
