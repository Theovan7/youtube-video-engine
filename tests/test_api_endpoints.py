"""Unit tests for API endpoints."""

import pytest
import json
from unittest.mock import Mock, patch
from flask import Flask

from app import create_app
from tests.conftest import (
    MockConfig,
    create_mock_airtable_service,
    create_mock_nca_service,
    create_mock_elevenlabs_service,
    create_mock_goapi_service,
    SAMPLE_SCRIPT,
    SAMPLE_VIDEO_DATA,
    SAMPLE_SEGMENT_DATA,
    SAMPLE_JOB_DATA,
    TEST_VIDEO_ID,
    TEST_SEGMENT_ID,
    TEST_JOB_ID
)


class TestProcessScriptEndpoint:
    """Test the process script endpoint."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
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
    
    def test_process_script_success(self):
        """Test successful script processing."""
        response = self.client.post('/api/v1/process-script', json={
            'script_text': SAMPLE_SCRIPT,
            'video_name': 'Test Video',
            'target_segment_duration': 30,
            'music_prompt': 'Background music'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert 'video_id' in data
        assert 'segments' in data
        assert 'message' in data
        assert len(data['segments']) > 0
        
        # Verify Airtable interactions
        self.mock_airtable.create_video.assert_called_once()
        assert self.mock_airtable.create_segment.call_count > 0
    
    def test_process_script_missing_text(self):
        """Test script processing with missing text."""
        response = self.client.post('/api/v1/process-script', json={
            'video_name': 'Test Video'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'script_text' in data['error']
    
    def test_process_script_empty_text(self):
        """Test script processing with empty text."""
        response = self.client.post('/api/v1/process-script', json={
            'script_text': '',
            'video_name': 'Test Video'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_process_script_custom_duration(self):
        """Test script processing with custom segment duration."""
        response = self.client.post('/api/v1/process-script', json={
            'script_text': SAMPLE_SCRIPT,
            'video_name': 'Test Video',
            'target_segment_duration': 60  # 60 seconds instead of default 30
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Should have fewer segments with longer duration
        assert len(data['segments']) >= 1
    
    def test_process_script_with_defaults(self):
        """Test script processing with default values."""
        response = self.client.post('/api/v1/process-script', json={
            'script_text': SAMPLE_SCRIPT
            # No video_name or other optional fields
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert 'video_id' in data
        assert 'segments' in data


class TestGenerateVoiceoverEndpoint:
    """Test the generate voiceover endpoint."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.mock_airtable = create_mock_airtable_service()
        self.mock_elevenlabs = create_mock_elevenlabs_service()
        
        self.patches = [
            patch('services.airtable_service.AirtableService', return_value=self.mock_airtable),
            patch('services.elevenlabs_service.ElevenLabsService', return_value=self.mock_elevenlabs),
            patch('api.routes.AirtableService', return_value=self.mock_airtable),
            patch('api.routes.ElevenLabsService', return_value=self.mock_elevenlabs)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_generate_voiceover_success(self):
        """Test successful voiceover generation."""
        response = self.client.post('/api/v1/generate-voiceover', json={
            'segment_id': TEST_SEGMENT_ID,
            'voice_id': 'test_voice_id',
            'stability': 0.5,
            'similarity_boost': 0.75
        })
        
        assert response.status_code == 202
        data = response.get_json()
        
        assert 'job_id' in data
        assert 'message' in data
        assert 'segment_id' in data
        
        # Verify service calls
        self.mock_airtable.get_segment.assert_called_with(TEST_SEGMENT_ID)
        self.mock_elevenlabs.generate_audio.assert_called_once()
        self.mock_airtable.create_job.assert_called_once()
    
    def test_generate_voiceover_missing_segment(self):
        """Test voiceover generation with missing segment."""
        response = self.client.post('/api/v1/generate-voiceover', json={
            'voice_id': 'test_voice_id'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'segment_id' in data['error']
    
    def test_generate_voiceover_segment_not_found(self):
        """Test voiceover generation when segment doesn't exist."""
        self.mock_airtable.get_segment.return_value = None
        
        response = self.client.post('/api/v1/generate-voiceover', json={
            'segment_id': 'nonexistent_segment',
            'voice_id': 'test_voice_id'
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error']
    
    def test_generate_voiceover_default_settings(self):
        """Test voiceover generation with default voice settings."""
        response = self.client.post('/api/v1/generate-voiceover', json={
            'segment_id': TEST_SEGMENT_ID,
            'voice_id': 'test_voice_id'
            # No stability or similarity_boost
        })
        
        assert response.status_code == 202
        
        # Verify default values were used
        call_args = self.mock_elevenlabs.generate_audio.call_args
        assert call_args[1]['voice_settings']['stability'] == 0.5
        assert call_args[1]['voice_settings']['similarity_boost'] == 0.5


class TestCombineSegmentMediaEndpoint:
    """Test the combine segment media endpoint."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.mock_airtable = create_mock_airtable_service()
        self.mock_nca = create_mock_nca_service()
        
        # Configure segment with required media
        segment_with_media = SAMPLE_SEGMENT_DATA.copy()
        segment_with_media['fields']['Base Video'] = [{'url': 'https://example.com/base.mp4'}]
        segment_with_media['fields']['Voiceover'] = [{'url': 'https://example.com/voice.mp3'}]
        self.mock_airtable.get_segment.return_value = segment_with_media
        
        self.patches = [
            patch('services.airtable_service.AirtableService', return_value=self.mock_airtable),
            patch('services.nca_service.NCAService', return_value=self.mock_nca),
            patch('api.routes.AirtableService', return_value=self.mock_airtable),
            patch('api.routes.NCAService', return_value=self.mock_nca)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_combine_media_success(self):
        """Test successful media combination."""
        response = self.client.post('/api/v1/combine-segment-media', json={
            'segment_id': TEST_SEGMENT_ID
        })
        
        assert response.status_code == 202
        data = response.get_json()
        
        assert 'job_id' in data
        assert 'nca_job_id' in data
        assert 'message' in data
        
        # Verify service calls
        self.mock_airtable.get_segment.assert_called_with(TEST_SEGMENT_ID)
        self.mock_nca.combine_audio_video.assert_called_once()
        self.mock_airtable.create_job.assert_called_once()
    
    def test_combine_media_missing_base_video(self):
        """Test combination when base video is missing."""
        segment_no_video = SAMPLE_SEGMENT_DATA.copy()
        segment_no_video['fields']['Voiceover'] = [{'url': 'https://example.com/voice.mp3'}]
        # No Base Video field
        self.mock_airtable.get_segment.return_value = segment_no_video
        
        response = self.client.post('/api/v1/combine-segment-media', json={
            'segment_id': TEST_SEGMENT_ID
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'base video' in data['error'].lower()
    
    def test_combine_media_missing_voiceover(self):
        """Test combination when voiceover is missing."""
        segment_no_voice = SAMPLE_SEGMENT_DATA.copy()
        segment_no_voice['fields']['Base Video'] = [{'url': 'https://example.com/base.mp4'}]
        # No Voiceover field
        self.mock_airtable.get_segment.return_value = segment_no_voice
        
        response = self.client.post('/api/v1/combine-segment-media', json={
            'segment_id': TEST_SEGMENT_ID
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'voiceover' in data['error'].lower()


class TestCombineAllSegmentsEndpoint:
    """Test the combine all segments endpoint."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.mock_airtable = create_mock_airtable_service()
        self.mock_nca = create_mock_nca_service()
        
        # Configure segments with combined videos
        segments = []
        for i in range(3):
            segment = {
                'id': f'seg_{i}',
                'fields': {
                    'Order': i + 1,
                    'Combined': [{'url': f'https://example.com/segment_{i}.mp4'}],
                    'Status': 'combined'
                }
            }
            segments.append(segment)
        self.mock_airtable.get_video_segments.return_value = segments
        
        self.patches = [
            patch('services.airtable_service.AirtableService', return_value=self.mock_airtable),
            patch('services.nca_service.NCAService', return_value=self.mock_nca),
            patch('api.routes.AirtableService', return_value=self.mock_airtable),
            patch('api.routes.NCAService', return_value=self.mock_nca)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_combine_all_segments_success(self):
        """Test successful combination of all segments."""
        response = self.client.post('/api/v1/combine-all-segments', json={
            'video_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 202
        data = response.get_json()
        
        assert 'job_id' in data
        assert 'nca_job_id' in data
        assert 'message' in data
        
        # Verify service calls
        self.mock_airtable.get_video.assert_called_with(TEST_VIDEO_ID)
        self.mock_airtable.get_video_segments.assert_called_with(TEST_VIDEO_ID)
        self.mock_nca.concatenate_videos.assert_called_once()
    
    def test_combine_all_segments_no_segments(self):
        """Test combination when no segments exist."""
        self.mock_airtable.get_video_segments.return_value = []
        
        response = self.client.post('/api/v1/combine-all-segments', json={
            'video_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'No segments' in data['error']
    
    def test_combine_all_segments_missing_combined_videos(self):
        """Test combination when segments lack combined videos."""
        segments = [{
            'id': 'seg_1',
            'fields': {
                'Order': 1,
                'Status': 'voiceover_ready'
                # No Combined field
            }
        }]
        self.mock_airtable.get_video_segments.return_value = segments
        
        response = self.client.post('/api/v1/combine-all-segments', json={
            'video_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestGenerateAndAddMusicEndpoint:
    """Test the generate and add music endpoint."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.mock_airtable = create_mock_airtable_service()
        self.mock_goapi = create_mock_goapi_service()
        
        # Configure video with music prompt
        video_with_prompt = SAMPLE_VIDEO_DATA.copy()
        video_with_prompt['fields']['Music Prompt'] = 'Tech background music'
        self.mock_airtable.get_video.return_value = video_with_prompt
        
        self.patches = [
            patch('services.airtable_service.AirtableService', return_value=self.mock_airtable),
            patch('services.goapi_service.GoAPIService', return_value=self.mock_goapi),
            patch('api.routes.AirtableService', return_value=self.mock_airtable),
            patch('api.routes.GoAPIService', return_value=self.mock_goapi)
        ]
        
        for p in self.patches:
            p.start()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_generate_music_success(self):
        """Test successful music generation."""
        response = self.client.post('/api/v1/generate-and-add-music', json={
            'video_id': TEST_VIDEO_ID,
            'duration': 180
        })
        
        assert response.status_code == 202
        data = response.get_json()
        
        assert 'job_id' in data
        assert 'goapi_task_id' in data
        assert 'message' in data
        
        # Verify service calls
        self.mock_airtable.get_video.assert_called_with(TEST_VIDEO_ID)
        self.mock_goapi.generate_music.assert_called_once()
        self.mock_airtable.create_job.assert_called_once()
    
    def test_generate_music_custom_prompt(self):
        """Test music generation with custom prompt."""
        response = self.client.post('/api/v1/generate-and-add-music', json={
            'video_id': TEST_VIDEO_ID,
            'music_prompt': 'Epic orchestral music',
            'duration': 120
        })
        
        assert response.status_code == 202
        
        # Verify custom prompt was used
        call_args = self.mock_goapi.generate_music.call_args
        assert 'Epic orchestral music' in call_args[0][0]
    
    def test_generate_music_missing_duration(self):
        """Test music generation without duration."""
        response = self.client.post('/api/v1/generate-and-add-music', json={
            'video_id': TEST_VIDEO_ID
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'duration' in data['error']


class TestJobStatusEndpoint:
    """Test the job status endpoint."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
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
    
    def test_get_job_status_success(self):
        """Test successful job status retrieval."""
        response = self.client.get(f'/api/v1/jobs/{TEST_JOB_ID}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == TEST_JOB_ID
        assert 'fields' in data
        assert data['fields']['Status'] == 'processing'
    
    def test_get_job_status_not_found(self):
        """Test job status when job doesn't exist."""
        self.mock_airtable.get_job.return_value = None
        
        response = self.client.get('/api/v1/jobs/nonexistent_job')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error']


class TestVideoDetailsEndpoints:
    """Test video information endpoints."""
    
    def setup_method(self):
        """Set up test client and mocks."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
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
    
    def test_get_video_details_success(self):
        """Test successful video details retrieval."""
        response = self.client.get(f'/api/v1/videos/{TEST_VIDEO_ID}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == TEST_VIDEO_ID
        assert 'fields' in data
        assert data['fields']['Name'] == 'AI Tutorial Video'
    
    def test_get_video_details_not_found(self):
        """Test video details when video doesn't exist."""
        self.mock_airtable.get_video.return_value = None
        
        response = self.client.get('/api/v1/videos/nonexistent_video')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_get_video_segments_success(self):
        """Test successful video segments retrieval."""
        response = self.client.get(f'/api/v1/videos/{TEST_VIDEO_ID}/segments')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]['id'] == TEST_SEGMENT_ID
    
    def test_get_video_segments_empty(self):
        """Test video segments when none exist."""
        self.mock_airtable.get_video_segments.return_value = []
        
        response = self.client.get(f'/api/v1/videos/{TEST_VIDEO_ID}/segments')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        assert len(data) == 0
