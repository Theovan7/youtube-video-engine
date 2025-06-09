#!/usr/bin/env python3
"""
Utility to upload test files to S3 for use in testing payloads
This allows you to test with real file URLs
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.nca_service import NCAService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_test_file(file_path: str, file_type: str = None) -> dict:
    """
    Upload a test file to S3 and return the URL
    
    Args:
        file_path: Path to the file to upload
        file_type: Type of file (voiceovers, videos, music, images)
                  If not provided, will be inferred from file extension
    
    Returns:
        Dictionary with upload result including URL
    """
    
    # Initialize NCA service
    nca = NCAService()
    
    # Read file
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # Determine file type if not provided
    if not file_type:
        ext = file_path.suffix.lower()
        if ext in ['.mp3', '.wav', '.m4a']:
            file_type = 'audio'
        elif ext in ['.mp4', '.mov', '.avi']:
            file_type = 'videos'
        elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
            file_type = 'images'
        else:
            file_type = 'misc'
    
    # Determine content type
    content_type_map = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.txt': 'text/plain'
    }
    content_type = content_type_map.get(file_path.suffix.lower(), 'application/octet-stream')
    
    # Upload file
    print(f"Uploading {file_path.name} as {file_type}...")
    
    try:
        result = nca.upload_file(
            file_data=file_data,
            filename=f"test_{file_path.name}",
            content_type=content_type,
            folder=f"test_inputs/{file_type}"
        )
        
        print(f"✅ Upload successful!")
        print(f"URL: {result['url']}")
        print(f"S3 Key: {result['key']}")
        
        if 'local_path' in result:
            print(f"Local backup: {result['local_path']}")
            
        return result
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise


def upload_directory(directory: str, file_type: str = None):
    """Upload all files in a directory"""
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    results = []
    for file_path in dir_path.iterdir():
        if file_path.is_file() and not file_path.name.startswith('.'):
            print(f"\n--- Uploading {file_path.name} ---")
            try:
                result = upload_test_file(str(file_path), file_type)
                results.append({
                    'file': file_path.name,
                    'url': result['url'],
                    'success': True
                })
            except Exception as e:
                results.append({
                    'file': file_path.name,
                    'error': str(e),
                    'success': False
                })
    
    # Print summary
    print("\n" + "="*60)
    print("Upload Summary")
    print("="*60)
    
    for r in results:
        if r['success']:
            print(f"✅ {r['file']}")
            print(f"   URL: {r['url']}")
        else:
            print(f"❌ {r['file']}: {r['error']}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload test files to S3")
    parser.add_argument("path", help="File or directory path to upload")
    parser.add_argument("--type", help="File type (voiceovers, videos, music, images)", 
                       choices=['voiceovers', 'videos', 'music', 'images', 'audio', 'misc'])
    parser.add_argument("--dir", action="store_true", help="Upload entire directory")
    
    args = parser.parse_args()
    
    if args.dir:
        results = upload_directory(args.path, args.type)
    else:
        result = upload_test_file(args.path, args.type)
        
        # Save URL for easy copying
        url_file = Path("test_file_urls.txt")
        with open(url_file, 'a') as f:
            f.write(f"{Path(args.path).name}: {result['url']}\n")
        
        print(f"\nURL saved to: {url_file}")