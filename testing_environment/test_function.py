#!/usr/bin/env python3
"""
Function-specific test runner for YouTube Video Engine
Tests individual API endpoints with prepared test data
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_environment.test_framework import VideoEngineTestFramework, WebhookSimulator
from testing_environment.upload_test_file import upload_test_file
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FunctionTester:
    """Test specific API functions with prepared test data"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('TEST_BASE_URL', 'http://localhost:5000')
        self.framework = VideoEngineTestFramework(self.base_url)
        self.webhook_sim = WebhookSimulator(self.base_url)
        self.test_inputs_dir = Path(__file__).parent / "test_inputs"
        
    def load_payload(self, payload_path: str) -> dict:
        """Load payload from JSON file"""
        with open(payload_path, 'r') as f:
            return json.load(f)
    
    def prepare_files(self, function_name: str) -> dict:
        """Upload necessary files for a function test"""
        uploaded = {}
        function_dir = self.test_inputs_dir / function_name
        
        # Define which subdirectories to check for each function
        upload_dirs = {
            "combine-segment-media": ["test_videos", "test_audio"],
            "generate-video": ["source_images"],
            "combine-all-segments": ["segment_videos"],
            "generate-and-add-music": ["test_videos", "music_samples"]
        }
        
        if function_name in upload_dirs:
            for subdir in upload_dirs[function_name]:
                dir_path = function_dir / subdir
                if dir_path.exists():
                    for file_path in dir_path.iterdir():
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            print(f"📤 Uploading {file_path.name}...")
                            try:
                                result = upload_test_file(str(file_path))
                                uploaded[file_path.name] = result['url']
                            except Exception as e:
                                print(f"❌ Failed to upload {file_path.name}: {e}")
                                
        return uploaded
    
    def test_process_script(self, payload_file: str = None):
        """Test script processing"""
        print("\n📝 Testing Script Processing...")
        
        # Load script
        script_file = self.test_inputs_dir / "process-script/scripts/short_demo.txt"
        if not script_file.exists():
            # Create default script
            script_file.parent.mkdir(parents=True, exist_ok=True)
            script_file.write_text("""Welcome to our automated video production demo.

This technology transforms simple text into engaging videos.

Watch as AI brings your words to life with stunning visuals.

The future of content creation is here.""")
        
        script_text = script_file.read_text()
        
        # Load or create payload
        if payload_file:
            payload = self.load_payload(payload_file)
        else:
            payload = {
                "script_text": script_text,
                "video_name": f"Function Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "target_segment_duration": 30
            }
        
        # Test endpoint
        result = self.framework.test_endpoint(
            endpoint="/api/v1/process-script",
            payload=payload
        )
        
        if result["success"]:
            segments = result["response"]["body"].get("segments", [])
            print(f"✅ Created {len(segments)} segments")
            
            # Save segment IDs for subsequent tests
            segment_ids_file = self.test_inputs_dir / "process-script/generated_segment_ids.json"
            segment_ids_file.parent.mkdir(exist_ok=True)
            with open(segment_ids_file, 'w') as f:
                json.dump({
                    "video_id": result["response"]["body"].get("video_id"),
                    "segment_ids": [s["id"] for s in segments]
                }, f, indent=2)
            print(f"💾 Saved segment IDs to: {segment_ids_file}")
            
        return result["success"]
    
    def test_generate_voiceover(self, payload_file: str = None):
        """Test voiceover generation"""
        print("\n🎤 Testing Voiceover Generation...")
        
        # Load or create payload
        if payload_file:
            payload = self.load_payload(payload_file)
            segment_id = payload.get("record_id")
        else:
            # Try to load segment ID from previous test
            segment_ids_file = self.test_inputs_dir / "process-script/generated_segment_ids.json"
            segment_id = None
            
            if segment_ids_file.exists():
                with open(segment_ids_file, 'r') as f:
                    data = json.load(f)
                    if data.get("segment_ids"):
                        segment_id = data["segment_ids"][0]
            
            if not segment_id:
                print("⚠️  No segment ID found. Run process-script test first or provide a payload file.")
                return False
                
            payload = {"record_id": segment_id}
        
        # Test endpoint
        result = self.framework.test_endpoint(
            endpoint="/api/v2/generate-voiceover",
            payload=payload,
            expected_files=[(segment_id, "voiceovers")]
        )
        
        return result["success"]
    
    def test_combine_segment_media(self, payload_file: str = None):
        """Test combining audio and video"""
        print("\n🎬 Testing Segment Media Combination...")
        
        # Upload test files
        uploaded = self.prepare_files("combine-segment-media")
        
        if len(uploaded) < 2:
            print("❌ Need both video and audio files for testing")
            return False
        
        # Get URLs
        video_url = next((url for name, url in uploaded.items() if "video" in name), None)
        audio_url = next((url for name, url in uploaded.items() if "audio" in name or "voiceover" in name), None)
        
        if not video_url or not audio_url:
            print("❌ Could not identify video and audio files")
            return False
        
        # Create test payload
        payload = {
            "video_url": video_url,
            "audio_url": audio_url,
            "output_filename": f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        }
        
        print(f"🎥 Video: {video_url}")
        print(f"🎵 Audio: {audio_url}")
        
        # Test direct combination endpoint
        result = self.framework.test_endpoint(
            endpoint="/api/v1/combine-media",
            payload=payload
        )
        
        if result["response"]["status_code"] == 202:
            print("⏳ Async job started, simulating webhook...")
            job_id = result["response"]["body"].get("job_id")
            
            # Wait and simulate webhook
            time.sleep(2)
            webhook_response = self.webhook_sim.simulate_nca_callback(
                job_id=job_id,
                success=True,
                output_url=f"https://example.com/combined/{payload['output_filename']}"
            )
            
            if webhook_response.status_code == 200:
                print("✅ Webhook processed successfully")
                return True
                
        return result["success"]
    
    def test_generate_ai_image(self, payload_file: str = None):
        """Test AI image generation"""
        print("\n🎨 Testing AI Image Generation...")
        
        # Need a segment ID
        segment_ids_file = self.test_inputs_dir / "process-script/generated_segment_ids.json"
        if segment_ids_file.exists():
            with open(segment_ids_file, 'r') as f:
                data = json.load(f)
                segment_id = data.get("segment_ids", [None])[0]
        else:
            print("⚠️  No segment ID found. Run process-script test first.")
            return False
        
        payload = {
            "record_id": segment_id,
            "style": "photorealistic",
            "aspect_ratio": "16:9"
        }
        
        result = self.framework.test_endpoint(
            endpoint="/api/v2/generate-ai-image",
            payload=payload,
            expected_files=[(segment_id, "images")]
        )
        
        return result["success"]
    
    def run_function_test(self, function_name: str, payload_file: str = None):
        """Run test for specific function"""
        
        # Map function names to test methods
        test_map = {
            "process-script": self.test_process_script,
            "generate-voiceover": self.test_generate_voiceover,
            "generate-ai-image": self.test_generate_ai_image,
            "combine-segment-media": self.test_combine_segment_media,
        }
        
        if function_name not in test_map:
            print(f"❌ Unknown function: {function_name}")
            print(f"Available functions: {', '.join(test_map.keys())}")
            return False
        
        # Setup
        self.framework.setup()
        
        # Run test
        print(f"\n{'='*60}")
        print(f"Testing Function: {function_name}")
        print(f"{'='*60}")
        
        try:
            success = test_map[function_name](payload_file)
            
            # Generate report
            report = self.framework.generate_report()
            report_file = f"test_report_{function_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\n📄 Report saved to: {report_file}")
            
            return success
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test specific API functions")
    parser.add_argument("--function", "-f", required=True,
                       help="Function to test (e.g., process-script, generate-voiceover)")
    parser.add_argument("--payload", "-p", help="Path to payload JSON file")
    parser.add_argument("--url", help="API base URL", default="http://localhost:5000")
    parser.add_argument("--list", action="store_true", help="List available functions")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available functions to test:")
        functions = [
            "process-script",
            "generate-voiceover", 
            "generate-ai-image",
            "generate-video",
            "combine-segment-media",
            "combine-all-segments",
            "generate-and-add-music"
        ]
        for f in functions:
            print(f"  - {f}")
        return
    
    tester = FunctionTester(args.url)
    success = tester.run_function_test(args.function, args.payload)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()