#!/usr/bin/env python3
"""Test script for ElevenLabs markup generation."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.script_processor import ScriptProcessor
from services.openai_service import OpenAIService


def test_markup_generation():
    """Test the markup generation functionality."""
    
    # Sample script with emotional content
    test_script = """The doctor entered the room with the test results.
I'm afraid I have some difficult news.
The cancer has returned.
Everything was going according to plan.
Then the alarms started blaring.
Red lights flashed everywhere.
She took a deep breath before speaking.
I can't do this anymore I just can't
Tears streamed down her face."""
    
    print("=== Testing ElevenLabs Markup Generation ===\n")
    print("Original Script:")
    print("-" * 50)
    print(test_script)
    print("-" * 50)
    
    # Initialize processor
    processor = ScriptProcessor()
    
    # Process script into segments
    print("\nProcessing script into segments...")
    segments = processor.process_script_by_newlines(test_script)
    print(f"Created {len(segments)} segments")
    
    # Process segments with markup
    print("\nGenerating ElevenLabs markup...")
    marked_segments = processor.process_segments_with_markup(segments)
    
    # Display results
    print("\n=== Results ===\n")
    for i, segment in enumerate(marked_segments):
        print(f"Segment {i + 1}:")
        print(f"Original: {segment['original_text']}")
        print(f"Marked:   {segment['text']}")
        print("-" * 50)


def test_single_markup():
    """Test single segment markup generation."""
    print("\n=== Testing Single Segment Markup ===\n")
    
    # Initialize OpenAI service
    openai_service = OpenAIService()
    
    # Test segments
    previous = "Everything was going according to plan."
    target = "Then the alarms started blaring."
    following = "Red lights flashed everywhere."
    
    print(f"Previous: {previous}")
    print(f"Target: {target}")
    print(f"Following: {following}")
    
    # Generate markup
    marked = openai_service.generate_elevenlabs_markup(target, previous, following)
    
    print(f"\nMarked up: {marked}")


if __name__ == "__main__":
    try:
        # Test single segment first
        test_single_markup()
        
        # Test full processing
        test_markup_generation()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()