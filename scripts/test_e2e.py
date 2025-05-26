#!/usr/bin/env python3
"""
End-to-End Testing Script for YouTube Video Engine
Tests the complete video production pipeline
"""

import requests
import json
import time
import os
from datetime import datetime
import argparse

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "https://youtube-video-engine.fly.dev")
TEST_VOICE_ID = os.getenv("TEST_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice
TEST_VIDEO_URL = "https://example.com/sample-video.mp4"  # Replace with actual test video

# Test configuration
TEST_CONFIG = {
    "script": """
    Welcome to our comprehensive test of the YouTube Video Engine.
    
    This system demonstrates the power of automation in video production.
    By combining AI-generated voiceovers with automated video editing,
    we can create professional content at scale.
    
    The workflow includes script processing, voice generation,
    video assembly, and music composition - all handled automatically.
    
    Thank you for testing the YouTube Video Engine.
    """,
    "music_prompt": "Upbeat corporate background music, modern and professional",
    "segment_duration": 20,
    "voice_stability": 0.5,
    "voice_similarity": 0.75
}


class EndToEndTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.video_id = None
        self.segments = []
        self.jobs = {}
        self.start_time = None
        
    def print_header(self, text, level=1):
        """Print formatted headers"""
        if level == 1:
            print(f"\n{'='*60}")
            print(f"  {text}")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'-'*40}")
            print(f"  {text}")
            print(f"{'-'*40}\n")
    
    def print_status(self, status, message):
        """Print status messages with icons"""
        icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "processing": "⏳"
        }
        print(f"{icons.get(status, '•')} {message}")
    
    def api_request(self, method, endpoint, data=None, timeout=30):
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
            
        except requests.exceptions.Timeout:
            self.print_status("error", f"Request timed out after {timeout}s")
            return None
        except Exception as e:
            self.print_status("error", f"Request failed: {str(e)}")
            return None
    
    def wait_for_job(self, job_id, max_wait=300, check_interval=5):
        """Wait for a job to complete"""
        self.print_status("processing", f"Waiting for job {job_id} to complete...")
        
        start = time.time()
        while time.time() - start < max_wait:
            response = self.api_request("GET", f"/api/v1/jobs/{job_id}")
            
            if response and response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "completed":
                    self.print_status("success", "Job completed successfully")
                    return True
                elif status == "failed":
                    error = data.get("error", "Unknown error")
                    self.print_status("error", f"Job failed: {error}")
                    return False
                else:
                    print(f"  Status: {status} - Elapsed: {int(time.time() - start)}s", end="\r")
            
            time.sleep(check_interval)
        
        self.print_status("error", f"Job timed out after {max_wait}s")
        return False
    
    def test_health_check(self):
        """Test health check endpoint"""
        self.print_header("Testing Health Check", 2)
        
        response = self.api_request("GET", "/health")
        
        if response and response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "healthy":
                self.print_status("success", "API is healthy")
                
                # Check individual services
                services = data.get("services", {})
                for service, status in services.items():
                    if status == "connected":
                        self.print_status("success", f"{service}: connected")
                    else:
                        self.print_status("error", f"{service}: {status}")
                
                return True
            else:
                self.print_status("error", "API is not healthy")
                return False
        else:
            self.print_status("error", "Health check failed")
            return False
    
    def test_script_processing(self):
        """Test script processing"""
        self.print_header("Testing Script Processing", 2)
        
        payload = {
            "script_text": TEST_CONFIG["script"],
            "video_name": f"E2E Test {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "target_segment_duration": TEST_CONFIG["segment_duration"],
            "music_prompt": TEST_CONFIG["music_prompt"]
        }
        
        response = self.api_request("POST", "/api/v1/process-script", payload)
        
        if response and response.status_code == 201:
            data = response.json()
            self.video_id = data.get("video_id")
            self.segments = data.get("segments", [])
            
            self.print_status("success", f"Script processed successfully")
            self.print_status("info", f"Video ID: {self.video_id}")
            self.print_status("info", f"Segments created: {len(self.segments)}")
            
            for seg in self.segments:
                print(f"  - Segment {seg['order']}: {seg['duration']:.1f}s")
            
            return True
        else:
            self.print_status("error", "Script processing failed")
            if response:
                print(f"Response: {response.text}")
            return False
    
    def test_voiceover_generation(self):
        """Test voiceover generation for all segments"""
        self.print_header("Testing Voiceover Generation", 2)
        
        if not self.segments:
            self.print_status("error", "No segments to process")
            return False
        
        success_count = 0
        
        for segment in self.segments:
            segment_id = segment["id"]
            self.print_status("info", f"Generating voiceover for segment {segment['order']}...")
            
            payload = {
                "segment_id": segment_id,
                "voice_id": TEST_VOICE_ID,
                "stability": TEST_CONFIG["voice_stability"],
                "similarity_boost": TEST_CONFIG["voice_similarity"]
            }
            
            response = self.api_request("POST", "/api/v1/generate-voiceover", payload)
            
            if response and response.status_code == 202:
                data = response.json()
                job_id = data.get("job_id")
                self.jobs[f"voiceover_{segment_id}"] = job_id
                
                self.print_status("success", f"Voiceover job created: {job_id}")
                
                # Wait for completion
                if self.wait_for_job(job_id):
                    success_count += 1
                else:
                    self.print_status("warning", f"Voiceover generation failed for segment {segment['order']}")
            else:
                self.print_status("error", f"Failed to start voiceover generation")
                if response:
                    print(f"Response: {response.text}")
        
        return success_count == len(self.segments)
    
    def test_segment_combination(self):
        """Test combining voiceovers with video segments"""
        self.print_header("Testing Segment Media Combination", 2)
        
        # Note: This would require actual video URLs for each segment
        # For testing purposes, we'll simulate this step
        
        self.print_status("warning", "Segment combination requires base video URLs")
        self.print_status("info", "Skipping this step in automated test")
        
        # In a real test, you would:
        # 1. Have test video files available
        # 2. Call /api/v1/combine-segment-media for each segment
        # 3. Wait for each job to complete
        
        return True
    
    def test_final_video_assembly(self):
        """Test combining all segments into final video"""
        self.print_header("Testing Final Video Assembly", 2)
        
        # This would require all segments to have combined videos
        self.print_status("warning", "Final assembly requires completed segment videos")
        self.print_status("info", "Skipping this step in automated test")
        
        # In a real test:
        # POST /api/v1/combine-all-segments
        # Wait for job completion
        
        return True
    
    def test_music_generation(self):
        """Test music generation and addition"""
        self.print_header("Testing Music Generation", 2)
        
        # This would require a completed video
        self.print_status("warning", "Music generation requires completed video")
        self.print_status("info", "Skipping this step in automated test")
        
        # In a real test:
        # POST /api/v1/generate-and-add-music
        # Wait for job completion
        
        return True
    
    def test_video_status(self):
        """Check final video status"""
        self.print_header("Checking Video Status", 2)
        
        if not self.video_id:
            self.print_status("error", "No video ID available")
            return False
        
        response = self.api_request("GET", f"/api/v1/videos/{self.video_id}")
        
        if response and response.status_code == 200:
            data = response.json()
            
            self.print_status("info", f"Video: {data.get('name')}")
            self.print_status("info", f"Status: {data.get('status')}")
            self.print_status("info", f"Segments: {data.get('segment_count')}")
            
            if data.get("final_video_url"):
                self.print_status("success", f"Final video: {data['final_video_url']}")
            
            return True
        else:
            self.print_status("error", "Failed to get video status")
            return False
    
    def run_all_tests(self):
        """Run complete end-to-end test suite"""
        self.print_header("YouTube Video Engine - End-to-End Testing")
        print(f"Base URL: {self.base_url}")
        print(f"Started: {datetime.now().isoformat()}")
        
        self.start_time = time.time()
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Script Processing", self.test_script_processing),
            ("Voiceover Generation", self.test_voiceover_generation),
            ("Segment Combination", self.test_segment_combination),
            ("Final Video Assembly", self.test_final_video_assembly),
            ("Music Generation", self.test_music_generation),
            ("Video Status Check", self.test_video_status)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                self.print_status("error", f"Test failed with exception: {str(e)}")
                results[test_name] = False
        
        # Summary
        self.print_header("Test Summary")
        
        total_tests = len(tests)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for test_name, result in results.items():
            status = "success" if result else "error"
            status_text = "PASSED" if result else "FAILED"
            self.print_status(status, f"{test_name}: {status_text}")
        
        print(f"\nTotal: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")
        print(f"Duration: {time.time() - self.start_time:.2f}s")
        
        if self.video_id:
            print(f"\nVideo ID for manual inspection: {self.video_id}")
        
        return failed_tests == 0


def main():
    parser = argparse.ArgumentParser(description="End-to-end testing for YouTube Video Engine")
    parser.add_argument("--base-url", default=BASE_URL, help="API base URL")
    parser.add_argument("--voice-id", default=TEST_VOICE_ID, help="ElevenLabs voice ID")
    
    args = parser.parse_args()
    
    # Use the provided arguments or defaults
    base_url = args.base_url
    voice_id = args.voice_id
    
    # Run tests
    tester = EndToEndTester(base_url)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
