"""Test the new webhook-based process script endpoint."""

import pytest
from unittest.mock import Mock, patch

from app import create_app
from tests.conftest import (
    MockConfig,
    create_mock_airtable_service,
    SAMPLE_VIDEO_DATA,
    SAMPLE_SEGMENT_DATA,
    TEST_VIDEO_ID
)


class TestProcessScriptWebhookEndpoint:
    """Test the webhook-based process script endpoint."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.mock_airtable = create_mock_airtable_service()
        
        # Configure video with script
        video_with_script = SAMPLE_VIDEO_DATA.copy()
        video_with_script['fields']['Video Script'] = """This is the first segment.
This is the second segment.
This is the third segment."""
        self.mock_airtable.get_video.return_value = video_with_script
        
        self.patches = [
            patch('services.airtable_service.AirtableService', return_value=self.mock_airtable),
            patch('api.routes.AirtableService', return_value=self.mock_airtable)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_process_script_webhook_success(self):
        """Test successful webhook-based script processing."""
        response = self.client.post('/api/v1/process-script-webhook', json={
            'record_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert 'video_id' in data
        assert 'total_segments' in data
        assert 'segments' in data
        assert data['video_id'] == TEST_VIDEO_ID
        assert data['total_segments'] == 3  # Three lines in the script
        assert len(data['segments']) == 3
        
        # Verify Airtable interactions
        self.mock_airtable.get_video.assert_called_once_with(TEST_VIDEO_ID)
        self.mock_airtable.create_segments.assert_called_once()
        
        # Verify segments were created with correct data
        call_args = self.mock_airtable.create_segments.call_args
        assert call_args[0][0] == TEST_VIDEO_ID  # video_id
        segments = call_args[0][1]  # segment_data
        
        assert len(segments) == 3
        assert segments[0]['text'] == 'This is the first segment.'
        assert segments[1]['text'] == 'This is the second segment.'
        assert segments[2]['text'] == 'This is the third segment.'
        
        # Verify timing calculations were done
        assert 'start_time' in segments[0]
        assert 'end_time' in segments[0]
        assert segments[0]['start_time'] == 0.0
        assert segments[1]['start_time'] == segments[0]['end_time']
        assert segments[2]['start_time'] == segments[1]['end_time']
    
    def test_process_script_webhook_missing_record_id(self):
        """Test webhook processing with missing record_id."""
        response = self.client.post('/api/v1/process-script-webhook', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'details' in data
        assert 'record_id' in data['details']
    
    def test_process_script_webhook_record_not_found(self):
        """Test webhook processing when record doesn't exist."""
        self.mock_airtable.get_video.return_value = None
        
        response = self.client.post('/api/v1/process-script-webhook', json={
            'record_id': 'nonexistent_record'
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error']
    
    def test_process_script_webhook_empty_script(self):
        """Test webhook processing when Video Script field is empty."""
        video_no_script = SAMPLE_VIDEO_DATA.copy()
        video_no_script['fields'].pop('Video Script', None)
        self.mock_airtable.get_video.return_value = video_no_script
        
        response = self.client.post('/api/v1/process-script-webhook', json={
            'record_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Video Script' in data['error']
    
    def test_process_script_webhook_script_with_empty_lines(self):
        """Test webhook processing with script containing empty lines."""
        video_with_script = SAMPLE_VIDEO_DATA.copy()
        video_with_script['fields']['Video Script'] = """This is the first segment.

This is the second segment after empty line.


This is the third segment after multiple empty lines."""
        self.mock_airtable.get_video.return_value = video_with_script
        
        response = self.client.post('/api/v1/process-script-webhook', json={
            'record_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['total_segments'] == 3  # Empty lines are filtered out
        assert len(data['segments']) == 3
    
    def test_process_script_webhook_single_line_script(self):
        """Test webhook processing with single-line script."""
        video_with_script = SAMPLE_VIDEO_DATA.copy()
        video_with_script['fields']['Video Script'] = "This is a single line script with no newlines."
        self.mock_airtable.get_video.return_value = video_with_script
        
        response = self.client.post('/api/v1/process-script-webhook', json={
            'record_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['total_segments'] == 1
        assert len(data['segments']) == 1
        assert data['segments'][0]['text'] == "This is a single line script with no newlines."
    
    def test_process_script_webhook_windows_line_endings(self):
        """Test webhook processing with Windows line endings."""
        video_with_script = SAMPLE_VIDEO_DATA.copy()
        video_with_script['fields']['Video Script'] = "Line one.\r\nLine two.\r\nLine three."
        self.mock_airtable.get_video.return_value = video_with_script
        
        response = self.client.post('/api/v1/process-script-webhook', json={
            'record_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['total_segments'] == 3
        assert data['segments'][0]['text'] == "Line one."
        assert data['segments'][1]['text'] == "Line two."
        assert data['segments'][2]['text'] == "Line three."
    
    def test_process_script_webhook_no_status_updates(self):
        """Test that webhook endpoint doesn't update video status fields."""
        response = self.client.post('/api/v1/process-script-webhook', json={
            'record_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 201
        
        # Verify NO status update was made
        # Only get_video and create_segments should be called, no update_video
        self.mock_airtable.get_video.assert_called_once()
        self.mock_airtable.create_segments.assert_called_once()
        self.mock_airtable.update_video.assert_not_called()
        self.mock_airtable.update_video_status.assert_not_called()
