"""
Utility for sending files to a remote backup location (e.g., local machine).
"""

import requests
import logging
from typing import Optional, Dict
import os

logger = logging.getLogger(__name__)


def send_to_remote_backup(file_data: bytes, filename: str, file_type: str = 'unknown',
                         original_path: Optional[str] = None) -> Optional[Dict]:
    """
    Send a file to a remote backup location.
    
    Args:
        file_data: The file content as bytes
        filename: The filename to save as
        file_type: Type of file (voiceovers, videos, music, images)
        original_path: Original S3 path for reference
        
    Returns:
        Response data from remote server or None if failed/not configured
    """
    # Get configuration from environment
    receiver_url = os.getenv('LOCAL_RECEIVER_URL')
    upload_secret = os.getenv('LOCAL_UPLOAD_SECRET')
    
    if not receiver_url:
        logger.debug("LOCAL_RECEIVER_URL not configured, skipping remote backup")
        return None
    
    if not upload_secret:
        logger.warning("LOCAL_UPLOAD_SECRET not configured, skipping remote backup for security")
        return None
    
    try:
        # Prepare the upload
        files = {'file': (filename, file_data)}
        data = {
            'file_type': file_type,
            'filename': filename
        }
        
        if original_path:
            data['original_path'] = original_path
        
        headers = {
            'X-Upload-Secret': upload_secret
        }
        
        # Send to remote receiver
        response = requests.post(
            f"{receiver_url}/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"File sent to remote backup: {filename} ({file_type})")
            return result
        else:
            logger.error(f"Remote backup failed with status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        logger.debug("Could not connect to remote backup receiver (this is normal if not running)")
        return None
    except Exception as e:
        logger.error(f"Error sending to remote backup: {e}")
        return None


def determine_file_type(filename: str, path: Optional[str] = None) -> str:
    """
    Determine the file type based on filename and path.
    
    Returns: voiceovers, videos, music, images, or unknown
    """
    filename_lower = filename.lower()
    path_lower = (path or '').lower()
    
    # Check by filename patterns
    if 'voiceover' in filename_lower or '.mp3' in filename_lower:
        return 'voiceovers'
    elif 'video' in filename_lower or '.mp4' in filename_lower:
        return 'videos'
    elif 'music' in filename_lower or 'audio' in filename_lower:
        return 'music'
    elif any(ext in filename_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
        return 'images'
    
    # Check by path patterns
    if 'voiceover' in path_lower:
        return 'voiceovers'
    elif 'video' in path_lower:
        return 'videos'
    elif 'music' in path_lower:
        return 'music'
    elif 'image' in path_lower:
        return 'images'
    
    return 'unknown'