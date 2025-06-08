#!/usr/bin/env python3
"""
Test script to verify local backup functionality for uploaded files.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.nca_service import NCAService
from config import Config

def test_local_backup():
    """Test uploading a file with local backup enabled."""
    
    # Initialize service
    nca = NCAService()
    
    # Create test data
    test_content = b"This is a test file for local backup functionality."
    test_filename = "test_backup.txt"
    
    print(f"Testing file upload with local backup...")
    print(f"Local backup path: {nca.config.LOCAL_BACKUP_PATH}")
    
    try:
        # Upload file
        result = nca.upload_file(
            file_data=test_content,
            filename=test_filename,
            content_type='text/plain'
        )
        
        print("\nUpload successful!")
        print(f"Remote URL: {result['url']}")
        print(f"S3 Key: {result['key']}")
        
        if 'local_path' in result:
            print(f"Local backup saved to: {result['local_path']}")
            
            # Verify local file exists
            if os.path.exists(result['local_path']):
                with open(result['local_path'], 'rb') as f:
                    saved_content = f.read()
                
                if saved_content == test_content:
                    print("✅ Local backup verified - content matches!")
                else:
                    print("❌ Local backup content mismatch!")
            else:
                print("❌ Local backup file not found!")
        else:
            print("⚠️  No local backup created (LOCAL_BACKUP_PATH not configured)")
            
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Local Backup Test")
    print("=================\n")
    
    # Check if LOCAL_BACKUP_PATH is set
    if os.getenv('LOCAL_BACKUP_PATH'):
        print(f"LOCAL_BACKUP_PATH is set to: {os.getenv('LOCAL_BACKUP_PATH')}")
    else:
        print("LOCAL_BACKUP_PATH not set, using default: ./local_backups")
    
    print()
    test_local_backup()