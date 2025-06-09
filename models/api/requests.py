"""
Pydantic models for API request validation.
Replaces Marshmallow schemas with Pydantic models for better type safety and performance.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


# Base API v1 Request Models (routes.py)

class ProcessScriptRequest(BaseModel):
    """Request model for process script endpoint."""
    script_text: str = Field(..., min_length=1, description="The script text to process")
    video_name: str = Field(default="Untitled Video", description="Name of the video")
    target_segment_duration: int = Field(
        default=30, 
        ge=10, 
        le=300,
        description="Target duration for each segment in seconds"
    )
    music_prompt: Optional[str] = Field(None, description="Prompt for music generation")


class GenerateVoiceoverRequest(BaseModel):
    """Request model for generate voiceover endpoint."""
    segment_id: str = Field(..., description="ID of the segment to generate voiceover for")
    voice_id: str = Field(..., description="ElevenLabs voice ID to use")
    stability: float = Field(default=0.5, ge=0.0, le=1.0, description="Voice stability parameter")
    similarity_boost: float = Field(default=0.5, ge=0.0, le=1.0, description="Voice similarity boost")
    style_exaggeration: float = Field(default=0.0, ge=0.0, le=1.0, description="Style exaggeration level")
    use_speaker_boost: bool = Field(default=True, description="Whether to use speaker boost")


class CombineSegmentMediaRequest(BaseModel):
    """Request model for combine segment media endpoint."""
    segment_id: str = Field(..., description="ID of the segment to combine media for")


class CombineAllSegmentsRequest(BaseModel):
    """Request model for combine all segments endpoint."""
    video_id: str = Field(..., description="ID of the video to combine segments for")


class GenerateAndAddMusicRequest(BaseModel):
    """Request model for generate and add music endpoint."""
    video_id: str = Field(..., description="ID of the video to add music to")
    music_prompt: str = Field(
        default="Calm, instrumental background music suitable for video content",
        description="Prompt for music generation"
    )
    duration: int = Field(default=180, ge=30, le=600, description="Duration of music in seconds")


# API v2 Webhook Request Models (routes_v2.py)

class ProcessScriptWebhookRequest(BaseModel):
    """Request model for webhook-based process script endpoint."""
    record_id: str = Field(..., description="Airtable record ID of the video")


class GenerateVoiceoverWebhookRequest(BaseModel):
    """Request model for webhook-based generate voiceover endpoint."""
    record_id: str = Field(..., description="Airtable record ID of the segment")


class CombineSegmentMediaWebhookRequest(BaseModel):
    """Request model for webhook-based combine segment media endpoint."""
    record_id: str = Field(..., description="Airtable record ID of the segment")


class CombineAllSegmentsWebhookRequest(BaseModel):
    """Request model for webhook-based combine all segments endpoint."""
    record_id: str = Field(..., description="Airtable record ID of the video")


class GenerateAndAddMusicWebhookRequest(BaseModel):
    """Request model for webhook-based generate and add music endpoint."""
    record_id: str = Field(..., description="Airtable record ID of the video")


class AddMusicToVideoWebhookRequest(BaseModel):
    """Request model for webhook-based add music to video endpoint."""
    record_id: str = Field(..., description="Airtable record ID of the video")


class GenerateAIImageWebhookRequest(BaseModel):
    """Request model for webhook-based generate AI image endpoint."""
    segment_id: str = Field(..., description="ID of the segment to generate image for")
    size: str = Field(
        default="1792x1008",
        description="Image size to generate"
    )
    
    @validator('size')
    def validate_size(cls, v):
        """Validate image size is supported."""
        valid_sizes = ['1920x1080', '1792x1008', '1024x576', 'auto']
        if v not in valid_sizes:
            raise ValueError(f"Size must be one of: {', '.join(valid_sizes)}")
        return v


class GenerateVideoWebhookRequest(BaseModel):
    """Request model for webhook-based generate video endpoint."""
    segment_id: str = Field(..., description="ID of the segment to generate video for")
    duration_override: Optional[int] = Field(
        None,
        description="Override duration for video generation"
    )
    aspect_ratio: str = Field(
        default="16:9",
        description="Aspect ratio for the video"
    )
    quality: str = Field(
        default="standard",
        description="Quality level for video generation"
    )
    
    @validator('duration_override')
    def validate_duration(cls, v):
        """Validate duration override is valid."""
        if v is not None and v not in [5, 10]:
            raise ValueError("Duration override must be 5 or 10 seconds")
        return v
    
    @validator('aspect_ratio')
    def validate_aspect_ratio(cls, v):
        """Validate aspect ratio is supported."""
        valid_ratios = ['1:1', '16:9', 'auto']
        if v not in valid_ratios:
            raise ValueError(f"Aspect ratio must be one of: {', '.join(valid_ratios)}")
        return v
    
    @validator('quality')
    def validate_quality(cls, v):
        """Validate quality is supported."""
        valid_qualities = ['standard', 'high']
        if v not in valid_qualities:
            raise ValueError(f"Quality must be one of: {', '.join(valid_qualities)}")
        return v