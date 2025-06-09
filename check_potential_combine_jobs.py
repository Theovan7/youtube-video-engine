#!/usr/bin/env python3
"""Check for potential combine jobs based on payloads or other indicators."""

import os
import json
from datetime import datetime, timedelta, timezone
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_potential_combine_jobs():
    """Check for jobs that might be combine jobs based on their payloads."""
    
    # Initialize Airtable
    api = Api(os.getenv('AIRTABLE_API_KEY'))
    base_id = os.getenv('AIRTABLE_BASE_ID')
    jobs_table = api.table(base_id, 'Jobs')
    
    print("Checking for potential combine jobs in the last 24 hours...")
    print("=" * 80)
    
    # Get all jobs
    all_jobs = jobs_table.all()
    
    # Calculate timestamp for 24 hours ago
    twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    
    # Look for potential combine jobs
    potential_combine_jobs = []
    
    for job in all_jobs:
        fields = job.get('fields', {})
        created_time = job.get('createdTime', '')
        
        if created_time:
            created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            
            # Only check jobs from last 24 hours
            if created_dt > twenty_four_hours_ago:
                # Check various indicators that might suggest this is a combine job
                request_payload = fields.get('Request Payload', '')
                response_payload = fields.get('Response Payload', '')
                external_job_id = fields.get('External Job ID', '')
                
                # Look for combine-related keywords in payloads
                is_potential_combine = False
                reason = ""
                
                # Check request payload
                if request_payload:
                    request_str = str(request_payload).lower()
                    if any(keyword in request_str for keyword in ['combine', 'merge', 'concatenate', 'video_reference', 'video_id']):
                        is_potential_combine = True
                        reason = "Request payload contains combine-related keywords"
                    
                    # Check if it's a dict with video_id
                    try:
                        if isinstance(request_payload, str):
                            request_dict = json.loads(request_payload)
                        else:
                            request_dict = request_payload
                        
                        if 'video_id' in request_dict or 'video_reference' in request_dict:
                            is_potential_combine = True
                            reason = "Request payload contains video_id or video_reference"
                    except:
                        pass
                
                # Check response payload
                if response_payload:
                    response_str = str(response_payload).lower()
                    if any(keyword in response_str for keyword in ['combine', 'merge', 'output', 'final']):
                        is_potential_combine = True
                        reason = "Response payload contains combine-related keywords"
                
                # Check if there's a video reference field
                video_ref = fields.get('Video Reference', [])
                if video_ref:
                    is_potential_combine = True
                    reason = "Has Video Reference field"
                
                if is_potential_combine:
                    potential_combine_jobs.append({
                        'record': job,
                        'created_dt': created_dt,
                        'reason': reason
                    })
    
    # Sort by creation time (most recent first)
    potential_combine_jobs.sort(key=lambda x: x['created_dt'], reverse=True)
    
    if not potential_combine_jobs:
        print("No potential combine jobs found in the last 24 hours.")
        return
    
    print(f"Found {len(potential_combine_jobs)} potential combine jobs in the last 24 hours.")
    print(f"Showing the 5 most recent:\n")
    
    # Show up to 5 most recent
    for idx, job_info in enumerate(potential_combine_jobs[:5], 1):
        job = job_info['record']
        fields = job.get('fields', {})
        
        print(f"Potential Combine Job #{idx}")
        print("-" * 40)
        print(f"Reason identified: {job_info['reason']}")
        print(f"1. Job ID: {job.get('id', 'N/A')}")
        
        external_job_id = fields.get('External Job ID', '')
        if external_job_id:
            print(f"2. External Job ID: {external_job_id}")
            print(f"   (External Job ID exists: YES)")
        else:
            print(f"2. External Job ID: None")
            print(f"   (External Job ID exists: NO - NULL)")
        
        print(f"3. Status: {fields.get('Status', 'N/A')}")
        
        # Show full request payload
        request_payload = fields.get('Request Payload', '')
        if request_payload:
            print(f"4. Request Payload:")
            try:
                if isinstance(request_payload, str):
                    parsed = json.loads(request_payload)
                    print(json.dumps(parsed, indent=2))
                else:
                    print(json.dumps(request_payload, indent=2))
            except:
                print(f"   {request_payload}")
        else:
            print(f"4. Request Payload: None")
        
        # Show response payload
        response_payload = fields.get('Response Payload', '')
        if response_payload:
            print(f"5. Response Payload:")
            try:
                if isinstance(response_payload, str):
                    parsed = json.loads(response_payload)
                    print(json.dumps(parsed, indent=2))
                else:
                    print(json.dumps(response_payload, indent=2))
            except:
                if len(str(response_payload)) > 200:
                    print(f"   {str(response_payload)[:200]}... (truncated)")
                else:
                    print(f"   {response_payload}")
        else:
            print(f"5. Response Payload: None")
        
        print(f"6. Created: {job_info['created_dt'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Additional info
        video_ref = fields.get('Video Reference', [])
        if video_ref:
            print(f"7. Video Reference: {video_ref}")
        
        print()

if __name__ == "__main__":
    try:
        check_potential_combine_jobs()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()