"""Unit tests for service modules."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests

from services.script_processor import ScriptProcessor
from services.airtable_service import AirtableService
from services.nca_service import NCAService
from services.elevenlabs_service import ElevenLabsService
from services.goapi_service import GoAPIService
from tests.conftest import MockConfig


class TestScriptProcessor:
    """Test the script processor service."""
    
    def test_split_into_segments_basic(self):
        """Test basic script splitting."""
        script = """First paragraph here.
        
        Second paragraph here.
        
        Third paragraph here."""
        
        processor = ScriptProcessor()
        segments = processor.split_into_segments(script, target_duration=30)
        
        assert len(segments) >= 1
        for segment in segments:
            assert 'text' in segment
            assert 'start_time' in segment
            assert 'end_time' in segment
            assert 'duration' in segment
            assert segment['duration'] == segment['end_time'] - segment['start_time']
    
    def test_split_into_segments_empty_script(self):
        """Test splitting empty script."""
        processor = ScriptProcessor()
        segments = processor.split_into_segments('', target_duration=30)
        
        assert len(segments) == 0
    
    def test_split_into_segments_single_paragraph(self):
        """Test splitting script with single paragraph."""
        script = "This is a single paragraph without any breaks."
        
        processor = ScriptProcessor()
        segments = processor.split_into_segments(script, target_duration=30)
        
        assert len(segments) == 1
        assert segments[0]['text'] == script.strip()
        assert segments[0]['start_time'] == 0
        assert segments[0]['duration'] == 30
    
    def test_split_into_segments_custom_duration(self):
        """Test splitting with custom duration."""
        script = """First segment.
        
        Second segment."""
        
        processor = ScriptProcessor()
        segments = processor.split_into_segments(script, target_duration=60)
        
        for segment in segments:
            assert segment['duration'] == 60
    
    def test_split_into_segments_preserves_order(self):
        """Test that segment order is preserved."""
        script = """Paragraph 1.
        
        Paragraph 2.
        
        Paragraph 3.
        
        Paragraph 4."""
        
        processor = ScriptProcessor()
        segments = processor.split_into_segments(script, target_duration=30)
        
        # Check that start times are sequential
        for i in range(1, len(segments)):
            assert segments[i]['start_time'] == segments[i-1]['end_time']
    
    def test_estimate_duration(self):
        """Test duration estimation."""
        processor = ScriptProcessor()
        
        # Test with typical reading speed (150 words per minute)
        text = " ".join(["word"] * 150)  # 150 words
        duration = processor.estimate_duration(text)
        assert 55 <= duration <= 65  # Should be around 60 seconds
        
        # Test with short text
        short_text = "Hello world"
        duration = processor.estimate_duration(short_text)
        assert duration > 0
    
    def test_clean_text(self):
        """Test text cleaning."""
        processor = ScriptProcessor()
        
        # Test removing extra whitespace
        text = "Hello    world\n\n\ntest"
        cleaned = processor.clean_text(text)
        assert cleaned == "Hello world test"
        
        # Test trimming
        text = "   Hello world   "
        cleaned = processor.clean_text(text)
        assert cleaned == "Hello world"


class TestAirtableService:
    """Test the Airtable service."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = MockConfig()
        
        # Mock pyairtable
        self.mock_api = Mock()
        self.mock_table = Mock()
        
        with patch('services.airtable_service.Api') as mock_api_class:
            mock_api_class.return_value = self.mock_api
            self.mock_api.table.return_value = self.mock_table
            
            self.service = AirtableService(self.config)
    
    def test_create_video(self):
        """Test video creation."""
        self.mock_table.create.return_value = {
            'id': 'test_video_id',
            'fields': {'Name': 'Test Video'}
        }
        
        result = self.service.create_video(
            name='Test Video',
            script='Test script',
            music_prompt='Test music'
        )
        
        assert result['id'] == 'test_video_id'
        self.mock_table.create.assert_called_once()
        
        # Check the fields passed to create
        call_args = self.mock_table.create.call_args[0][0]
        assert call_args['Name'] == 'Test Video'
        assert call_args['Script'] == 'Test script'
        assert call_args['Music Prompt'] == 'Test music'
        assert call_args['Status'] == 'pending'
    
    def test_get_video(self):
        """Test video retrieval."""
        self.mock_table.get.return_value = {
            'id': 'test_video_id',
            'fields': {'Name': 'Test Video'}
        }
        
        result = self.service.get_video('test_video_id')
        
        assert result['id'] == 'test_video_id'
        self.mock_table.get.assert_called_with('test_video_id')
    
    def test_update_video_status(self):
        """Test video status update."""
        self.mock_table.update.return_value = {
            'id': 'test_video_id',
            'fields': {'Status': 'processing'}
        }
        
        result = self.service.update_video_status(
            'test_video_id',
            'processing',
            'Processing started'
        )
        
        assert result['fields']['Status'] == 'processing'
        self.mock_table.update.assert_called_once()
        
        # Check the fields passed to update
        call_args = self.mock_table.update.call_args[0]
        assert call_args[0] == 'test_video_id'
        assert call_args[1]['Status'] == 'processing'
        assert 'Updated' in call_args[1]
    
    def test_create_segment(self):
        """Test segment creation."""
        self.mock_table.create.return_value = {
            'id': 'test_segment_id',
            'fields': {'Name': 'Segment 1'}
        }
        
        result = self.service.create_segment(
            video_id='test_video_id',
            text='Test text',
            order=1,
            start_time=0,
            end_time=30
        )
        
        assert result['id'] == 'test_segment_id'
        self.mock_table.create.assert_called_once()
    
    def test_create_job(self):
        """Test job creation."""
        self.mock_table.create.return_value = {
            'id': 'test_job_id',
            'fields': {'Type': 'voiceover'}
        }
        
        result = self.service.create_job(
            job_type='voiceover',
            video_id='test_video_id',
            segment_id='test_segment_id',
            request_payload={'test': 'data'}
        )
        
        assert result['id'] == 'test_job_id'
        self.mock_table.create.assert_called_once()
    
    def test_complete_job(self):
        """Test job completion."""
        self.mock_table.update.return_value = {
            'id': 'test_job_id',
            'fields': {'Status': 'completed'}
        }
        
        result = self.service.complete_job(
            'test_job_id',
            {'result': 'success'}
        )
        
        assert result['fields']['Status'] == 'completed'
        
        # Check the update call
        call_args = self.mock_table.update.call_args[0]
        assert call_args[1]['Status'] == 'completed'
        assert 'Response Payload' in call_args[1]
    
    def test_fail_job(self):
        """Test job failure."""
        self.mock_table.update.return_value = {
            'id': 'test_job_id',
            'fields': {'Status': 'failed'}
        }
        
        result = self.service.fail_job(
            'test_job_id',
            'Test error message'
        )
        
        assert result['fields']['Status'] == 'failed'
        
        # Check the update call
        call_args = self.mock_table.update.call_args[0]
        assert call_args[1]['Status'] == 'failed'
        assert call_args[1]['Error Details'] == 'Test error message'


class TestNCAService:
    """Test the NCA Toolkit service."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = MockConfig()
        
        # Mock requests
        self.mock_response = Mock()
        self.mock_response.status_code = 202
        self.mock_response.json.return_value = {
            'job_id': 'nca_job_123',
            'code': 202,
            'message': 'processing'
        }
        
        with patch('services.nca_service.requests') as mock_requests:
            mock_requests.post.return_value = self.mock_response
            self.service = NCAService(self.config)
            self.mock_requests = mock_requests
    
    def test_upload_file(self):
        """Test file upload to storage."""
        self.mock_response.json.return_value = {
            'url': 'https://storage.example.com/test.mp4',
            'key': 'test.mp4'
        }
        
        result = self.service.upload_file(
            file_data=b'test data',
            filename='test.mp4',
            content_type='video/mp4'
        )
        
        assert result['url'] == 'https://storage.example.com/test.mp4'
        
        # Verify the upload request
        self.mock_requests.post.assert_called()
        call_args = self.mock_requests.post.call_args
        assert '/v1/s3/upload' in call_args[0][0]
    
    def test_combine_audio_video(self):
        """Test audio/video combination."""
        result = self.service.combine_audio_video(
            video_url='https://example.com/video.mp4',
            audio_url='https://example.com/audio.mp3',
            output_filename='combined.mp4',
            webhook_url='https://example.com/webhook'
        )
        
        assert result['job_id'] == 'nca_job_123'
        
        # Verify the request
        self.mock_requests.post.assert_called()
        call_args = self.mock_requests.post.call_args
        assert '/v1/ffmpeg/compose' in call_args[0][0]
        
        # Check payload
        payload = call_args[1]['json']
        assert len(payload['inputs']) == 2
        assert payload['filename'] == 'combined.mp4'
        assert payload['webhook_url'] == 'https://example.com/webhook'
    
    def test_concatenate_videos(self):
        """Test video concatenation."""
        video_urls = [
            'https://example.com/video1.mp4',
            'https://example.com/video2.mp4'
        ]
        
        result = self.service.concatenate_videos(
            video_urls=video_urls,
            output_filename='concatenated.mp4',
            webhook_url='https://example.com/webhook'
        )
        
        assert result['job_id'] == 'nca_job_123'
        
        # Verify the request
        self.mock_requests.post.assert_called()
        call_args = self.mock_requests.post.call_args
        assert '/v1/video/combine' in call_args[0][0]
        
        # Check payload
        payload = call_args[1]['json']
        assert payload['video_urls'] == video_urls
        assert payload['filename'] == 'concatenated.mp4'
    
    def test_add_background_music(self):
        """Test background music addition."""
        result = self.service.add_background_music(
            video_url='https://example.com/video.mp4',
            music_url='https://example.com/music.mp3',
            output_filename='final.mp4',
            volume_ratio=0.2,
            webhook_url='https://example.com/webhook'
        )
        
        assert result['job_id'] == 'nca_job_123'
        
        # Verify the request
        self.mock_requests.post.assert_called()
        call_args = self.mock_requests.post.call_args
        assert '/v1/ffmpeg/compose' in call_args[0][0]
        
        # Check payload includes volume filter
        payload = call_args[1]['json']
        assert 'filters' in payload
        assert 'volume=0.2' in payload['filters']


class TestElevenLabsService:
    """Test the ElevenLabs service."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = MockConfig()
        
        # Mock requests
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'audio_url': 'https://api.elevenlabs.io/audio/test.mp3'
        }
        
        with patch('services.elevenlabs_service.requests') as mock_requests:
            mock_requests.get.return_value = self.mock_response
            mock_requests.post.return_value = self.mock_response
            self.service = ElevenLabsService(self.config)
            self.mock_requests = mock_requests
    
    def test_get_voices(self):
        """Test voice list retrieval."""
        self.mock_response.json.return_value = {
            'voices': [
                {'voice_id': 'voice1', 'name': 'Voice 1'},
                {'voice_id': 'voice2', 'name': 'Voice 2'}
            ]
        }
        
        voices = self.service.get_voices()
        
        assert len(voices) == 2
        assert voices[0]['voice_id'] == 'voice1'
        
        # Verify the request
        self.mock_requests.get.assert_called()
        call_args = self.mock_requests.get.call_args
        assert '/voices' in call_args[0][0]
    
    def test_generate_audio(self):
        """Test audio generation."""
        result = self.service.generate_audio(
            text='Test text',
            voice_id='test_voice',
            webhook_url='https://example.com/webhook',
            voice_settings={
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        )
        
        assert 'audio_url' in result
        
        # Verify the request
        self.mock_requests.post.assert_called()
        call_args = self.mock_requests.post.call_args
        assert f'/text-to-speech/test_voice' in call_args[0][0]
        
        # Check payload
        payload = call_args[1]['json']
        assert payload['text'] == 'Test text'
        assert payload['voice_settings']['stability'] == 0.5


class TestGoAPIService:
    """Test the GoAPI service."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = MockConfig()
        
        # Mock requests
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'task_id': 'goapi_task_123',
            'status': 'processing'
        }
        
        with patch('services.goapi_service.requests') as mock_requests:
            mock_requests.post.return_value = self.mock_response
            self.service = GoAPIService(self.config)
            self.mock_requests = mock_requests
    
    def test_generate_music(self):
        """Test music generation."""
        result = self.service.generate_music(
            prompt='Upbeat tech music',
            duration=180,
            webhook_url='https://example.com/webhook'
        )
        
        assert result['task_id'] == 'goapi_task_123'
        
        # Verify the request
        self.mock_requests.post.assert_called()
        call_args = self.mock_requests.post.call_args
        assert '/music/generate' in call_args[0][0]
        
        # Check payload
        payload = call_args[1]['json']
        assert payload['prompt'] == 'Upbeat tech music'
        assert payload['duration'] == 180
        assert payload['webhook_url'] == 'https://example.com/webhook'
    
    def test_generate_music_with_defaults(self):
        """Test music generation with default parameters."""
        result = self.service.generate_music(
            prompt='Test music'
        )
        
        assert result['task_id'] == 'goapi_task_123'
        
        # Check default duration was used
        call_args = self.mock_requests.post.call_args
        payload = call_args[1]['json']
        assert 'duration' in payload
        assert payload['duration'] > 0
