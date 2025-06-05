#!/usr/bin/env python3
"""
Enhanced GoAPI debugging script for troubleshooting video generation issues.
This script will provide detailed logging to diagnose the exact problem.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from services.goapi_service_enhanced import EnhancedGoAPIService
from services.airtable_service import AirtableService

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('goapi_debug.log')
    ]
)

logger = logging.getLogger(__name__)

def test_specific_segment(segment_id: str = "recxGRBRi1Qe9sLDn"):
    """Test the exact same request that's failing with enhanced logging."""
    
    print("🔍 Enhanced GoAPI Debugging Test")
    print("="*80)
    print(f"📋 Testing segment: {segment_id}")
    print("="*80)
    
    try:
        # Initialize services
        logger.info("🔧 Initializing services...")
        airtable = AirtableService()
        goapi = EnhancedGoAPIService()
        
        # 1. Health check first
        logger.info("🏥 Step 1: Checking GoAPI health...")
        if not goapi.check_health():
            logger.error("❌ GoAPI health check failed - stopping test")
            return False
        
        # 2. Get segment data
        logger.info("📊 Step 2: Fetching segment data from Airtable...")
        segment = airtable.get_segment(segment_id)
        if not segment:
            logger.error(f"❌ Segment {segment_id} not found in Airtable")
            return False
        
        logger.info(f"✅ Segment found: {segment['fields'].get('SRT Text', 'No text')[:50]}...")
        
        # 3. Check for upscale image
        upscale_images = segment['fields'].get('Upscale Image')
        if not upscale_images:
            logger.error("❌ No upscale image found in segment")
            logger.info("💡 Available fields in segment:")
            for field_name in segment['fields'].keys():
                logger.info(f"   - {field_name}: {type(segment['fields'][field_name])}")
            return False
        
        image_url = upscale_images[0]['url']
        logger.info(f"✅ Image URL found: {image_url}")
        
        # 4. Determine duration
        segment_duration = segment['fields'].get('Duration', 0)
        duration = 5 if segment_duration < 5 else 10
        logger.info(f"✅ Duration calculated: {duration} seconds (segment duration: {segment_duration})")
        
        # 5. Test the exact same request
        logger.info("🎬 Step 3: Testing video generation request...")
        logger.info("📋 Request parameters:")
        logger.info(f"   - Image URL: {image_url}")
        logger.info(f"   - Duration: {duration}")
        logger.info(f"   - Aspect Ratio: 16:9")
        logger.info(f"   - Quality: standard")
        
        # This is where the enhanced logging will show us exactly what happens
        result = goapi.generate_video(
            image_url=image_url,
            duration=duration,
            aspect_ratio="16:9",
            quality="standard"
        )
        
        logger.info("🎉 SUCCESS! Video generation request completed:")
        logger.info(f"   Task ID: {result.get('id', 'N/A')}")
        logger.info(f"   Status: {result.get('status', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Test failed with exception: {type(e).__name__}: {e}")
        return False

def test_simple_health_check():
    """Simple health check test."""
    print("\n🏥 Simple Health Check Test")
    print("="*50)
    
    try:
        goapi = EnhancedGoAPIService()
        result = goapi.check_health()
        if result:
            print("✅ GoAPI health check passed")
        else:
            print("❌ GoAPI health check failed")
        return result
    except Exception as e:
        print(f"💥 Health check exception: {e}")
        return False

def test_connectivity():
    """Test basic connectivity to GoAPI."""
    print("\n🌐 Connectivity Test")
    print("="*50)
    
    import requests
    
    try:
        # Test basic connectivity
        response = requests.get("https://api.goapi.ai", timeout=10)
        print(f"✅ Basic connectivity test: {response.status_code}")
        
        # Test with curl simulation
        import subprocess
        result = subprocess.run(
            ["curl", "-I", "https://api.goapi.ai/api/v1/task"], 
            capture_output=True, 
            text=True,
            timeout=10
        )
        print(f"🔍 Curl test result: {result.returncode}")
        if result.stdout:
            print(f"   Headers: {result.stdout.split()[1] if len(result.stdout.split()) > 1 else 'N/A'}")
        
    except Exception as e:
        print(f"💥 Connectivity test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Enhanced GoAPI Debugging Session")
    print("="*80)
    
    # Run all tests
    print("\n1️⃣  Testing basic connectivity...")
    test_connectivity()
    
    print("\n2️⃣  Testing health check...")
    test_simple_health_check()
    
    print("\n3️⃣  Testing specific failing segment...")
    success = test_specific_segment()
    
    print("\n" + "="*80)
    if success:
        print("🎉 ALL TESTS PASSED - Issue may be resolved!")
    else:
        print("❌ TESTS FAILED - Check the detailed logs above")
        print("📋 Log file created: goapi_debug.log")
    print("="*80)
