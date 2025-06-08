#!/usr/bin/env python3
"""
Sync files from DigitalOcean Spaces (production) to local backup folder.
This script downloads all files from the production bucket that aren't already
in your local backup folder.
"""

import os
import boto3
from botocore.client import Config
from datetime import datetime
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

def sync_from_spaces(prefix='youtube-video-engine/', dry_run=False):
    """
    Sync files from DigitalOcean Spaces to local backup folder.
    
    Args:
        prefix: Prefix to filter files (default: youtube-video-engine/)
        dry_run: If True, only show what would be downloaded without actually downloading
    """
    # Initialize S3 client for DigitalOcean Spaces
    s3_client = boto3.client(
        's3',
        endpoint_url='https://nyc3.digitaloceanspaces.com',
        aws_access_key_id=os.getenv('NCA_S3_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('NCA_S3_SECRET_KEY'),
        config=Config(signature_version='s3v4'),
        region_name='nyc3'
    )
    
    bucket_name = os.getenv('NCA_S3_BUCKET_NAME', 'phi-bucket')
    local_backup_path = os.getenv('LOCAL_BACKUP_PATH', './local_backups')
    
    print(f"Syncing from: {bucket_name}/{prefix}")
    print(f"Syncing to: {local_backup_path}")
    print("-" * 80)
    
    try:
        # List all objects with the prefix
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        
        downloaded_count = 0
        skipped_count = 0
        total_size = 0
        
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                size = obj['Size']
                
                # Skip if it's a directory marker
                if key.endswith('/'):
                    continue
                
                # Construct local file path
                local_file_path = os.path.join(local_backup_path, key)
                
                # Check if file already exists locally
                if os.path.exists(local_file_path) and os.path.getsize(local_file_path) == size:
                    print(f"✓ Already exists: {key}")
                    skipped_count += 1
                    continue
                
                if dry_run:
                    print(f"Would download: {key} ({size:,} bytes)")
                    downloaded_count += 1
                    total_size += size
                else:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                    
                    # Download the file
                    print(f"↓ Downloading: {key} ({size:,} bytes)...", end='', flush=True)
                    s3_client.download_file(bucket_name, key, local_file_path)
                    print(" Done!")
                    
                    downloaded_count += 1
                    total_size += size
        
        print("\n" + "=" * 80)
        print(f"Summary:")
        print(f"  Files downloaded: {downloaded_count}")
        print(f"  Files skipped (already exist): {skipped_count}")
        print(f"  Total downloaded size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        
        if dry_run:
            print("\nThis was a dry run. Use --sync to actually download files.")
            
    except Exception as e:
        print(f"Error syncing files: {e}")
        return False
    
    return True

def watch_and_sync(interval=60):
    """
    Continuously watch and sync new files every N seconds.
    
    Args:
        interval: Check interval in seconds (default: 60)
    """
    import time
    
    print(f"Starting continuous sync every {interval} seconds...")
    print("Press Ctrl+C to stop")
    
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new files...")
            sync_from_spaces()
            print(f"Next check in {interval} seconds...")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopping sync...")
            break
        except Exception as e:
            print(f"Error during sync: {e}")
            print(f"Retrying in {interval} seconds...")
            time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync files from production to local backup')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without downloading')
    parser.add_argument('--watch', action='store_true', help='Continuously watch and sync files')
    parser.add_argument('--interval', type=int, default=60, help='Watch interval in seconds (default: 60)')
    parser.add_argument('--prefix', default='youtube-video-engine/', help='Prefix to filter files')
    
    args = parser.parse_args()
    
    print("Production File Sync Tool")
    print("========================\n")
    
    if args.watch:
        watch_and_sync(args.interval)
    else:
        sync_from_spaces(prefix=args.prefix, dry_run=args.dry_run)