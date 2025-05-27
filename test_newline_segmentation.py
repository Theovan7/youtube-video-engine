#!/usr/bin/env python3
"""Test script for newline-based segmentation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.script_processor import ScriptProcessor

def test_newline_segmentation():
    """Test the newline-based segmentation functionality."""
    processor = ScriptProcessor()
    
    # Test 1: Basic newline separation
    print("Test 1: Basic newline separation")
    script1 = """This is the first segment.
This is the second segment.
This is the third segment."""
    
    segments1 = processor.process_script_by_newlines(script1)
    print(f"Number of segments: {len(segments1)}")
    for i, seg in enumerate(segments1):
        print(f"Segment {i+1}: '{seg.text}' (duration: {seg.estimated_duration:.2f}s)")
    print()
    
    # Test 2: Script with empty lines
    print("Test 2: Script with empty lines")
    script2 = """This is the first segment.

This is the second segment after empty line.


This is the third segment after multiple empty lines."""
    
    segments2 = processor.process_script_by_newlines(script2)
    print(f"Number of segments: {len(segments2)}")
    for i, seg in enumerate(segments2):
        print(f"Segment {i+1}: '{seg.text}' (duration: {seg.estimated_duration:.2f}s)")
    print()
    
    # Test 3: Windows line endings
    print("Test 3: Windows line endings")
    script3 = "This is line one.\r\nThis is line two.\r\nThis is line three."
    
    segments3 = processor.process_script_by_newlines(script3)
    print(f"Number of segments: {len(segments3)}")
    for i, seg in enumerate(segments3):
        print(f"Segment {i+1}: '{seg.text}' (duration: {seg.estimated_duration:.2f}s)")
    print()
    
    # Test 4: Single line script
    print("Test 4: Single line script")
    script4 = "This is a single line script with no newlines."
    
    segments4 = processor.process_script_by_newlines(script4)
    print(f"Number of segments: {len(segments4)}")
    for i, seg in enumerate(segments4):
        print(f"Segment {i+1}: '{seg.text}' (duration: {seg.estimated_duration:.2f}s)")
    print()
    
    # Test 5: Timing validation
    print("Test 5: Timing validation")
    script5 = """Short segment.
This is a much longer segment with many more words to see how the timing calculation works.
Medium length segment here."""
    
    segments5 = processor.process_script_by_newlines(script5)
    print(f"Number of segments: {len(segments5)}")
    total_duration = 0
    for i, seg in enumerate(segments5):
        print(f"Segment {i+1}:")
        print(f"  Text: '{seg.text}'")
        print(f"  Word count: {seg.word_count}")
        print(f"  Start: {seg.start_time:.2f}s, End: {seg.end_time:.2f}s")
        print(f"  Duration: {seg.estimated_duration:.2f}s")
        total_duration += seg.estimated_duration
    print(f"Total duration: {total_duration:.2f}s")

if __name__ == "__main__":
    test_newline_segmentation()
