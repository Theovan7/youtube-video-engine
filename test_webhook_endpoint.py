#!/usr/bin/env python3
"""Test script for the new webhook-based process script endpoint."""

import requests
import json
import time
from services.airtable_service import AirtableService
from config import get_config

def test_webhook_endpoint():
    """Test the new webhook-based process script endpoint."""
    
    # Initialize services
    airtable = AirtableService()
    config = get_config()()
    
    # Create a test video record with a script that has newlines
    test_script = """Welcome to our amazing video series!
In this episode, we'll explore the wonders of technology.
First, let's talk about artificial intelligence and how it's changing our world.
Next, we'll discuss machine learning algorithms and their applications.
Finally, we'll look at the future of AI and what it means for humanity.
Thank you for watching, and don't forget to subscribe!"""
    
    print("Creating test video record...")
    try:
        video = airtable.create_video(
            name="Webhook Test Video",
            script=test_script
        )
        video_id = video['id']
        print(f"✅ Created video record: {video_id}")
        
        # Test the webhook endpoint
        webhook_url = "http://localhost:5000/api/v2/process-script"
        payload = {"record_id": video_id}
        
        print(f"Testing webhook endpoint: {webhook_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Make the request
        response = requests.post(webhook_url, json=payload)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 201:
            print("✅ Webhook endpoint test PASSED!")
            
            # Check if segments were created correctly
            segments = airtable.get_video_segments(video_id)
            print(f"✅ Created {len(segments)} segments")
            
            # Print segments for verification
            for i, segment in enumerate(segments):
                print(f"Segment {i+1}: {segment['fields'].get('SRT Text', '')[:50]}...")
                
            return True
        else:
            print("❌ Webhook endpoint test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Starting webhook endpoint test...")
    success = test_webhook_endpoint()
    print(f"Test {'PASSED' if success else 'FAILED'}")
