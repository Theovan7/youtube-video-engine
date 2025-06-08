#!/usr/bin/env python3
"""
Test webhook connectivity directly to production.
"""

import requests
import json
import time
from datetime import datetime

def test_production_webhook():
    """Test the production webhook endpoint directly."""
    
    # Production webhook URL
    base_url = "https://youtube-video-engine.fly.dev"
    
    print("Testing Production Webhook Connectivity")
    print("=" * 50)
    
    # 1. Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Test webhook endpoint with minimal payload
    print("\n2. Testing NCA webhook endpoint...")
    webhook_url = f"{base_url}/webhooks/nca-toolkit"
    
    # Minimal valid payload that should be accepted
    test_payload = {
        "id": "test_webhook_connectivity_123",  # Airtable job ID
        "job_id": "nca_test_job_456",          # NCA job ID
        "code": 200,
        "response": {
            "url": "https://example.com/test_output.mp4"
        }
    }
    
    print(f"   URL: {webhook_url}")
    print(f"   Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"\n   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text[:500]}")  # First 500 chars
        
        if response.status_code == 400:
            print("\n   Note: 400 error likely means job ID not found in Airtable (expected for test)")
        elif response.status_code == 404:
            print("\n   Note: 404 error means webhook endpoint not found")
        elif response.status_code == 500:
            print("\n   Note: 500 error indicates server error - check logs")
            
    except requests.exceptions.Timeout:
        print("   Error: Request timed out (>10 seconds)")
    except requests.exceptions.ConnectionError as e:
        print(f"   Error: Connection failed - {e}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Test with webhook.site
    print("\n3. Testing with webhook.site (external service)...")
    print("   Visit https://webhook.site to get a unique URL")
    print("   Then use that URL in NCA requests to verify they send webhooks")
    
    # 4. Check DNS resolution
    print("\n4. Checking DNS resolution...")
    import socket
    try:
        ip = socket.gethostbyname("youtube-video-engine.fly.dev")
        print(f"   youtube-video-engine.fly.dev resolves to: {ip}")
    except Exception as e:
        print(f"   DNS resolution error: {e}")
    
    # 5. Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("- If health check works but webhook fails: Authentication/routing issue")
    print("- If both fail: App may be down or network issue")
    print("- If webhook returns 400/404: Check webhook path in routes")
    print("- If webhook returns 500: Check application logs for errors")

if __name__ == "__main__":
    test_production_webhook()