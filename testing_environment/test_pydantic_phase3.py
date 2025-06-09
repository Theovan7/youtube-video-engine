#!/usr/bin/env python3
"""
Test Pydantic Phase 3 models with real data from services.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_framework import VideoEngineTestFramework

# Import all Phase 3 models
from models.services.elevenlabs_models import (
    ElevenLabsTTSRequest, ElevenLabsTTSResponse, VoiceSettings
)
from models.services.openai_models import (
    ChatCompletionRequest, ChatCompletionResponse, ChatMessage,
    ImageGenerationRequest, ImageGenerationResponse, ProcessedScript
)
from models.services.goapi_models import (
    VideoGenerationRequest, VideoGenerationResponse,
    MusicGenerationRequest, MusicGenerationResponse
)
from models.services.nca_models import (
    CombineMediaRequest, ConcatenateVideosRequest,
    NCATaskResponse, NCATaskResult
)
from models.airtable_models import (
    VideoRecord, SegmentRecord, JobRecord, AirtableResponse
)
from config_pydantic import Settings, get_settings
from pydantic import ValidationError


class Phase3Tester(VideoEngineTestFramework):
    """Test Pydantic Phase 3 models with real service data"""
    
    def __init__(self):
        super().__init__()
        self.results = {
            'elevenlabs': {'success': 0, 'failed': 0, 'errors': []},
            'openai': {'success': 0, 'failed': 0, 'errors': []},
            'goapi': {'success': 0, 'failed': 0, 'errors': []},
            'nca': {'success': 0, 'failed': 0, 'errors': []},
            'airtable': {'success': 0, 'failed': 0, 'errors': []},
            'config': {'success': 0, 'failed': 0, 'errors': []},
        }
    
    def test_elevenlabs_models(self):
        """Test ElevenLabs models with real patterns"""
        print("\n=== Testing ElevenLabs Models ===")
        print("-" * 50)
        
        # Test TTS Request
        test_cases = [
            {
                "name": "Basic TTS request",
                "data": {
                    "text": "Hello, this is a test of the ElevenLabs text-to-speech API.",
                    "voice_id": "EXAVITQu4vr4xnSDxMaL",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                }
            },
            {
                "name": "TTS with custom model",
                "data": {
                    "text": "Testing with a different model.",
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.3,
                        "similarity_boost": 0.9
                    }
                }
            }
        ]
        
        for test_case in test_cases:
            try:
                request = ElevenLabsTTSRequest(**test_case['data'])
                print(f"✓ {test_case['name']} - Valid request")
                print(f"  - Voice: {request.voice_id}")
                print(f"  - Model: {request.model_id}")
                self.results['elevenlabs']['success'] += 1
                
                # Test response
                response = ElevenLabsTTSResponse(
                    audio_url="https://example.com/audio.mp3",
                    character_count=len(request.text),
                    voice_id=request.voice_id,
                    model_id=request.model_id
                )
                print(f"✓ Response created successfully")
                self.results['elevenlabs']['success'] += 1
                
            except ValidationError as e:
                print(f"✗ {test_case['name']} - Failed: {e}")
                self.results['elevenlabs']['failed'] += 1
                self.results['elevenlabs']['errors'].append(str(e))
    
    def test_openai_models(self):
        """Test OpenAI models with real patterns"""
        print("\n=== Testing OpenAI Models ===")
        print("-" * 50)
        
        # Test Chat Completion
        try:
            messages = [
                ChatMessage(role="system", content="You are a helpful assistant."),
                ChatMessage(role="user", content="Generate a script about AI technology.")
            ]
            
            request = ChatCompletionRequest(
                model="gpt-4",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            print("✓ Chat completion request created")
            print(f"  - Model: {request.model}")
            print(f"  - Messages: {len(request.messages)}")
            self.results['openai']['success'] += 1
            
            # Test response
            response = ChatCompletionResponse(
                id="chatcmpl-123",
                object="chat.completion",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "AI is transforming our world..."
                    },
                    "finish_reason": "stop"
                }]
            )
            
            print("✓ Chat completion response created")
            print(f"  - Content preview: {response.get_content()[:50]}...")
            self.results['openai']['success'] += 1
            
        except ValidationError as e:
            print(f"✗ Chat completion failed: {e}")
            self.results['openai']['failed'] += 1
        
        # Test Image Generation
        try:
            image_request = ImageGenerationRequest(
                prompt="A futuristic city with AI robots",
                size="1024x1024",
                quality="hd",
                style="vivid"
            )
            
            print("✓ Image generation request created")
            print(f"  - Size: {image_request.size}")
            print(f"  - Quality: {image_request.quality}")
            self.results['openai']['success'] += 1
            
        except ValidationError as e:
            print(f"✗ Image generation failed: {e}")
            self.results['openai']['failed'] += 1
    
    def test_goapi_models(self):
        """Test GoAPI models with real patterns"""
        print("\n=== Testing GoAPI Models ===")
        print("-" * 50)
        
        # Test Video Generation
        try:
            video_request = VideoGenerationRequest(
                prompt="A peaceful mountain landscape with clouds",
                aspect_ratio="16:9",
                duration=10,
                quality="high",
                webhook_url="https://example.com/webhook"
            )
            
            print("✓ Video generation request created")
            print(f"  - Aspect ratio: {video_request.aspect_ratio}")
            print(f"  - Duration: {video_request.duration}s")
            self.results['goapi']['success'] += 1
            
            # Test response
            video_response = VideoGenerationResponse(
                id="task_123",
                status="completed",
                video_url="https://example.com/video.mp4",
                duration=10.5,
                created_at=datetime.now()
            )
            
            print("✓ Video generation response created")
            self.results['goapi']['success'] += 1
            
        except ValidationError as e:
            print(f"✗ Video generation failed: {e}")
            self.results['goapi']['failed'] += 1
        
        # Test Music Generation
        try:
            music_request = MusicGenerationRequest(
                prompt="Upbeat electronic music for a tech video",
                duration=60,
                genre="electronic",
                mood="energetic",
                tempo="fast"
            )
            
            print("✓ Music generation request created")
            print(f"  - Genre: {music_request.genre}")
            print(f"  - Duration: {music_request.duration}s")
            self.results['goapi']['success'] += 1
            
        except ValidationError as e:
            print(f"✗ Music generation failed: {e}")
            self.results['goapi']['failed'] += 1
    
    def test_nca_models(self):
        """Test NCA models with real patterns"""
        print("\n=== Testing NCA Models ===")
        print("-" * 50)
        
        # Test Combine Media
        try:
            combine_request = CombineMediaRequest(
                video_url="https://example.com/video.mp4",
                audio_url="https://example.com/audio.mp3",
                output_format="mp4",
                preset="medium",
                crf=23
            )
            
            print("✓ Combine media request created")
            print(f"  - Format: {combine_request.output_format}")
            print(f"  - CRF: {combine_request.crf}")
            self.results['nca']['success'] += 1
            
            # Test response
            task_response = NCATaskResponse(
                task_id="nca_task_123",
                status="queued",
                operation="combine",
                created_at=datetime.now().isoformat()
            )
            
            print("✓ NCA task response created")
            self.results['nca']['success'] += 1
            
        except ValidationError as e:
            print(f"✗ Combine media failed: {e}")
            self.results['nca']['failed'] += 1
        
        # Test Concatenate Videos
        try:
            concat_request = ConcatenateVideosRequest(
                video_urls=[
                    "https://example.com/video1.mp4",
                    "https://example.com/video2.mp4",
                    "https://example.com/video3.mp4"
                ],
                transition="fade",
                transition_duration=0.5
            )
            
            print("✓ Concatenate videos request created")
            print(f"  - Videos: {len(concat_request.video_urls)}")
            print(f"  - Transition: {concat_request.transition}")
            self.results['nca']['success'] += 1
            
        except ValidationError as e:
            print(f"✗ Concatenate videos failed: {e}")
            self.results['nca']['failed'] += 1
    
    def test_airtable_models(self):
        """Test Airtable models with real data"""
        print("\n=== Testing Airtable Models ===")
        print("-" * 50)
        
        # Get real data from Airtable
        from services.airtable_service import AirtableService
        airtable = AirtableService()
        
        # Test Video Records
        try:
            videos = airtable.videos_table.all(max_records=5)
            for video_data in videos[:2]:
                try:
                    # Create model from Airtable data
                    video = VideoRecord(
                        id=video_data['id'],
                        created_time=video_data.get('createdTime'),
                        **video_data['fields']
                    )
                    
                    print(f"✓ Video record {video.id}")
                    print(f"  - Description: {video.description[:50]}...")
                    if video.production_video:
                        print(f"  - Has production video: Yes")
                    self.results['airtable']['success'] += 1
                    
                except ValidationError as e:
                    print(f"✗ Video record {video_data['id']} failed: {e}")
                    self.results['airtable']['failed'] += 1
        
        except Exception as e:
            print(f"✗ Failed to fetch videos: {e}")
            self.results['airtable']['failed'] += 1
        
        # Test Segment Records
        try:
            segments = airtable.segments_table.all(max_records=5)
            for segment_data in segments[:2]:
                try:
                    segment = SegmentRecord(
                        id=segment_data['id'],
                        created_time=segment_data.get('createdTime'),
                        **segment_data['fields']
                    )
                    
                    print(f"✓ Segment record {segment.id}")
                    print(f"  - Text preview: {segment.srt_text[:30]}...")
                    print(f"  - Has voiceover: {segment.has_voiceover()}")
                    print(f"  - Has video: {segment.has_video()}")
                    self.results['airtable']['success'] += 1
                    
                except ValidationError as e:
                    print(f"✗ Segment record {segment_data['id']} failed: {e}")
                    self.results['airtable']['failed'] += 1
        
        except Exception as e:
            print(f"✗ Failed to fetch segments: {e}")
            self.results['airtable']['failed'] += 1
        
        # Test Job Records
        try:
            jobs = airtable.jobs_table.all(max_records=5)
            for job_data in jobs[:2]:
                try:
                    job = JobRecord(
                        id=job_data['id'],
                        created_time=job_data.get('createdTime'),
                        **job_data['fields']
                    )
                    
                    print(f"✓ Job record {job.id}")
                    print(f"  - Type: {job.type}")
                    print(f"  - Status: {job.status}")
                    print(f"  - Is complete: {job.is_complete()}")
                    self.results['airtable']['success'] += 1
                    
                except ValidationError as e:
                    print(f"✗ Job record {job_data['id']} failed: {e}")
                    self.results['airtable']['failed'] += 1
        
        except Exception as e:
            print(f"✗ Failed to fetch jobs: {e}")
            self.results['airtable']['failed'] += 1
    
    def test_config_settings(self):
        """Test Pydantic settings configuration"""
        print("\n=== Testing Configuration Settings ===")
        print("-" * 50)
        
        # Test loading settings
        try:
            settings = get_settings()
            print("✓ Settings loaded successfully")
            print(f"  - Environment: {settings.flask_env}")
            print(f"  - Debug: {settings.debug}")
            print(f"  - Webhook URL: {settings.webhook_base_url}")
            print(f"  - Polling enabled: {settings.polling_enabled}")
            self.results['config']['success'] += 1
            
            # Test validation
            assert settings.airtable_api_key, "Airtable API key should be set"
            assert settings.polling_interval_minutes >= 1, "Polling interval should be >= 1"
            print("✓ Settings validation passed")
            self.results['config']['success'] += 1
            
        except ValidationError as e:
            print(f"✗ Settings validation failed: {e}")
            self.results['config']['failed'] += 1
        except Exception as e:
            print(f"✗ Settings loading failed: {e}")
            self.results['config']['failed'] += 1
        
        # Test different environments
        try:
            # Test production settings
            import os
            # Temporarily set env to production
            original_env = os.environ.get('FLASK_ENV')
            os.environ['FLASK_ENV'] = 'production'
            prod_settings = get_settings('production')
            if original_env:
                os.environ['FLASK_ENV'] = original_env
            else:
                del os.environ['FLASK_ENV']
                
            assert not prod_settings.debug, "Production should not have debug enabled"
            assert 'fly.dev' in str(prod_settings.webhook_base_url), "Production should use fly.dev URL"
            print("✓ Production settings validated")
            self.results['config']['success'] += 1
            
        except Exception as e:
            print(f"✗ Production settings failed: {e}")
            self.results['config']['failed'] += 1
    
    def test_integration_flow(self):
        """Test integration between models"""
        print("\n=== Testing Model Integration ===")
        print("-" * 50)
        
        try:
            # 1. Create OpenAI request for script processing
            chat_request = ChatCompletionRequest(
                messages=[
                    ChatMessage(role="system", content="Process this video script"),
                    ChatMessage(role="user", content="AI is amazing. It helps us daily.")
                ]
            )
            print("✓ Step 1: OpenAI request created")
            
            # 2. Simulate script processing response
            processed = ProcessedScript(
                segments=[
                    {"text": "AI is amazing.", "order": 1, "duration_estimate": 3.0, "word_count": 3},
                    {"text": "It helps us daily.", "order": 2, "duration_estimate": 3.5, "word_count": 4}
                ],
                total_duration=6.5,
                total_words=7,
                ai_image_prompts=["Futuristic AI visualization"],
                music_prompt="Upbeat tech music"
            )
            print("✓ Step 2: Script processed into segments")
            
            # 3. Create ElevenLabs request for first segment
            tts_request = ElevenLabsTTSRequest(
                text=processed.segments[0].text,
                voice_id="EXAVITQu4vr4xnSDxMaL"
            )
            print("✓ Step 3: TTS request created")
            
            # 4. Create GoAPI video request
            video_request = VideoGenerationRequest(
                prompt=processed.ai_image_prompts[0],
                duration=int(processed.segments[0].duration_estimate),
                aspect_ratio="16:9"
            )
            print("✓ Step 4: Video generation request created")
            
            # 5. Create NCA combine request
            combine_request = CombineMediaRequest(
                video_url="https://example.com/generated_video.mp4",
                audio_url="https://example.com/generated_audio.mp3"
            )
            print("✓ Step 5: Media combination request created")
            
            print("\n✓ Integration flow completed successfully!")
            self.results['config']['success'] += 1
            
        except Exception as e:
            print(f"✗ Integration flow failed: {e}")
            self.results['config']['failed'] += 1
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("PHASE 3 TEST SUMMARY - Service Integration Models")
        print("=" * 70)
        
        total_success = 0
        total_failed = 0
        
        for service, results in self.results.items():
            if results['success'] + results['failed'] > 0:
                total = results['success'] + results['failed']
                success_rate = (results['success'] / total) * 100
                
                print(f"\n{service.upper()}:")
                print(f"  ✓ Success: {results['success']}")
                print(f"  ✗ Failed: {results['failed']}")
                print(f"  Success Rate: {success_rate:.1f}%")
                
                if results['errors']:
                    print(f"  Errors: {len(results['errors'])}")
                
                total_success += results['success']
                total_failed += results['failed']
        
        # Overall stats
        if total_success + total_failed > 0:
            overall_rate = (total_success / (total_success + total_failed)) * 100
            print(f"\nOVERALL:")
            print(f"  Total Tests: {total_success + total_failed}")
            print(f"  Success Rate: {overall_rate:.1f}%")
            
            if overall_rate == 100:
                print("\n🎉 All Phase 3 models validated successfully!")
                print("✅ Service integration models are production-ready!")
            else:
                print(f"\n⚠️  {total_failed} tests failed. Review errors for details.")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("=== Testing Pydantic Phase 3 - Service Integration ===")
        
        # Setup
        self.setup()
        
        # Run tests
        self.test_elevenlabs_models()
        self.test_openai_models()
        self.test_goapi_models()
        self.test_nca_models()
        self.test_airtable_models()
        self.test_config_settings()
        self.test_integration_flow()
        
        # Summary
        self.print_summary()


def main():
    """Run the tests"""
    tester = Phase3Tester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()