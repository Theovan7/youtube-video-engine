#!/usr/bin/env python3
"""
Check segments that might be waiting for combination.
"""

from datetime import datetime, timedelta
from services.airtable_service import AirtableService

airtable = AirtableService()

def check_segments_status():
    """Check segments status, especially those in 'Combining Media' state."""
    print("Checking Segments Status...")
    print("=" * 80)
    
    try:
        # Get segments table
        segments_table = airtable.segments_table
        all_segments = segments_table.all()
        
        # Categorize segments
        status_counts = {}
        combining_segments = []
        ready_segments = []
        recent_segments = []
        
        current_time = datetime.utcnow()
        
        for segment in all_segments:
            fields = segment.get('fields', {})
            status = fields.get('Status', 'Unknown')
            
            # Count by status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Check if in combining state
            if status == 'Combining Media':
                combining_segments.append(segment)
            
            # Check if ready for combination (has both voiceover and video)
            has_voiceover = bool(fields.get('Voiceover'))
            has_video = bool(fields.get('Video'))
            has_combined = bool(fields.get('Voiceover + Video'))
            
            if has_voiceover and has_video and not has_combined and status != 'combined':
                ready_segments.append(segment)
            
            # Check recent segments
            created_time = fields.get('Created Time', '')
            if created_time:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', ''))
                    age_minutes = (current_time - created_dt).total_seconds() / 60
                    if age_minutes <= 30:
                        recent_segments.append({
                            'segment': segment,
                            'age_minutes': age_minutes
                        })
                except:
                    pass
        
        # Show status summary
        print("\nSEGMENT STATUS SUMMARY:")
        print("-" * 40)
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
        print(f"\nTotal segments: {len(all_segments)}")
        
        # Show segments in "Combining Media" state
        if combining_segments:
            print(f"\n\nSEGMENTS IN 'Combining Media' STATE: {len(combining_segments)}")
            print("-" * 80)
            
            for segment in combining_segments[:10]:
                analyze_segment(segment)
        
        # Show segments ready for combination
        if ready_segments:
            print(f"\n\nSEGMENTS READY FOR COMBINATION: {len(ready_segments)}")
            print("(Have both voiceover and video but no combined output)")
            print("-" * 80)
            
            for segment in ready_segments[:10]:
                analyze_segment(segment)
        
        # Show recent segments
        if recent_segments:
            print(f"\n\nRECENT SEGMENTS (last 30 minutes): {len(recent_segments)}")
            print("-" * 80)
            
            recent_segments.sort(key=lambda x: x['age_minutes'])
            
            for item in recent_segments[:10]:
                print(f"\nAge: {item['age_minutes']:.1f} minutes")
                analyze_segment(item['segment'])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def analyze_segment(segment):
    """Analyze a single segment."""
    segment_id = segment['id']
    fields = segment.get('fields', {})
    
    print(f"\nSegment: {segment_id}")
    print(f"  Status: {fields.get('Status', 'Unknown')}")
    print(f"  Text: {fields.get('Text', '')[:50]}...")
    
    # Check media files
    has_voiceover = bool(fields.get('Voiceover'))
    has_video = bool(fields.get('Video'))
    has_combined = bool(fields.get('Voiceover + Video'))
    
    print(f"  Voiceover: {'YES ✓' if has_voiceover else 'NO ✗'}")
    print(f"  Video: {'YES ✓' if has_video else 'NO ✗'}")
    print(f"  Combined: {'YES ✓' if has_combined else 'NO ✗'}")
    
    # Check related jobs
    jobs = fields.get('Jobs', [])
    if jobs:
        print(f"  Related Jobs: {len(jobs)} job(s)")
        # Show last job
        if jobs:
            print(f"    Last Job: {jobs[-1]}")
    
    # If stuck in combining, check when it started
    if fields.get('Status') == 'Combining Media':
        # Try to estimate how long it's been combining
        voiceover_urls = fields.get('Voiceover', [])
        video_urls = fields.get('Video', [])
        
        if voiceover_urls and video_urls:
            print(f"  ⚠️  Has both files but stuck in 'Combining Media'")
            print(f"  Voiceover URL: {voiceover_urls[0].get('url', 'N/A')[:50]}...")
            print(f"  Video URL: {video_urls[0].get('url', 'N/A')[:50]}...")

if __name__ == "__main__":
    check_segments_status()