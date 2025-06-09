#!/usr/bin/env python3
"""Analyze the most recent jobs in detail."""

import os
import json
from datetime import datetime, timedelta, timezone
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_recent_jobs():
    """Analyze the most recent jobs in detail."""
    
    # Initialize Airtable
    api = Api(os.getenv('AIRTABLE_API_KEY'))
    base_id = os.getenv('AIRTABLE_BASE_ID')
    jobs_table = api.table(base_id, 'Jobs')
    
    print("Analyzing the 10 most recent jobs...")
    print("=" * 80)
    
    # Get all jobs
    all_jobs = jobs_table.all()
    
    if not all_jobs:
        print("No jobs found in the Jobs table.")
        return
    
    # Sort by creation time
    jobs_with_time = []
    for job in all_jobs:
        created_time = job.get('createdTime', '')
        if created_time:
            created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            jobs_with_time.append({
                'record': job,
                'created_dt': created_dt
            })
    
    # Sort by creation time (most recent first)
    jobs_with_time.sort(key=lambda x: x['created_dt'], reverse=True)
    
    # Analyze the 10 most recent
    for idx, job_info in enumerate(jobs_with_time[:10], 1):
        job = job_info['record']
        fields = job.get('fields', {})
        
        print(f"\nJob #{idx}")
        print("-" * 60)
        print(f"Job ID: {job.get('id', 'N/A')}")
        print(f"Created: {job_info['created_dt'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Show all fields
        print("\nAll fields:")
        for field_name, field_value in fields.items():
            if field_name in ['Request Payload', 'Response Payload']:
                print(f"  {field_name}:")
                try:
                    if isinstance(field_value, str):
                        parsed = json.loads(field_value)
                        print(f"    {json.dumps(parsed, indent=4)}")
                    else:
                        print(f"    {json.dumps(field_value, indent=4)}")
                except:
                    if len(str(field_value)) > 200:
                        print(f"    {str(field_value)[:200]}... (truncated)")
                    else:
                        print(f"    {field_value}")
            else:
                if isinstance(field_value, list) and len(field_value) > 0:
                    print(f"  {field_name}: {field_value}")
                elif field_value:
                    print(f"  {field_name}: {field_value}")
        
        # Check time since creation
        time_since = datetime.now(timezone.utc) - job_info['created_dt']
        hours = time_since.total_seconds() / 3600
        print(f"\nTime since creation: {hours:.1f} hours")
        
        # Check if this looks like it's stuck
        status = fields.get('Status', 'Unknown')
        if status == 'processing' and hours > 1:
            print("⚠️  WARNING: Job has been in 'processing' status for over 1 hour!")

if __name__ == "__main__":
    try:
        analyze_recent_jobs()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()