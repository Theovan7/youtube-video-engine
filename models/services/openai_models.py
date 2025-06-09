"""
Pydantic models for OpenAI API integration.
"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, HttpUrl, validator


class ChatMessage(BaseModel):
    """Model for a chat message."""
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


class ChatCompletionRequest(BaseModel):
    """Request model for OpenAI chat completion."""
    model: str = Field(default="gpt-4")
    messages: List[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1)
    stream: bool = Field(default=False)
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    
    @validator('messages')
    def validate_messages(cls, v):
        """Ensure at least one message is provided."""
        if not v:
            raise ValueError('At least one message is required')
        return v


class Choice(BaseModel):
    """Model for a completion choice."""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Model for token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response model for OpenAI chat completion."""
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None
    
    def get_content(self) -> str:
        """Get the content from the first choice."""
        if self.choices:
            return self.choices[0].message.content
        return ""


class ImageSize(str):
    """Valid image sizes for DALL-E."""
    SIZE_256 = "256x256"
    SIZE_512 = "512x512"
    SIZE_1024 = "1024x1024"
    SIZE_1792x1024 = "1792x1024"
    SIZE_1024x1792 = "1024x1792"


class ImageGenerationRequest(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(..., min_length=1, max_length=4000)
    model: str = Field(default="dall-e-3")
    n: int = Field(default=1, ge=1, le=10)
    quality: Literal["standard", "hd"] = Field(default="standard")
    response_format: Literal["url", "b64_json"] = Field(default="url")
    size: str = Field(default=ImageSize.SIZE_1024)
    style: Literal["natural", "vivid"] = Field(default="vivid")
    user: Optional[str] = None
    
    @validator('size')
    def validate_size(cls, v, values):
        """Validate size based on model."""
        model = values.get('model', 'dall-e-3')
        if model == 'dall-e-2':
            valid_sizes = [ImageSize.SIZE_256, ImageSize.SIZE_512, ImageSize.SIZE_1024]
        else:  # dall-e-3
            valid_sizes = [ImageSize.SIZE_1024, ImageSize.SIZE_1792x1024, ImageSize.SIZE_1024x1792]
        
        if v not in valid_sizes:
            raise ValueError(f"Invalid size {v} for model {model}")
        return v


class ImageData(BaseModel):
    """Model for generated image data."""
    url: Optional[HttpUrl] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None
    
    @validator('url', 'b64_json')
    def validate_image_data(cls, v, values):
        """Ensure at least one format is provided."""
        if not v and not values.get('url') and not values.get('b64_json'):
            raise ValueError('Either url or b64_json must be provided')
        return v


class ImageGenerationResponse(BaseModel):
    """Response model for image generation."""
    created: int
    data: List[ImageData]
    
    def get_image_url(self) -> Optional[str]:
        """Get the URL of the first generated image."""
        if self.data and self.data[0].url:
            return str(self.data[0].url)
        return None


class EmbeddingRequest(BaseModel):
    """Request model for text embeddings."""
    input: Union[str, List[str], List[int], List[List[int]]]
    model: str = Field(default="text-embedding-ada-002")
    encoding_format: Literal["float", "base64"] = Field(default="float")
    user: Optional[str] = None


class EmbeddingData(BaseModel):
    """Model for embedding data."""
    index: int
    embedding: Union[List[float], str]
    object: str = "embedding"


class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: Usage


class OpenAIError(BaseModel):
    """Error response from OpenAI API."""
    error: Dict[str, Any]
    
    @property
    def message(self) -> str:
        """Get error message."""
        return self.error.get('message', 'Unknown error')
    
    @property
    def type(self) -> str:
        """Get error type."""
        return self.error.get('type', 'unknown_error')
    
    @property
    def code(self) -> Optional[str]:
        """Get error code."""
        return self.error.get('code')


class ScriptSegment(BaseModel):
    """Model for a processed script segment."""
    text: str
    order: int
    duration_estimate: float
    word_count: int
    
    @validator('text')
    def clean_text(cls, v):
        """Clean and validate segment text."""
        v = ' '.join(v.split())
        return v.strip()


class ProcessedScript(BaseModel):
    """Model for a fully processed script."""
    segments: List[ScriptSegment]
    total_duration: float
    total_words: int
    ai_image_prompts: Optional[List[str]] = None
    music_prompt: Optional[str] = None
    
    @validator('segments')
    def validate_segments(cls, v):
        """Ensure segments are properly ordered."""
        if not v:
            raise ValueError('At least one segment is required')
        
        # Check order is sequential
        orders = [s.order for s in v]
        expected = list(range(1, len(v) + 1))
        if orders != expected:
            raise ValueError('Segments must have sequential order starting from 1')
        
        return v