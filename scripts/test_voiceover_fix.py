#!/usr/bin/env python3
"""
Test script for voiceover generation fix
Tests the ElevenLabs integration directly
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_BASE_URL = 'https://api.elevenlabs.io/v1'
TEST_VOICE_ID = '21m00Tcm4TlvDq8ikWAM'  # Rachel voice
TEST_TEXT = "Hello, this is a test of the voiceover generation system."

def test_elevenlabs_direct():
    """Test ElevenLabs API directly"""
    print("Testing ElevenLabs API directly...")
    
    # Test 1: Check if API key is valid
    headers = {
        'xi-api-key': ELEVENLABS_API_KEY
    }
    
    response = requests.get(f"{ELEVENLABS_BASE_URL}/voices", headers=headers)
    print(f"Voices endpoint status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return False
    
    # Test 2: Try sync text-to-speech
    print("\nTesting sync text-to-speech...")
    
    payload = {
        'text': TEST_TEXT,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.5
        }
    }
    
    headers = {
        'xi-api-key': ELEVENLABS_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    
    response = requests.post(
        f"{ELEVENLABS_BASE_URL}/text-to-speech/{TEST_VOICE_ID}",
        json=payload,
        headers=headers
    )
    
    print(f"TTS endpoint status: {response.status_code}")
    
    if response.status_code == 200:
        print("Success! Audio generated.")
        print(f"Audio size: {len(response.content)} bytes")
        
        # Save audio for verification
        with open('test_voiceover.mp3', 'wb') as f:
            f.write(response.content)
        print("Audio saved to test_voiceover.mp3")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_async_with_webhook():
    """Test async TTS with webhook (simulated)"""
    print("\n\nTesting async text-to-speech with webhook...")
    
    # Note: We can't actually test webhook delivery without a public URL
    # But we can test if the API accepts our webhook parameter
    
    payload = {
        'text': TEST_TEXT,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.5
        },
        'webhook_url': 'https://youtube-video-engine.fly.dev/webhooks/elevenlabs?job_id=test123',
        'webhook_method': 'POST'
    }
    
    headers = {
        'xi-api-key': ELEVENLABS_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Try the endpoint without /stream
    response = requests.post(
        f"{ELEVENLABS_BASE_URL}/text-to-speech/{TEST_VOICE_ID}?enable_logging=true",
        json=payload,
        headers=headers
    )
    
    print(f"Async TTS endpoint status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code in [200, 202]:
        request_id = response.headers.get('request-id')
        print(f"Request ID: {request_id}")
        
        # Check if we got audio back (sync) or just acknowledgment (async)
        if response.headers.get('content-type', '').startswith('audio'):
            print("Received audio directly (sync mode)")
        else:
            print("Request accepted for async processing")
            
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """Run all tests"""
    print("ElevenLabs Voiceover Generation Test")
    print("=" * 50)
    
    if not ELEVENLABS_API_KEY:
        print("Error: ELEVENLABS_API_KEY not found in environment")
        return
    
    # Test direct API
    direct_ok = test_elevenlabs_direct()
    
    # Test async with webhook
    async_ok = test_async_with_webhook()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Direct API Test: {'PASSED' if direct_ok else 'FAILED'}")
    print(f"Async API Test: {'PASSED' if async_ok else 'FAILED'}")
    
    if direct_ok and async_ok:
        print("\n✅ All tests passed! The fix should work.")
    else:
        print("\n❌ Some tests failed. Additional debugging needed.")

if __name__ == "__main__":
    main()