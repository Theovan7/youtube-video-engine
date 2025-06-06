#!/usr/bin/env python3
"""Test AI image generation webhook with automatic prompt generation."""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_webhook_integration():
    """Test the generate-ai-image webhook with automatic prompt generation."""
    
    # Test configuration
    BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    API_URL = f"{BASE_URL}/api/v2/generate-ai-image"
    
    # You'll need to provide a valid segment ID from your Airtable
    # that has:
    # - No AI Image Prompt (empty field)
    # - A linked Video with Video Script
    # - Original SRT Text field populated
    # - Optionally: An Image Theme with Theme Description
    
    SEGMENT_ID = os.getenv('TEST_SEGMENT_ID')
    
    if not SEGMENT_ID:
        logger.error("Please set TEST_SEGMENT_ID environment variable with a valid segment ID for testing")
        logger.info("The segment should have:")
        logger.info("- Empty 'AI Image Prompt' field")
        logger.info("- A linked Video with 'Video Script'")
        logger.info("- 'Original SRT Text' field populated")
        return
    
    # Test payload
    payload = {
        "segment_id": SEGMENT_ID,
        "size": "1792x1008"  # YouTube optimized size
    }
    
    try:
        logger.info(f"Testing generate-ai-image webhook with segment ID: {SEGMENT_ID}")
        logger.info(f"API URL: {API_URL}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Make the request
        response = requests.post(API_URL, json=payload)
        
        # Log response
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Success! Response: {json.dumps(result, indent=2)}")
            
            # Check if prompt was generated
            if 'prompt' in result:
                logger.info(f"\n📝 Generated AI Image Prompt:\n{result['prompt']}")
            
            # Check if images were generated
            if 'image_urls' in result:
                logger.info(f"\n🖼️  Generated {result.get('image_count', 0)} images:")
                for i, url in enumerate(result['image_urls'], 1):
                    logger.info(f"   Image {i}: {url}")
        else:
            logger.error(f"❌ Request failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise

def test_local_server():
    """Quick test to check if local server is running."""
    try:
        response = requests.get('http://localhost:5000/health', timeout=2)
        if response.status_code == 200:
            logger.info("✅ Local server is running")
            return True
    except:
        logger.warning("⚠️  Local server is not running. Start it with: python app.py")
        return False
    return False

if __name__ == "__main__":
    logger.info("AI Image Generation Webhook Integration Test")
    logger.info("=" * 50)
    
    if test_local_server():
        test_webhook_integration()
    else:
        logger.info("\nTo run this test:")
        logger.info("1. Start the Flask server: python app.py")
        logger.info("2. Set TEST_SEGMENT_ID environment variable")
        logger.info("3. Run this test again")