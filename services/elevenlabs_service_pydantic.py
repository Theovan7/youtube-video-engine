"""
ElevenLabs service with Pydantic models.
Example of how to refactor services to use Pydantic models.
"""

import requests
import base64
from typing import Optional
from models.services.elevenlabs_models import (
    ElevenLabsTTSRequest,
    ElevenLabsTTSResponse,
    VoiceSettings,
    ElevenLabsError
)
from config_pydantic import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class ElevenLabsServicePydantic:
    """ElevenLabs service using Pydantic models."""
    
    def __init__(self):
        """Initialize the service."""
        self.settings = get_settings()
        self.api_key = self.settings.elevenlabs_api_key
        self.base_url = self.settings.elevenlabs_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def generate_speech(self, request: ElevenLabsTTSRequest) -> ElevenLabsTTSResponse:
        """
        Generate speech using ElevenLabs API with Pydantic models.
        
        Args:
            request: Pydantic TTS request model
            
        Returns:
            Pydantic TTS response model
            
        Raises:
            ValueError: If API returns an error
        """
        url = f"{self.base_url}/text-to-speech/{request.voice_id}"
        
        # Convert Pydantic model to dict for API call
        payload = {
            "text": request.text,
            "model_id": request.model_id,
            "voice_settings": request.voice_settings.dict()
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            # Get audio data
            audio_data = response.content
            
            # Create response model
            return ElevenLabsTTSResponse(
                audio_base64=base64.b64encode(audio_data).decode('utf-8'),
                character_count=len(request.text),
                voice_id=request.voice_id,
                model_id=request.model_id
            )
            
        except requests.exceptions.HTTPError as e:
            # Parse error response
            error_data = e.response.json()
            error = ElevenLabsError(**error_data)
            
            logger.error(f"ElevenLabs API error: {error.message}")
            raise ValueError(f"ElevenLabs API error: {error.message}")
        
        except Exception as e:
            logger.error(f"Failed to generate speech: {str(e)}")
            raise
    
    def generate_speech_simple(
        self,
        text: str,
        voice_id: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> ElevenLabsTTSResponse:
        """
        Simple interface for generating speech.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            stability: Voice stability setting
            similarity_boost: Voice similarity boost setting
            
        Returns:
            Pydantic TTS response model
        """
        # Create request model
        request = ElevenLabsTTSRequest(
            text=text,
            voice_id=voice_id,
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost
            )
        )
        
        return self.generate_speech(request)


# Example usage
if __name__ == "__main__":
    # Example of using the service with Pydantic models
    service = ElevenLabsServicePydantic()
    
    # Create a request using Pydantic model
    request = ElevenLabsTTSRequest(
        text="Hello, this is a test of Pydantic models.",
        voice_id="EXAVITQu4vr4xnSDxMaL",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            use_speaker_boost=True
        )
    )
    
    # The service handles validation automatically
    try:
        response = service.generate_speech(request)
        print(f"Generated audio with {response.character_count} characters")
    except ValidationError as e:
        print(f"Validation error: {e}")
    except ValueError as e:
        print(f"API error: {e}")