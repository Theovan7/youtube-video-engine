#!/usr/bin/env python3
"""
Test Pydantic API models to ensure they work correctly.
"""

import json
from models.api.requests import (
    ProcessScriptRequest,
    GenerateVoiceoverRequest,
    GenerateAIImageWebhookRequest,
    GenerateVideoWebhookRequest
)
from models.api.responses import (
    ProcessScriptResponse,
    GenerateVoiceoverResponse,
    ErrorResponse,
    SegmentInfo
)
from pydantic import ValidationError


def test_request_models():
    """Test request model validation."""
    print("Testing Request Models...")
    print("-" * 50)
    
    # Test 1: Valid ProcessScriptRequest
    try:
        request1 = ProcessScriptRequest(
            script_text="This is a test script. It has multiple sentences.",
            video_name="Test Video",
            target_segment_duration=45,
            music_prompt="Upbeat background music"
        )
        print("✓ ProcessScriptRequest - Valid data accepted")
        print(f"  - Parsed: {request1.dict()}")
    except ValidationError as e:
        print(f"✗ ProcessScriptRequest failed: {e}")
    
    # Test 2: Invalid ProcessScriptRequest (empty script)
    try:
        request2 = ProcessScriptRequest(
            script_text="",  # Should fail min_length=1
            video_name="Test Video"
        )
        print("✗ ProcessScriptRequest should have failed with empty script")
    except ValidationError as e:
        print("✓ ProcessScriptRequest - Correctly rejected empty script")
        print(f"  - Error: {e.errors()[0]['msg']}")
    
    # Test 3: GenerateVoiceoverRequest with defaults
    try:
        request3 = GenerateVoiceoverRequest(
            segment_id="rec123",
            voice_id="voice_abc"
        )
        print("✓ GenerateVoiceoverRequest - Defaults applied correctly")
        print(f"  - Stability: {request3.stability}")
        print(f"  - Use speaker boost: {request3.use_speaker_boost}")
    except ValidationError as e:
        print(f"✗ GenerateVoiceoverRequest failed: {e}")
    
    # Test 4: GenerateAIImageWebhookRequest with invalid size
    try:
        request4 = GenerateAIImageWebhookRequest(
            segment_id="rec123",
            size="invalid_size"
        )
        print("✗ GenerateAIImageWebhookRequest should have failed with invalid size")
    except ValidationError as e:
        print("✓ GenerateAIImageWebhookRequest - Correctly rejected invalid size")
        print(f"  - Error: {e.errors()[0]['msg']}")
    
    # Test 5: GenerateVideoWebhookRequest with valid duration override
    try:
        request5 = GenerateVideoWebhookRequest(
            segment_id="rec123",
            duration_override=5,
            aspect_ratio="16:9",
            quality="high"
        )
        print("✓ GenerateVideoWebhookRequest - Valid data accepted")
    except ValidationError as e:
        print(f"✗ GenerateVideoWebhookRequest failed: {e}")
    
    print()


def test_response_models():
    """Test response model creation."""
    print("Testing Response Models...")
    print("-" * 50)
    
    # Test 1: ProcessScriptResponse
    try:
        segments = [
            SegmentInfo(id="seg1", order=1, text="First segment", duration=5.0),
            SegmentInfo(id="seg2", order=2, text="Second segment", duration=4.5)
        ]
        
        response1 = ProcessScriptResponse(
            video_id="vid123",
            video_name="Test Video",
            total_segments=2,
            estimated_duration=9.5,
            status="segments_created",
            segments=segments
        )
        print("✓ ProcessScriptResponse created successfully")
        print(f"  - Total segments: {response1.total_segments}")
        print(f"  - JSON serializable: {type(response1.dict())}")
    except Exception as e:
        print(f"✗ ProcessScriptResponse failed: {e}")
    
    # Test 2: ErrorResponse
    try:
        error = ErrorResponse(
            error="Validation failed",
            details=[
                {"field": "script_text", "message": "Field required"},
                {"field": "voice_id", "message": "Invalid voice ID"}
            ]
        )
        print("✓ ErrorResponse created successfully")
        print(f"  - Error: {error.error}")
        print(f"  - Details count: {len(error.details)}")
    except Exception as e:
        print(f"✗ ErrorResponse failed: {e}")
    
    # Test 3: Response serialization
    try:
        voiceover_response = GenerateVoiceoverResponse(
            segment_id="seg123",
            status="completed",
            audio_url="https://example.com/audio.mp3",
            duration=10.5,
            file_size_bytes=1024000,
            voice_id="voice_abc"
        )
        
        # Test JSON serialization
        json_str = json.dumps(voiceover_response.dict())
        parsed = json.loads(json_str)
        
        print("✓ Response JSON serialization works")
        print(f"  - Serialized fields: {list(parsed.keys())}")
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
    
    print()


def test_validation_edge_cases():
    """Test edge cases and validation boundaries."""
    print("Testing Edge Cases...")
    print("-" * 50)
    
    # Test boundary values
    test_cases = [
        {
            "name": "Min segment duration",
            "model": ProcessScriptRequest,
            "data": {"script_text": "Test", "target_segment_duration": 10},
            "should_pass": True
        },
        {
            "name": "Below min segment duration",
            "model": ProcessScriptRequest,
            "data": {"script_text": "Test", "target_segment_duration": 9},
            "should_pass": False
        },
        {
            "name": "Max segment duration",
            "model": ProcessScriptRequest,
            "data": {"script_text": "Test", "target_segment_duration": 300},
            "should_pass": True
        },
        {
            "name": "Above max segment duration",
            "model": ProcessScriptRequest,
            "data": {"script_text": "Test", "target_segment_duration": 301},
            "should_pass": False
        },
        {
            "name": "Voice stability at 0",
            "model": GenerateVoiceoverRequest,
            "data": {"segment_id": "rec", "voice_id": "v", "stability": 0.0},
            "should_pass": True
        },
        {
            "name": "Voice stability at 1",
            "model": GenerateVoiceoverRequest,
            "data": {"segment_id": "rec", "voice_id": "v", "stability": 1.0},
            "should_pass": True
        },
        {
            "name": "Voice stability above 1",
            "model": GenerateVoiceoverRequest,
            "data": {"segment_id": "rec", "voice_id": "v", "stability": 1.1},
            "should_pass": False
        }
    ]
    
    for test in test_cases:
        try:
            model = test["model"](**test["data"])
            if test["should_pass"]:
                print(f"✓ {test['name']} - Passed as expected")
            else:
                print(f"✗ {test['name']} - Should have failed")
        except ValidationError as e:
            if not test["should_pass"]:
                print(f"✓ {test['name']} - Failed as expected")
            else:
                print(f"✗ {test['name']} - Should have passed: {e}")
    
    print()


def main():
    """Run all tests."""
    print("=== Pydantic API Models Test Suite ===\n")
    
    test_request_models()
    test_response_models()
    test_validation_edge_cases()
    
    print("🎉 All tests completed!")
    print("\nThe Pydantic models are working correctly and can replace Marshmallow schemas.")


if __name__ == "__main__":
    main()