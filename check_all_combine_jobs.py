#!/usr/bin/env python3
"""Check all combine jobs in the Jobs table."""

import os
import sys
from datetime import datetime
from pyairtable import Api
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_all_combine_jobs():
    """Check all combine jobs and their status."""
    
    # Initialize Airtable
    api = Api(os.getenv('AIRTABLE_API_KEY'))
    base_id = os.getenv('AIRTABLE_BASE_ID')
    jobs_table = api.table(base_id, 'Jobs')
    
    print("Checking all combine jobs in the Jobs table...")
    print("=" * 80)
    
    # Get all jobs and filter for combine jobs
    all_jobs = jobs_table.all()
    
    # Filter for combine jobs
    combine_jobs = []
    for job in all_jobs:
        fields = job.get('fields', {})
        job_type = fields.get('Job Type', '')
        created_time = job.get('createdTime', '')
        
        if job_type == 'combine':
            # Parse the created time if available
            created_dt = None
            if created_time:
                created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            
            combine_jobs.append({
                'record': job,
                'created_dt': created_dt
            })
    
    # Sort by creation time (most recent first)
    combine_jobs.sort(key=lambda x: x['created_dt'] if x['created_dt'] else datetime.min, reverse=True)
    
    if not combine_jobs:
        print("No combine jobs found in the Jobs table.")
        return
    
    print(f"Found {len(combine_jobs)} combine jobs total.")
    print(f"Showing the 10 most recent:\n")
    
    # Show up to 10 most recent
    for idx, job_info in enumerate(combine_jobs[:10], 1):
        job = job_info['record']
        fields = job.get('fields', {})
        created_dt = job_info['created_dt']
        
        print(f"Job #{idx}")
        print("-" * 40)
        print(f"1. Job ID: {job.get('id', 'N/A')}")
        
        external_job_id = fields.get('External Job ID', '')
        if external_job_id:
            print(f"2. External Job ID: {external_job_id}")
            print(f"   (External Job ID exists: YES)")
        else:
            print(f"2. External Job ID: None")
            print(f"   (External Job ID exists: NO - NULL)")
        
        print(f"3. Status: {fields.get('Status', 'N/A')}")
        
        response_payload = fields.get('Response Payload', '')
        if response_payload:
            try:
                # Try to parse and pretty print JSON
                parsed = json.loads(response_payload)
                print(f"4. Response Payload:")
                # Limit the output for readability
                payload_str = json.dumps(parsed, indent=2)
                if len(payload_str) > 500:
                    print(payload_str[:500] + "\n   ... (truncated)")
                else:
                    print(payload_str)
            except:
                # If not valid JSON, print as is
                if len(response_payload) > 200:
                    print(f"4. Response Payload: {response_payload[:200]}... (truncated)")
                else:
                    print(f"4. Response Payload: {response_payload}")
        else:
            print(f"4. Response Payload: None")
        
        if created_dt:
            print(f"5. Created: {created_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        else:
            print(f"5. Created: Unknown")
        
        # Additional info
        video_ref = fields.get('Video Reference', [])
        if video_ref:
            print(f"   Video Reference: {video_ref}")
        
        print()

if __name__ == "__main__":
    try:
        check_all_combine_jobs()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()