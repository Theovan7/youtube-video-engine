"""
Pydantic models for NCA Toolkit service integration.
"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, HttpUrl, validator
import json


class MediaInput(BaseModel):
    """Model for media input file."""
    url: HttpUrl
    type: Literal["video", "audio", "image"]
    duration: Optional[float] = Field(None, gt=0)
    
    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is accessible."""
        # In production, might want to check if URL is reachable
        return v


class FFmpegFilter(BaseModel):
    """Model for FFmpeg filter."""
    name: str
    params: Optional[Dict[str, Any]] = None
    
    def to_string(self) -> str:
        """Convert to FFmpeg filter string."""
        if self.params:
            param_str = ":".join(f"{k}={v}" for k, v in self.params.items())
            return f"{self.name}={param_str}"
        return self.name


class CombineMediaRequest(BaseModel):
    """Request model for combining video and audio."""
    video_url: HttpUrl
    audio_url: HttpUrl
    output_format: Literal["mp4", "webm", "mov"] = Field(default="mp4")
    video_codec: Optional[str] = Field(default="libx264")
    audio_codec: Optional[str] = Field(default="aac")
    preset: Optional[str] = Field(default="medium")
    crf: Optional[int] = Field(default=23, ge=0, le=51)
    webhook_url: Optional[HttpUrl] = None
    filters: Optional[List[FFmpegFilter]] = None
    
    @validator('crf')
    def validate_crf(cls, v, values):
        """Validate CRF based on codec."""
        codec = values.get('video_codec', 'libx264')
        if codec == 'libx264' and not (0 <= v <= 51):
            raise ValueError('CRF for H.264 must be between 0 and 51')
        return v


class ConcatenateVideosRequest(BaseModel):
    """Request model for concatenating multiple videos."""
    video_urls: List[HttpUrl] = Field(..., min_items=2)
    output_format: Literal["mp4", "webm", "mov"] = Field(default="mp4")
    video_codec: Optional[str] = Field(default="libx264")
    audio_codec: Optional[str] = Field(default="aac")
    preset: Optional[str] = Field(default="medium")
    transition: Optional[Literal["none", "fade", "dissolve"]] = Field(default="none")
    transition_duration: Optional[float] = Field(default=0.5, gt=0, le=2.0)
    webhook_url: Optional[HttpUrl] = None
    
    @validator('video_urls')
    def validate_video_count(cls, v):
        """Ensure at least 2 videos for concatenation."""
        if len(v) < 2:
            raise ValueError('At least 2 videos required for concatenation')
        return v


class AddMusicRequest(BaseModel):
    """Request model for adding background music to video."""
    video_url: HttpUrl
    music_url: HttpUrl
    music_volume: float = Field(default=0.3, ge=0.0, le=1.0)
    fade_in: Optional[float] = Field(default=2.0, ge=0.0)
    fade_out: Optional[float] = Field(default=2.0, ge=0.0)
    loop_music: bool = Field(default=True)
    output_format: Literal["mp4", "webm", "mov"] = Field(default="mp4")
    webhook_url: Optional[HttpUrl] = None


class MediaInfo(BaseModel):
    """Model for media file information."""
    duration: float
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    bitrate: Optional[int] = None
    size_bytes: Optional[int] = None
    format: str


class NCATaskRequest(BaseModel):
    """Generic NCA task request."""
    operation: Literal["combine", "concatenate", "add_music", "probe"]
    inputs: Union[CombineMediaRequest, ConcatenateVideosRequest, AddMusicRequest]
    priority: Optional[Literal["low", "normal", "high"]] = Field(default="normal")
    webhook_url: Optional[HttpUrl] = None
    metadata: Optional[Dict[str, Any]] = None


class NCATaskResponse(BaseModel):
    """Response model for NCA task creation."""
    task_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    operation: str
    created_at: str
    webhook_url: Optional[HttpUrl] = None
    estimated_duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.dict(exclude_none=True)


class NCAProgressUpdate(BaseModel):
    """Progress update from NCA."""
    task_id: str
    status: Literal["processing", "completed", "failed"]
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    eta_seconds: Optional[float] = None
    message: Optional[str] = None


class NCATaskResult(BaseModel):
    """Result of completed NCA task."""
    task_id: str
    status: Literal["completed", "failed"]
    output_url: Optional[HttpUrl] = None
    output_size_bytes: Optional[int] = None
    processing_time_seconds: float
    media_info: Optional[MediaInfo] = None
    error: Optional[str] = None
    ffmpeg_command: Optional[str] = None
    logs: Optional[List[str]] = None
    
    @validator('output_url')
    def validate_output(cls, v, values):
        """Ensure output_url exists for completed tasks."""
        if values.get('status') == 'completed' and not v:
            raise ValueError('output_url is required for completed tasks')
        return v


class NCAWebhookPayload(BaseModel):
    """Webhook payload from NCA."""
    task_id: str
    operation: str
    status: Literal["completed", "failed", "progress"]
    result: Optional[NCATaskResult] = None
    progress: Optional[NCAProgressUpdate] = None
    timestamp: str
    
    @validator('result', 'progress')
    def validate_payload_type(cls, v, values):
        """Ensure correct payload based on status."""
        status = values.get('status')
        if status in ['completed', 'failed'] and not values.get('result'):
            raise ValueError(f'result is required for {status} status')
        if status == 'progress' and not values.get('progress'):
            raise ValueError('progress is required for progress status')
        return v


class NCAError(BaseModel):
    """Error response from NCA."""
    error: str
    message: str
    code: Optional[str] = None
    task_id: Optional[str] = None
    ffmpeg_error: Optional[str] = None
    command: Optional[str] = None