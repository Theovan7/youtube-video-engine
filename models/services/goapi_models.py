"""
Pydantic models for GoAPI service integration.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime


class VideoGenerationRequest(BaseModel):
    """Request model for GoAPI video generation."""
    prompt: str = Field(..., min_length=1, max_length=2000)
    aspect_ratio: Literal["16:9", "9:16", "1:1", "4:3", "3:4"] = Field(default="16:9")
    duration: Optional[int] = Field(default=None, ge=1, le=60)
    quality: Literal["standard", "high"] = Field(default="standard")
    style: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None
    
    @validator('prompt')
    def clean_prompt(cls, v):
        """Clean and validate prompt."""
        v = ' '.join(v.split())
        return v.strip()


class VideoGenerationResponse(BaseModel):
    """Response model for GoAPI video generation."""
    id: str
    status: Literal["pending", "processing", "completed", "failed"]
    video_url: Optional[HttpUrl] = None
    thumbnail_url: Optional[HttpUrl] = None
    duration: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None
    metadata: Optional[Dict[str, Any]] = None


class MusicGenerationRequest(BaseModel):
    """Request model for GoAPI music generation."""
    prompt: str = Field(..., min_length=1, max_length=1000)
    duration: int = Field(..., ge=1, le=600)  # 1 second to 10 minutes
    genre: Optional[str] = None
    mood: Optional[str] = None
    tempo: Optional[Literal["slow", "medium", "fast"]] = None
    instruments: Optional[List[str]] = None
    webhook_url: Optional[HttpUrl] = None
    
    @validator('prompt')
    def clean_prompt(cls, v):
        """Clean and validate prompt."""
        v = ' '.join(v.split())
        return v.strip()


class MusicGenerationResponse(BaseModel):
    """Response model for GoAPI music generation."""
    id: str
    status: Literal["pending", "processing", "completed", "failed"]
    audio_url: Optional[HttpUrl] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskStatusRequest(BaseModel):
    """Request model for checking task status."""
    task_id: str = Field(..., min_length=1)


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    id: str
    type: Literal["video", "music", "image"]
    status: Literal["pending", "processing", "completed", "failed", "cancelled"]
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    result_url: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in ["completed", "failed", "cancelled"]
    
    def is_successful(self) -> bool:
        """Check if task completed successfully."""
        return self.status == "completed" and self.result_url is not None


class GoAPIWebhookPayload(BaseModel):
    """Webhook payload from GoAPI."""
    task_id: str
    type: Literal["video", "music", "image"]
    status: Literal["completed", "failed"]
    result_url: Optional[HttpUrl] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('result_url')
    def validate_result(cls, v, values):
        """Ensure result_url is provided for completed status."""
        if values.get('status') == 'completed' and not v:
            raise ValueError('result_url is required for completed status')
        return v


class GoAPIError(BaseModel):
    """Error response from GoAPI."""
    error: str
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class VideoMetadata(BaseModel):
    """Metadata for generated video."""
    width: int
    height: int
    fps: float
    codec: str
    bitrate: Optional[int] = None
    size_bytes: int
    
    @property
    def aspect_ratio(self) -> str:
        """Calculate aspect ratio."""
        gcd = self._gcd(self.width, self.height)
        return f"{self.width//gcd}:{self.height//gcd}"
    
    @staticmethod
    def _gcd(a: int, b: int) -> int:
        """Calculate greatest common divisor."""
        while b:
            a, b = b, a % b
        return a


class MusicMetadata(BaseModel):
    """Metadata for generated music."""
    duration_seconds: float
    format: str
    bitrate: int
    sample_rate: int
    channels: int
    size_bytes: int