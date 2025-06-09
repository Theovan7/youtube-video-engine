"""
Pydantic models for Airtable records.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime


class AirtableRecord(BaseModel):
    """Base model for Airtable records."""
    id: str = Field(..., regex=r'^rec[a-zA-Z0-9]{14}$')
    created_time: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        extra = 'allow'  # Allow extra fields from Airtable


class VideoRecord(AirtableRecord):
    """Model for Videos table record."""
    description: str = Field(..., alias='Description')
    video_script: Optional[str] = Field(None, alias='Video Script')
    script_segments: Optional[List[str]] = Field(None, alias='Script Segments')
    production_video: Optional[List[HttpUrl]] = Field(None, alias='Production Video')
    music: Optional[List[HttpUrl]] = Field(None, alias='Music')
    thumbnail: Optional[List[HttpUrl]] = Field(None, alias='Thumbnail')
    duration: Optional[float] = Field(None, alias='Duration')
    status: Optional[str] = Field(None, alias='Status')
    music_prompt: Optional[str] = Field(None, alias='Music Prompt')
    target_segment_duration: Optional[int] = Field(None, alias='Target Segment Duration')
    
    @validator('script_segments', pre=True)
    def parse_segments(cls, v):
        """Parse segment IDs from Airtable."""
        if isinstance(v, list):
            return v
        return []
    
    @validator('production_video', 'music', 'thumbnail', pre=True)
    def parse_attachments(cls, v):
        """Parse attachment URLs from Airtable format."""
        if not v:
            return []
        if isinstance(v, list):
            urls = []
            for item in v:
                if isinstance(item, dict) and 'url' in item:
                    urls.append(item['url'])
                elif isinstance(item, str):
                    urls.append(item)
            return urls
        return []
    
    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name = True


class SegmentRecord(AirtableRecord):
    """Model for Script Segments table record."""
    srt_text: str = Field(..., alias='SRT Text')
    videos: Optional[List[str]] = Field(None, alias='Videos')
    voiceover: Optional[List[HttpUrl]] = Field(None, alias='Voiceover')
    video: Optional[List[HttpUrl]] = Field(None, alias='Video')
    voiceover_video: Optional[List[HttpUrl]] = Field(None, alias='Voiceover + Video')
    ai_image: Optional[List[HttpUrl]] = Field(None, alias='AI Image')
    order: Optional[int] = Field(None, alias='Order')
    duration: Optional[float] = Field(None, alias='Duration')
    status: Optional[str] = Field(None, alias='Status')
    voiceover_url: Optional[HttpUrl] = Field(None, alias='Voiceover URL')
    video_url: Optional[HttpUrl] = Field(None, alias='Video URL')
    combined_url: Optional[HttpUrl] = Field(None, alias='Combined URL')
    
    @validator('videos', pre=True)
    def parse_video_ids(cls, v):
        """Parse video IDs from Airtable."""
        if isinstance(v, list):
            return v
        return []
    
    @validator('voiceover', 'video', 'voiceover_video', 'ai_image', pre=True)
    def parse_attachments(cls, v):
        """Parse attachment URLs from Airtable format."""
        if not v:
            return []
        if isinstance(v, list):
            urls = []
            for item in v:
                if isinstance(item, dict) and 'url' in item:
                    urls.append(item['url'])
                elif isinstance(item, str):
                    urls.append(item)
            return urls
        return []
    
    def has_voiceover(self) -> bool:
        """Check if segment has voiceover."""
        return bool(self.voiceover or self.voiceover_url)
    
    def has_video(self) -> bool:
        """Check if segment has video."""
        return bool(self.video or self.video_url)
    
    def has_combined(self) -> bool:
        """Check if segment has combined media."""
        return bool(self.voiceover_video or self.combined_url)
    
    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name = True


class JobRecord(AirtableRecord):
    """Model for Jobs table record."""
    type: str = Field(..., alias='Type')
    status: str = Field(..., alias='Status')
    service: Optional[str] = Field(None, alias='Service')
    external_job_id: Optional[str] = Field(None, alias='External Job ID')
    webhook_url: Optional[HttpUrl] = Field(None, alias='Webhook URL')
    request_payload: Optional[Dict[str, Any]] = Field(None, alias='Request Payload')
    response_payload: Optional[Dict[str, Any]] = Field(None, alias='Response Payload')
    error_message: Optional[str] = Field(None, alias='Error Message')
    started_at: Optional[datetime] = Field(None, alias='Started At')
    completed_at: Optional[datetime] = Field(None, alias='Completed At')
    video: Optional[List[str]] = Field(None, alias='Video')
    segment: Optional[List[str]] = Field(None, alias='Segment')
    result_url: Optional[HttpUrl] = Field(None, alias='Result URL')
    retry_count: Optional[int] = Field(None, alias='Retry Count')
    
    @validator('request_payload', 'response_payload', pre=True)
    def parse_json_payload(cls, v):
        """Parse JSON payloads from string if needed."""
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except:
                return v
        return v
    
    @validator('video', 'segment', pre=True)
    def parse_record_ids(cls, v):
        """Parse record IDs from Airtable."""
        if isinstance(v, list):
            return v
        return []
    
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status.lower() in ['completed', 'failed']
    
    def is_successful(self) -> bool:
        """Check if job completed successfully."""
        return self.status.lower() == 'completed'
    
    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name = True


class AirtableResponse(BaseModel):
    """Model for Airtable API response."""
    records: List[Dict[str, Any]]
    offset: Optional[str] = None
    
    def to_models(self, model_class: type) -> List[Any]:
        """Convert records to Pydantic models."""
        models = []
        for record in self.records:
            try:
                # Combine id and fields for the model
                data = {'id': record['id'], **record.get('fields', {})}
                if 'createdTime' in record:
                    data['created_time'] = record['createdTime']
                models.append(model_class(**data))
            except Exception as e:
                # Log error but continue processing other records
                print(f"Error parsing record {record.get('id')}: {e}")
        return models


class AirtableError(BaseModel):
    """Error response from Airtable API."""
    error: Dict[str, Any]
    
    @property
    def type(self) -> str:
        """Get error type."""
        return self.error.get('type', 'UNKNOWN_ERROR')
    
    @property
    def message(self) -> str:
        """Get error message."""
        return self.error.get('message', 'Unknown error occurred')