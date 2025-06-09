"""
Pydantic models for NCA Toolkit webhook payloads.

Based on the various webhook payload structures observed in the codebase,
NCA can send different formats depending on the operation type.
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator


class NCAOutput(BaseModel):
    """Output object in NCA response for ffmpeg/compose operations."""
    url: Optional[str] = None


class NCAResponseData(BaseModel):
    """Response data that can be either a string URL or a complex object."""
    # For ffmpeg/compose operations
    outputs: Optional[List[NCAOutput]] = None
    
    # Direct URL fields
    url: Optional[str] = None
    output_url: Optional[str] = None
    text_url: Optional[str] = None
    file_url: Optional[str] = None
    
    # Error fields
    error: Optional[str] = None
    message: Optional[str] = None


class NCAWebhookPayload(BaseModel):
    """
    Main NCA webhook payload model.
    
    NCA sends different structures based on operation type:
    1. Priority format: 'code' and 'response' (common for direct callbacks)
    2. Alternative format: 'status' and direct URL fields
    3. Message-based format: 'message' field indicating success/failure
    """
    # Priority 1: Code-based response
    code: Optional[int] = None
    response: Optional[Union[str, Dict[str, Any], List[Dict[str, Any]], NCAResponseData]] = None
    
    # Priority 2: Status-based response
    status: Optional[str] = None
    output_url: Optional[str] = None
    file_url: Optional[str] = None
    url: Optional[str] = None
    
    # Priority 3: Message-based response
    message: Optional[str] = None
    
    # Error fields
    error: Optional[str] = None
    error_details: Optional[str] = None
    
    # Additional fields for tracking
    job_id: Optional[str] = Field(None, alias="jobId")
    
    @validator('response', pre=True, always=True)
    def parse_response(cls, v):
        """Parse response field which can be string, dict, or list."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        elif isinstance(v, dict):
            return NCAResponseData(**v)
        elif isinstance(v, list):
            # Handle list response (e.g., ffmpeg/compose format)
            return v
        return v
    
    def get_status(self) -> Optional[str]:
        """
        Determine job status from various payload formats.
        Returns: 'completed', 'failed', or None
        """
        # Priority 1: Check code
        if self.code is not None:
            if self.code == 200:
                return 'completed'
            elif self.code >= 400:
                return 'failed'
        
        # Priority 2: Check status field
        if self.status:
            status_lower = self.status.lower()
            if status_lower in ['completed', 'success']:
                return 'completed'
            elif status_lower in ['failed', 'error']:
                return 'failed'
        
        # Priority 3: Check message field
        if self.message:
            msg_lower = self.message.lower()
            if 'success' in msg_lower or 'complete' in msg_lower:
                return 'completed'
            elif 'error' in msg_lower or 'fail' in msg_lower:
                return 'failed'
        
        return None
    
    def get_output_url(self) -> Optional[str]:
        """
        Extract output URL from various possible locations.
        Returns the first valid URL found.
        """
        # Check response field first (Priority 1)
        if self.response:
            if isinstance(self.response, str):
                return self.response
            elif isinstance(self.response, list):
                # Handle list response (e.g., ffmpeg/compose with array format)
                if len(self.response) > 0 and isinstance(self.response[0], dict):
                    return self.response[0].get('file_url')
            elif isinstance(self.response, (NCAResponseData, dict)):
                # Handle both NCAResponseData instance and dict
                if isinstance(self.response, dict):
                    # Check ffmpeg/compose structure
                    outputs = self.response.get('outputs', [])
                    if outputs and len(outputs) > 0:
                        if isinstance(outputs[0], dict) and outputs[0].get('url'):
                            return outputs[0]['url']
                        elif hasattr(outputs[0], 'url') and outputs[0].url:
                            return outputs[0].url
                    
                    # Check direct URL fields in response dict
                    return (
                        self.response.get('url') or
                        self.response.get('output_url') or
                        self.response.get('text_url') or
                        self.response.get('file_url')
                    )
                else:
                    # NCAResponseData instance
                    if self.response.outputs and len(self.response.outputs) > 0:
                        if self.response.outputs[0].url:
                            return self.response.outputs[0].url
                    
                    # Check direct URL fields in response
                    return (
                        self.response.url or
                        self.response.output_url or
                        self.response.text_url or
                        self.response.file_url
                    )
        
        # Check root-level URL fields (Priority 2)
        return (
            self.output_url or
            self.file_url or
            self.url
        )
    
    def get_error_message(self) -> Optional[str]:
        """
        Extract error message from various possible locations.
        """
        # Check response for error
        if self.response:
            if isinstance(self.response, dict):
                # Handle dict response
                error_msg = self.response.get('error') or self.response.get('message')
                if error_msg:
                    return error_msg
            elif isinstance(self.response, NCAResponseData):
                if self.response.error:
                    return self.response.error
                elif self.response.message:
                    return self.response.message
            elif isinstance(self.response, str) and self.code and self.code >= 400:
                return self.response
        
        # Check root-level error fields
        return (
            self.error or
            self.error_details or
            (self.message if self.get_status() == 'failed' else None)
        )
    
    class Config:
        allow_population_by_field_name = True  # Allow field population by alias