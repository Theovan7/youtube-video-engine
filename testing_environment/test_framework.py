#!/usr/bin/env python3
"""
YouTube Video Engine Testing Framework
Provides utilities for testing API endpoints with local backup validation
"""

import os
import json
import time
import requests
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import subprocess

class VideoEngineTestFramework:
    """Main testing framework for YouTube Video Engine"""
    
    def __init__(self, base_url: str = "http://localhost:5000", 
                 local_backup_path: str = "./local_backups"):
        self.base_url = base_url
        self.local_backup_path = Path(local_backup_path)
        self.test_results = []
        
    def setup(self):
        """Ensure test environment is ready"""
        # Create local backup directories if they don't exist
        for subdir in ['voiceovers', 'videos', 'music', 'images']:
            path = self.local_backup_path / 'youtube-video-engine' / subdir
            path.mkdir(parents=True, exist_ok=True)
            
    def wait_for_local_file(self, filename_pattern: str, file_type: str, 
                           timeout: int = 30) -> Optional[Path]:
        """
        Wait for a file to appear in local backups
        
        Args:
            filename_pattern: Pattern to match (can be partial filename)
            file_type: Type of file (voiceovers, videos, music, images)
            timeout: Maximum seconds to wait
            
        Returns:
            Path to the file if found, None otherwise
        """
        search_dir = self.local_backup_path / 'youtube-video-engine' / file_type
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # List all files in directory
            if search_dir.exists():
                for file_path in search_dir.iterdir():
                    if filename_pattern in file_path.name:
                        return file_path
            
            time.sleep(0.5)  # Check every 500ms
            
        return None
    
    def validate_file(self, file_path: Path, expected_type: str) -> Dict[str, Any]:
        """
        Validate a file exists and has expected properties
        
        Returns dict with validation results
        """
        if not file_path.exists():
            return {"valid": False, "error": "File does not exist"}
            
        result = {
            "valid": True,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        # Calculate checksum
        with open(file_path, 'rb') as f:
            result["checksum"] = hashlib.md5(f.read()).hexdigest()
        
        # Type-specific validation
        if expected_type == "voiceovers" and file_path.suffix == ".mp3":
            # Check MP3 duration using ffprobe
            try:
                duration = self._get_media_duration(file_path)
                result["duration"] = duration
                result["valid"] = duration > 0
            except:
                result["valid"] = False
                result["error"] = "Could not read audio duration"
                
        elif expected_type == "videos" and file_path.suffix == ".mp4":
            # Check video properties
            try:
                duration = self._get_media_duration(file_path)
                result["duration"] = duration
                result["valid"] = duration > 0
            except:
                result["valid"] = False
                result["error"] = "Could not read video duration"
                
        elif expected_type == "images" and file_path.suffix in [".png", ".jpg", ".jpeg"]:
            # Just check file size for images
            result["valid"] = result["size"] > 1000  # At least 1KB
            
        return result
    
    def _get_media_duration(self, file_path: Path) -> float:
        """Get duration of audio/video file using ffprobe"""
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    
    def test_endpoint(self, endpoint: str, method: str = "POST", 
                     payload: Dict[str, Any] = None,
                     expected_files: List[Tuple[str, str]] = None) -> Dict[str, Any]:
        """
        Test an API endpoint and validate expected files
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            payload: Request payload
            expected_files: List of (filename_pattern, file_type) tuples
            
        Returns:
            Test result dictionary
        """
        test_result = {
            "endpoint": endpoint,
            "method": method,
            "timestamp": datetime.now().isoformat(),
            "request": payload,
            "response": None,
            "files": [],
            "success": False
        }
        
        # Make API request
        try:
            url = f"{self.base_url}{endpoint}"
            if method == "POST":
                response = requests.post(url, json=payload, timeout=60)
            elif method == "GET":
                response = requests.get(url, params=payload, timeout=60)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            test_result["response"] = {
                "status_code": response.status_code,
                "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            # For successful requests, wait for expected files
            if response.status_code in [200, 201, 202]:
                if expected_files:
                    for filename_pattern, file_type in expected_files:
                        print(f"Waiting for {file_type}: {filename_pattern}...")
                        file_path = self.wait_for_local_file(filename_pattern, file_type)
                        
                        if file_path:
                            validation = self.validate_file(file_path, file_type)
                            test_result["files"].append({
                                "pattern": filename_pattern,
                                "type": file_type,
                                "found": True,
                                "validation": validation
                            })
                        else:
                            test_result["files"].append({
                                "pattern": filename_pattern,
                                "type": file_type,
                                "found": False
                            })
                
                # Check if all expected files were found
                test_result["success"] = all(f["found"] for f in test_result["files"]) if expected_files else True
            
        except Exception as e:
            test_result["error"] = str(e)
            
        self.test_results.append(test_result)
        return test_result
    
    def generate_report(self) -> str:
        """Generate a test report"""
        report = []
        report.append("YouTube Video Engine Test Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Total Tests: {len(self.test_results)}")
        report.append("")
        
        passed = sum(1 for r in self.test_results if r.get("success"))
        report.append(f"Passed: {passed}/{len(self.test_results)}")
        report.append("")
        
        for i, result in enumerate(self.test_results, 1):
            report.append(f"Test {i}: {result['endpoint']}")
            report.append(f"  Status: {'✅ PASS' if result['success'] else '❌ FAIL'}")
            
            if result.get("response"):
                report.append(f"  Response: {result['response']['status_code']}")
                
            if result.get("files"):
                report.append(f"  Files:")
                for f in result["files"]:
                    status = "✓" if f["found"] else "✗"
                    report.append(f"    {status} {f['type']}/{f['pattern']}")
                    if f["found"] and f.get("validation"):
                        val = f["validation"]
                        report.append(f"      Size: {val['size']:,} bytes")
                        if "duration" in val:
                            report.append(f"      Duration: {val['duration']:.1f}s")
                            
            if result.get("error"):
                report.append(f"  Error: {result['error']}")
                
            report.append("")
            
        return "\n".join(report)

    def cleanup_test_files(self):
        """Clean up test files from local backups"""
        # Implementation depends on your cleanup strategy
        pass


class WebhookSimulator:
    """Simulates webhook callbacks for testing async operations"""
    
    def __init__(self, target_url: str):
        self.target_url = target_url
        
    def simulate_nca_callback(self, job_id: str, success: bool = True, 
                            output_url: str = None) -> requests.Response:
        """Simulate an NCA webhook callback"""
        payload = {
            "id": job_id,
            "job_id": f"nca-{int(time.time())}",
            "code": 200 if success else 500,
            "response": {
                "url": output_url or f"https://phi-bucket.nyc3.digitaloceanspaces.com/test/{job_id}.mp4"
            } if success else {
                "error": "Processing failed"
            }
        }
        
        return requests.post(f"{self.target_url}/webhooks/nca-toolkit", json=payload)
    
    def simulate_goapi_callback(self, job_id: str, task_type: str, 
                              success: bool = True) -> requests.Response:
        """Simulate a GoAPI webhook callback"""
        payload = {
            "data": {
                "id": job_id,
                "task": task_type,
                "status": "completed" if success else "failed"
            }
        }
        
        if success:
            if task_type == "musicgen":
                payload["data"]["music_result"] = {
                    "audio_url": f"https://example.com/music/{job_id}.mp3"
                }
            elif task_type == "kling":
                payload["data"]["video_result"] = {
                    "video_url": f"https://example.com/video/{job_id}.mp4"
                }
                
        return requests.post(f"{self.target_url}/webhooks/goapi", json=payload)