#!/usr/bin/env python3
"""Check the status of the latest combine jobs."""

from datetime import datetime, timedelta
from services.airtable_service import AirtableService
import json

airtable = AirtableService()

def check_latest_jobs():
    """Check the latest combine jobs."""
    print("Checking Latest Combine Jobs")
    print("=" * 80)
    
    # Get jobs table
    jobs_table = airtable.jobs_table
    all_jobs = jobs_table.all()
    
    # Filter for recent combine jobs
    recent_jobs = []
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    for job in all_jobs:
        fields = job.get('fields', {})
        created_time = fields.get('Created Time', '')
        job_type = fields.get('Job Type', '')
        
        if created_time and job_type == 'combine':
            try:
                created_dt = datetime.fromisoformat(created_time.replace('Z', ''))
                if created_dt > one_hour_ago:
                    recent_jobs.append({
                        'id': job['id'],
                        'created': created_dt,
                        'status': fields.get('Status', 'Unknown'),
                        'external_id': fields.get('External Job ID'),
                        'segment_id': fields.get('Segment ID'),
                        'response': fields.get('Response Payload')
                    })
            except:
                pass
    
    # Sort by creation time
    recent_jobs.sort(key=lambda x: x['created'], reverse=True)
    
    print(f"\nFound {len(recent_jobs)} combine jobs in the last hour:\n")
    
    for job in recent_jobs[:10]:  # Show latest 10
        time_ago = datetime.now() - job['created'].replace(tzinfo=None)
        minutes = int(time_ago.total_seconds() / 60)
        
        print(f"Job: {job['id']}")
        print(f"  Created: {minutes} minutes ago")
        print(f"  Status: {job['status']}")
        print(f"  Segment: {job['segment_id']}")
        print(f"  External ID: {job['external_id']}")
        
        if job['response']:
            try:
                response = json.loads(job['response']) if isinstance(job['response'], str) else job['response']
                if 'error' in response:
                    print(f"  ❌ Error: {response['error']}")
                elif 'job_id' in response:
                    print(f"  ✓ NCA Job ID: {response['job_id']}")
            except:
                print(f"  Response: {job['response'][:100]}")
        
        print("-" * 40)

if __name__ == "__main__":
    check_latest_jobs()