"""Base test configuration and utilities."""

import os
import pytest
from unittest.mock import Mock
from datetime import datetime
import json

# Test configuration
TEST_VIDEO_ID = "test_video_123"
TEST_SEGMENT_ID = "test_segment_456"
TEST_JOB_ID = "test_job_789"
TEST_WEBHOOK_EVENT_ID = "test_event_101"

# Sample test data
SAMPLE_SCRIPT = """
Welcome to our comprehensive tutorial on artificial intelligence.

In this first segment, we'll explore the fundamental concepts of AI and machine learning. These technologies are transforming how we interact with computers.

Next, let's discuss neural networks. These are computational models inspired by the human brain. They consist of interconnected nodes that process information.

Moving on to practical applications. AI is being used in healthcare, finance, transportation, and many other industries. The possibilities are endless.

Finally, we'll look at the future of AI. As technology advances, we can expect even more impressive capabilities and applications.

Thank you for joining us on this journey into the world of artificial intelligence.
"""

SAMPLE_VIDEO_DATA = {
    'id': TEST_VIDEO_ID,
    'fields': {
        'Name': 'AI Tutorial Video',
        'Script': SAMPLE_SCRIPT,
        'Status': 'pending',
        'Music Prompt': 'Tech-inspired background music',
        'Created': datetime.now().isoformat()
    }
}

SAMPLE_SEGMENT_DATA = {
    'id': TEST_SEGMENT_ID,
    'fields': {
        'Name': 'Segment 1',
        'Video': [TEST_VIDEO_ID],
        'Text': 'Welcome to our comprehensive tutorial on artificial intelligence.',
        'Order': 1,
        'Start Time': 0,
        'End Time': 30,
        'Duration': 30,
        'Voice ID': 'test_voice_id',
        'Status': 'pending'
    }
}

SAMPLE_JOB_DATA = {
    'id': TEST_JOB_ID,
    'fields': {
        'Job ID': 'job_123456',
        'Type': 'voiceover',
        'Status': 'processing',
        'Related Video': [TEST_VIDEO_ID],
        'Related Segment': [TEST_SEGMENT_ID],
        'External Job ID': 'ext_job_123',
        'Webhook URL': 'http://localhost:5000/webhooks/test',
        'Request Payload': json.dumps({'test': 'data'}),
        'Created': datetime.now().isoformat()
    }
}


def create_mock_airtable_service():
    """Create a mock Airtable service for testing."""
    mock = Mock()
    
    # Mock video operations
    mock.create_video.return_value = SAMPLE_VIDEO_DATA
    mock.get_video.return_value = SAMPLE_VIDEO_DATA
    mock.update_video.return_value = SAMPLE_VIDEO_DATA
    mock.update_video_status.return_value = SAMPLE_VIDEO_DATA
    
    # Mock segment operations
    mock.create_segment.return_value = SAMPLE_SEGMENT_DATA
    mock.get_segment.return_value = SAMPLE_SEGMENT_DATA
    mock.update_segment.return_value = SAMPLE_SEGMENT_DATA
    mock.get_video_segments.return_value = [SAMPLE_SEGMENT_DATA]
    
    # Mock job operations
    mock.create_job.return_value = SAMPLE_JOB_DATA
    mock.get_job.return_value = SAMPLE_JOB_DATA
    mock.update_job.return_value = SAMPLE_JOB_DATA
    mock.complete_job.return_value = SAMPLE_JOB_DATA
    mock.fail_job.return_value = SAMPLE_JOB_DATA
    
    # Mock webhook operations
    mock.create_webhook_event.return_value = {'id': TEST_WEBHOOK_EVENT_ID}
    mock.mark_webhook_processed.return_value = True
    
    return mock


def create_mock_nca_service():
    """Create a mock NCA service for testing."""
    mock = Mock()
    
    # Mock file operations
    mock.upload_file.return_value = {
        'url': 'https://storage.example.com/test_file.mp4',
        'key': 'test_file.mp4'
    }
    
    # Mock FFmpeg operations
    mock.combine_audio_video.return_value = {
        'job_id': 'nca_job_123',
        'status': 'processing'
    }
    
    mock.concatenate_videos.return_value = {
        'job_id': 'nca_job_456',
        'status': 'processing'
    }
    
    mock.add_background_music.return_value = {
        'job_id': 'nca_job_789',
        'status': 'processing'
    }
    
    return mock


def create_mock_elevenlabs_service():
    """Create a mock ElevenLabs service for testing."""
    mock = Mock()
    
    # Mock voice operations
    mock.get_voices.return_value = [
        {'voice_id': 'voice_1', 'name': 'Test Voice 1'},
        {'voice_id': 'voice_2', 'name': 'Test Voice 2'}
    ]
    
    mock.generate_audio.return_value = {
        'audio_url': 'https://api.elevenlabs.io/v1/audio/test.mp3',
        'request_id': 'elevenlabs_req_123'
    }
    
    return mock


def create_mock_goapi_service():
    """Create a mock GoAPI service for testing."""
    mock = Mock()
    
    # Mock music generation
    mock.generate_music.return_value = {
        'task_id': 'goapi_task_123',
        'status': 'processing'
    }
    
    return mock


class MockConfig:
    """Mock configuration for testing."""
    
    # Flask Configuration
    SECRET_KEY = 'test-secret-key'
    DEBUG = True
    TESTING = True
    
    # Airtable Configuration
    AIRTABLE_API_KEY = 'test-airtable-key'
    AIRTABLE_BASE_ID = 'test-base-id'
    
    # NCA Toolkit Configuration
    NCA_API_KEY = 'test-nca-key'
    NCA_BASE_URL = 'http://nca.test'
    NCA_S3_BUCKET_NAME = 'test-bucket'
    NCA_S3_ENDPOINT_URL = 'http://s3.test'
    NCA_S3_ACCESS_KEY = 'test-access-key'
    NCA_S3_SECRET_KEY = 'test-secret-key'
    NCA_S3_REGION = 'test-region'
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = 'test-elevenlabs-key'
    ELEVENLABS_BASE_URL = 'http://elevenlabs.test'
    
    # GoAPI Configuration
    GOAPI_API_KEY = 'test-goapi-key'
    GOAPI_BASE_URL = 'http://goapi.test'
    
    # Application Configuration
    WEBHOOK_BASE_URL = 'http://localhost:5000'
    LOG_LEVEL = 'DEBUG'
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '1000 per hour'
    
    # Default Values
    DEFAULT_SEGMENT_DURATION = 30
    MAX_PROCESSING_TIME = 300
    
    # Airtable Table Names
    VIDEOS_TABLE = 'Videos'
    SEGMENTS_TABLE = 'Segments'
    JOBS_TABLE = 'Jobs'
    WEBHOOK_EVENTS_TABLE = 'Webhook Events'
    
    # Job Types
    JOB_TYPE_VOICEOVER = 'voiceover'
    JOB_TYPE_COMBINE = 'combine'
    JOB_TYPE_CONCATENATE = 'concatenate'
    JOB_TYPE_MUSIC = 'music'
    JOB_TYPE_FINAL = 'final'
    
    # Status Values
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    # Webhook Validation
    WEBHOOK_VALIDATION_ELEVENLABS_ENABLED = False
    WEBHOOK_SECRET_ELEVENLABS = ''
    WEBHOOK_VALIDATION_NCA_ENABLED = False
    WEBHOOK_SECRET_NCA = ''
    WEBHOOK_VALIDATION_GOAPI_ENABLED = False
    WEBHOOK_SECRET_GOAPI = ''
    
    def validate_environment(self):
        """Skip validation for testing."""
        pass
