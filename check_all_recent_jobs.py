#!/usr/bin/env python3
"""Check all recent jobs regardless of status."""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
JOBS_TABLE = os.getenv('AIRTABLE_JOBS_TABLE', 'Jobs')

def check_all_jobs():
    """Check all recent jobs."""
    
    # Airtable API URL
    url = f"https://api.airtable.com/v0/{BASE_ID}/{JOBS_TABLE}"
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Get recent jobs
    params = {
        'maxRecords': 10,
        'view': 'Grid view'  # Use default view
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        records = data.get('records', [])
        
        if not records:
            print("No jobs found in Airtable.")
            return
        
        print("=" * 80)
        print(f"RECENT JOBS IN AIRTABLE (Total: {len(records)})")
        print("=" * 80)
        
        # Group by status
        status_groups = {}
        
        for record in records:
            fields = record.get('fields', {})
            status = fields.get('Status', 'Unknown')
            
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(record)
        
        # Show summary
        print("\nSTATUS SUMMARY:")
        for status, jobs in status_groups.items():
            print(f"  {status}: {len(jobs)} job(s)")
        
        # Show details for each status group
        for status, jobs in status_groups.items():
            print(f"\n--- {status.upper()} JOBS ({len(jobs)}) ---")
            
            for record in jobs[:3]:  # Show max 3 per status
                fields = record.get('fields', {})
                job_id = record.get('id')
                job_type = fields.get('Type', 'Unknown')
                external_job_id = fields.get('External Job ID', 'N/A')
                
                print(f"\nJob ID: {job_id}")
                print(f"  Type: {job_type}")
                print(f"  External ID: {external_job_id}")
                
                # Get related records
                video_ids = fields.get('Related Video', [])
                segment_ids = fields.get('Related Segment', [])
                
                if video_ids:
                    print(f"  Video: {video_ids[0]}")
                if segment_ids:
                    print(f"  Segment: {segment_ids[0]}")
                
                # Show error if failed
                if status in ['failed', 'Failed']:
                    error = fields.get('Error Details', '')
                    if error:
                        print(f"  Error: {error[:100]}...")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("ANALYSIS:")
        print("=" * 80)
        
        processing_jobs = status_groups.get('processing', []) + status_groups.get('Processing', [])
        if processing_jobs:
            print(f"\n⚠️  {len(processing_jobs)} job(s) are stuck in processing state")
            print("   These NCA jobs returned 404, suggesting they may have failed or been cleaned up")
            print("\nRECOMMENDED ACTIONS:")
            print("1. Update these jobs to 'failed' status in Airtable")
            print("2. Retry the operations if needed")
            
            # Show the update commands
            print("\nTo update stuck jobs to failed status, run:")
            for job in processing_jobs:
                job_id = job.get('id')
                print(f"   # Update job {job_id} to failed status")
        else:
            print("\n✅ No stuck jobs found")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching jobs from Airtable: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    check_all_jobs()