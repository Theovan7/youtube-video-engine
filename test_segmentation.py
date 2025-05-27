#!/usr/bin/env python3
"""Test script for newline-based segmentation logic."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.script_processor import ScriptProcessor

def test_newline_segmentation():
    """Test the newline-based segmentation."""
    
    processor = ScriptProcessor()
    
    # Test script with various newline scenarios
    test_scripts = [
        {
            "name": "Basic newlines",
            "script": """Welcome to our amazing video series!
In this episode, we'll explore the wonders of technology.
First, let's talk about artificial intelligence and how it's changing our world.
Next, we'll discuss machine learning algorithms and their applications.
Finally, we'll look at the future of AI and what it means for humanity.
Thank you for watching, and don't forget to subscribe!"""
        },
        {
            "name": "Windows line endings",
            "script": "Line 1\r\nLine 2\r\nLine 3"
        },
        {
            "name": "Mixed line endings", 
            "script": "Line 1\nLine 2\r\nLine 3\rLine 4"
        },
        {
            "name": "Empty lines",
            "script": """Line 1

Line 2

Line 3"""
        },
        {
            "name": "Single line",
            "script": "Just one line of text here."
        }
    ]
    
    print("Testing newline-based segmentation...")
    print("=" * 50)
    
    all_passed = True
    
    for test in test_scripts:
        print(f"\nTest: {test['name']}")
        print(f"Input: {repr(test['script'])}")
        
        try:
            segments = processor.process_script_by_newlines(test['script'])
            
            print(f"✅ Generated {len(segments)} segments:")
            for i, segment in enumerate(segments):
                print(f"  {i+1}. {segment.text[:60]}{'...' if len(segment.text) > 60 else ''}")
                print(f"      Duration: {segment.estimated_duration:.2f}s, Words: {segment.word_count}")
                print(f"      Time: {segment.start_time:.2f}s → {segment.end_time:.2f}s")
            
            # Basic validation
            if len(segments) > 0:
                expected_lines = len([line.strip() for line in test['script'].replace('\r\n', '\n').replace('\r', '\n').split('\n') if line.strip()])
                if len(segments) == expected_lines:
                    print(f"✅ Correct number of segments: {len(segments)}")
                else:
                    print(f"❌ Expected {expected_lines} segments, got {len(segments)}")
                    all_passed = False
            else:
                print("❌ No segments generated")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    print(f"Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    return all_passed

if __name__ == "__main__":
    success = test_newline_segmentation()
    sys.exit(0 if success else 1)
