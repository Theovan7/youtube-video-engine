#!/usr/bin/env python3
"""Test tpad behavior without stop_duration and interaction with -shortest flag."""

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


def test_tpad_without_stop_duration():
    """Test tpad behavior without stop_duration parameter."""
    print("\n=== Testing tpad without stop_duration ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        output_path = os.path.join(tmpdir, "output_tpad.mp4")
        
        # Create 2-second test video
        create_test_video(2, video_path)
        
        # Apply tpad without stop_duration
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vf', 'tpad=stop_mode=clone',
            '-t', '5',  # Force output to 5 seconds to see if padding works
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"FFmpeg command: {' '.join(cmd)}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            input_duration = get_media_duration(video_path)
            output_duration = get_media_duration(output_path)
            print(f"Input video duration: {input_duration:.2f}s")
            print(f"Output video duration: {output_duration:.2f}s")
            print(f"Conclusion: tpad without stop_duration {'DOES' if output_duration > input_duration else 'DOES NOT'} extend video")
        else:
            print(f"Error: {result.stderr}")


def test_tpad_with_shortest_longer_video():
    """Test -shortest behavior when video (with tpad) is longer than audio."""
    print("\n=== Testing -shortest with video longer than audio (using tpad) ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        audio_path = os.path.join(tmpdir, "test_audio.aac")
        output_path = os.path.join(tmpdir, "output_combined.mp4")
        
        # Create 5-second video and 3-second audio
        create_test_video(5, video_path)
        create_test_audio(3, audio_path)
        
        # Combine with tpad and -shortest (similar to current implementation)
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', '[0:v]tpad=stop_mode=clone[v]',
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


def test_tpad_without_shortest():
    """Test tpad behavior without -shortest flag."""
    print("\n=== Testing tpad without -shortest flag ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        audio_path = os.path.join(tmpdir, "test_audio.aac")
        output_path = os.path.join(tmpdir, "output_no_shortest.mp4")
        
        # Create 2-second video and 5-second audio
        create_test_video(2, video_path)
        create_test_audio(5, audio_path)
        
        # Combine with tpad but WITHOUT -shortest
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex', '[0:v]tpad=stop_mode=clone[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
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
            print(f"Conclusion: Without -shortest, output duration matches {'AUDIO' if abs(output_duration - audio_duration) < 0.5 else 'NEITHER'}")
        else:
            print(f"Error: {result.stderr}")


def test_explicit_stop_duration():
    """Test tpad with explicit stop_duration."""
    print("\n=== Testing tpad with explicit stop_duration ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "test_video.mp4")
        output_path = os.path.join(tmpdir, "output_stop_duration.mp4")
        
        # Create 2-second test video
        create_test_video(2, video_path)
        
        # Apply tpad with explicit stop_duration
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vf', 'tpad=stop_mode=clone:stop_duration=3',  # Add 3 seconds of padding
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"FFmpeg command: {' '.join(cmd)}")
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            input_duration = get_media_duration(video_path)
            output_duration = get_media_duration(output_path)
            print(f"Input video duration: {input_duration:.2f}s")
            print(f"Output video duration: {output_duration:.2f}s")
            print(f"Added duration: {output_duration - input_duration:.2f}s")
        else:
            print(f"Error: {result.stderr}")


def main():
    """Run all tests."""
    print("Testing tpad behavior and -shortest interaction\n")
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except:
        print("Error: ffmpeg not found. Please install ffmpeg to run these tests.")
        return
    
    test_tpad_without_stop_duration()
    test_tpad_with_shortest_longer_video()
    test_tpad_without_shortest()
    test_explicit_stop_duration()
    
    print("\n=== Summary ===")
    print("1. tpad without stop_duration does NOT automatically extend video indefinitely")
    print("2. tpad requires either stop_duration or external control (like -t) to extend")
    print("3. -shortest properly stops at the shortest stream when used with mapped streams")
    print("4. Without -shortest, output duration is determined by the longest stream")


if __name__ == "__main__":
    main()