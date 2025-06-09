#!/usr/bin/env python3
"""Check status of specific segments"""

import os
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Airtable
api = Api(os.getenv('AIRTABLE_API_KEY'))
base = api.base(os.getenv('AIRTABLE_BASE_ID'))
segments_table = base.table('Segments')

# Segment IDs to check
segment_ids = [
    'recTuqCj6GN2ajsxp',
    'reci0gT2LhNaIaFtp',
    'recjDBBDr7h8KwnTU',
    'recmXnXCm5tFVAlFo',
    'recphkqVVvJEwM19c'
]

print('Checking status of 5 segments...\n')
print('=' * 80)

# Track status
stuck_segments = []
completed_segments = []
pending_segments = []

for segment_id in segment_ids:
    try:
        record = segments_table.get(segment_id)
        fields = record.get('fields', {})
        
        status = fields.get('Status', 'No status')
        segment_number = fields.get('Segment #', 'Unknown')
        video_id_list = fields.get('Video ID', [])
        video_id = video_id_list[0] if video_id_list else 'Unknown'
        
        # Check media fields
        has_voiceover = bool(fields.get('Voiceover URL'))
        has_video = bool(fields.get('Video URL'))
        has_combined = bool(fields.get('Voiceover + Video'))
        
        print(f'\nSegment ID: {segment_id}')
        print(f'  Video ID: {video_id}')
        print(f'  Segment #: {segment_number}')
        print(f'  Current Status: {status}')
        print(f'  Media Present:')
        print(f'    - Voiceover URL: {"Yes" if has_voiceover else "No"}')
        print(f'    - Video URL: {"Yes" if has_video else "No"}')
        print(f'    - Combined Output: {"Yes" if has_combined else "No"}')
        
        # Categorize
        if status == 'Combining Media' and not has_combined:
            print('  => STUCK: In "Combining Media" but no output')
            stuck_segments.append(segment_id)
        elif status == 'combined' and has_combined:
            print('  => COMPLETE: Successfully combined')
            completed_segments.append(segment_id)
        elif status == 'Voiceover Ready':
            print('  => PENDING: Ready for combination')
            pending_segments.append(segment_id)
        else:
            print(f'  => OTHER: {status}')
            
    except Exception as e:
        print(f'\nError checking segment {segment_id}: {str(e)}')

print('\n' + '=' * 80)
print('\nFINAL SUMMARY:')
print(f'\n1. COMPLETED ({len(completed_segments)}):')
for seg in completed_segments:
    print(f'   - {seg}')

print(f'\n2. STUCK IN "Combining Media" ({len(stuck_segments)}):')
for seg in stuck_segments:
    print(f'   - {seg}')
    
print(f'\n3. PENDING ({len(pending_segments)}):')
for seg in pending_segments:
    print(f'   - {seg}')

print('\n' + '=' * 80)