#!/usr/bin/env python3
"""
Direct test for voiceover generation for a specific segment
"""

import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_voiceover_generation(segment_id: str = "recmXnXCm5tFVAlFo"):
    """Test voiceover generation for a specific segment"""
    
    # Configuration
    base_url = os.getenv('TEST_BASE_URL', 'http://localhost:5000')
    
    print(f"🎤 Testing Voiceover Generation")
    print(f"{'='*50}")
    print(f"Segment ID: {segment_id}")
    print(f"API URL: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # First, let's check API health
    print("1️⃣ Checking API health...")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ API Status: {health_data.get('status', 'unknown')}")
            services = health_data.get('services', {})
            for service, status in services.items():
                emoji = "✅" if status == "connected" else "❌"
                print(f"  {emoji} {service}: {status}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Could not connect to API: {e}")
        return False
    
    print()
    
    # Test voiceover generation
    print("2️⃣ Testing voiceover generation...")
    
    payload = {
        "record_id": segment_id
    }
    
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(
            f"{base_url}/api/v2/generate-voiceover",
            json=payload,
            timeout=60
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Voiceover generated successfully!")
            print(f"Response: {data}")
            
            # Check local backup
            local_backup_path = os.getenv('LOCAL_BACKUP_PATH', './local_backups')
            voiceover_dir = Path(local_backup_path) / 'youtube-video-engine' / 'voiceovers'
            
            print()
            print("3️⃣ Checking local backup...")
            print(f"Looking in: {voiceover_dir}")
            
            # Wait for file to appear
            start_time = time.time()
            timeout = 30
            file_found = False
            
            while time.time() - start_time < timeout:
                if voiceover_dir.exists():
                    for file_path in voiceover_dir.iterdir():
                        if segment_id in file_path.name:
                            print(f"✅ Found file: {file_path.name}")
                            print(f"   Size: {file_path.stat().st_size:,} bytes")
                            print(f"   Modified: {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
                            file_found = True
                            break
                
                if file_found:
                    break
                    
                time.sleep(0.5)
            
            if not file_found:
                print("⚠️  Voiceover file not found in local backup")
                
        elif response.status_code == 403:
            print("❌ 403 Forbidden - Check API authentication")
            print("   Make sure the API is running and accessible")
            print(f"   Response: {response.text}")
        elif response.status_code == 404:
            print("❌ 404 Not Found - Endpoint might not exist")
            print(f"   Response: {response.text}")
        elif response.status_code == 400:
            print("❌ 400 Bad Request")
            print(f"   Response: {response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
        print("   Make sure the API is running at:", base_url)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test voiceover generation")
    parser.add_argument("--segment-id", default="recmXnXCm5tFVAlFo",
                       help="Airtable segment ID to test")
    parser.add_argument("--url", help="API base URL")
    
    args = parser.parse_args()
    
    if args.url:
        os.environ['TEST_BASE_URL'] = args.url
    
    test_voiceover_generation(args.segment_id)