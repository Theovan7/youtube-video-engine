"""
Pydantic models for ElevenLabs API integration.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator


class VoiceSettings(BaseModel):
    """Voice settings for text-to-speech generation."""
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.0, ge=0.0, le=1.0)
    use_speaker_boost: bool = Field(default=True)


class ElevenLabsTTSRequest(BaseModel):
    """Request model for ElevenLabs text-to-speech API."""
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(..., min_length=1)
    model_id: str = Field(default="eleven_monolingual_v1")
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings)
    
    @validator('text')
    def clean_text(cls, v):
        """Clean and validate text."""
        # Remove extra whitespace
        v = ' '.join(v.split())
        return v.strip()


class ElevenLabsTTSResponse(BaseModel):
    """Response model for ElevenLabs text-to-speech API."""
    audio_base64: Optional[str] = None
    audio_url: Optional[HttpUrl] = None
    character_count: int
    voice_id: str
    model_id: str
    
    @validator('audio_base64', 'audio_url')
    def validate_audio_data(cls, v, values):
        """Ensure at least one audio format is provided."""
        if not v and not values.get('audio_base64') and not values.get('audio_url'):
            raise ValueError('Either audio_base64 or audio_url must be provided')
        return v


class Voice(BaseModel):
    """Model for an ElevenLabs voice."""
    voice_id: str
    name: str
    samples: Optional[List[Dict[str, Any]]] = None
    category: Optional[str] = None
    fine_tuning: Optional[Dict[str, Any]] = None
    labels: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    preview_url: Optional[HttpUrl] = None
    available_for_tiers: Optional[List[str]] = None
    settings: Optional[VoiceSettings] = None


class VoicesResponse(BaseModel):
    """Response model for listing available voices."""
    voices: List[Voice]


class HistoryItem(BaseModel):
    """Model for a text-to-speech history item."""
    history_item_id: str
    request_id: str
    voice_id: str
    voice_name: str
    text: str
    date_unix: int
    character_count_change_from: int
    character_count_change_to: int
    content_type: str
    state: str
    settings: Optional[VoiceSettings] = None
    feedback: Optional[Dict[str, Any]] = None


class HistoryResponse(BaseModel):
    """Response model for text-to-speech history."""
    history: List[HistoryItem]
    last_history_item_id: Optional[str] = None
    has_more: bool = False


class UserSubscription(BaseModel):
    """Model for user subscription information."""
    tier: str
    character_count: int
    character_limit: int
    can_extend_character_limit: bool
    allowed_to_extend_character_limit: bool
    next_character_count_reset_unix: int
    voice_limit: int
    max_voice_add_edits: int
    voice_add_edit_counter: int
    professional_voice_limit: int
    can_extend_voice_limit: bool
    can_use_instant_voice_cloning: bool
    can_use_professional_voice_cloning: bool
    currency: Optional[str] = None
    status: str


class UserResponse(BaseModel):
    """Response model for user information."""
    subscription: UserSubscription
    is_new_user: bool
    xi_api_key: str


class ElevenLabsError(BaseModel):
    """Error response from ElevenLabs API."""
    error: str
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None