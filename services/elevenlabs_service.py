"""ElevenLabs service for AI voice generation."""

import logging
import requests
import uuid
from typing import Dict, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import get_config
from utils.logger import APILogger

logger = logging.getLogger(__name__)
api_logger = APILogger()


class ElevenLabsService:
    """Service for interacting with ElevenLabs API."""
    
    def __init__(self):
        """Initialize ElevenLabs service."""
        self.config = get_config()()
        self.api_key = self.config.ELEVENLABS_API_KEY
        self.base_url = self.config.ELEVENLABS_BASE_URL
        
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
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def check_health(self) -> bool:
        """Check if ElevenLabs service is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/voices", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ElevenLabs health check failed: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict]:
        """Get list of available voices."""
        try:
            api_logger.log_api_request('elevenlabs', 'get_available_voices', {})
            
            response = self.session.get(f"{self.base_url}/voices")
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('elevenlabs', 'get_available_voices', 
                                      response.status_code, result)
            
            return result.get('voices', [])
        except Exception as e:
            api_logger.log_error('elevenlabs', e, {'operation': 'get_available_voices'})
            raise
    
    def generate_voice_sync(self, text: str, voice_id: str, 
                           stability: float = 0.5, similarity_boost: float = 0.5,
                           speed: float = 1.0, style_exaggeration: float = 0.0,
                           use_speaker_boost: bool = True) -> Dict:
        """Generate voice synchronously - no webhooks needed.
        
        ElevenLabs standard TTS API does not support webhooks.
        This method performs synchronous text-to-speech conversion.
        """
        try:
            payload = {
                'text': text,
                'model_id': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': stability,
                    'similarity_boost': similarity_boost,
                    'speed': speed,
                    'style_exaggeration': style_exaggeration,
                    'use_speaker_boost': use_speaker_boost
                }
            }
            
            api_logger.log_api_request('elevenlabs', 'generate_voice_sync', {
                'voice_id': voice_id,
                'text_length': len(text)
            })
            
            # Use synchronous endpoint - no webhook support needed
            endpoint = f"{self.base_url}/text-to-speech/{voice_id}"
            headers = {
                'xi-api-key': self.api_key,
                'Content-Type': 'application/json',
                'Accept': 'audio/mpeg'
            }
            
            response = self.session.post(
                endpoint, 
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            # Return audio data immediately
            result = {
                'audio_data': response.content,
                'status': 'completed',
                'request_id': response.headers.get('request-id', str(uuid.uuid4()))
            }
            
            api_logger.log_api_response('elevenlabs', 'generate_voice_sync', 
                                      response.status_code, {
                                          'status': 'success',
                                          'audio_size_bytes': len(response.content)
                                      })
            
            return result
        except Exception as e:
            api_logger.log_error('elevenlabs', e, {'operation': 'generate_voice_sync'})
            raise
    
    def generate_voice(self, text: str, voice_id: str, 
                      stability: float = 0.5, similarity_boost: float = 0.5,
                      speed: float = 1.0, style_exaggeration: float = 0.0,
                      use_speaker_boost: bool = True, # Added use_speaker_boost
                      webhook_url: Optional[str] = None) -> Dict:
        """Generate voice from text.
        
        DEPRECATED: Use generate_voice_sync() instead.
        ElevenLabs standard TTS API does not support webhooks.
        This method now redirects to synchronous processing.
        """
        logger.warning("generate_voice() with webhook_url is deprecated. Use generate_voice_sync() instead.")
        return self.generate_voice_sync(text, voice_id, stability, similarity_boost, speed, style_exaggeration, use_speaker_boost)
    
    def get_voice_settings(self, voice_id: str) -> Dict:
        """Get voice settings."""
        try:
            api_logger.log_api_request('elevenlabs', 'get_voice_settings', 
                                     {'voice_id': voice_id})
            
            response = self.session.get(
                f"{self.base_url}/voices/{voice_id}/settings"
            )
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('elevenlabs', 'get_voice_settings', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('elevenlabs', e, {'operation': 'get_voice_settings'})
            raise
    
    def get_user_info(self) -> Dict:
        """Get user subscription info."""
        try:
            api_logger.log_api_request('elevenlabs', 'get_user_info', {})
            
            response = self.session.get(f"{self.base_url}/user")
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('elevenlabs', 'get_user_info', 
                                      response.status_code, result)
            
            return result
        except Exception as e:
            api_logger.log_error('elevenlabs', e, {'operation': 'get_user_info'})
            raise
    
    def get_history(self) -> List[Dict]:
        """Get generation history."""
        try:
            api_logger.log_api_request('elevenlabs', 'get_history', {})
            
            response = self.session.get(f"{self.base_url}/history")
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('elevenlabs', 'get_history', 
                                      response.status_code, result)
            
            return result.get('history', [])
        except Exception as e:
            api_logger.log_error('elevenlabs', e, {'operation': 'get_history'})
            raise