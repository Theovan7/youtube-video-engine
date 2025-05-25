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
            response = self.session.get(f"{self.base_url}/v1/toolkit/test", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"NCA Toolkit health check failed: {e}")
            return False
    
    @retry(max_attempts=3, exceptions=(requests.RequestException,))
    def upload_file(self, file_data: bytes, filename: str, 
                   content_type: str = 'application/octet-stream') -> Dict:
        """Upload a file to NCA Toolkit storage."""
        try:
            api_logger.log_api_request('nca', 'upload_file', {
                'filename': filename,
                'content_type': content_type,
                'size': len(file_data)
            })
            
            files = {
                'file': (filename, file_data, content_type)
            }
            
            # For file upload, we need to remove Content-Type from headers
            headers = {'X-API-Key': self.api_key}
            
            response = self.session.post(
                f"{self.base_url}/api/upload",
                files=files,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'upload_file', response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'upload_file'})
            raise
    
    def combine_audio_video(self, video_url: str, audio_url: str, 
                          output_filename: str, webhook_url: Optional[str] = None) -> Dict:
        """Combine audio and video files."""
        try:
            payload = {
                'video_url': video_url,
                'audio_url': audio_url,
                'output_filename': output_filename
            }
            
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            api_logger.log_api_request('nca', 'combine_audio_video', payload)
            
            response = self.session.post(
                f"{self.base_url}/api/media/combine",
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
                         webhook_url: Optional[str] = None) -> Dict:
        """Concatenate multiple videos into one."""
        try:
            payload = {
                'video_urls': video_urls,
                'output_filename': output_filename
            }
            
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            api_logger.log_api_request('nca', 'concatenate_videos', payload)
            
            response = self.session.post(
                f"{self.base_url}/api/media/concatenate",
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
                           webhook_url: Optional[str] = None) -> Dict:
        """Add background music to a video."""
        try:
            payload = {
                'video_url': video_url,
                'music_url': music_url,
                'output_filename': output_filename,
                'volume_ratio': volume_ratio
            }
            
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            api_logger.log_api_request('nca', 'add_background_music', payload)
            
            response = self.session.post(
                f"{self.base_url}/api/media/add-music",
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
        """Get the status of a processing job."""
        try:
            api_logger.log_api_request('nca', 'get_job_status', {'job_id': job_id})
            
            response = self.session.get(
                f"{self.base_url}/api/jobs/{job_id}"
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('nca', 'get_job_status', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('nca', e, {'operation': 'get_job_status'})
            raise
