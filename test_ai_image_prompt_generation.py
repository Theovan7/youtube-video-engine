#!/usr/bin/env python3
"""Test AI image prompt generation functionality."""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from services.openai_service import OpenAIService

def test_ai_image_prompt_generation():
    """Test the AI image prompt generation functionality."""
    
    # Sample data for testing
    segment_text = "The storm clouds gathered ominously over the ancient castle, lightning illuminating its weathered stone walls."
    
    full_video_script = """In a remote corner of Scotland, an ancient castle stood as a silent witness to centuries of history.
The storm clouds gathered ominously over the ancient castle, lightning illuminating its weathered stone walls.
Inside, a young archaeologist discovered a hidden chamber that would change everything.
The chamber contained artifacts that proved the existence of a lost civilization.
As she examined the relics, strange symbols began to glow with an otherworldly light."""
    
    theme_description = "Dark, atmospheric cinematography with gothic elements. Use dramatic lighting, deep shadows, and rich color grading reminiscent of classic horror films. Focus on creating tension through visual composition."
    
    try:
        # Initialize OpenAI service
        openai_service = OpenAIService()
        
        # Test 1: Generate prompt with theme description
        logger.info("Test 1: Generating AI image prompt with theme description...")
        prompt_with_theme = openai_service.generate_ai_image_prompt(
            segment_text=segment_text,
            full_video_script=full_video_script,
            theme_description=theme_description
        )
        logger.info(f"Generated prompt with theme: {prompt_with_theme}")
        
        # Test 2: Generate prompt without theme description
        logger.info("\nTest 2: Generating AI image prompt without theme description...")
        prompt_without_theme = openai_service.generate_ai_image_prompt(
            segment_text=segment_text,
            full_video_script=full_video_script,
            theme_description=None
        )
        logger.info(f"Generated prompt without theme: {prompt_without_theme}")
        
        # Test 3: Different segment from the same story
        different_segment = "Inside, a young archaeologist discovered a hidden chamber that would change everything."
        logger.info("\nTest 3: Generating prompt for different segment...")
        prompt_different = openai_service.generate_ai_image_prompt(
            segment_text=different_segment,
            full_video_script=full_video_script,
            theme_description=theme_description
        )
        logger.info(f"Generated prompt for different segment: {prompt_different}")
        
        logger.info("\n✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    test_ai_image_prompt_generation()