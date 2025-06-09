"""
Pydantic models for ElevenLabs webhook payloads.

Note: ElevenLabs standard TTS API doesn't actually support webhooks.
This module is kept for completeness and potential future use,
but the webhook endpoint is deprecated in favor of synchronous processing.
"""

from typing import Optional
from pydantic import BaseModel


class ElevenLabsWebhookPayload(BaseModel):
    """
    Placeholder model for ElevenLabs webhook payload.
    
    ElevenLabs TTS API does not support webhooks, so this model
    is not actively used. All voice generation is done synchronously.
    """
    status: Optional[str] = None
    message: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields for future compatibility