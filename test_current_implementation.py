#!/usr/bin/env python3
"""Test the current implementation's tpad behavior."""

import subprocess
import tempfile
import os


def get_media_duration(file_path):
    """Get duration of media file using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def create_test_video(duration, filename):
    """Create a test video with specified duration."""
    cmd = [
        'ffmpeg', '-y', '-f', 'lavfi', '-i', f'color=c=blue:s=640x480:d={duration}',
        '-c:v', 'libx264', '-preset', 'ultrafast', filename
    ]
    subprocess.run(cmd, capture_output=True)


def create_test_audio(duration, filename):
    """Create a test audio with specified duration."""
    cmd = [
        'ffmpeg', '-y', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={duration}',
        '-c:a', 'aac', filename
    ]
    subprocess.run(cmd, capture_output=True)


def test_current_vs_documented():
    """Compare current implementation vs documented behavior."""
    print("\n=== Testing Current Implementation vs Documentation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        audio_path = os.path.join(tmpdir, "test_audio.aac")
        output_current = os.path.join(tmpdir, "output_current.mp4")
        output_documented = os.path.join(tmpdir, "output_documented.mp4")
        
        # Create 2-second video and 5-second audio
        create_test_video(2, video_path)
        create_test_audio(5, audio_path)
        
        # Test 1: Current implementation (tpad without stop_duration + -shortest)
        cmd_current = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', '[0:v]tpad=stop_mode=clone[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-shortest',
            output_current
        ]
        
        result1 = subprocess.run(cmd_current, capture_output=True, text=True)
        print("\nCurrent Implementation (from nca_service.py line 141):")
        print("Filter: '[0:v]tpad=stop_mode=clone[v]'")
        print("With -shortest flag")
        
        if result1.returncode == 0:
            duration1 = get_media_duration(output_current)
            print(f"Result: Output duration = {duration1:.2f}s")
        else:
            print(f"Error: {result1.stderr[:200]}")
        
        # Test 2: Documented implementation (tpad with stop_duration, no -shortest)
        cmd_documented = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', '[0:v]tpad=stop_mode=clone:stop_duration=300[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
            output_documented
        ]
        
        result2 = subprocess.run(cmd_documented, capture_output=True, text=True)
        print("\nDocumented Implementation (from VIDEO_PROCESSING.md):")
        print("Filter: '[0:v]tpad=stop_mode=clone:stop_duration=300[v]'")
        print("Without -shortest flag")
        
        if result2.returncode == 0:
            duration2 = get_media_duration(output_documented)
            print(f"Result: Output duration = {duration2:.2f}s")
        else:
            print(f"Error: {result2.stderr[:200]}")
        
        video_duration = get_media_duration(video_path)
        audio_duration = get_media_duration(audio_path)
        
        print(f"\nComparison:")
        print(f"Input video: {video_duration:.2f}s")
        print(f"Input audio: {audio_duration:.2f}s")
        print(f"Current implementation output: {duration1:.2f}s (should be {audio_duration:.2f}s)")
        print(f"Documented implementation output: {duration2:.2f}s (should be {audio_duration:.2f}s)")
        
        print("\n=== Issues Found ===")
        print("1. Current implementation uses tpad WITHOUT stop_duration")
        print("   - This does NOT extend the video indefinitely")
        print("   - The comment on line 119 is incorrect")
        print("2. Current implementation uses -shortest flag")
        print("   - This would stop at the shorter stream")
        print("   - But since tpad doesn't extend, video remains 2s, making it the shortest")
        print("3. Result: Output is only 2 seconds instead of 5 seconds!")


def test_fix_recommendation():
    """Test the recommended fix."""
    print("\n\n=== Testing Recommended Fix ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        audio_path = os.path.join(tmpdir, "test_audio.aac")
        output_fixed = os.path.join(tmpdir, "output_fixed.mp4")
        
        # Create 2-second video and 5-second audio
        create_test_video(2, video_path)
        create_test_audio(5, audio_path)
        
        # Recommended fix: Add stop_duration to tpad
        cmd_fixed = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', '[0:v]tpad=stop_mode=clone:stop_duration=10000[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-shortest',
            output_fixed
        ]
        
        result = subprocess.run(cmd_fixed, capture_output=True, text=True)
        print("Recommended Fix:")
        print("Change line 141 from:")
        print("  {'filter': '[0:v]tpad=stop_mode=clone[v]'}")
        print("To:")
        print("  {'filter': '[0:v]tpad=stop_mode=clone:stop_duration=10000[v]'}")
        print("\nThis adds stop_duration=10000 (2.78 hours of padding)")
        
        if result.returncode == 0:
            video_duration = get_media_duration(video_path)
            audio_duration = get_media_duration(audio_path)
            output_duration = get_media_duration(output_fixed)
            print(f"\nResult:")
            print(f"Input video: {video_duration:.2f}s")
            print(f"Input audio: {audio_duration:.2f}s")
            print(f"Output: {output_duration:.2f}s")
            print(f"Success: Output matches audio duration!" if abs(output_duration - audio_duration) < 0.5 else "Failed!")
        else:
            print(f"Error: {result.stderr[:200]}")


def main():
    """Run tests."""
    print("Analyzing Current Implementation Issues")
    print("=" * 60)
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except:
        print("Error: ffmpeg not found. Please install ffmpeg to run these tests.")
        return
    
    test_current_vs_documented()
    test_fix_recommendation()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("The current implementation has a bug on line 141 of nca_service.py")
    print("The tpad filter needs stop_duration parameter to extend video")
    print("Without it, the video doesn't extend and -shortest makes it stop at 2s")


if __name__ == "__main__":
    main()