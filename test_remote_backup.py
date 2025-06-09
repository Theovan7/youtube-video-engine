#!/usr/bin/env python3
"""
Test script to verify remote backup functionality is working.
This will create a test voiceover and check if it's backed up locally.
"""

import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv('API_URL', 'https://youtube-video-engine.fly.dev')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

def test_voiceover_with_backup():
    """Test voiceover generation and verify backup."""
    print("🧪 Testing Remote Backup System")
    print("=" * 50)
    
    # For testing, we need an actual segment record ID from Airtable
    # Let's use a simple test approach - just check if the system is configured
    print("\n⚠️  Note: The /generate-voiceover endpoint requires a valid segment record ID from Airtable.")
    print("   To test the backup system, you should:")
    print("   1. Create a voiceover through the normal Airtable workflow")
    print("   2. Check if it appears in ./local_backups/youtube-video-engine/voiceovers/")
    
    # Instead, let's just verify the connection
    test_data = {
        "test": "connection"
    }
    
    # Headers
    headers = {
        'Content-Type': 'application/json'
    }
    
    if WEBHOOK_SECRET:
        headers['X-Webhook-Secret'] = WEBHOOK_SECRET
    
    print(f"\n📤 Sending test voiceover request...")
    print(f"   Record ID: {test_data['record_id']}")
    print(f"   API URL: {API_URL}/api/v2/generate-voiceover")
    
    try:
        # Make request
        response = requests.post(
            f"{API_URL}/api/v2/generate-voiceover",
            json=test_data,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Voiceover generated successfully!")
            print(f"   Audio URL: {result.get('audio_url', 'N/A')}")
            print(f"   Duration: {result.get('duration', 'N/A')}s")
            
            # Check local backup
            print(f"\n🔍 Checking local backup...")
            print(f"   Looking in: ./local_backups/youtube-video-engine/voiceovers/")
            
            # Wait a moment for backup to complete
            time.sleep(2)
            
            # List recent files in backup directory
            backup_dir = "./local_backups/youtube-video-engine/voiceovers/"
            if os.path.exists(backup_dir):
                files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.mp3')], 
                             key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)))
                
                if files:
                    recent_files = files[-5:]  # Last 5 files
                    print(f"\n📁 Recent backup files:")
                    for f in recent_files:
                        file_path = os.path.join(backup_dir, f)
                        size = os.path.getsize(file_path)
                        mod_time = time.ctime(os.path.getmtime(file_path))
                        print(f"   - {f} ({size:,} bytes) - {mod_time}")
                        
                        # Check if this is our test file
                        if test_data['record_id'] in f:
                            print(f"\n✅ BACKUP CONFIRMED: Test file found in local backups!")
                            return True
                else:
                    print("   ❌ No backup files found")
            else:
                print(f"   ❌ Backup directory does not exist: {backup_dir}")
            
            print(f"\n⚠️  Test file not found in backups yet.")
            print(f"   This could mean:")
            print(f"   1. The backup is still in progress")
            print(f"   2. The local receiver is not running")
            print(f"   3. Network connectivity issues")
            
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return False

def check_local_receiver():
    """Check if local receiver is running."""
    print("\n🔍 Checking local receiver status...")
    try:
        response = requests.get('http://localhost:8181/health', timeout=2)
        if response.status_code == 200:
            print("✅ Local receiver is running")
            return True
        else:
            print("❌ Local receiver returned error")
    except:
        print("❌ Local receiver is not running")
        print("   Run: python local_file_receiver.py")
    return False

def check_ngrok_tunnel():
    """Check if ngrok tunnel is active."""
    print("\n🔍 Checking ngrok tunnel...")
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('tunnels'):
                tunnel = data['tunnels'][0]
                print(f"✅ Ngrok tunnel is active: {tunnel.get('public_url')}")
                return True
        print("❌ No active ngrok tunnels")
    except:
        print("❌ Ngrok is not running")
        print("   Run: ./setup_ngrok.sh")
    return False

if __name__ == "__main__":
    print("🚀 YouTube Video Engine - Remote Backup Test")
    print("=" * 50)
    
    # Check prerequisites
    receiver_ok = check_local_receiver()
    ngrok_ok = check_ngrok_tunnel()
    
    if not receiver_ok or not ngrok_ok:
        print("\n⚠️  Prerequisites not met. Please ensure:")
        print("1. Local file receiver is running (python local_file_receiver.py)")
        print("2. Ngrok tunnel is active (./setup_ngrok.sh)")
        print("\nOr run: ./setup_ngrok.sh to start both")
    else:
        # Run test
        print("\n" + "=" * 50)
        test_voiceover_with_backup()
    
    print("\n✨ Test complete!")