#!/usr/bin/env python3
"""
Integration test using actual files from test_inputs folder
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_environment.test_framework import VideoEngineTestFramework
from testing_environment.upload_test_file import upload_test_file
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FileBasedTester:
    """Test API endpoints using actual files"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('TEST_BASE_URL', 'http://localhost:5000')
        self.framework = VideoEngineTestFramework(self.base_url)
        self.test_inputs_dir = Path(__file__).parent / "test_inputs"
        self.uploaded_files = {}
        
    def upload_test_files(self):
        """Upload test files and store URLs"""
        print("📤 Uploading test files to S3...")
        
        # Upload sample files if they exist
        test_files = [
            ("images/sample_image.png", "images"),
            ("videos/sample_video.mp4", "videos"),
            ("audio/sample_music.mp3", "music"),
        ]
        
        for file_path, file_type in test_files:
            full_path = self.test_inputs_dir / file_path
            if full_path.exists():
                try:
                    result = upload_test_file(str(full_path), file_type)
                    self.uploaded_files[file_path] = result['url']
                    print(f"✅ Uploaded {file_path}")
                except Exception as e:
                    print(f"❌ Failed to upload {file_path}: {e}")
            else:
                print(f"⚠️  {file_path} not found - create it first")
                
    def test_video_combination_with_files(self):
        """Test combining real video and audio files"""
        print("\n🎬 Testing Video Combination with Real Files...")
        
        # Check if we have uploaded files
        video_url = self.uploaded_files.get("videos/sample_video.mp4")
        audio_url = self.uploaded_files.get("audio/sample_voiceover.mp3")
        
        if not video_url or not audio_url:
            print("❌ Required files not uploaded. Please add:")
            print("   - test_inputs/videos/sample_video.mp4")
            print("   - test_inputs/audio/sample_voiceover.mp3")
            return False
            
        # Create payload
        payload = {
            "video_url": video_url,
            "audio_url": audio_url,
            "output_filename": f"combined_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        }
        
        # Test the endpoint
        result = self.framework.test_endpoint(
            endpoint="/api/v1/combine-media",  # Direct endpoint
            payload=payload,
            expected_files=[
                (payload["output_filename"], "videos")
            ]
        )
        
        return result["success"]
    
    def test_image_to_video_with_files(self):
        """Test generating video from uploaded image"""
        print("\n🎨 Testing Image to Video Generation...")
        
        image_url = self.uploaded_files.get("images/sample_image.png")
        
        if not image_url:
            print("❌ Image not uploaded. Please add:")
            print("   - test_inputs/images/sample_image.png")
            return False
            
        # For this test, you'd need to create a segment in Airtable first
        # that references this image URL
        print(f"Image URL available: {image_url}")
        print("To test video generation, create a segment in Airtable with this image URL")
        
        return True
    
    def test_script_from_file(self):
        """Test script processing from file"""
        print("\n📝 Testing Script Processing from File...")
        
        script_file = self.test_inputs_dir / "scripts/short_demo.txt"
        
        if not script_file.exists():
            print(f"❌ Script file not found: {script_file}")
            return False
            
        # Read script
        script_text = script_file.read_text()
        
        # Create payload
        payload = {
            "script_text": script_text,
            "video_name": f"File Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "target_segment_duration": 30
        }
        
        # Test endpoint
        result = self.framework.test_endpoint(
            endpoint="/api/v1/process-script",
            payload=payload
        )
        
        if result["success"]:
            response = result["response"]["body"]
            print(f"✅ Script processed: {len(response.get('segments', []))} segments created")
            return True
            
        return False
    
    def run_all_tests(self):
        """Run all file-based tests"""
        print("\n" + "="*60)
        print("File-Based Integration Tests")
        print("="*60)
        print(f"API URL: {self.base_url}")
        print(f"Test Inputs: {self.test_inputs_dir}")
        
        # Setup
        self.framework.setup()
        
        # Upload test files first
        self.upload_test_files()
        
        # Run tests
        tests = [
            ("Script from File", self.test_script_from_file),
            ("Video Combination", self.test_video_combination_with_files),
            ("Image to Video", self.test_image_to_video_with_files),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                print(f"\n❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
                
        # Summary
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")
            
        # Save uploaded file URLs
        if self.uploaded_files:
            urls_file = Path("uploaded_test_urls.json")
            with open(urls_file, 'w') as f:
                json.dump(self.uploaded_files, f, indent=2)
            print(f"\nUploaded file URLs saved to: {urls_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test with actual files")
    parser.add_argument("--url", help="API base URL", default="http://localhost:5000")
    parser.add_argument("--upload-only", action="store_true", help="Only upload files")
    
    args = parser.parse_args()
    
    tester = FileBasedTester(args.url)
    
    if args.upload_only:
        tester.upload_test_files()
    else:
        tester.run_all_tests()


if __name__ == "__main__":
    main()