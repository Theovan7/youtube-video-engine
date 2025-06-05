"""Enhanced GoAPI service with comprehensive logging for troubleshooting."""

import logging
import requests
import time
import json
from typing import Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import get_config
from utils.logger import APILogger

logger = logging.getLogger(__name__)
api_logger = APILogger()


class EnhancedGoAPIService:
    """Enhanced GoAPI service with detailed logging for troubleshooting."""
    
    def __init__(self):
        """Initialize GoAPI service with enhanced logging."""
        self.config = get_config()()
        self.api_key = self.config.GOAPI_API_KEY
        self.base_url = self.config.GOAPI_BASE_URL
        
        # Log initialization details
        logger.info(f"🔧 Initializing GoAPI service:")
        logger.info(f"   Base URL: {self.base_url}")
        logger.info(f"   API Key: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else '[REDACTED]'}")
        
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
            'Content-Type': 'application/json',
            'User-Agent': 'YouTube-Video-Engine/1.0'
        })
        
        logger.info(f"🔧 Session configured with retry strategy: {retry_strategy.total} retries")
        logger.info(f"🔧 Default headers set: {list(self.session.headers.keys())}")
    
    def _log_request_details(self, method: str, url: str, payload: dict = None, headers: dict = None):
        """Log detailed request information."""
        logger.info("="*80)
        logger.info(f"🚀 OUTGOING REQUEST - {method.upper()} {url}")
        logger.info("="*80)
        logger.info(f"📍 Full URL: {url}")
        logger.info(f"🗝️  Method: {method.upper()}")
        
        # Log headers (redact sensitive info)
        effective_headers = self.session.headers.copy()
        if headers:
            effective_headers.update(headers)
        
        safe_headers = {}
        for key, value in effective_headers.items():
            if key.lower() in ['authorization', 'x-api-key']:
                safe_headers[key] = f"{value[:10]}...{value[-4:] if len(value) > 14 else '[REDACTED]'}"
            else:
                safe_headers[key] = value
        
        logger.info(f"📋 Headers: {json.dumps(safe_headers, indent=2)}")
        
        # Log payload
        if payload:
            logger.info(f"📦 Payload size: {len(json.dumps(payload))} characters")
            logger.info(f"📦 Payload: {json.dumps(payload, indent=2)}")
        else:
            logger.info("📦 Payload: None")
        
        logger.info("="*80)
    
    def _log_response_details(self, response: requests.Response, duration: float):
        """Log detailed response information."""
        logger.info("="*80)
        logger.info(f"📥 INCOMING RESPONSE - {response.status_code}")
        logger.info("="*80)
        logger.info(f"⏱️  Duration: {duration:.3f} seconds")
        logger.info(f"🔢 Status Code: {response.status_code}")
        logger.info(f"📍 URL: {response.url}")
        
        # Log response headers
        logger.info(f"📋 Response Headers: {dict(response.headers)}")
        
        # Log response body
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                response_json = response.json()
                logger.info(f"📦 Response Body (JSON): {json.dumps(response_json, indent=2)}")
            else:
                response_text = response.text[:1000]  # First 1000 chars
                logger.info(f"📦 Response Body (Text): {response_text}")
                if len(response.text) > 1000:
                    logger.info(f"📦 (Response truncated - full length: {len(response.text)} chars)")
        except Exception as e:
            logger.warning(f"⚠️  Could not parse response body: {e}")
            logger.info(f"📦 Raw Response: {response.content[:500]}...")
        
        logger.info("="*80)
    
    def _log_exception_details(self, exception: Exception, context: dict = None):
        """Log detailed exception information."""
        logger.error("="*80)
        logger.error(f"💥 EXCEPTION OCCURRED - {type(exception).__name__}")
        logger.error("="*80)
        logger.error(f"🔥 Exception Type: {type(exception).__name__}")
        logger.error(f"🔥 Exception Message: {str(exception)}")
        
        if context:
            logger.error(f"🔍 Context: {json.dumps(context, indent=2)}")
        
        # Log additional details for specific exception types
        if isinstance(exception, requests.exceptions.RequestException):
            logger.error(f"🌐 Request Exception Details:")
            if hasattr(exception, 'response') and exception.response is not None:
                logger.error(f"   Status Code: {exception.response.status_code}")
                logger.error(f"   Response Headers: {dict(exception.response.headers)}")
                try:
                    logger.error(f"   Response Body: {exception.response.text[:500]}")
                except:
                    logger.error(f"   Response Body: [Could not decode]")
            
            if hasattr(exception, 'request') and exception.request is not None:
                logger.error(f"   Request URL: {exception.request.url}")
                logger.error(f"   Request Method: {exception.request.method}")
        
        logger.error("="*80)
    
    def check_health(self) -> bool:
        """Check if GoAPI service is healthy with detailed logging."""
        logger.info("🏥 Starting GoAPI health check...")
        
        try:
            url = f"{self.base_url}/api/v1/generate/credit"
            self._log_request_details("GET", url)
            
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            duration = time.time() - start_time
            
            self._log_response_details(response, duration)
            
            if response.status_code == 401:
                logger.error(f"❌ GoAPI health check failed: Authentication error - API key may be invalid")
                return False
            elif response.status_code == 200:
                logger.info(f"✅ GoAPI health check passed")
                return True
            else:
                logger.error(f"❌ GoAPI health check failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self._log_exception_details(e, {'operation': 'health_check'})
            return False
    
    def generate_video(self, image_url: str, duration: int = 5, 
                      aspect_ratio: str = '16:9', quality: str = 'standard',
                      webhook_url: Optional[str] = None) -> Dict:
        """Generate video from image using Kling model with enhanced logging."""
        
        logger.info("🎬 Starting video generation with enhanced logging...")
        
        try:
            # Map quality to Kling mode
            mode_mapping = {
                'standard': 'std',
                'high': 'pro',
                'pro': 'pro'
            }
            mode = mode_mapping.get(quality, 'std')
            
            # Prepare payload
            payload = {
                'model': 'kling',
                'task_type': 'video_generation',
                'version': '1.6',  # Latest Kling version with 195% improvement
                'mode': mode,
                'effect': 'expansion',
                'aspect_ratio': aspect_ratio,
                'cfg_scale': 0.5,
                'prompt': 'animate the video',
                'duration': duration,
                'image_url': image_url,
                # Camera control settings for natural movement
                'camera_control': {
                    'type': 'simple',
                    'horizontal': 0,
                    'vertical': 2,
                    'pan': -10,
                    'tilt': 0,
                    'roll': 0,
                    'zoom': 0
                }
            }
            
            if webhook_url:
                payload['webhook_url'] = webhook_url
                logger.info(f"🔗 Webhook URL configured: {webhook_url}")
            
            # Log pre-request validation
            logger.info("🔍 Pre-request validation:")
            logger.info(f"   Image URL accessible: {image_url}")
            logger.info(f"   Duration: {duration} seconds")
            logger.info(f"   Quality/Mode: {quality} -> {mode}")
            logger.info(f"   Aspect Ratio: {aspect_ratio}")
            
            # Make the request
            url = f"{self.base_url}/api/v1/task"
            self._log_request_details("POST", url, payload)
            
            api_logger.log_api_request('goapi', 'generate_video', payload)
            
            start_time = time.time()
            
            # Make the actual request
            logger.info("🚀 Sending request to GoAPI...")
            response = self.session.post(
                url,
                json=payload,
                timeout=30  # Shorter timeout for initial request
            )
            
            duration_seconds = time.time() - start_time
            
            self._log_response_details(response, duration_seconds)
            
            # Raise for status to trigger exception handling for HTTP errors
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('goapi', 'generate_video', 
                                      response.status_code, result)
            
            logger.info(f"✅ Video generation request successful!")
            logger.info(f"📊 Response summary:")
            logger.info(f"   Task ID: {result.get('id', 'N/A')}")
            logger.info(f"   Status: {result.get('status', 'N/A')}")
            
            return result
            
        except requests.exceptions.Timeout as e:
            self._log_exception_details(e, {
                'operation': 'generate_video',
                'timeout': 30,
                'url': f"{self.base_url}/api/v1/task"
            })
            api_logger.log_error('goapi', e, {'operation': 'generate_video'})
            raise
            
        except requests.exceptions.ConnectionError as e:
            self._log_exception_details(e, {
                'operation': 'generate_video',
                'url': f"{self.base_url}/api/v1/task",
                'possible_causes': [
                    'Network connectivity issue',
                    'DNS resolution failure', 
                    'Service unavailable',
                    'Firewall blocking request'
                ]
            })
            api_logger.log_error('goapi', e, {'operation': 'generate_video'})
            raise
            
        except requests.exceptions.HTTPError as e:
            self._log_exception_details(e, {
                'operation': 'generate_video',
                'status_code': e.response.status_code if e.response else 'N/A',
                'url': f"{self.base_url}/api/v1/task"
            })
            api_logger.log_error('goapi', e, {'operation': 'generate_video'})
            raise
            
        except Exception as e:
            self._log_exception_details(e, {
                'operation': 'generate_video',
                'payload_size': len(json.dumps(payload)) if 'payload' in locals() else 'N/A'
            })
            api_logger.log_error('goapi', e, {'operation': 'generate_video'})
            raise
    
    def get_video_status(self, task_id: str) -> Dict:
        """Get status of video generation task with enhanced logging."""
        logger.info(f"📊 Checking video status for task: {task_id}")
        
        try:
            url = f"{self.base_url}/api/v1/task/{task_id}"
            self._log_request_details("GET", url)
            
            api_logger.log_api_request('goapi', 'get_video_status', {'task_id': task_id})
            
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            duration = time.time() - start_time
            
            self._log_response_details(response, duration)
            response.raise_for_status()
            
            result = response.json()
            api_logger.log_api_response('goapi', 'get_video_status', 
                                      response.status_code, result)
            
            logger.info(f"✅ Status check successful for task: {task_id}")
            return result
            
        except Exception as e:
            self._log_exception_details(e, {'operation': 'get_video_status', 'task_id': task_id})
            api_logger.log_error('goapi', e, {'operation': 'get_video_status'})
            raise