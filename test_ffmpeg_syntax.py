#!/usr/bin/env python3
"""Test FFmpeg filter syntax and behavior with -shortest flag."""

import subprocess
import os
import tempfile

def test_tpad_syntax():
    """Test if the tpad filter syntax is valid."""
    
    print("Testing FFmpeg tpad filter syntax")
    print("=" * 50)
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a 5-second test video
        video_file = os.path.join(tmpdir, "test_video.mp4")
        audio_file = os.path.join(tmpdir, "test_audio.mp3")
        output_file = os.path.join(tmpdir, "output.mp4")
        
        # Generate 5-second test video
        video_cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'testsrc=duration=5:size=320x240:rate=30',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            video_file
        ]
        
        # Generate 10-second test audio
        audio_cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'sine=frequency=440:duration=10',
            '-c:a', 'mp3',
            audio_file
        ]
        
        print("Creating test files...")
        subprocess.run(video_cmd, capture_output=True, check=True)
        subprocess.run(audio_cmd, capture_output=True, check=True)
        
        # Test the exact filter syntax from nca_service.py
        test_cmd = [
            'ffmpeg', '-y',
            '-i', video_file,
            '-i', audio_file,
            '-filter_complex', '[0:v]tpad=stop_mode=clone:stop_duration=10000[v]',
            '-map', '[v]',
            '-map', '1:a:0',
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-shortest',
            output_file
        ]
        
        print("\nTesting FFmpeg command:")
        print(" ".join(test_cmd))
        
        try:
            result = subprocess.run(test_cmd, capture_output=True, text=True, check=True)
            print("\n✓ FFmpeg command executed successfully!")
            
            # Check output duration
            probe_cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                output_file
            ]
            
            duration_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            output_duration = float(duration_result.stdout.strip())
            
            print(f"\nDurations:")
            print(f"- Video: 5 seconds")
            print(f"- Audio: 10 seconds")
            print(f"- Output: {output_duration:.2f} seconds")
            
            # Analyze behavior with -shortest flag
            print("\nAnalysis of -shortest flag behavior:")
            print("=" * 30)
            
            if abs(output_duration - 10.0) < 0.5:
                print("✓ Output matches audio duration (10s)")
                print("✓ Video was extended with last frame hold")
                print("✓ -shortest flag correctly uses audio as limiting factor")
            elif abs(output_duration - 5.0) < 0.5:
                print("✗ Output matches video duration (5s)")
                print("✗ -shortest flag may be limiting to original video length")
                print("✗ This suggests tpad might not be working as expected with -shortest")
            else:
                print(f"? Unexpected output duration: {output_duration:.2f}s")
            
            # Test without -shortest flag
            print("\n\nTesting WITHOUT -shortest flag:")
            print("=" * 30)
            
            output_file2 = os.path.join(tmpdir, "output_no_shortest.mp4")
            test_cmd2 = test_cmd[:-2] + [output_file2]  # Remove -shortest
            
            result2 = subprocess.run(test_cmd2, capture_output=True, text=True, check=True)
            
            duration_result2 = subprocess.run(
                probe_cmd[:-1] + [output_file2], 
                capture_output=True, text=True, check=True
            )
            output_duration2 = float(duration_result2.stdout.strip())
            
            print(f"Output duration without -shortest: {output_duration2:.2f} seconds")
            
            if abs(output_duration2 - 10.0) < 0.5:
                print("✓ Output correctly matches audio duration")
                print("✓ tpad filter extends video to match audio length")
            
        except subprocess.CalledProcessError as e:
            print(f"\n✗ FFmpeg command failed!")
            print(f"Error: {e.stderr}")
            
            # Check if it's a syntax error
            if "Invalid argument" in e.stderr or "No such filter" in e.stderr:
                print("\nThe filter syntax appears to be invalid.")
            else:
                print("\nThe command failed for another reason.")

def analyze_shortest_behavior():
    """Analyze how -shortest interacts with tpad filter."""
    
    print("\n\nUnderstanding -shortest flag with tpad:")
    print("=" * 50)
    
    print("The -shortest flag behavior:")
    print("- It stops encoding when the shortest input stream ends")
    print("- With tpad filter extending video to 10000 seconds:")
    print("  • Video stream: effectively 10000 seconds (padded)")
    print("  • Audio stream: actual audio duration (e.g., 10 seconds)")
    print("  • Result: -shortest stops at audio end (10 seconds)")
    print("\nThis is the CORRECT behavior for the use case!")
    print("The combination ensures output always matches audio duration.")

if __name__ == "__main__":
    test_tpad_syntax()
    analyze_shortest_behavior()