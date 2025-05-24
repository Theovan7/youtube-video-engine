"""Unit tests for webhook handlers."""

import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

from app import create_app
from tests.conftest import (
    MockConfig,
    create_mock_airtable_service,
    create_mock_nca_service,
    TEST_VIDEO_ID,
    TEST_SEGMENT_ID,
    TEST_JOB_ID,
    TEST_WEBHOOK_EVENT_ID
)


class TestElevenLabsWebhook:
    """Test ElevenLabs webhook handler."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.mock_airtable = create_mock_airtable_service()
        self.mock_nca = create_mock_nca_service()
        
        # Configure job with segment
        job_data = {
            'id': TEST_JOB_ID,
            'fields': {
                'Job ID': 'job_123',
                'Type': 'voiceover',
                'Status': 'processing',
                'Related Segment': [TEST_SEGMENT_ID]
            }
        }
        self.mock_airtable.get_job.return_value = job_data
        
        # Mock requests.get for audio download
        self.mock_response = Mock()
        self.mock_response.content = b'fake audio data'
        self.mock_response.raise_for_status.return_value = None
        
        self.patches = [
            patch('api.webhooks.AirtableService', return_value=self.mock_airtable),
            patch('api.webhooks.NCAService', return_value=self.mock_nca),
            patch('api.webhooks.requests.get', return_value=self.mock_response)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_elevenlabs_webhook_success(self):
        """Test successful ElevenLabs webhook processing."""
        webhook_payload = {
            'status': 'completed',
            'output': {
                'url': 'https://api.elevenlabs.io/v1/audio/test.mp3'
            }
        }
        
        response = self.client.post(
            f'/webhooks/elevenlabs?job_id={TEST_JOB_ID}',
            json=webhook_payload
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'segment_id' in data
        
        # Verify webhook event was created
        self.mock_airtable.create_webhook_event.assert_called_once()
        
        # Verify audio was downloaded and uploaded
        self.mock_nca.upload_file.assert_called_once()
        
        # Verify segment was updated
        self.mock_airtable.update_segment.assert_called_with(TEST_SEGMENT_ID, {
            'Voiceover': [{'url': 'https://storage.example.com/test_file.mp4'}],
            'Status': 'voiceover_ready'
        })
        
        # Verify job was completed
        self.mock_airtable.complete_job.assert_called_once()
        
        # Verify webhook was marked as processed
        self.mock_airtable.mark_webhook_processed.assert_called_with(
            TEST_WEBHOOK_EVENT_ID, 
            success=True
        )
    
    def test_elevenlabs_webhook_failure(self):
        """Test ElevenLabs webhook with failure status."""
        webhook_payload = {
            'status': 'failed',
            'error': {
                'message': 'Voice generation failed'
            }
        }
        
        response = self.client.post(
            f'/webhooks/elevenlabs?job_id={TEST_JOB_ID}',
            json=webhook_payload
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'failed'
        
        # Verify segment status was updated
        self.mock_airtable.update_segment.assert_called_with(TEST_SEGMENT_ID, {
            'Status': 'voiceover_failed'
        })
        
        # Verify job was failed
        self.mock_airtable.fail_job.assert_called_with(
            TEST_JOB_ID, 
            'Voice generation failed'
        )
    
    def test_elevenlabs_webhook_no_job_id(self):
        """Test ElevenLabs webhook without job ID."""
        response = self.client.post('/webhooks/elevenlabs', json={
            'status': 'completed'
        })
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    def test_elevenlabs_webhook_job_not_found(self):
        """Test ElevenLabs webhook when job doesn't exist."""
        self.mock_airtable.get_job.return_value = None
        
        response = self.client.post(
            f'/webhooks/elevenlabs?job_id=nonexistent',
            json={'status': 'completed'}
        )
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    def test_elevenlabs_webhook_no_audio_url(self):
        """Test ElevenLabs webhook without audio URL."""
        webhook_payload = {
            'status': 'completed',
            'output': {}  # No URL
        }
        
        response = self.client.post(
            f'/webhooks/elevenlabs?job_id={TEST_JOB_ID}',
            json=webhook_payload
        )
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestNCAToolkitWebhook:
    """Test NCA Toolkit webhook handler."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.mock_airtable = create_mock_airtable_service()
        
        self.patches = [
            patch('api.webhooks.AirtableService', return_value=self.mock_airtable)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_nca_webhook_combine_success(self):
        """Test successful NCA webhook for segment combination."""
        # Configure job with segment
        job_data = {
            'id': TEST_JOB_ID,
            'fields': {
                'Type': 'combine',
                'Related Segment': [TEST_SEGMENT_ID]
            }
        }
        self.mock_airtable.get_job.return_value = job_data
        
        webhook_payload = {
            'status': 'completed',
            'output_url': 'https://storage.example.com/combined_segment.mp4'
        }
        
        response = self.client.post(
            f'/webhooks/nca-toolkit?job_id={TEST_JOB_ID}&operation=combine',
            json=webhook_payload
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        
        # Verify segment was updated
        self.mock_airtable.update_segment.assert_called_with(TEST_SEGMENT_ID, {
            'Combined': [{'url': 'https://storage.example.com/combined_segment.mp4'}],
            'Status': 'combined'
        })
    
    def test_nca_webhook_concatenate_success(self):
        """Test successful NCA webhook for video concatenation."""
        # Configure job with video
        job_data = {
            'id': TEST_JOB_ID,
            'fields': {
                'Type': 'concatenate',
                'Related Video': [TEST_VIDEO_ID]
            }
        }
        self.mock_airtable.get_job.return_value = job_data
        
        webhook_payload = {
            'status': 'completed',
            'output_url': 'https://storage.example.com/concatenated_video.mp4'
        }
        
        response = self.client.post(
            f'/webhooks/nca-toolkit?job_id={TEST_JOB_ID}&operation=concatenate',
            json=webhook_payload
        )
        
        assert response.status_code == 200
        
        # Verify video was updated
        self.mock_airtable.update_video.assert_called_with(TEST_VIDEO_ID, {
            'Combined Segments Video': [{'url': 'https://storage.example.com/concatenated_video.mp4'}],
            'Status': 'segments_combined'
        })
    
    def test_nca_webhook_add_music_success(self):
        """Test successful NCA webhook for music addition."""
        # Configure job with video
        job_data = {
            'id': TEST_JOB_ID,
            'fields': {
                'Type': 'final',
                'Related Video': [TEST_VIDEO_ID]
            }
        }
        self.mock_airtable.get_job.return_value = job_data
        
        webhook_payload = {
            'status': 'completed',
            'output_url': 'https://storage.example.com/final_video.mp4'
        }
        
        response = self.client.post(
            f'/webhooks/nca-toolkit?job_id={TEST_JOB_ID}&operation=add_music',
            json=webhook_payload
        )
        
        assert response.status_code == 200
        
        # Verify video was updated with final video
        self.mock_airtable.update_video.assert_called_with(TEST_VIDEO_ID, {
            'Final Video': [{'url': 'https://storage.example.com/final_video.mp4'}],
            'Status': 'completed'
        })
    
    def test_nca_webhook_failure(self):
        """Test NCA webhook with failure status."""
        job_data = {
            'id': TEST_JOB_ID,
            'fields': {
                'Type': 'combine',
                'Related Segment': [TEST_SEGMENT_ID]
            }
        }
        self.mock_airtable.get_job.return_value = job_data
        
        webhook_payload = {
            'status': 'failed',
            'error': 'FFmpeg processing failed'
        }
        
        response = self.client.post(
            f'/webhooks/nca-toolkit?job_id={TEST_JOB_ID}&operation=combine',
            json=webhook_payload
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'failed'
        
        # Verify segment status was updated
        self.mock_airtable.update_segment.assert_called_with(TEST_SEGMENT_ID, {
            'Status': 'combination_failed'
        })
        
        # Verify job was failed
        self.mock_airtable.fail_job.assert_called_with(
            TEST_JOB_ID,
            'FFmpeg processing failed'
        )
    
    def test_nca_webhook_unknown_operation(self):
        """Test NCA webhook with unknown operation."""
        job_data = {
            'id': TEST_JOB_ID,
            'fields': {'Type': 'unknown'}
        }
        self.mock_airtable.get_job.return_value = job_data
        
        response = self.client.post(
            f'/webhooks/nca-toolkit?job_id={TEST_JOB_ID}&operation=unknown',
            json={'status': 'completed', 'output_url': 'test.mp4'}
        )
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestGoAPIWebhook:
    """Test GoAPI webhook handler."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.mock_airtable = create_mock_airtable_service()
        self.mock_nca = create_mock_nca_service()
        
        # Configure job with video
        job_data = {
            'id': TEST_JOB_ID,
            'fields': {
                'Type': 'music',
                'Related Video': [TEST_VIDEO_ID]
            }
        }
        self.mock_airtable.get_job.return_value = job_data
        
        # Configure video with combined video
        video_data = {
            'id': TEST_VIDEO_ID,
            'fields': {
                'Combined Segments Video': [{'url': 'https://storage.example.com/combined.mp4'}]
            }
        }
        self.mock_airtable.get_video.return_value = video_data
        
        self.patches = [
            patch('api.webhooks.AirtableService', return_value=self.mock_airtable),
            patch('api.webhooks.NCAService', return_value=self.mock_nca)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_goapi_webhook_success(self):
        """Test successful GoAPI webhook processing."""
        webhook_payload = {
            'status': 'completed',
            'output': {
                'audio_url': 'https://api.goapi.ai/music/test.mp3'
            }
        }
        
        response = self.client.post(
            f'/webhooks/goapi?job_id={TEST_JOB_ID}',
            json=webhook_payload
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'video_id' in data
        assert 'music_job_id' in data
        
        # Verify video was updated with music
        self.mock_airtable.update_video.assert_called_with(TEST_VIDEO_ID, {
            'Music': [{'url': 'https://api.goapi.ai/music/test.mp3'}],
            'Status': 'adding_music'
        })
        
        # Verify new job was created for adding music
        assert self.mock_airtable.create_job.call_count == 1
        
        # Verify NCA was called to add music
        self.mock_nca.add_background_music.assert_called_once()
    
    def test_goapi_webhook_failure(self):
        """Test GoAPI webhook with failure status."""
        webhook_payload = {
            'status': 'failed',
            'error': {
                'message': 'Music generation failed'
            }
        }
        
        response = self.client.post(
            f'/webhooks/goapi?job_id={TEST_JOB_ID}',
            json=webhook_payload
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'failed'
        
        # Verify video status was updated
        self.mock_airtable.update_video_status.assert_called_with(
            TEST_VIDEO_ID,
            'music_generation_failed',
            'Music generation failed'
        )
    
    def test_goapi_webhook_no_music_url(self):
        """Test GoAPI webhook without music URL."""
        webhook_payload = {
            'status': 'completed',
            'output': {}  # No music URL
        }
        
        response = self.client.post(
            f'/webhooks/goapi?job_id={TEST_JOB_ID}',
            json=webhook_payload
        )
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    def test_goapi_webhook_no_combined_video(self):
        """Test GoAPI webhook when combined video doesn't exist."""
        # Configure video without combined video
        video_data = {
            'id': TEST_VIDEO_ID,
            'fields': {}  # No Combined Segments Video
        }
        self.mock_airtable.get_video.return_value = video_data
        
        webhook_payload = {
            'status': 'completed',
            'output': {
                'audio_url': 'https://api.goapi.ai/music/test.mp3'
            }
        }
        
        response = self.client.post(
            f'/webhooks/goapi?job_id={TEST_JOB_ID}',
            json=webhook_payload
        )
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert 'combined video' in data['error'].lower()


class TestWebhookTestEndpoint:
    """Test the webhook test endpoint."""
    
    def setup_method(self):
        """Set up test client."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
    
    def test_webhook_test_endpoint(self):
        """Test the webhook test endpoint."""
        test_payload = {
            'test': 'data',
            'status': 'testing'
        }
        
        response = self.client.post('/webhooks/test', json=test_payload)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['message'] == 'Webhook received'
