#!/usr/bin/env python3
"""
Check segments related to stuck jobs to find their external job IDs.
"""

from services.airtable_service import AirtableService
import ast

airtable = AirtableService()

def check_segments_for_jobs():
    """Check segments to find external job IDs."""
    
    # The stuck job IDs
    job_ids = ['reci0gT2LhNaIaFtp', 'recphkqVVvJEwM19c']
    
    for job_id in job_ids:
        print(f"\nChecking job: {job_id}")
        print("-" * 50)
        
        try:
            # Get the job
            job = airtable.get_job(job_id)
            if not job:
                print(f"Job not found")
                continue
                
            fields = job['fields']
            print(f"Status: {fields.get('Status')}")
            print(f"Type: {fields.get('Job Type')}")
            print(f"Created: {fields.get('Created Time')}")
            
            # Parse request payload to find segment ID
            request_payload = fields.get('Request Payload', '{}')
            segment_id = None
            
            try:
                if request_payload and request_payload != '{}':
                    payload_data = ast.literal_eval(request_payload)
                    segment_id = payload_data.get('segment_id') or payload_data.get('record_id')
                    print(f"Segment ID from payload: {segment_id}")
            except:
                print("Could not parse request payload")
            
            # Check Related Segment Video field
            related_segments = fields.get('Related Segment Video', [])
            if related_segments:
                segment_id = related_segments[0]
                print(f"Segment ID from Related field: {segment_id}")
            
            # If we found a segment ID, check the segment
            if segment_id:
                try:
                    segment = airtable.get_segment(segment_id)
                    if segment:
                        seg_fields = segment['fields']
                        print(f"\nSegment {segment_id}:")
                        print(f"  Status: {seg_fields.get('Status')}")
                        print(f"  Has Voiceover: {'Yes' if seg_fields.get('Voiceover') else 'No'}")
                        print(f"  Has Video: {'Yes' if seg_fields.get('Video') else 'No'}")
                        print(f"  Has Combined: {'Yes' if seg_fields.get('Voiceover + Video') else 'No'}")
                        
                        # Check if combined video exists
                        combined = seg_fields.get('Voiceover + Video')
                        if combined and len(combined) > 0:
                            url = combined[0].get('url', '')
                            print(f"  Combined video URL: {url}")
                            
                            # Extract external job ID from URL if possible
                            if 'phi-bucket' in url:
                                parts = url.split('/')
                                filename = parts[-1]
                                if filename.endswith('_output_0.mp4'):
                                    external_id = filename.replace('_output_0.mp4', '')
                                    print(f"  Extracted External ID: {external_id}")
                except Exception as e:
                    print(f"Error checking segment: {e}")
                    
        except Exception as e:
            print(f"Error checking job: {e}")

if __name__ == "__main__":
    check_segments_for_jobs()