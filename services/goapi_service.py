"""GoAPI service for AI music generation."""

import logging
import requests
from typing import Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import get_config
from utils.logger import APILogger

logger = logging.getLogger(__name__)
api_logger = APILogger()


class GoAPIService:
    """Service for interacting with GoAPI for music generation."""
    
    def __init__(self):
        """Initialize GoAPI service."""
        self.config = get_config()()
        self.api_key = self.config.GOAPI_API_KEY
        self.base_url = self.config.GOAPI_BASE_URL
        
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
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def check_health(self) -> bool:
        """Check if GoAPI service is healthy."""
        try:
            # Check credit balance as a health indicator
            response = self.session.get(f"{self.base_url}/api/v1/generate/credit", timeout=10)
            if response.status_code == 401:
                logger.error(f"GoAPI health check failed: Authentication error - API key may be invalid")
                return False
            elif response.status_code == 200:
                return True
            else:
                logger.error(f"GoAPI health check failed: HTTP {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"GoAPI health check failed: {e}")
            return False
    
    def generate_music(self, prompt: str, duration: int = 180, 
                      webhook_url: Optional[str] = None) -> Dict:
        """Generate music based on prompt."""
        try:
            payload = {
                'prompt': prompt,
                'duration': duration,
                'model': 'suno-v3.5',  # Latest Suno model
                'instrumental': True,  # For background music
                'wait_audio': False  # Use async generation
            }
            
            if webhook_url:
                payload['webhook_url'] = webhook_url
            
            api_logger.log_api_request('goapi', 'generate_music', payload)
            
            response = self.session.post(
                f"{self.base_url}/music/suno",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('goapi', 'generate_music', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('goapi', e, {'operation': 'generate_music'})
            raise
    
    def get_music_status(self, job_id: str) -> Dict:
        """Get status of music generation job."""
        try:
            api_logger.log_api_request('goapi', 'get_music_status', {'job_id': job_id})
            
            response = self.session.get(
                f"{self.base_url}/music/suno/{job_id}"
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('goapi', 'get_music_status', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('goapi', e, {'operation': 'get_music_status'})
            raise
    
    def get_user_info(self) -> Dict:
        """Get user account information."""
        try:
            api_logger.log_api_request('goapi', 'get_user_info', {})
            
            response = self.session.get(f"{self.base_url}/user")
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('goapi', 'get_user_info', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('goapi', e, {'operation': 'get_user_info'})
            raise
    
    def get_available_models(self) -> Dict:
        """Get available music generation models."""
        try:
            api_logger.log_api_request('goapi', 'get_available_models', {})
            
            response = self.session.get(f"{self.base_url}/music/models")
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('goapi', 'get_available_models', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('goapi', e, {'operation': 'get_available_models'})
            raise
