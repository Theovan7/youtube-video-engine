"""
Pydantic models for API responses.
Provides structured, type-safe responses for all API endpoints.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Common response models

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    details: Optional[Any] = Field(None, description="Additional error details")


class SegmentInfo(BaseModel):
    """Information about a segment."""
    id: str = Field(..., description="Segment ID")
    order: int = Field(..., description="Segment order/position")
    text: str = Field(..., description="Segment text content")
    duration: float = Field(..., description="Segment duration in seconds")


# API v1 Response Models

class ProcessScriptResponse(BaseModel):
    """Response model for process script endpoint."""
    video_id: str = Field(..., description="ID of the created video")
    video_name: str = Field(..., description="Name of the video")
    total_segments: int = Field(..., description="Total number of segments created")
    estimated_duration: float = Field(..., description="Total estimated duration in seconds")
    status: str = Field(..., description="Processing status")
    segments: List[SegmentInfo] = Field(..., description="List of created segments")


class GenerateVoiceoverResponse(BaseModel):
    """Response model for generate voiceover endpoint."""
    segment_id: str = Field(..., description="ID of the segment")
    status: str = Field(..., description="Generation status")
    audio_url: str = Field(..., description="URL of the generated audio file")
    duration: float = Field(..., description="Duration of the audio in seconds")
    file_size_bytes: int = Field(..., description="Size of the audio file in bytes")
    voice_id: str = Field(..., description="Voice ID used for generation")


class CombineMediaResponse(BaseModel):
    """Response model for combine media endpoints."""
    status: str = Field(..., description="Combination status")
    message: str = Field(..., description="Status message")
    job_id: Optional[str] = Field(None, description="Job ID for tracking")
    output_url: Optional[str] = Field(None, description="URL of the combined media")


class JobCreatedResponse(BaseModel):
    """Response model for job creation endpoints."""
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    job_id: str = Field(..., description="Created job ID")
    external_job_id: Optional[str] = Field(None, description="External service job ID")


# API v2 Webhook Response Models

class WebhookAcceptedResponse(BaseModel):
    """Response model for webhook endpoints that accept requests for processing."""
    status: str = Field(default="accepted", description="Request status")
    message: str = Field(..., description="Status message")
    job_id: str = Field(..., description="Airtable job ID for tracking")
    external_job_id: Optional[str] = Field(None, description="External service job ID")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for callbacks")


class VoiceoverGeneratedResponse(BaseModel):
    """Response model for synchronous voiceover generation."""
    status: str = Field(default="success", description="Generation status")
    segment_id: str = Field(..., description="ID of the segment")
    audio_url: str = Field(..., description="URL of the generated audio")
    duration: float = Field(..., description="Audio duration in seconds")
    transcript: str = Field(..., description="Text that was converted to speech")


class ProcessScriptWebhookResponse(BaseModel):
    """Response model for webhook-based script processing."""
    status: str = Field(default="success", description="Processing status")
    video_id: str = Field(..., description="ID of the video")
    segments_created: int = Field(..., description="Number of segments created")
    message: str = Field(..., description="Status message")


# Health check and status responses

class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    status: str = Field(default="ok", description="Service status")
    message: str = Field(..., description="Status message")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(default="healthy", description="Service health status")
    services: Dict[str, bool] = Field(..., description="Status of individual services")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")