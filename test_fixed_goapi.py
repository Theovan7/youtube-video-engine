#!/usr/bin/env python3
"""Test the fixed GoAPI service with proper response parsing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.goapi_service import GoAPIService
from datetime import datetime

def test_fixed_goapi():
    """Test the fixed GoAPI service."""
    
    print("🧪 Testing Fixed GoAPI Service")
    print("=" * 80)
    
    # Test image URL from the failing segment
    test_image_url = "https://v5.airtableusercontent.com/v3/u/41/41/1748505600000/V8-5J9iorvnECRZqfLlSVw/0-HJEoTS0J06sXlyY-NsgliQyaYMyCgNVWoUXxm_xIic1YbBp_yhjZvDlmA9_nioaCP8K-hCkEW_502W8StPPArimVeAiQBEQQo_UaIxePV-79-mNS3dhr_vMzzxbAYnqhnmU8hWxjwxjdYXKb7N3I4WuNukJ3tO0NwN2D1FpdTVAQK4ze3KqM5LtxPapbTZEZIy4br3gb0yCuuSADnABGcIXqCv4cjmMhBZpWYTcgbl9RI9yQSO3-75uhOEfyks/Dp4rrzHZx3wF89He7W3JfG-1_Ukym1oMHgfnWY20Pcs"
    
    try:
        # Initialize service
        goapi = GoAPIService()
        
        # Test health check
        print("📋 Testing health check...")
        health_ok = goapi.check_health()
        print(f"   Health check: {'✅ PASSED' if health_ok else '❌ FAILED'}")
        print()
        
        # Test video generation
        print("🎬 Testing video generation with fixed response parsing...")
        result = goapi.generate_video(
            image_url=test_image_url,
            duration=5,
            aspect_ratio='16:9',
            quality='standard'
        )
        
        print(f"\n✅ SUCCESS! Video generation request accepted")
        print(f"   Task ID: {result['id']}")
        print(f"   Status: {result['status']}")
        print(f"   Service: {result['service']}")
        
        # Test status check
        print(f"\n📊 Testing status check for task: {result['id']}")
        status = goapi.get_video_status(result['id'])
        
        print(f"   Task Status: {status.get('status', 'unknown')}")
        print(f"   Created At: {status.get('meta', {}).get('created_at', 'unknown')}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"📅 Test completed at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    test_fixed_goapi()
