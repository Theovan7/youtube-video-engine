#!/usr/bin/env python3
"""
Verify NCA setup and configuration.
"""

import os
import requests
from config import get_config

config = get_config()()

def verify_nca_setup():
    """Verify NCA is properly configured."""
    print("NCA Configuration Verification")
    print("=" * 80)
    
    # 1. Check environment variables
    print("\n1. Environment Variables:")
    print(f"   NCA_API_KEY: {'SET ✓' if config.NCA_API_KEY else 'NOT SET ✗'}")
    print(f"   NCA_BASE_URL: {config.NCA_BASE_URL}")
    print(f"   NCA_S3_BUCKET_NAME: {config.NCA_S3_BUCKET_NAME}")
    print(f"   NCA_S3_ACCESS_KEY: {'SET ✓' if config.NCA_S3_ACCESS_KEY else 'NOT SET ✗'}")
    print(f"   NCA_S3_SECRET_KEY: {'SET ✓' if config.NCA_S3_SECRET_KEY else 'NOT SET ✗'}")
    
    # 2. Test API key validity
    print("\n2. Testing API Key Validity...")
    headers = {'x-api-key': config.NCA_API_KEY}
    
    try:
        # Test with the toolkit test endpoint
        response = requests.get(
            f"{config.NCA_BASE_URL}/v1/toolkit/test",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✓ API Key is valid")
            print(f"   Response: {response.text[:100]}")
        elif response.status_code == 401:
            print("   ✗ API Key is INVALID (401 Unauthorized)")
        elif response.status_code == 403:
            print("   ✗ API Key lacks permissions (403 Forbidden)")
        else:
            print(f"   ? Unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ✗ Error testing API key: {e}")
    
    # 3. Test specific endpoints
    print("\n3. Testing Endpoint Access...")
    
    endpoints = [
        ("/v1/toolkit/test", "Toolkit Test"),
        ("/v1/ffmpeg/compose", "FFmpeg Compose"),
        ("/v1/video/concatenate", "Video Concatenate"),
    ]
    
    for path, name in endpoints:
        print(f"\n   Testing {name} ({path})...")
        try:
            # Use OPTIONS to check if endpoint exists without sending data
            response = requests.options(
                f"{config.NCA_BASE_URL}{path}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 204]:
                print(f"   ✓ Endpoint exists")
            elif response.status_code == 405:
                # Method not allowed means endpoint exists but doesn't support OPTIONS
                print(f"   ✓ Endpoint exists (doesn't support OPTIONS)")
            elif response.status_code == 404:
                print(f"   ✗ Endpoint NOT FOUND")
            elif response.status_code == 401:
                print(f"   ✗ Unauthorized - API key issue")
            else:
                print(f"   ? Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Error: {str(e)[:50]}")
    
    # 4. Check account limits
    print("\n\n4. Possible Issues:")
    print("   - API key might not have access to ffmpeg endpoints")
    print("   - Account might be on a plan that doesn't include video processing")
    print("   - Service might be rate limited or quota exceeded")
    print("   - NCA service might be experiencing ongoing issues")
    
    # 5. Alternative services
    print("\n5. Alternative Video Processing Services:")
    print("   - Shotstack API (shotstack.io)")
    print("   - Bannerbear API (bannerbear.com)")
    print("   - Creatomate (creatomate.com)")
    print("   - Local FFmpeg processing")
    print("   - AWS MediaConvert")

if __name__ == "__main__":
    verify_nca_setup()