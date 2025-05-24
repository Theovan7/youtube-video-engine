"""Test script to verify YouTube Video Engine endpoints."""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"  # Change to production URL when deployed
API_KEY = "test-api-key"  # Not used yet, but ready for auth implementation

# Test data
TEST_SCRIPT = """
Welcome to our YouTube video creation tutorial. In this video, we'll explore how to create engaging content for your audience. 

First, let's talk about the importance of a good hook. Your opening seconds are crucial for capturing viewer attention.

Next, we'll discuss the main content. Keep your message clear and concise. Break complex topics into digestible segments.

Finally, always end with a clear call to action. Tell your viewers what you want them to do next.

Thank you for watching! Don't forget to like and subscribe for more content.
"""

def test_health_check():
    """Test the health check endpoint."""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_process_script():
    """Test the process script endpoint."""
    print("\n=== Testing Process Script ===")
    
    payload = {
        "script_text": TEST_SCRIPT,
        "video_name": "Test Video Tutorial",
        "target_segment_duration": 30,
        "music_prompt": "Upbeat tutorial background music"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/process-script",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        data = response.json()
        return data.get('video_id'), data.get('segments', [])
    return None, []


def test_job_status(job_id):
    """Test the job status endpoint."""
    print(f"\n=== Testing Job Status for {job_id} ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_video_details(video_id):
    """Test the video details endpoint."""
    print(f"\n=== Testing Video Details for {video_id} ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/videos/{video_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_video_segments(video_id):
    """Test the video segments endpoint."""
    print(f"\n=== Testing Video Segments for {video_id} ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/videos/{video_id}/segments")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def run_tests():
    """Run all tests."""
    print("Starting YouTube Video Engine Tests")
    print("=" * 50)
    
    # Test health check
    health_ok = test_health_check()
    if not health_ok:
        print("\n❌ Health check failed. Is the server running?")
        return
    
    # Test process script
    video_id, segments = test_process_script()
    if not video_id:
        print("\n❌ Process script failed")
        return
    
    print(f"\n✅ Created video with ID: {video_id}")
    print(f"✅ Created {len(segments)} segments")
    
    # Wait a bit for processing
    time.sleep(2)
    
    # Test video details
    if test_video_details(video_id):
        print("\n✅ Video details retrieved successfully")
    
    # Test video segments
    if test_video_segments(video_id):
        print("\n✅ Video segments retrieved successfully")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    
    # Next steps
    print("\nNext steps to test the full pipeline:")
    print("1. Generate voiceovers for each segment")
    print("2. Combine voiceovers with base videos")
    print("3. Concatenate all segments")
    print("4. Generate and add background music")
    print("\nEach step requires external API keys (ElevenLabs, GoAPI) and base video URLs")


if __name__ == "__main__":
    run_tests()
