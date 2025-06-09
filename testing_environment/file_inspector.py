#!/usr/bin/env python3
"""
File Inspector for YouTube Video Engine
Monitors and analyzes files in local_backups directory
"""

import os
import sys
import time
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileInspector(FileSystemEventHandler):
    """Monitors and inspects files in local backup directory"""
    
    def __init__(self, backup_path: str = "./local_backups"):
        self.backup_path = Path(backup_path) / "youtube-video-engine"
        self.files_info = {}
        self.stats = {
            "voiceovers": {"count": 0, "total_size": 0, "total_duration": 0},
            "videos": {"count": 0, "total_size": 0, "total_duration": 0},
            "music": {"count": 0, "total_size": 0},
            "images": {"count": 0, "total_size": 0}
        }
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self.inspect_file(Path(event.src_path))
            
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self.inspect_file(Path(event.src_path))
    
    def inspect_file(self, file_path: Path) -> Dict:
        """Inspect a single file and extract metadata"""
        if not file_path.exists():
            return None
            
        info = {
            "path": str(file_path),
            "name": file_path.name,
            "size": file_path.stat().st_size,
            "created": datetime.fromtimestamp(file_path.stat().st_ctime),
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
            "type": self._determine_file_type(file_path),
            "checksum": self._calculate_checksum(file_path)
        }
        
        # Extract media-specific metadata
        if file_path.suffix in [".mp3", ".mp4", ".wav", ".m4a"]:
            media_info = self._get_media_info(file_path)
            info.update(media_info)
            
        # Extract segment/job IDs from filename
        ids = self._extract_ids(file_path.name)
        info.update(ids)
        
        # Store in our database
        self.files_info[str(file_path)] = info
        
        # Update statistics
        self._update_stats(info)
        
        # Print summary
        self._print_file_summary(info)
        
        return info
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determine file type from path and extension"""
        path_str = str(file_path).lower()
        
        if "voiceover" in path_str or file_path.suffix == ".mp3":
            return "voiceover"
        elif "video" in path_str or file_path.suffix == ".mp4":
            return "video"
        elif "music" in path_str:
            return "music"
        elif file_path.suffix in [".png", ".jpg", ".jpeg", ".webp"]:
            return "image"
        else:
            return "unknown"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def _get_media_info(self, file_path: Path) -> Dict:
        """Extract media information using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                info = {}
                
                # Extract format info
                if 'format' in data:
                    fmt = data['format']
                    info['duration'] = float(fmt.get('duration', 0))
                    info['bitrate'] = int(fmt.get('bit_rate', 0))
                    info['format_name'] = fmt.get('format_name', '')
                    
                # Extract stream info
                if 'streams' in data:
                    for stream in data['streams']:
                        if stream['codec_type'] == 'video':
                            info['video_codec'] = stream.get('codec_name', '')
                            info['width'] = stream.get('width', 0)
                            info['height'] = stream.get('height', 0)
                            info['fps'] = eval(stream.get('r_frame_rate', '0/1'))
                        elif stream['codec_type'] == 'audio':
                            info['audio_codec'] = stream.get('codec_name', '')
                            info['sample_rate'] = int(stream.get('sample_rate', 0))
                            info['channels'] = stream.get('channels', 0)
                            
                return info
        except Exception as e:
            print(f"Error getting media info: {e}")
            
        return {}
    
    def _extract_ids(self, filename: str) -> Dict:
        """Extract Airtable record IDs from filename"""
        ids = {}
        
        # Common patterns
        if filename.startswith("rec") and len(filename) >= 17:
            ids["record_id"] = filename[:17]
            
        # Look for segment pattern (e.g., segment_recXXX)
        if "segment_" in filename:
            parts = filename.split("segment_")
            if len(parts) > 1 and parts[1].startswith("rec"):
                ids["segment_id"] = parts[1][:17]
                
        # Look for video pattern
        if "video_" in filename:
            parts = filename.split("video_")
            if len(parts) > 1 and parts[1].startswith("rec"):
                ids["video_id"] = parts[1][:17]
                
        return ids
    
    def _update_stats(self, file_info: Dict):
        """Update statistics based on file info"""
        file_type = file_info.get("type")
        
        if file_type == "voiceover":
            self.stats["voiceovers"]["count"] += 1
            self.stats["voiceovers"]["total_size"] += file_info["size"]
            if "duration" in file_info:
                self.stats["voiceovers"]["total_duration"] += file_info["duration"]
                
        elif file_type == "video":
            self.stats["videos"]["count"] += 1
            self.stats["videos"]["total_size"] += file_info["size"]
            if "duration" in file_info:
                self.stats["videos"]["total_duration"] += file_info["duration"]
                
        elif file_type == "music":
            self.stats["music"]["count"] += 1
            self.stats["music"]["total_size"] += file_info["size"]
            
        elif file_type == "image":
            self.stats["images"]["count"] += 1
            self.stats["images"]["total_size"] += file_info["size"]
    
    def _print_file_summary(self, info: Dict):
        """Print a summary of the file"""
        emoji_map = {
            "voiceover": "🎤",
            "video": "🎬",
            "music": "🎵",
            "image": "🖼️",
            "unknown": "📄"
        }
        
        emoji = emoji_map.get(info["type"], "📄")
        print(f"\n{emoji} New file detected: {info['name']}")
        print(f"   Type: {info['type']}")
        print(f"   Size: {info['size']:,} bytes")
        
        if "duration" in info:
            print(f"   Duration: {info['duration']:.1f} seconds")
            
        if "width" in info and "height" in info:
            print(f"   Resolution: {info['width']}x{info['height']}")
            
        if "record_id" in info:
            print(f"   Record ID: {info['record_id']}")
            
        print(f"   Checksum: {info['checksum'][:8]}...")
    
    def scan_existing_files(self):
        """Scan all existing files in backup directory"""
        print("Scanning existing files...")
        
        for file_type in ["voiceovers", "videos", "music", "images"]:
            type_dir = self.backup_path / file_type
            if type_dir.exists():
                for file_path in type_dir.iterdir():
                    if file_path.is_file():
                        self.inspect_file(file_path)
                        
        self.print_statistics()
    
    def print_statistics(self):
        """Print current statistics"""
        print("\n" + "="*60)
        print("Local Backup Statistics")
        print("="*60)
        
        for file_type, stats in self.stats.items():
            if stats["count"] > 0:
                print(f"\n{file_type.capitalize()}:")
                print(f"  Count: {stats['count']}")
                print(f"  Total Size: {stats['total_size']:,} bytes ({stats['total_size']/1024/1024:.1f} MB)")
                
                if "total_duration" in stats and stats["total_duration"] > 0:
                    avg_duration = stats["total_duration"] / stats["count"]
                    print(f"  Total Duration: {stats['total_duration']:.1f} seconds")
                    print(f"  Average Duration: {avg_duration:.1f} seconds")
    
    def find_files_by_id(self, record_id: str) -> List[Dict]:
        """Find all files related to a specific Airtable record ID"""
        matching_files = []
        
        for file_path, info in self.files_info.items():
            if (info.get("record_id") == record_id or 
                info.get("segment_id") == record_id or
                info.get("video_id") == record_id or
                record_id in info["name"]):
                matching_files.append(info)
                
        return matching_files
    
    def export_report(self, output_path: str = "backup_inspection_report.json"):
        """Export detailed report of all files"""
        report = {
            "generated": datetime.now().isoformat(),
            "backup_path": str(self.backup_path),
            "statistics": self.stats,
            "files": list(self.files_info.values())
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"\nReport exported to: {output_path}")


def main():
    """Main function for file inspector"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inspect files in local backup")
    parser.add_argument("--path", help="Local backup path", default="./local_backups")
    parser.add_argument("--watch", action="store_true", help="Watch for new files")
    parser.add_argument("--find", help="Find files by record ID")
    parser.add_argument("--export", action="store_true", help="Export detailed report")
    
    args = parser.parse_args()
    
    inspector = FileInspector(args.path)
    
    # Always scan existing files first
    inspector.scan_existing_files()
    
    if args.find:
        print(f"\nSearching for files with ID: {args.find}")
        files = inspector.find_files_by_id(args.find)
        
        if files:
            print(f"Found {len(files)} file(s):")
            for f in files:
                print(f"  - {f['name']} ({f['type']}, {f['size']:,} bytes)")
        else:
            print("No files found with that ID")
            
    if args.export:
        inspector.export_report()
    
    if args.watch:
        print("\n👁️  Watching for new files... (Press Ctrl+C to stop)")
        
        observer = Observer()
        observer.schedule(inspector, str(inspector.backup_path), recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\nStopped watching.")
            
        observer.join()
        
        # Final statistics
        inspector.print_statistics()
        
        if args.export:
            inspector.export_report()


if __name__ == "__main__":
    main()