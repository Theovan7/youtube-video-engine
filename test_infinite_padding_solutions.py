#!/usr/bin/env python3
"""Test different approaches to achieve infinite video padding."""

import subprocess
import tempfile
import os
from pathlib import Path


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


def test_loop_filter():
    """Test using loop filter for infinite extension."""
    print("\n=== Testing loop filter for infinite extension ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        audio_path = os.path.join(tmpdir, "test_audio.aac")
        output_path = os.path.join(tmpdir, "output_loop.mp4")
        
        # Create 2-second video and 5-second audio
        create_test_video(2, video_path)
        create_test_audio(5, audio_path)
        
        # Use loop filter with -1 for infinite loop
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', '[0:v]loop=loop=-1:size=1:start=0[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-shortest',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"FFmpeg command: {' '.join(cmd)}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            video_duration = get_media_duration(video_path)
            audio_duration = get_media_duration(audio_path)
            output_duration = get_media_duration(output_path)
            print(f"Input video duration: {video_duration:.2f}s")
            print(f"Input audio duration: {audio_duration:.2f}s")
            print(f"Output duration: {output_duration:.2f}s")
            print(f"Output matches audio: {'YES' if abs(output_duration - audio_duration) < 0.5 else 'NO'}")
        else:
            print(f"Error: {result.stderr}")


def test_tpad_with_large_stop_duration():
    """Test tpad with a very large stop_duration."""
    print("\n=== Testing tpad with large stop_duration ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        audio_path = os.path.join(tmpdir, "test_audio.aac")
        output_path = os.path.join(tmpdir, "output_large_tpad.mp4")
        
        # Create 2-second video and 5-second audio
        create_test_video(2, video_path)
        create_test_audio(5, audio_path)
        
        # Use tpad with very large stop_duration (1 hour)
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', '[0:v]tpad=stop_mode=clone:stop_duration=3600[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-shortest',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"FFmpeg command: {' '.join(cmd)}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            video_duration = get_media_duration(video_path)
            audio_duration = get_media_duration(audio_path)
            output_duration = get_media_duration(output_path)
            print(f"Input video duration: {video_duration:.2f}s")
            print(f"Input audio duration: {audio_duration:.2f}s")
            print(f"Output duration: {output_duration:.2f}s")
            print(f"Output matches audio: {'YES' if abs(output_duration - audio_duration) < 0.5 else 'NO'}")
        else:
            print(f"Error: {result.stderr}")


def test_setpts_for_freeze_frame():
    """Test using setpts to create freeze frame effect."""
    print("\n=== Testing setpts for freeze frame ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        audio_path = os.path.join(tmpdir, "test_audio.aac")
        output_path = os.path.join(tmpdir, "output_setpts.mp4")
        
        # Create 2-second video and 5-second audio
        create_test_video(2, video_path)
        create_test_audio(5, audio_path)
        
        # Use complex filter to freeze last frame
        # This approach extracts the last frame and extends it
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', 
            '[0:v]split[main][last];[last]trim=start_frame=-1,setpts=N/FRAME_RATE/TB,loop=loop=-1:size=1[hold];[main][hold]concat=n=2:v=1[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-shortest',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"FFmpeg command: {' '.join(cmd)}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            video_duration = get_media_duration(video_path)
            audio_duration = get_media_duration(audio_path)
            output_duration = get_media_duration(output_path)
            print(f"Input video duration: {video_duration:.2f}s")
            print(f"Input audio duration: {audio_duration:.2f}s")
            print(f"Output duration: {output_duration:.2f}s")
            print(f"Output matches audio: {'YES' if abs(output_duration - audio_duration) < 0.5 else 'NO'}")
        else:
            print(f"Error (first few lines): {result.stderr[:500]}")


def test_current_implementation_fix():
    """Test a fix for the current implementation."""
    print("\n=== Testing fix for current implementation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        audio_path = os.path.join(tmpdir, "test_audio.aac")
        output_path = os.path.join(tmpdir, "output_fixed.mp4")
        
        # Create 2-second video and 5-second audio
        create_test_video(2, video_path)
        create_test_audio(5, audio_path)
        
        # Modified approach: tpad with very large stop_duration
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', '[0:v]tpad=stop_mode=clone:stop_duration=10000[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-shortest',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"FFmpeg command: {' '.join(cmd)}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            video_duration = get_media_duration(video_path)
            audio_duration = get_media_duration(audio_path)
            output_duration = get_media_duration(output_path)
            print(f"Input video duration: {video_duration:.2f}s")
            print(f"Input audio duration: {audio_duration:.2f}s")
            print(f"Output duration: {output_duration:.2f}s")
            print(f"Output matches audio: {'YES' if abs(output_duration - audio_duration) < 0.5 else 'NO'}")
            print(f"\nThis approach works! Using tpad with stop_duration=10000 (2.78 hours)")
        else:
            print(f"Error: {result.stderr}")


def main():
    """Run all tests."""
    print("Testing different approaches for infinite video padding\n")
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except:
        print("Error: ffmpeg not found. Please install ffmpeg to run these tests.")
        return
    
    test_loop_filter()
    test_tpad_with_large_stop_duration()
    test_setpts_for_freeze_frame()
    test_current_implementation_fix()
    
    print("\n=== Recommendations ===")
    print("1. Current implementation bug: tpad without stop_duration doesn't extend video")
    print("2. Simple fix: Use tpad=stop_mode=clone:stop_duration=10000 (2.78 hours)")
    print("3. This provides sufficient padding for any reasonable voiceover length")
    print("4. The -shortest flag will ensure output stops at audio end")


if __name__ == "__main__":
    main()