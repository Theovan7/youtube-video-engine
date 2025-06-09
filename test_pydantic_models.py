#!/usr/bin/env python3
"""
Test script for Pydantic webhook models.
Tests various webhook payload formats to ensure models parse correctly.
"""

import json
from models.webhooks.nca_models import NCAWebhookPayload
from models.webhooks.goapi_models import GoAPIWebhookPayload


def test_nca_models():
    """Test NCA webhook payload parsing."""
    print("Testing NCA Webhook Models...")
    
    # Test case 1: Code-based successful response with ffmpeg/compose structure
    payload1 = {
        "code": 200,
        "response": {
            "outputs": [
                {"url": "https://phi-bucket.nyc3.digitaloceanspaces.com/test1.mp4"}
            ]
        }
    }
    
    model1 = NCAWebhookPayload(**payload1)
    status = model1.get_status()
    url = model1.get_output_url()
    print(f"Debug: status={status}, url={url}")
    print(f"Debug: response type={type(model1.response)}")
    print(f"Debug: response value={model1.response}")
    if hasattr(model1.response, 'outputs'):
        print(f"Debug: response.outputs={model1.response.outputs}")
    assert status == "completed", f"Expected 'completed', got {status}"
    assert url == "https://phi-bucket.nyc3.digitaloceanspaces.com/test1.mp4", f"Expected URL, got {url}"
    print("✓ Test 1 passed: Code-based success with outputs array")
    
    # Test case 2: Code-based response with direct URL string
    payload2 = {
        "code": 200,
        "response": "https://phi-bucket.nyc3.digitaloceanspaces.com/test2.mp4"
    }
    
    model2 = NCAWebhookPayload(**payload2)
    assert model2.get_status() == "completed"
    assert model2.get_output_url() == "https://phi-bucket.nyc3.digitaloceanspaces.com/test2.mp4"
    print("✓ Test 2 passed: Code-based success with direct URL string")
    
    # Test case 3: Status-based format
    payload3 = {
        "status": "completed",
        "output_url": "https://phi-bucket.nyc3.digitaloceanspaces.com/test3.mp4"
    }
    
    model3 = NCAWebhookPayload(**payload3)
    assert model3.get_status() == "completed"
    assert model3.get_output_url() == "https://phi-bucket.nyc3.digitaloceanspaces.com/test3.mp4"
    print("✓ Test 3 passed: Status-based format")
    
    # Test case 4: Failed response
    payload4 = {
        "code": 400,
        "response": {
            "error": "Invalid input format"
        }
    }
    
    model4 = NCAWebhookPayload(**payload4)
    assert model4.get_status() == "failed"
    assert model4.get_error_message() == "Invalid input format"
    print("✓ Test 4 passed: Failed response with error")
    
    # Test case 5: Message-based success
    payload5 = {
        "message": "Job completed successfully",
        "file_url": "https://phi-bucket.nyc3.digitaloceanspaces.com/test5.mp4"
    }
    
    model5 = NCAWebhookPayload(**payload5)
    assert model5.get_status() == "completed"
    assert model5.get_output_url() == "https://phi-bucket.nyc3.digitaloceanspaces.com/test5.mp4"
    print("✓ Test 5 passed: Message-based success")
    
    print("✅ All NCA model tests passed!\n")


def test_goapi_models():
    """Test GoAPI webhook payload parsing."""
    print("Testing GoAPI Webhook Models...")
    
    # Test case 1: New format with data wrapper (Kling video)
    payload1 = {
        "data": {
            "status": "completed",
            "output": {
                "works": [
                    {
                        "video": {
                            "resource": "https://example.com/video.mp4",
                            "resource_without_watermark": "https://example.com/video_clean.mp4"
                        }
                    }
                ]
            }
        }
    }
    
    model1 = GoAPIWebhookPayload(**payload1)
    assert model1.get_status() == "completed"
    assert model1.get_video_url() == "https://example.com/video_clean.mp4"
    assert model1.is_completed() is True
    print("✓ Test 1 passed: Kling video format with works array")
    
    # Test case 2: Music generation format
    payload2 = {
        "data": {
            "status": "completed",
            "output": {
                "audio_url": "https://example.com/music.mp3"
            }
        }
    }
    
    model2 = GoAPIWebhookPayload(**payload2)
    assert model2.get_status() == "completed"
    assert model2.get_music_url() == "https://example.com/music.mp3"
    print("✓ Test 2 passed: Music generation format")
    
    # Test case 3: Old format with root-level fields
    payload3 = {
        "status": "completed",
        "output": {
            "video_url": "https://example.com/video_old.mp4"
        }
    }
    
    model3 = GoAPIWebhookPayload(**payload3)
    assert model3.get_status() == "completed"
    assert model3.get_video_url() == "https://example.com/video_old.mp4"
    print("✓ Test 3 passed: Old format with root-level status")
    
    # Test case 4: Failed response
    payload4 = {
        "data": {
            "status": "failed",
            "error": {
                "message": "Insufficient credits",
                "raw_message": "User has insufficient credits for this operation"
            }
        }
    }
    
    model4 = GoAPIWebhookPayload(**payload4)
    assert model4.get_status() == "failed"
    assert model4.is_failed() is True
    assert model4.get_error_message() == "Insufficient credits"
    print("✓ Test 4 passed: Failed response with error")
    
    # Test case 5: Generic URL fallback
    payload5 = {
        "status": "completed",
        "output": {
            "url": "https://example.com/generic.mp4"
        }
    }
    
    model5 = GoAPIWebhookPayload(**payload5)
    assert model5.get_status() == "completed"
    assert model5.get_video_url() == "https://example.com/generic.mp4"
    assert model5.get_music_url() == "https://example.com/generic.mp4"
    print("✓ Test 5 passed: Generic URL fallback")
    
    print("✅ All GoAPI model tests passed!\n")


def main():
    """Run all tests."""
    print("=== Pydantic Webhook Models Test Suite ===\n")
    
    try:
        test_nca_models()
        test_goapi_models()
        
        print("🎉 All tests passed successfully!")
        print("\nThe Pydantic models are correctly parsing various webhook payload formats.")
        
    except AssertionError as e:
        import traceback
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return 1
    except Exception as e:
        import traceback
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())