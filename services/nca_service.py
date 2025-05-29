"""NCA Toolkit service for media processing and file storage."""

import logging
import json
import requests
from typing import Dict, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import get_config
from utils.logger import APILogger
from utils.decorators import retry, rate_limit

logger = logging.getLogger(__name__)
api_logger = APILogger()


class NCAService:
    """Service for interacting with NCA Toolkit API."""
    
    def __init__(self):
        """Initialize NCA service."""
        self.config = get_config()()
        self.api_key = self.config.NCA_API_KEY
        self.base_url = self.config.NCA_BASE_URL
        
        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def check_health(self) -> bool:
        """Check if NCA Toolkit service is healthy."""
        try:
            # Use the NCA Toolkit test endpoint for health check
            # Using a GET request with proper headers
            headers = {'x-api-key': self.api_key}
            response = requests.get(
                f"{self.base_url}/v1/toolkit/test", 
                headers=headers,
                timeout=10  # Increased timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"NCA Toolkit health check failed: {e}")
            return False
    
    @retry(max_attempts=3, exceptions=(requests.RequestException,))
    def upload_file(self, file_data: bytes, filename: str, 
                   content_type: str = 'application/octet-stream') -> Dict:
        """Upload a file directly to S3 storage."""
        try:
            import boto3
            from botocore.client import Config
            
            # Initialize S3 client with DigitalOcean Spaces credentials
            s3_client = boto3.client(
                's3',
                endpoint_url='https://nyc3.digitaloceanspaces.com',
                aws_access_key_id=self.config.NCA_S3_ACCESS_KEY,
                aws_secret_access_key=self.config.NCA_S3_SECRET_KEY,
                config=Config(signature_version='s3v4'),
                region_name=self.config.NCA_S3_REGION
            )
            
            # Generate a unique key for the file
            from datetime import datetime
            import uuid
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            key = f"youtube-video-engine/voiceovers/{timestamp}_{unique_id}_{filename}"
            
            # Upload to S3
            s3_client.put_object(
                Bucket=self.config.NCA_S3_BUCKET_NAME,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                ACL='public-read'  # Make it publicly accessible
            )
            
            # Return the public URL
            public_url = f"https://{self.config.NCA_S3_BUCKET_NAME}.nyc3.digitaloceanspaces.com/{key}"
            
            return {
                'url': public_url,
                'key': key,
                'bucket': self.config.NCA_S3_BUCKET_NAME
            }
            
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'upload_file'})
            raise
    
    def combine_audio_video(self, video_url: str, audio_url: str, 
                          output_filename: str, webhook_url: Optional[str] = None,
                          custom_id: Optional[str] = None) -> Dict:
        """Combine audio and video files using FFmpeg compose endpoint."""
        try:
            # Ensure output filename has proper extension
            if not output_filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                output_filename = f"{output_filename}.mp4"
            
            payload = {
                'inputs': [
                    {'file_url': video_url},
                    {'file_url': audio_url}
                ],
                'filename': output_filename,
                'filters': [
                    {'filter': '[0:v]copy[vout]'},  # Copy video stream
                    {'filter': '[1:a]copy[aout]'}   # Copy audio stream
                ],
                'outputs': [
                    {
                        'options': [
                            {'option': '-map', 'argument': '[vout]'},
                            {'option': '-map', 'argument': '[aout]'},
                            {'option': '-c:v', 'argument': 'copy'},
                            {'option': '-c:a', 'argument': 'aac'},
                            {'option': '-shortest'}
                        ]
                    }
                ]
            }
            
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            if custom_id:
                payload['id'] = custom_id
            
            api_logger.log_api_request('nca', 'combine_audio_video', payload)
            
            # Use correct NCA Toolkit endpoint
            response = self.session.post(
                f"{self.base_url}/v1/ffmpeg/compose",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'combine_audio_video', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'combine_audio_video'})
            raise
    
    def concatenate_videos(self, video_urls: List[str], output_filename: str,
                         webhook_url: Optional[str] = None, 
                         custom_id: Optional[str] = None) -> Dict:
        """Concatenate multiple videos into one using NCA video combine endpoint."""
        try:
            # Ensure output filename has proper extension
            if not output_filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                output_filename = f"{output_filename}.mp4"
            
            payload = {
                'video_urls': video_urls,
                'filename': output_filename,
                'transition': 'none',  # No transition between videos
                'output_format': 'mp4'
            }
            
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            if custom_id:
                payload['id'] = custom_id
            
            api_logger.log_api_request('nca', 'concatenate_videos', payload)
            
            # Use correct NCA Toolkit endpoint
            response = self.session.post(
                f"{self.base_url}/v1/video/combine",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'concatenate_videos', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'concatenate_videos'})
            raise
    
    def add_background_music(self, video_url: str, music_url: str, 
                           output_filename: str, volume_ratio: float = 0.2,
                           webhook_url: Optional[str] = None,
                           custom_id: Optional[str] = None) -> Dict:
        """Add background music to a video using FFmpeg compose endpoint."""
        try:
            # Ensure output filename has proper extension
            if not output_filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                output_filename = f"{output_filename}.mp4"
            
            payload = {
                'inputs': [
                    {'file_url': video_url},
                    {'file_url': music_url}
                ],
                'filename': output_filename,
                'filters': [
                    {'filter': f'[0:a]volume=1.0[a0]'},  # Keep video audio at 100%
                    {'filter': f'[1:a]volume={volume_ratio}[a1]'},  # Reduce music volume
                    {'filter': '[a0][a1]amix=inputs=2:duration=shortest:dropout_transition=2[aout]'}  # Mix both
                ],
                'outputs': [
                    {
                        'options': [
                            {'option': '-map', 'argument': '0:v'},  # Keep original video
                            {'option': '-map', 'argument': '[aout]'},  # Use mixed audio
                            {'option': '-c:v', 'argument': 'copy'},  # Copy video without re-encoding
                            {'option': '-shortest'}  # Stop when shortest input ends
                        ]
                    }
                ]
            }
            
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            if custom_id:
                payload['id'] = custom_id
            
            api_logger.log_api_request('nca', 'add_background_music', payload)
            
            # Use correct NCA Toolkit endpoint
            response = self.session.post(
                f"{self.base_url}/v1/ffmpeg/compose",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'add_background_music', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'add_background_music'})
            raise
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get the status of a processing job using correct NCA endpoint."""
        try:
            api_logger.log_api_request('nca', 'get_job_status', {'job_id': job_id})
            
            # Use correct NCA Toolkit endpoint
            response = self.session.get(
                f"{self.base_url}/v1/job/status/{job_id}"
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'get_job_status', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'get_job_status'})
            raise
