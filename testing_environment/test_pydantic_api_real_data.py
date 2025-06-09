#!/usr/bin/env python3
"""
Test Pydantic API models with real data from Airtable using the testing framework.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_framework import VideoEngineTestFramework
from models.api.requests import (
    ProcessScriptWebhookRequest,
    GenerateVoiceoverWebhookRequest,
    GenerateAIImageWebhookRequest,
    GenerateVideoWebhookRequest,
    CombineAllSegmentsWebhookRequest,
    GenerateAndAddMusicWebhookRequest
)
from models.api.responses import (
    WebhookAcceptedResponse,
    ProcessScriptWebhookResponse,
    VoiceoverGeneratedResponse,
    ErrorResponse
)
from pydantic import ValidationError


class PydanticAPITester(VideoEngineTestFramework):
    """Test Pydantic API models with real Airtable data"""
    
    def __init__(self):
        super().__init__()
        self.real_data_path = Path("test_inputs/api_requests/real_data")
        self.results = {
            'request_validation': {'success': 0, 'failed': 0, 'errors': []},
            'response_creation': {'success': 0, 'failed': 0, 'errors': []},
            'api_integration': {'success': 0, 'failed': 0, 'errors': []}
        }
    
    def load_real_payloads(self, filename: str) -> List[Dict]:
        """Load real payloads from extracted data"""
        file_path = self.real_data_path / filename
        if not file_path.exists():
            print(f"Warning: No data found at {file_path}")
            return []
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def test_request_validation_with_real_data(self):
        """Test request validation with real Airtable payloads"""
        print("\n=== Testing Request Validation with Real Data ===")
        print("-" * 60)
        
        # Test Generate Video requests (most common)
        print("\n1. Testing GenerateVideoWebhookRequest with real payloads...")
        video_payloads = self.load_real_payloads('generate_video_requests.json')
        
        for payload_data in video_payloads[:5]:  # Test first 5
            try:
                request_payload = payload_data['request_payload']
                job_id = payload_data['job_id']
                
                # Validate with Pydantic
                model = GenerateVideoWebhookRequest(**request_payload)
                
                print(f"✓ Job {job_id} - Valid GenerateVideoWebhookRequest")
                print(f"  - Segment ID: {model.segment_id}")
                print(f"  - Duration: {model.duration_override}")
                print(f"  - Aspect Ratio: {model.aspect_ratio}")
                print(f"  - Quality: {model.quality}")
                
                self.results['request_validation']['success'] += 1
                
            except ValidationError as e:
                print(f"✗ Job {job_id} - Validation failed: {e}")
                self.results['request_validation']['failed'] += 1
                self.results['request_validation']['errors'].append({
                    'job_id': job_id,
                    'error': str(e),
                    'payload': request_payload
                })
        
        # Test Generate AI Image requests
        print("\n2. Testing GenerateAIImageWebhookRequest with real payloads...")
        image_payloads = self.load_real_payloads('generate_image_requests.json')
        
        for payload_data in image_payloads:
            try:
                request_payload = payload_data['request_payload']
                job_id = payload_data['job_id']
                
                # Validate with Pydantic
                model = GenerateAIImageWebhookRequest(**request_payload)
                
                print(f"✓ Job {job_id} - Valid GenerateAIImageWebhookRequest")
                print(f"  - Segment ID: {model.segment_id}")
                print(f"  - Size: {model.size}")
                
                self.results['request_validation']['success'] += 1
                
            except ValidationError as e:
                print(f"✗ Job {job_id} - Validation failed: {e}")
                self.results['request_validation']['failed'] += 1
        
        # Test Music Generation requests
        print("\n3. Testing GenerateAndAddMusicWebhookRequest with real payloads...")
        music_payloads = self.load_real_payloads('generate_music_requests.json')
        
        for payload_data in music_payloads[:3]:  # Test first 3
            try:
                request_payload = payload_data['request_payload']
                job_id = payload_data['job_id']
                
                # Map video_id to record_id if needed
                if 'video_id' in request_payload and 'record_id' not in request_payload:
                    request_payload['record_id'] = request_payload['video_id']
                
                # Validate with Pydantic
                model = GenerateAndAddMusicWebhookRequest(**request_payload)
                
                print(f"✓ Job {job_id} - Valid GenerateAndAddMusicWebhookRequest")
                print(f"  - Record ID: {model.record_id}")
                
                self.results['request_validation']['success'] += 1
                
            except ValidationError as e:
                print(f"✗ Job {job_id} - Validation failed: {e}")
                self.results['request_validation']['failed'] += 1
        
        # Test Concatenate Videos requests
        print("\n4. Testing CombineAllSegmentsWebhookRequest with real payloads...")
        concat_payloads = self.load_real_payloads('concatenate_videos_requests.json')
        
        for payload_data in concat_payloads:
            try:
                request_payload = payload_data['request_payload']
                job_id = payload_data['job_id']
                
                # Map video_id to record_id if needed
                if 'video_id' in request_payload and 'record_id' not in request_payload:
                    request_payload['record_id'] = request_payload['video_id']
                
                # Validate with Pydantic
                model = CombineAllSegmentsWebhookRequest(**request_payload)
                
                print(f"✓ Job {job_id} - Valid CombineAllSegmentsWebhookRequest")
                print(f"  - Record ID: {model.record_id}")
                
                self.results['request_validation']['success'] += 1
                
            except ValidationError as e:
                print(f"✗ Job {job_id} - Validation failed: {e}")
                self.results['request_validation']['failed'] += 1
    
    def test_response_creation_with_real_data(self):
        """Test creating response models with real data patterns"""
        print("\n=== Testing Response Creation with Real Data ===")
        print("-" * 60)
        
        # Load sample segments and videos
        segments = self.load_real_payloads('../sample_segments.json')
        videos = self.load_real_payloads('../sample_videos.json')
        
        # Test WebhookAcceptedResponse
        print("\n1. Testing WebhookAcceptedResponse creation...")
        try:
            response = WebhookAcceptedResponse(
                status="accepted",
                message="Video generation job submitted",
                job_id="rec" + "x" * 14,  # Simulate Airtable ID
                external_job_id="task_123456",
                webhook_url="https://api.example.com/webhooks/goapi?job_id=recxxxxx"
            )
            
            print("✓ WebhookAcceptedResponse created successfully")
            print(f"  - JSON: {json.dumps(response.dict(), indent=2)}")
            self.results['response_creation']['success'] += 1
            
        except Exception as e:
            print(f"✗ WebhookAcceptedResponse failed: {e}")
            self.results['response_creation']['failed'] += 1
        
        # Test VoiceoverGeneratedResponse with real segment data
        print("\n2. Testing VoiceoverGeneratedResponse with real segment data...")
        if segments:
            segment = segments[0]
            try:
                response = VoiceoverGeneratedResponse(
                    status="success",
                    segment_id=segment['segment_id'],
                    audio_url="https://example.com/audio/voiceover_" + segment['segment_id'] + ".mp3",
                    duration=5.5,  # Would be calculated from actual audio
                    transcript=segment['text']
                )
                
                print("✓ VoiceoverGeneratedResponse created successfully")
                print(f"  - Segment: {response.segment_id}")
                print(f"  - Transcript preview: {response.transcript[:50]}...")
                self.results['response_creation']['success'] += 1
                
            except Exception as e:
                print(f"✗ VoiceoverGeneratedResponse failed: {e}")
                self.results['response_creation']['failed'] += 1
        
        # Test ErrorResponse with validation errors
        print("\n3. Testing ErrorResponse with validation errors...")
        try:
            error = ErrorResponse(
                error="Validation error",
                details=[
                    {
                        "field": "segment_id",
                        "message": "Segment not found",
                        "type": "not_found"
                    }
                ]
            )
            
            print("✓ ErrorResponse created successfully")
            print(f"  - Error: {error.error}")
            print(f"  - Details: {error.details}")
            self.results['response_creation']['success'] += 1
            
        except Exception as e:
            print(f"✗ ErrorResponse failed: {e}")
            self.results['response_creation']['failed'] += 1
    
    def test_edge_cases_with_real_data(self):
        """Test edge cases found in real data"""
        print("\n=== Testing Edge Cases from Real Data ===")
        print("-" * 60)
        
        # Test cases where fields might be missing or have unexpected values
        edge_cases = [
            {
                "name": "Video request with null duration",
                "model": GenerateVideoWebhookRequest,
                "payload": {"segment_id": "recTest123", "duration_override": None}
            },
            {
                "name": "Image request with auto size",
                "model": GenerateAIImageWebhookRequest,
                "payload": {"segment_id": "recTest123", "size": "auto"}
            },
            {
                "name": "Music request with just record_id",
                "model": GenerateAndAddMusicWebhookRequest,
                "payload": {"record_id": "recTest123"}
            }
        ]
        
        for test_case in edge_cases:
            try:
                model = test_case["model"](**test_case["payload"])
                print(f"✓ {test_case['name']} - Handled correctly")
                print(f"  - Model: {model}")
                self.results['request_validation']['success'] += 1
            except ValidationError as e:
                print(f"✗ {test_case['name']} - Failed: {e}")
                self.results['request_validation']['failed'] += 1
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("SUMMARY - Pydantic API Models with Real Airtable Data")
        print("=" * 70)
        
        for category, results in self.results.items():
            total = results['success'] + results['failed']
            if total > 0:
                success_rate = (results['success'] / total) * 100
                print(f"\n{category.replace('_', ' ').title()}:")
                print(f"  ✓ Success: {results['success']}")
                print(f"  ✗ Failed: {results['failed']}")
                print(f"  Success Rate: {success_rate:.1f}%")
                
                if results['errors']:
                    print(f"  Errors: {len(results['errors'])} unique failures")
        
        # Overall stats
        total_success = sum(r['success'] for r in self.results.values())
        total_failed = sum(r['failed'] for r in self.results.values())
        total_tests = total_success + total_failed
        
        if total_tests > 0:
            overall_rate = (total_success / total_tests) * 100
            print(f"\nOverall:")
            print(f"  Total Tests: {total_tests}")
            print(f"  Success Rate: {overall_rate:.1f}%")
            
            if overall_rate == 100:
                print("\n🎉 All Pydantic models validated successfully with real production data!")
            else:
                print(f"\n⚠️  {total_failed} tests failed. Review errors for details.")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("=== Testing Pydantic API Models with Real Airtable Data ===")
        print(f"Using data from: {self.real_data_path}")
        
        # Setup
        self.setup()
        
        # Run tests
        self.test_request_validation_with_real_data()
        self.test_response_creation_with_real_data()
        self.test_edge_cases_with_real_data()
        
        # Summary
        self.print_summary()
        
        # Save detailed error report if any failures
        if any(r['failed'] > 0 for r in self.results.values()):
            self.save_error_report()
    
    def save_error_report(self):
        """Save detailed error report"""
        report = {
            'summary': {
                category: {
                    'success': results['success'],
                    'failed': results['failed']
                }
                for category, results in self.results.items()
            },
            'errors': {
                category: results['errors']
                for category, results in self.results.items()
                if results['errors']
            }
        }
        
        with open('pydantic_api_test_errors.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed error report saved to pydantic_api_test_errors.json")


def main():
    """Run the tests"""
    tester = PydanticAPITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()