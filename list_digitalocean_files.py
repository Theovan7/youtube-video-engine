#!/usr/bin/env python3
"""
Script to list and optionally download files from DigitalOcean Spaces.
"""

import os
import boto3
from botocore.client import Config
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def list_digitalocean_spaces_files(prefix='', max_keys=100):
    """
    List files in your DigitalOcean Spaces bucket.
    
    Args:
        prefix: Optional prefix to filter files (e.g., 'voiceovers/')
        max_keys: Maximum number of files to list
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
    
    print(f"Listing files in bucket: {bucket_name}")
    if prefix:
        print(f"With prefix: {prefix}")
    print("-" * 80)
    
    try:
        # List objects
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        
        if 'Contents' not in response:
            print("No files found.")
            return []
        
        files = []
        for obj in response['Contents']:
            file_info = {
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'],
                'url': f"https://{bucket_name}.nyc3.digitaloceanspaces.com/{obj['Key']}"
            }
            files.append(file_info)
            
            # Print file info
            print(f"File: {obj['Key']}")
            print(f"  Size: {obj['Size']:,} bytes")
            print(f"  Modified: {obj['LastModified']}")
            print(f"  URL: {file_info['url']}")
            print()
        
        print(f"\nTotal files found: {len(files)}")
        return files
        
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_file_from_spaces(key, local_path=None):
    """
    Download a file from DigitalOcean Spaces.
    
    Args:
        key: The file key/path in the bucket
        local_path: Local path to save the file (defaults to current directory)
    """
    s3_client = boto3.client(
        's3',
        endpoint_url='https://nyc3.digitaloceanspaces.com',
        aws_access_key_id=os.getenv('NCA_S3_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('NCA_S3_SECRET_KEY'),
        config=Config(signature_version='s3v4'),
        region_name='nyc3'
    )
    
    bucket_name = os.getenv('NCA_S3_BUCKET_NAME', 'phi-bucket')
    
    if local_path is None:
        local_path = os.path.basename(key)
    
    try:
        print(f"Downloading {key} to {local_path}...")
        s3_client.download_file(bucket_name, key, local_path)
        print(f"Successfully downloaded to: {local_path}")
        return local_path
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def get_file_content(key):
    """
    Get file content directly from DigitalOcean Spaces without downloading.
    
    Args:
        key: The file key/path in the bucket
    """
    s3_client = boto3.client(
        's3',
        endpoint_url='https://nyc3.digitaloceanspaces.com',
        aws_access_key_id=os.getenv('NCA_S3_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('NCA_S3_SECRET_KEY'),
        config=Config(signature_version='s3v4'),
        region_name='nyc3'
    )
    
    bucket_name = os.getenv('NCA_S3_BUCKET_NAME', 'phi-bucket')
    
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read()
        return content
    except Exception as e:
        print(f"Error getting file content: {e}")
        return None

if __name__ == "__main__":
    print("DigitalOcean Spaces File Listing Tool")
    print("=====================================\n")
    
    # Example usage:
    
    # List all files
    # files = list_digitalocean_spaces_files()
    
    # List only voiceovers
    print("\n📢 Listing voiceovers:")
    voiceover_files = list_digitalocean_spaces_files(prefix='voiceovers/', max_keys=10)
    
    # List only videos
    print("\n🎥 Listing videos:")
    video_files = list_digitalocean_spaces_files(prefix='videos/', max_keys=10)
    
    # List only music
    print("\n🎵 Listing music:")
    music_files = list_digitalocean_spaces_files(prefix='music/', max_keys=10)
    
    # Example: Download a specific file
    # if voiceover_files:
    #     first_file = voiceover_files[0]
    #     download_file_from_spaces(first_file['key'], 'downloaded_voiceover.mp3')
