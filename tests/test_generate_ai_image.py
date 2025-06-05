"""Test the generate AI image endpoint."""

import os
import json
import pytest
from unittest.mock import patch, Mock, MagicMock
from api.routes_v2 import api_v2_bp


class TestGenerateAIImage:
    """Test cases for the generate AI image endpoint."""
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        app.register_blueprint(api_v2_bp, url_prefix='/api/v2')
        return app.test_client()
    
    @pytest.fixture
    def mock_airtable(self):
        """Mock AirtableService."""
        with patch('api.routes_v2.airtable') as mock:
            # Mock segment with AI image prompt
            mock.get_segment.return_value = {
                'id': 'rec123',
                'fields': {
                    'AI Image Prompt': 'A beautiful sunset over mountains with vibrant colors',
                    'Status': 'Ready'
                }
            }
            
            # Mock job creation
            mock.create_job.return_value = {
                'id': 'recJob123',
                'fields': {
                    'Job Type': 'ai_image',
                    'Status': 'pending'
                }
            }
            
            yield mock
    
    @pytest.fixture
    def mock_nca(self):
        """Mock NCAService."""
        with patch('api.routes_v2.NCAService') as mock_class:
            mock_instance = Mock()
            mock_instance.upload_file.return_value = {
                'url': 'https://phi-bucket.nyc3.digitaloceanspaces.com/ai_generated_rec123_20250528_110000.png',
                'key': 'ai_generated_rec123_20250528_110000.png'
            }
            mock_class.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock successful OpenAI API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {
            'created': 1709825000,
            'data': [{
                'b64_json': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',  # 1x1 red pixel PNG
                'revised_prompt': 'A stunning sunset over majestic mountains with vibrant orange and purple colors'
            }]
        }
        return mock_response
    
    def test_generate_ai_image_success(self, client, mock_airtable, mock_nca, mock_openai_response):
        """Test successful AI image generation."""
        with patch('requests.post', return_value=mock_openai_response) as mock_post:
            response = client.post('/api/v2/generate-ai-image', 
                                 json={'segment_id': 'rec123'},
                                 headers={'Content-Type': 'application/json'})
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Check response structure
            assert 'job_id' in data
            assert 'segment_id' in data
            assert 'image_url' in data
            assert 'prompt' in data
            assert 'size' in data
            assert 'quality' in data
            assert data['status'] == 'completed'
            
            # Verify OpenAI API was called correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert 'images/generations' in call_args[0][0]
            
            # Check request payload
            request_data = call_args[1]['json']
            assert request_data['model'] == 'dall-e-3'
            assert request_data['prompt'] == 'A beautiful sunset over mountains with vibrant colors'
            assert request_data['size'] == '1024x1792'  # Default size
            assert request_data['quality'] == 'hd'  # Default high quality
            assert request_data['n'] == 1
            assert request_data['response_format'] == 'b64_json'
            
            # Verify Airtable updates
            mock_airtable.update_segment.assert_any_call('rec123', {'Status': 'Generating Image'})
            mock_airtable.update_segment.assert_any_call('rec123', {
                'Image': [{'url': 'https://phi-bucket.nyc3.digitaloceanspaces.com/ai_generated_rec123_20250528_110000.png'}],
                'Status': 'Image Ready'
            })
    
    def test_generate_ai_image_with_custom_parameters(self, client, mock_airtable, mock_nca, mock_openai_response):
        """Test AI image generation with custom size and quality parameters."""
        with patch('requests.post', return_value=mock_openai_response) as mock_post:
            response = client.post('/api/v2/generate-ai-image', 
                                 json={
                                     'segment_id': 'rec123',
                                     'size': '1024x1024',
                                     'quality': 'medium'
                                 },
                                 headers={'Content-Type': 'application/json'})
            
            assert response.status_code == 200
            
            # Check OpenAI request used custom parameters
            request_data = mock_post.call_args[1]['json']
            assert request_data['size'] == '1024x1024'
            assert request_data['quality'] == 'standard'  # medium maps to standard
    
    def test_generate_ai_image_missing_segment(self, client, mock_airtable, mock_nca):
        """Test AI image generation with missing segment."""
        mock_airtable.get_segment.return_value = None
        
        response = client.post('/api/v2/generate-ai-image', 
                             json={'segment_id': 'recNotFound'},
                             headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error']
    
    def test_generate_ai_image_missing_prompt(self, client, mock_airtable, mock_nca):
        """Test AI image generation with missing prompt."""
        mock_airtable.get_segment.return_value = {
            'id': 'rec123',
            'fields': {
                'Status': 'Ready'
                # No AI Image Prompt field
            }
        }
        
        response = client.post('/api/v2/generate-ai-image', 
                             json={'segment_id': 'rec123'},
                             headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'AI Image Prompt field is empty' in data['error']
    
    def test_generate_ai_image_openai_error(self, client, mock_airtable, mock_nca):
        """Test AI image generation with OpenAI API error."""
        # Mock OpenAI error response
        mock_error_response = Mock()
        mock_error_response.status_code = 400
        mock_error_response.headers = {'content-type': 'application/json'}
        mock_error_response.json.return_value = {
            'error': {
                'message': 'Invalid prompt',
                'type': 'invalid_request_error'
            }
        }
        
        with patch('requests.post', return_value=mock_error_response):
            response = client.post('/api/v2/generate-ai-image', 
                                 json={'segment_id': 'rec123'},
                                 headers={'Content-Type': 'application/json'})
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert 'Failed to generate AI image' in data['error']
            
            # Verify status was updated to failed
            mock_airtable.update_segment.assert_any_call('rec123', {
                'Status': 'Image Generation Failed'
            })
    
    def test_generate_ai_image_validation_error(self, client):
        """Test AI image generation with validation errors."""
        # Test missing segment_id
        response = client.post('/api/v2/generate-ai-image', 
                             json={},
                             headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Validation error' in data['error']
        
        # Test invalid size
        response = client.post('/api/v2/generate-ai-image', 
                             json={
                                 'segment_id': 'rec123',
                                 'size': 'invalid_size'
                             },
                             headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Validation error' in data['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
