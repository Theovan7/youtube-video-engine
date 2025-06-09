#!/usr/bin/env python3
"""
Main test runner for YouTube Video Engine
Tests API endpoints and validates files in local backups
"""

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_environment.test_framework import VideoEngineTestFramework, WebhookSimulator
from testing_environment.sample_payloads import (
    PAYLOADS, SAMPLE_VIDEO_ID, SAMPLE_SEGMENT_ID, 
    get_payload_with_timestamp, VOICE_IDS
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class VideoEngineTestRunner:
    """Orchestrates test execution"""
    
    def __init__(self, base_url: str = None, local_backup_path: str = None):
        self.base_url = base_url or os.getenv('TEST_BASE_URL', 'http://localhost:5000')
        self.local_backup_path = local_backup_path or os.getenv('LOCAL_BACKUP_PATH', './local_backups')
        self.framework = VideoEngineTestFramework(self.base_url, self.local_backup_path)
        self.webhook_sim = WebhookSimulator(self.base_url)
        
    def test_health_check(self):
        """Test the health check endpoint"""
        print("\n🏥 Testing Health Check...")
        result = self.framework.test_endpoint(
            endpoint="/health",
            method="GET"
        )
        
        if result["response"]["status_code"] == 200:
            services = result["response"]["body"].get("services", {})
            print(f"✅ API is healthy")
            for service, status in services.items():
                emoji = "✅" if status == "connected" else "❌"
                print(f"  {emoji} {service}: {status}")
        else:
            print(f"❌ Health check failed: {result['response']['status_code']}")
            
        return result["response"]["status_code"] == 200
    
    def test_voiceover_generation(self, segment_id: str = None):
        """Test voiceover generation (synchronous)"""
        print("\n🎤 Testing Voiceover Generation...")
        
        # Use provided segment_id or sample
        segment_id = segment_id or SAMPLE_SEGMENT_ID
        
        # Test V2 endpoint (synchronous ElevenLabs)
        payload = {"record_id": segment_id}
        
        result = self.framework.test_endpoint(
            endpoint="/api/v2/generate-voiceover",
            payload=payload,
            expected_files=[
                (segment_id, "voiceovers")  # Expect file with segment ID in name
            ]
        )
        
        if result["success"]:
            print("✅ Voiceover generated successfully")
            for file_info in result["files"]:
                if file_info["found"]:
                    val = file_info["validation"]
                    print(f"  📁 File: {Path(val['path']).name}")
                    print(f"  📏 Size: {val['size']:,} bytes")
                    if "duration" in val:
                        print(f"  ⏱️  Duration: {val['duration']:.1f} seconds")
        else:
            print("❌ Voiceover generation failed")
            if result.get("error"):
                print(f"  Error: {result['error']}")
                
        return result["success"]
    
    def test_ai_image_generation(self, segment_id: str = None):
        """Test AI image generation"""
        print("\n🎨 Testing AI Image Generation...")
        
        segment_id = segment_id or SAMPLE_SEGMENT_ID
        
        payload = {
            "record_id": segment_id,
            "style": "photorealistic",
            "aspect_ratio": "16:9"
        }
        
        result = self.framework.test_endpoint(
            endpoint="/api/v2/generate-ai-image",
            payload=payload,
            expected_files=[
                (segment_id, "images")  # Expect 4 images
            ]
        )
        
        if result["success"]:
            print("✅ AI images generated successfully")
            # Wait a bit more for all 4 images
            time.sleep(2)
            
            # Count images
            image_dir = Path(self.local_backup_path) / "youtube-video-engine" / "images"
            images = list(image_dir.glob(f"*{segment_id}*"))
            print(f"  🖼️  Generated {len(images)} images")
            
            for img in images[:2]:  # Show first 2
                print(f"  📁 {img.name} ({img.stat().st_size:,} bytes)")
        else:
            print("❌ AI image generation failed")
            
        return result["success"]
    
    def test_video_combination(self, segment_id: str = None):
        """Test combining voiceover with video (async with webhook)"""
        print("\n🎬 Testing Video Combination...")
        
        segment_id = segment_id or SAMPLE_SEGMENT_ID
        
        # First, make the combine request
        payload = {"segment_id": segment_id}
        
        result = self.framework.test_endpoint(
            endpoint="/api/v2/combine-segment-media",
            payload=payload
        )
        
        if result["response"]["status_code"] == 202:
            print("✅ Combination job started")
            job_id = result["response"]["body"].get("job_id")
            
            if job_id:
                print(f"  Job ID: {job_id}")
                print("  Simulating webhook callback...")
                
                # Wait a moment
                time.sleep(2)
                
                # Simulate successful webhook
                webhook_response = self.webhook_sim.simulate_nca_callback(
                    job_id=job_id,
                    success=True,
                    output_url=f"https://phi-bucket.nyc3.digitaloceanspaces.com/youtube-video-engine/videos/{segment_id}_combined.mp4"
                )
                
                if webhook_response.status_code == 200:
                    print("  ✅ Webhook processed successfully")
                    
                    # Now wait for the file
                    file_path = self.framework.wait_for_local_file(
                        f"{segment_id}_combined",
                        "videos",
                        timeout=10
                    )
                    
                    if file_path:
                        val = self.framework.validate_file(file_path, "videos")
                        print(f"  📁 Combined video saved: {file_path.name}")
                        print(f"  📏 Size: {val['size']:,} bytes")
                        if "duration" in val:
                            print(f"  ⏱️  Duration: {val['duration']:.1f} seconds")
                        return True
                    else:
                        print("  ❌ Combined video not found in local backup")
                else:
                    print(f"  ❌ Webhook failed: {webhook_response.status_code}")
        else:
            print(f"❌ Combination request failed: {result['response']['status_code']}")
            
        return False
    
    def test_full_pipeline(self, script_text: str = None):
        """Test the complete video production pipeline"""
        print("\n🚀 Testing Full Video Production Pipeline...")
        print("=" * 60)
        
        # Step 1: Process Script (using V1 for simplicity)
        print("\n📝 Step 1: Processing Script...")
        
        script_payload = get_payload_with_timestamp("process_script_v1")
        if script_text:
            script_payload["script_text"] = script_text
            
        result = self.framework.test_endpoint(
            endpoint="/api/v1/process-script",
            payload=script_payload
        )
        
        if not result["success"]:
            print("❌ Script processing failed")
            return False
            
        video_id = result["response"]["body"].get("video_id")
        segments = result["response"]["body"].get("segments", [])
        
        print(f"✅ Script processed: {len(segments)} segments created")
        print(f"  Video ID: {video_id}")
        
        # Step 2: Generate voiceovers for each segment
        print("\n🎤 Step 2: Generating Voiceovers...")
        
        for i, segment in enumerate(segments[:2]):  # Test first 2 segments
            print(f"\n  Segment {i+1}/{len(segments[:2])}: {segment['id']}")
            self.test_voiceover_generation(segment['id'])
            time.sleep(1)  # Rate limiting
            
        # Step 3: Generate AI images
        print("\n🎨 Step 3: Generating AI Images...")
        
        for i, segment in enumerate(segments[:1]):  # Test first segment only
            print(f"\n  Segment {i+1}: {segment['id']}")
            self.test_ai_image_generation(segment['id'])
            
        print("\n✅ Pipeline test completed!")
        print(f"  Check local backups at: {self.local_backup_path}")
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("YouTube Video Engine - Comprehensive Test Suite")
        print("="*60)
        print(f"API URL: {self.base_url}")
        print(f"Local Backup Path: {self.local_backup_path}")
        print(f"Started: {datetime.now().isoformat()}")
        
        # Setup
        self.framework.setup()
        
        # Run tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Voiceover Generation", self.test_voiceover_generation),
            ("AI Image Generation", self.test_ai_image_generation),
            ("Video Combination", self.test_video_combination),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                print(f"\n❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
                
        # Generate report
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")
            
        # Save detailed report
        report = self.framework.generate_report()
        report_path = Path("test_report.txt")
        report_path.write_text(report)
        print(f"\nDetailed report saved to: {report_path}")
        
        # Overall success
        total_passed = sum(1 for _, success in results if success)
        print(f"\nOverall: {total_passed}/{len(results)} tests passed")
        
        return total_passed == len(results)


def main():
    parser = argparse.ArgumentParser(description="Test YouTube Video Engine")
    parser.add_argument("--url", help="API base URL", default="http://localhost:5000")
    parser.add_argument("--backup-path", help="Local backup path", default="./local_backups")
    parser.add_argument("--test", help="Specific test to run", 
                       choices=["health", "voiceover", "image", "combine", "pipeline", "all"],
                       default="all")
    parser.add_argument("--segment-id", help="Segment ID for testing")
    parser.add_argument("--video-id", help="Video ID for testing")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = VideoEngineTestRunner(args.url, args.backup_path)
    
    # Run requested test
    if args.test == "health":
        runner.test_health_check()
    elif args.test == "voiceover":
        runner.test_voiceover_generation(args.segment_id)
    elif args.test == "image":
        runner.test_ai_image_generation(args.segment_id)
    elif args.test == "combine":
        runner.test_video_combination(args.segment_id)
    elif args.test == "pipeline":
        runner.test_full_pipeline()
    else:
        runner.run_all_tests()


if __name__ == "__main__":
    main()