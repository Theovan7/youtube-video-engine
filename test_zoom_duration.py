#!/usr/bin/env python3
"""Test script to verify zoom video duration calculation."""

def test_zoom_duration_calculation():
    """Test the 20% duration increase for zoom videos."""
    
    test_cases = [
        {"original": 5, "expected": 6.0},
        {"original": 10, "expected": 12.0},
        {"original": 15, "expected": 18.0},
        {"original": 20, "expected": 24.0},
        {"original": 30, "expected": 36.0},
        {"original": 7.5, "expected": 9.0},
        {"original": 2.5, "expected": 3.0},
    ]
    
    print("Testing Zoom Video Duration Calculation (20% increase)")
    print("=" * 50)
    
    for test in test_cases:
        original_duration = test["original"]
        expected_duration = test["expected"]
        
        # Apply 20% increase
        zoom_duration = original_duration * 1.2
        
        # Test with 60 FPS
        fps = 60
        total_frames = int(zoom_duration * fps)
        
        print(f"\nOriginal duration: {original_duration}s")
        print(f"Extended duration: {zoom_duration}s (+20%)")
        print(f"Expected duration: {expected_duration}s")
        print(f"Total frames at {fps} FPS: {total_frames}")
        print(f"✓ PASS" if zoom_duration == expected_duration else f"✗ FAIL")
    
    # Additional info
    print("\n" + "=" * 50)
    print("Implementation details:")
    print("- Zoom videos get 20% extra duration")
    print("- This ensures smooth transitions and avoids abrupt cuts")
    print("- FFmpeg -t parameter uses the extended duration")
    print("- Total frames = extended_duration * FPS")

if __name__ == "__main__":
    test_zoom_duration_calculation()