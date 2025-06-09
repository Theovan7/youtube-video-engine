#!/usr/bin/env python3
"""Check what types of jobs exist in the Jobs table."""

import os
from datetime import datetime
from pyairtable import Api
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_job_types():
    """Check all job types in the Jobs table."""
    
    # Initialize Airtable
    api = Api(os.getenv('AIRTABLE_API_KEY'))
    base_id = os.getenv('AIRTABLE_BASE_ID')
    jobs_table = api.table(base_id, 'Jobs')
    
    print("Checking all job types in the Jobs table...")
    print("=" * 80)
    
    # Get all jobs
    all_jobs = jobs_table.all()
    
    if not all_jobs:
        print("No jobs found in the Jobs table.")
        return
    
    # Count job types
    job_types = Counter()
    recent_jobs = []
    
    for job in all_jobs:
        fields = job.get('fields', {})
        job_type = fields.get('Job Type', 'Unknown')
        job_types[job_type] += 1
        
        # Collect recent jobs
        created_time = job.get('createdTime', '')
        if created_time:
            created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            recent_jobs.append({
                'record': job,
                'created_dt': created_dt,
                'job_type': job_type
            })
    
    print(f"Total jobs found: {len(all_jobs)}")
    print("\nJob types distribution:")
    for job_type, count in job_types.most_common():
        print(f"  - {job_type}: {count}")
    
    # Sort by creation time and show 5 most recent
    recent_jobs.sort(key=lambda x: x['created_dt'], reverse=True)
    
    print("\n5 Most Recent Jobs (any type):")
    print("-" * 80)
    
    for idx, job_info in enumerate(recent_jobs[:5], 1):
        job = job_info['record']
        fields = job.get('fields', {})
        
        print(f"\nJob #{idx}")
        print(f"  Job ID: {job.get('id', 'N/A')}")
        print(f"  Job Type: {job_info['job_type']}")
        print(f"  External Job ID: {fields.get('External Job ID', 'None')}")
        print(f"  Status: {fields.get('Status', 'N/A')}")
        print(f"  Created: {job_info['created_dt'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Show request/response payloads if they exist
        request_payload = fields.get('Request Payload', '')
        if request_payload and len(request_payload) > 100:
            print(f"  Request Payload: {request_payload[:100]}... (truncated)")
        elif request_payload:
            print(f"  Request Payload: {request_payload}")
            
        response_payload = fields.get('Response Payload', '')
        if response_payload and len(response_payload) > 100:
            print(f"  Response Payload: {response_payload[:100]}... (truncated)")
        elif response_payload:
            print(f"  Response Payload: {response_payload}")

if __name__ == "__main__":
    try:
        check_job_types()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()