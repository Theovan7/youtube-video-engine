#!/usr/bin/env python3
"""
Test script to verify the remote backup system status and check for recent backups.
"""

import os
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_local_receiver():
    """Check if local receiver is running."""
    print("🔍 Checking local receiver status...")
    try:
        response = requests.get('http://localhost:8181/health', timeout=2)
        if response.status_code == 200:
            print("✅ Local receiver is running")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Timestamp: {data.get('timestamp')}")
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
                public_url = tunnel.get('public_url')
                print(f"✅ Ngrok tunnel is active: {public_url}")
                
                # Get tunnel metrics
                metrics = tunnel.get('metrics', {})
                conns = metrics.get('conns', {})
                print(f"   Connections: {conns.get('count', 0)}")
                return True, public_url
        print("❌ No active ngrok tunnels")
    except:
        print("❌ Ngrok is not running")
        print("   Run: ngrok http 8181")
    return False, None

def check_production_config():
    """Check if production is configured with the correct URL."""
    print("\n🔍 Checking production configuration...")
    local_url = os.getenv('LOCAL_RECEIVER_URL')
    secret = os.getenv('LOCAL_UPLOAD_SECRET')
    
    if local_url:
        print(f"✅ LOCAL_RECEIVER_URL is set: {local_url}")
    else:
        print("❌ LOCAL_RECEIVER_URL is not set in .env")
    
    if secret:
        print("✅ LOCAL_UPLOAD_SECRET is configured")
    else:
        print("❌ LOCAL_UPLOAD_SECRET is not set in .env")
    
    return bool(local_url and secret)

def check_backup_directory():
    """Check backup directory and list recent files."""
    print("\n📁 Checking backup directory...")
    backup_base = "./local_backups/youtube-video-engine"
    
    if not os.path.exists(backup_base):
        print(f"❌ Backup directory does not exist: {backup_base}")
        return False
    
    print(f"✅ Backup directory exists: {backup_base}")
    
    # Check each file type directory
    file_types = ['voiceovers', 'videos', 'music', 'images']
    total_files = 0
    recent_files = []
    
    for file_type in file_types:
        type_dir = os.path.join(backup_base, file_type)
        if os.path.exists(type_dir):
            files = [f for f in os.listdir(type_dir) if os.path.isfile(os.path.join(type_dir, f))]
            if files:
                print(f"\n   📂 {file_type}/: {len(files)} files")
                # Get most recent file
                files_with_time = [(f, os.path.getmtime(os.path.join(type_dir, f))) for f in files]
                files_with_time.sort(key=lambda x: x[1], reverse=True)
                
                # Show last 3 files
                for filename, mtime in files_with_time[:3]:
                    file_path = os.path.join(type_dir, filename)
                    size = os.path.getsize(file_path)
                    mod_datetime = datetime.fromtimestamp(mtime)
                    age = datetime.now() - mod_datetime
                    
                    # Format age
                    if age.days > 0:
                        age_str = f"{age.days}d ago"
                    elif age.seconds > 3600:
                        age_str = f"{age.seconds // 3600}h ago"
                    elif age.seconds > 60:
                        age_str = f"{age.seconds // 60}m ago"
                    else:
                        age_str = f"{age.seconds}s ago"
                    
                    print(f"      - {filename} ({size:,} bytes) - {age_str}")
                    recent_files.append((file_type, filename, mod_datetime))
                
                total_files += len(files)
        else:
            print(f"\n   📂 {file_type}/: Directory not created yet")
    
    print(f"\n📊 Total backup files: {total_files}")
    
    # Check for very recent files (last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_count = sum(1 for _, _, mtime in recent_files if mtime > one_hour_ago)
    
    if recent_count > 0:
        print(f"✅ {recent_count} files backed up in the last hour")
    else:
        print("⚠️  No files backed up in the last hour")
    
    return total_files > 0

def test_production_health():
    """Test if production API is accessible."""
    print("\n🔍 Checking production API...")
    api_url = os.getenv('API_URL', 'https://youtube-video-engine.fly.dev')
    
    try:
        response = requests.get(f"{api_url}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Production API is healthy")
            print(f"   Status: {data.get('status')}")
            print(f"   Environment: {data.get('environment')}")
            return True
        else:
            print(f"❌ Production API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Could not reach production API: {e}")
    
    return False

def main():
    """Run all checks."""
    print("🚀 YouTube Video Engine - Remote Backup System Test")
    print("=" * 60)
    
    # Run all checks
    receiver_ok = check_local_receiver()
    ngrok_ok, ngrok_url = check_ngrok_tunnel()
    config_ok = check_production_config()
    backup_ok = check_backup_directory()
    prod_ok = test_production_health()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    checks = [
        ("Local Receiver", receiver_ok),
        ("Ngrok Tunnel", ngrok_ok),
        ("Environment Config", config_ok),
        ("Backup Directory", backup_ok),
        ("Production API", prod_ok)
    ]
    
    all_ok = all(status for _, status in checks)
    
    for check_name, status in checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {check_name}")
    
    if all_ok:
        print("\n✨ All systems operational! Remote backup is ready.")
        print("\nTo test end-to-end:")
        print("1. Create a voiceover through Airtable")
        print("2. Watch the local receiver logs")
        print("3. Check ./local_backups/youtube-video-engine/voiceovers/")
        
        if ngrok_ok and ngrok_url:
            print(f"\n📌 Make sure production has LOCAL_RECEIVER_URL set to: {ngrok_url}")
    else:
        print("\n⚠️  Some components need attention.")
        
        if not receiver_ok:
            print("\n🔧 Start local receiver:")
            print("   python local_file_receiver.py")
        
        if not ngrok_ok:
            print("\n🔧 Start ngrok tunnel:")
            print("   ngrok http 8181")
            
        if not config_ok:
            print("\n🔧 Configure environment:")
            print("   Add to .env:")
            print("   LOCAL_RECEIVER_URL=<your-ngrok-url>")
            print("   LOCAL_UPLOAD_SECRET=<your-secret>")

if __name__ == "__main__":
    main()