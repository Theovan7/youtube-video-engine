#!/usr/bin/env python3
"""
Extract real API request payloads from Airtable Jobs table for testing Pydantic models.
"""

import json
import os
import ast
from services.airtable_service import AirtableService
from config import get_config

def extract_api_request_data():
    """Extract real API request payloads from Airtable."""
    config = get_config()()
    airtable = AirtableService()
    
    print("Extracting API request data from Airtable Jobs table...")
    
    # Get recent jobs with request payloads
    jobs = airtable.jobs_table.all(max_records=100)
    
    # Organize payloads by job type
    payloads = {
        'process_script': [],
        'generate_voiceover': [],
        'combine_media': [],
        'concatenate_videos': [],
        'generate_music': [],
        'generate_image': [],
        'generate_video': []
    }
    
    # Also get some segments and videos for context
    segments = airtable.segments_table.all(max_records=20)
    videos = airtable.videos_table.all(max_records=10)
    
    print(f"Found {len(jobs)} jobs, {len(segments)} segments, {len(videos)} videos")
    
    print(f"\nProcessing jobs...")
    job_count = 0
    for job in jobs:
        fields = job['fields']
        job_type = fields.get('Type', '').lower()  # Changed from 'Job Type' to 'Type'
        request_payload = fields.get('Request Payload', '')
        response_payload = fields.get('Response Payload', '')
        status = fields.get('Status', '')
        
        job_count += 1
        if job_count <= 5:  # Debug first 5 jobs
            all_fields = list(fields.keys())
            print(f"Job {job['id']}: Fields={all_fields[:5]}...")  # Show first 5 fields
        
        if request_payload:
            # Parse payload
            try:
                if isinstance(request_payload, str) and request_payload.strip():
                    # Try JSON first
                    try:
                        payload = json.loads(request_payload)
                    except:
                        # Try Python literal
                        payload = ast.literal_eval(request_payload)
                else:
                    continue
                    
                # Add metadata
                payload_data = {
                    'job_id': job['id'],
                    'job_type': fields.get('Type', ''),  # Keep original case
                    'status': status,
                    'request_payload': payload,
                    'response_payload': response_payload,
                    'service': fields.get('Service', ''),
                    'external_job_id': fields.get('External Job ID', '')
                }
                
                # Categorize by job type
                if 'voiceover' in job_type:
                    payloads['generate_voiceover'].append(payload_data)
                elif 'combine' in job_type and 'segment' in job_type:
                    payloads['combine_media'].append(payload_data)
                elif 'concatenate' in job_type or ('combine' in job_type and 'all' in job_type):
                    payloads['concatenate_videos'].append(payload_data)
                elif 'music' in job_type:
                    payloads['generate_music'].append(payload_data)
                elif 'image' in job_type:
                    payloads['generate_image'].append(payload_data)
                elif 'video' in job_type and 'concatenate' not in job_type:
                    payloads['generate_video'].append(payload_data)
                    
            except Exception as e:
                print(f"Failed to parse payload for job {job['id']}: {e}")
    
    # Save extracted data
    os.makedirs('testing_environment/test_inputs/api_requests/real_data', exist_ok=True)
    
    # Save job payloads
    for job_type, job_payloads in payloads.items():
        if job_payloads:
            filename = f'testing_environment/test_inputs/api_requests/real_data/{job_type}_requests.json'
            with open(filename, 'w') as f:
                json.dump(job_payloads, f, indent=2)
            print(f"Saved {len(job_payloads)} {job_type} request payloads")
    
    # Save sample segments and videos for reference
    segments_data = []
    for segment in segments[:10]:  # Just first 10
        fields = segment['fields']
        segments_data.append({
            'segment_id': segment['id'],
            'text': fields.get('SRT Text', ''),
            'video_id': fields.get('Videos', [None])[0],
            'status': fields.get('Status', ''),
            'voiceover': bool(fields.get('Voiceover')),
            'video': bool(fields.get('Video')),
            'combined': bool(fields.get('Voiceover + Video'))
        })
    
    with open('testing_environment/test_inputs/api_requests/real_data/sample_segments.json', 'w') as f:
        json.dump(segments_data, f, indent=2)
    
    videos_data = []
    for video in videos[:5]:  # Just first 5
        fields = video['fields']
        videos_data.append({
            'video_id': video['id'],
            'description': fields.get('Description', ''),
            'script': fields.get('Video Script', '')[:100] + '...' if fields.get('Video Script') else '',
            'has_production_video': bool(fields.get('Production Video')),
            'has_music': bool(fields.get('Music'))
        })
    
    with open('testing_environment/test_inputs/api_requests/real_data/sample_videos.json', 'w') as f:
        json.dump(videos_data, f, indent=2)
    
    return payloads

if __name__ == "__main__":
    payloads = extract_api_request_data()
    
    # Print summary
    print("\nSummary:")
    for job_type, job_payloads in payloads.items():
        if job_payloads:
            print(f"- {job_type}: {len(job_payloads)} payloads")
            # Show example
            if job_payloads:
                example = job_payloads[0]['request_payload']
                print(f"  Example keys: {list(example.keys()) if isinstance(example, dict) else type(example)}")