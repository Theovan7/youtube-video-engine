"""
Pydantic models for GoAPI webhook payloads.

GoAPI sends webhooks for various operations including:
- Video generation (Kling AI)
- Music generation
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field


class GoAPIVideo(BaseModel):
    """Video information in GoAPI response."""
    resource: Optional[str] = None
    resource_without_watermark: Optional[str] = None


class GoAPIWork(BaseModel):
    """Work item in GoAPI response for video generation."""
    video: Optional[GoAPIVideo] = None


class GoAPIOutput(BaseModel):
    """Output section of GoAPI response."""
    # For video generation (Kling format)
    works: Optional[List[GoAPIWork]] = None
    
    # Direct URL fields
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    url: Optional[str] = None  # Generic fallback


class GoAPIError(BaseModel):
    """Error information in GoAPI response."""
    message: Optional[str] = None
    raw_message: Optional[str] = None


class GoAPIData(BaseModel):
    """Data section of GoAPI webhook (newer format)."""
    status: Optional[str] = None
    output: Optional[GoAPIOutput] = None
    error: Optional[GoAPIError] = None


class GoAPIWebhookPayload(BaseModel):
    """
    Main GoAPI webhook payload model.
    
    GoAPI sends two formats:
    1. Newer format: data.status, data.output, data.error
    2. Older format: status, output, error at root level
    """
    # Newer format with data wrapper
    data: Optional[GoAPIData] = None
    
    # Older format with fields at root
    status: Optional[str] = None
    output: Optional[GoAPIOutput] = None
    error: Optional[Union[GoAPIError, Dict[str, Any], str]] = None
    
    def get_status(self) -> Optional[str]:
        """Get status from either format."""
        if self.data and self.data.status:
            return self.data.status
        return self.status
    
    def get_video_url(self) -> Optional[str]:
        """Extract video URL from various possible locations."""
        output = self.data.output if self.data else self.output
        
        if output:
            # Check Kling format: works[0].video.resource_without_watermark
            if output.works and len(output.works) > 0:
                work = output.works[0]
                if work.video:
                    return work.video.resource_without_watermark or work.video.resource
            
            # Check direct video_url
            if output.video_url:
                return output.video_url
            
            # Fallback to generic URL
            if output.url:
                return output.url
        
        return None
    
    def get_music_url(self) -> Optional[str]:
        """Extract music/audio URL from various possible locations."""
        output = self.data.output if self.data else self.output
        
        if output:
            # Check audio_url first
            if output.audio_url:
                return output.audio_url
            
            # Fallback to generic URL
            if output.url:
                return output.url
        
        return None
    
    def get_error_message(self) -> Optional[str]:
        """Extract error message from various possible locations."""
        # Check data.error first
        if self.data and self.data.error:
            return self.data.error.message or self.data.error.raw_message
        
        # Check root error
        if self.error:
            if isinstance(self.error, GoAPIError):
                return self.error.message or self.error.raw_message
            elif isinstance(self.error, dict):
                return self.error.get('message', 'Unknown error')
            else:
                return str(self.error)
        
        return None
    
    def is_completed(self) -> bool:
        """Check if the job completed successfully."""
        status = self.get_status()
        return status == 'completed' if status else False
    
    def is_failed(self) -> bool:
        """Check if the job failed."""
        status = self.get_status()
        return status in ['failed', 'error'] if status else False