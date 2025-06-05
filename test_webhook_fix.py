#!/usr/bin/env python3
"""
Test script for the NCA Toolkit webhook fix.
Tests the scenario where NCA Toolkit sends status: None in webhook payload.
"""

import requests
import json
import time
from services.airtable_service import AirtableService

def test_webhook_fix():
    """Test the webhook handler with None status payload."""
    
    # Initialize Airtable service
    airtable = AirtableService()
    
    print("🔍 Testing NCA Toolkit webhook fix for None status...")
    
    # Test segment from troubleshooting log
    segment_id = "recXwiLcbFPcIQxI7"
    
    try:
        # Get the segment to check current status
        segment = airtable.get_segment(segment_id)
        current_status = segment['fields'].get('Status', 'Unknown')
        print(f"📊 Segment {segment_id} current status: {current_status}")
        
        # Get the failing NCA job from troubleshooting log
        job_id = "rechCYmUPdGvRoARK"
        
        try:
            job = airtable.get_job(job_id)
            job_status = job['fields'].get('Status', 'Unknown')
            external_job_id = job['fields'].get('External Job ID', 'None')
            print(f"📋 Job {job_id} status: {job_status}")
            print(f"🔗 External Job ID: {external_job_id}")
        except Exception as e:
            print(f"⚠️  Could not retrieve job {job_id}: {e}")
        
        # Test the webhook endpoint with None status payload
        webhook_url = "http://localhost:5000/webhooks/nca-toolkit"
        params = {
            'job_id': job_id,
            'operation': 'combine'
        }
        
        # Test Case 1: None status (original failing scenario)
        print("\n🧪 Test Case 1: Webhook with status: None")
        test_payload_none = {
            "status": None,
            "output_url": "https://test-output.example.com/test_video.mp4"
        }
        
        print(f"📤 Sending payload: {json.dumps(test_payload_none, indent=2)}")
        
        try:
            response = requests.post(
                webhook_url,
                json=test_payload_none,
                params=params,
                timeout=10
            )
            print(f"📨 Response Status: {response.status_code}")
            print(f"📨 Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ None status handled successfully!")
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Cannot connect to webhook endpoint - app may not be running")
            print("   Run the app first with: python app.py")
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        # Test Case 2: None status with alternative in data.status
        print("\n🧪 Test Case 2: None status with alternative in data.status")
        test_payload_alternative = {
            "status": None,
            "data": {
                "status": "completed"
            },
            "output_url": "https://test-output.example.com/test_video.mp4"
        }
        
        print(f"📤 Sending payload: {json.dumps(test_payload_alternative, indent=2)}")
        
        try:
            response = requests.post(
                webhook_url,
                json=test_payload_alternative,
                params=params,
                timeout=10
            )
            print(f"📨 Response Status: {response.status_code}")
            print(f"📨 Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Alternative status detection working!")
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Cannot connect to webhook endpoint - app may not be running")
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        # Test Case 3: Valid status (should work as before)
        print("\n🧪 Test Case 3: Valid status (control test)")
        test_payload_valid = {
            "status": "completed",
            "output_url": "https://test-output.example.com/test_video.mp4"
        }
        
        print(f"📤 Sending payload: {json.dumps(test_payload_valid, indent=2)}")
        
        try:
            response = requests.post(
                webhook_url,
                json=test_payload_valid,
                params=params,
                timeout=10
            )
            print(f"📨 Response Status: {response.status_code}")
            print(f"📨 Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Valid status still working correctly!")
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Cannot connect to webhook endpoint - app may not be running")
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
    
    print("\n🏁 Webhook fix testing complete!")
    print("\n💡 Summary:")
    print("   - ✅ Added None status handling")
    print("   - ✅ Added alternative status location checking")
    print("   - ✅ Added enhanced logging for debugging")
    print("   - ✅ Added fallback to treat None as failure")

def test_segment_retry():
    """Test retrying the failing segment combination."""
    
    print("\n🔄 Testing segment combination retry...")
    
    # Initialize Airtable service
    airtable = AirtableService()
    
    segment_id = "recXwiLcbFPcIQxI7"
    
    try:
        # Get segment details
        segment = airtable.get_segment(segment_id)
        print(f"📊 Segment {segment_id}:")
        print(f"   Status: {segment['fields'].get('Status', 'Unknown')}")
        print(f"   Combine: {segment['fields'].get('Combine', 'Unknown')}")
        
        # Check for video and audio files
        video_file = segment['fields'].get('Video', [])
        audio_file = segment['fields'].get('Voiceover', [])
        
        print(f"   Video File: {'✅ Present' if video_file else '❌ Missing'}")
        print(f"   Audio File: {'✅ Present' if audio_file else '❌ Missing'}")
        
        if video_file and audio_file:
            print("📋 Both files present - segment ready for combination retry")
            print("💡 To retry combination:")
            print(f"   1. Update segment {segment_id} Status to 'Video Ready'")
            print("   2. The pipeline should automatically detect and retry combination")
        else:
            print("⚠️  Missing required files for combination")
            
    except Exception as e:
        print(f"❌ Failed to check segment: {e}")

if __name__ == "__main__":
    print("🚀 NCA Toolkit Webhook Fix Test")
    print("================================")
    
    # Test the webhook fix
    test_webhook_fix()
    
    # Test segment retry possibility
    test_segment_retry()
    
    print("\n✅ Testing complete!")
