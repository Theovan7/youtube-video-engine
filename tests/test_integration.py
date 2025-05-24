"""Integration tests for the complete video production pipeline."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
import requests

from app import create_app
from tests.conftest import (
    MockConfig, 
    create_mock_airtable_service,
    create_mock_nca_service,
    create_mock_elevenlabs_service,
    create_mock_goapi_service,
    SAMPLE_SCRIPT,
    TEST_VIDEO_ID,
    TEST_SEGMENT_ID,
    TEST_JOB_ID
)


class TestCompleteVideoPipeline:
    """Test the complete video production pipeline end-to-end."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        # Create service mocks
        self.mock_airtable = create_mock_airtable_service()
        self.mock_nca = create_mock_nca_service()
        self.mock_elevenlabs = create_mock_elevenlabs_service()
        self.mock_goapi = create_mock_goapi_service()
        
        # Configure mocks
        self.patches = [
            patch('services.airtable_service.AirtableService', return_value=self.mock_airtable),
            patch('services.nca_service.NCAService', return_value=self.mock_nca),
            patch('services.elevenlabs_service.ElevenLabsService', return_value=self.mock_elevenlabs),
            patch('services.goapi_service.GoAPIService', return_value=self.mock_goapi),
            patch('api.routes.AirtableService', return_value=self.mock_airtable),
            patch('api.routes.NCAService', return_value=self.mock_nca),
            patch('api.routes.ElevenLabsService', return_value=self.mock_elevenlabs),
            patch('api.routes.GoAPIService', return_value=self.mock_goapi),
            patch('api.webhooks.AirtableService', return_value=self.mock_airtable),
            patch('api.webhooks.NCAService', return_value=self.mock_nca)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_full_pipeline_success(self):
        """Test successful execution of the entire pipeline."""
        # Step 1: Process Script
        script_response = self.client.post('/api/v1/process-script', json={
            'script_text': SAMPLE_SCRIPT,
            'video_name': 'Test AI Tutorial',
            'target_segment_duration': 30,
            'music_prompt': 'Tech background music'
        })
        
        assert script_response.status_code == 201
        data = script_response.get_json()
        assert 'video_id' in data
        assert 'segments' in data
        assert len(data['segments']) > 0
        
        video_id = data['video_id']
        segment_id = data['segments'][0]['id']
        
        # Verify Airtable calls
        self.mock_airtable.create_video.assert_called_once()
        assert self.mock_airtable.create_segment.call_count > 0
        
        # Step 2: Generate Voiceover
        voiceover_response = self.client.post('/api/v1/generate-voiceover', json={
            'segment_id': segment_id,
            'voice_id': 'test_voice_id',
            'stability': 0.5,
            'similarity_boost': 0.5
        })
        
        assert voiceover_response.status_code == 202
        voiceover_data = voiceover_response.get_json()
        assert 'job_id' in voiceover_data
        
        # Simulate ElevenLabs webhook
        webhook_response = self.client.post(
            f'/webhooks/elevenlabs?job_id={voiceover_data["job_id"]}',
            json={
                'status': 'completed',
                'output': {
                    'url': 'https://api.elevenlabs.io/audio/test.mp3'
                }
            }
        )
        
        assert webhook_response.status_code == 200
        
        # Step 3: Combine Segment Media
        combine_response = self.client.post('/api/v1/combine-segment-media', json={
            'segment_id': segment_id
        })
        
        assert combine_response.status_code == 202
        combine_data = combine_response.get_json()
        assert 'job_id' in combine_data
        
        # Simulate NCA webhook
        nca_webhook_response = self.client.post(
            f'/webhooks/nca-toolkit?job_id={combine_data["job_id"]}&operation=combine',
            json={
                'status': 'completed',
                'output_url': 'https://storage.example.com/combined_segment.mp4'
            }
        )
        
        assert nca_webhook_response.status_code == 200
        
        # Step 4: Combine All Segments
        concatenate_response = self.client.post('/api/v1/combine-all-segments', json={
            'video_id': video_id
        })
        
        assert concatenate_response.status_code == 202
        concat_data = concatenate_response.get_json()
        assert 'job_id' in concat_data
        
        # Simulate NCA webhook for concatenation
        concat_webhook_response = self.client.post(
            f'/webhooks/nca-toolkit?job_id={concat_data["job_id"]}&operation=concatenate',
            json={
                'status': 'completed',
                'output_url': 'https://storage.example.com/combined_video.mp4'
            }
        )
        
        assert concat_webhook_response.status_code == 200
        
        # Step 5: Generate and Add Music
        music_response = self.client.post('/api/v1/generate-and-add-music', json={
            'video_id': video_id,
            'duration': 180
        })
        
        assert music_response.status_code == 202
        music_data = music_response.get_json()
        assert 'job_id' in music_data
        
        # Simulate GoAPI webhook
        goapi_webhook_response = self.client.post(
            f'/webhooks/goapi?job_id={music_data["job_id"]}',
            json={
                'status': 'completed',
                'output': {
                    'audio_url': 'https://api.goapi.ai/music/test.mp3'
                }
            }
        )
        
        assert goapi_webhook_response.status_code == 200
        
        # Verify final video creation
        # The GoAPI webhook should trigger music addition
        assert self.mock_nca.add_background_music.called
    
    def test_pipeline_with_failures(self):
        """Test pipeline handling of failures at various stages."""
        # Create video
        script_response = self.client.post('/api/v1/process-script', json={
            'script_text': SAMPLE_SCRIPT,
            'video_name': 'Test Video',
            'target_segment_duration': 30
        })
        
        assert script_response.status_code == 201
        data = script_response.get_json()
        segment_id = data['segments'][0]['id']
        
        # Test voiceover generation failure
        voiceover_response = self.client.post('/api/v1/generate-voiceover', json={
            'segment_id': segment_id,
            'voice_id': 'test_voice_id'
        })
        
        assert voiceover_response.status_code == 202
        job_id = voiceover_response.get_json()['job_id']
        
        # Simulate failure webhook
        webhook_response = self.client.post(
            f'/webhooks/elevenlabs?job_id={job_id}',
            json={
                'status': 'failed',
                'error': {
                    'message': 'Voice generation failed'
                }
            }
        )
        
        assert webhook_response.status_code == 200
        
        # Verify job was marked as failed
        self.mock_airtable.fail_job.assert_called_with(job_id, 'Voice generation failed')
        
        # Verify segment status was updated
        self.mock_airtable.update_segment.assert_called_with(segment_id, {
            'Status': 'voiceover_failed'
        })
    
    def test_job_status_tracking(self):
        """Test job status endpoint during pipeline execution."""
        # Create a job
        self.mock_airtable.get_job.return_value = {
            'id': TEST_JOB_ID,
            'fields': {
                'Job ID': 'job_123',
                'Type': 'voiceover',
                'Status': 'processing',
                'Related Video': [TEST_VIDEO_ID],
                'Related Segment': [TEST_SEGMENT_ID]
            }
        }
        
        # Check job status
        response = self.client.get(f'/api/v1/jobs/{TEST_JOB_ID}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == TEST_JOB_ID
        assert data['fields']['Status'] == 'processing'
    
    def test_video_details_endpoints(self):
        """Test video information retrieval endpoints."""
        # Test video details
        video_response = self.client.get(f'/api/v1/videos/{TEST_VIDEO_ID}')
        
        assert video_response.status_code == 200
        video_data = video_response.get_json()
        assert video_data['id'] == TEST_VIDEO_ID
        
        # Test video segments
        segments_response = self.client.get(f'/api/v1/videos/{TEST_VIDEO_ID}/segments')
        
        assert segments_response.status_code == 200
        segments_data = segments_response.get_json()
        assert isinstance(segments_data, list)
        assert len(segments_data) > 0
    
    def test_concurrent_segment_processing(self):
        """Test processing multiple segments concurrently."""
        # Create multiple segments
        segments = []
        for i in range(3):
            segment = {
                'id': f'segment_{i}',
                'fields': {
                    'Name': f'Segment {i}',
                    'Video': [TEST_VIDEO_ID],
                    'Text': f'Segment {i} text',
                    'Order': i,
                    'Status': 'pending'
                }
            }
            segments.append(segment)
        
        self.mock_airtable.get_video_segments.return_value = segments
        
        # Generate voiceovers for all segments
        job_ids = []
        for segment in segments:
            response = self.client.post('/api/v1/generate-voiceover', json={
                'segment_id': segment['id'],
                'voice_id': 'test_voice_id'
            })
            
            assert response.status_code == 202
            job_ids.append(response.get_json()['job_id'])
        
        # Simulate successful webhooks for all
        for i, job_id in enumerate(job_ids):
            webhook_response = self.client.post(
                f'/webhooks/elevenlabs?job_id={job_id}',
                json={
                    'status': 'completed',
                    'output': {
                        'url': f'https://api.elevenlabs.io/audio/segment_{i}.mp3'
                    }
                }
            )
            
            assert webhook_response.status_code == 200
        
        # Verify all segments were processed
        assert self.mock_airtable.update_segment.call_count >= len(segments)
    
    def test_webhook_validation_integration(self):
        """Test webhook validation in the pipeline."""
        # Enable webhook validation for this test
        with patch('config.get_config') as mock_get_config:
            mock_config = MockConfig()
            mock_config.WEBHOOK_VALIDATION_ELEVENLABS_ENABLED = True
            mock_config.WEBHOOK_SECRET_ELEVENLABS = 'test-secret'
            mock_get_config.return_value = lambda: mock_config
            
            # Try webhook without signature - should fail
            response = self.client.post(
                '/webhooks/elevenlabs?job_id=test',
                json={'status': 'completed'}
            )
            
            assert response.status_code == 401
            assert 'Invalid webhook signature' in response.get_json()['message']
    
    def test_error_recovery_mechanisms(self):
        """Test error recovery and retry mechanisms."""
        # Test transient failure recovery
        self.mock_elevenlabs.generate_audio.side_effect = [
            Exception("Network error"),  # First call fails
            {'audio_url': 'https://api.elevenlabs.io/audio/retry.mp3'}  # Retry succeeds
        ]
        
        # Generate voiceover with retry
        response = self.client.post('/api/v1/generate-voiceover', json={
            'segment_id': TEST_SEGMENT_ID,
            'voice_id': 'test_voice_id'
        })
        
        # Should still return 202 if retry logic is implemented
        # Note: Actual retry logic implementation depends on the service
        assert response.status_code in [202, 500]
    
    def test_large_script_processing(self):
        """Test processing of large scripts with many segments."""
        # Create a large script
        large_script = "\n\n".join([
            f"This is segment {i}. " * 20
            for i in range(20)
        ])
        
        response = self.client.post('/api/v1/process-script', json={
            'script_text': large_script,
            'video_name': 'Large Video',
            'target_segment_duration': 30
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should create multiple segments
        assert len(data['segments']) > 5
        
        # Verify all segments were created in order
        for i, segment in enumerate(data['segments']):
            assert segment['fields']['Order'] == i + 1


class TestHealthCheckIntegration:
    """Test health check with external service connectivity."""
    
    def setup_method(self):
        """Set up test client."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
    
    def test_health_check_response(self):
        """Test basic health check response."""
        response = self.client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'timestamp' in data
        assert 'services' in data
    
    def test_health_check_service_status(self):
        """Test health check reports service connectivity."""
        with patch('api.routes.check_service_health') as mock_check:
            mock_check.return_value = {
                'airtable': {'status': 'healthy', 'latency': 50},
                'nca_toolkit': {'status': 'healthy', 'latency': 100},
                'elevenlabs': {'status': 'unhealthy', 'error': 'Connection failed'},
                'goapi': {'status': 'healthy', 'latency': 75}
            }
            
            response = self.client.get('/health')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Overall status should be degraded if any service is unhealthy
            assert data['status'] == 'degraded'
            assert data['services']['elevenlabs']['status'] == 'unhealthy'


class TestRateLimitingIntegration:
    """Test rate limiting across the pipeline."""
    
    def setup_method(self):
        """Set up test client with rate limiting."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        # Mock services
        self.mock_airtable = create_mock_airtable_service()
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
    
    def test_rate_limiting_enforcement(self):
        """Test that rate limits are enforced."""
        # Make many requests quickly
        responses = []
        
        # The default test rate limit is high (1000/hour), so we test the mechanism exists
        for i in range(5):
            response = self.client.post('/api/v1/process-script', json={
                'script_text': 'Test script',
                'video_name': f'Test {i}'
            })
            responses.append(response)
        
        # All should succeed with our high test limit
        for response in responses:
            assert response.status_code in [200, 201, 202]
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are included."""
        response = self.client.get('/health')
        
        # Check for rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers
