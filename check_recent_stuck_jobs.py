#!/usr/bin/env python3
"""Check for the last 3 stuck processes in Airtable Jobs."""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
JOBS_TABLE = os.getenv('AIRTABLE_JOBS_TABLE', 'Jobs')

def check_recent_jobs():
    """Check the last 3 jobs for stuck processes."""
    
    # Airtable API URL
    url = f"https://api.airtable.com/v0/{BASE_ID}/{JOBS_TABLE}"
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Get recent jobs (without sorting due to field name issues)
    params = {
        'maxRecords': 20  # Get more records to find recent ones
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
        print("CHECKING LAST 3 PROCESSES FOR STUCK JOBS")
        print("=" * 80)
        
        # Track processing jobs
        processing_jobs = []
        
        for record in records:
            fields = record.get('fields', {})
            status = fields.get('Status', 'Unknown')
            
            # Check if job is in a "processing" state
            if status in ['processing', 'Processing', 'pending', 'Pending']:
                processing_jobs.append(record)
                
            if len(processing_jobs) >= 3:
                break
        
        if not processing_jobs:
            print("\nNo jobs currently in processing state.")
            # Show last 3 jobs regardless of status
            print("\nShowing last 3 jobs (any status):")
            processing_jobs = records[:3]
        
        # Analyze each job
        for idx, record in enumerate(processing_jobs, 1):
            fields = record.get('fields', {})
            job_id = record.get('id')
            job_type = fields.get('Type', 'Unknown')
            status = fields.get('Status', 'Unknown')
            created_time = fields.get('Created', '')
            external_job_id = fields.get('External Job ID', 'N/A')
            error_details = fields.get('Error Details', '')
            
            print(f"\n{idx}. Job ID: {job_id}")
            print(f"   Type: {job_type}")
            print(f"   Status: {status}")
            print(f"   External Job ID: {external_job_id}")
            print(f"   Created: {created_time}")
            
            # Calculate how long ago it was created
            if created_time:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    age = datetime.now(created_dt.tzinfo) - created_dt
                    print(f"   Age: {age}")
                    
                    # Flag if stuck (processing for more than 10 minutes)
                    if status in ['processing', 'Processing'] and age > timedelta(minutes=10):
                        print(f"   ⚠️  WARNING: Job has been processing for {age} - may be stuck!")
                        
                except Exception as e:
                    print(f"   Could not calculate age: {e}")
            
            if error_details:
                print(f"   Error: {error_details[:100]}...")
            
            # Get related video/segment info
            video_ids = fields.get('Related Video', [])
            segment_ids = fields.get('Related Segment', [])
            
            if video_ids:
                print(f"   Related Video: {video_ids[0]}")
            if segment_ids:
                print(f"   Related Segment: {segment_ids[0]}")
                
            # Check webhook URL
            webhook_url = fields.get('Webhook URL', '')
            if webhook_url:
                print(f"   Webhook URL: {webhook_url}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        print("=" * 80)
        
        stuck_count = 0
        for record in processing_jobs:
            fields = record.get('fields', {})
            status = fields.get('Status', 'Unknown')
            created_time = fields.get('Created', '')
            
            if created_time and status in ['processing', 'Processing']:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    age = datetime.now(created_dt.tzinfo) - created_dt
                    
                    if age > timedelta(minutes=10):
                        stuck_count += 1
                        job_id = record.get('id')
                        job_type = fields.get('Type', 'Unknown')
                        print(f"\n• Job {job_id} ({job_type}) appears stuck")
                        print(f"  - Check external service status")
                        print(f"  - Verify webhook endpoint is accessible")
                        print(f"  - Consider manual recovery if needed")
                        
                except Exception:
                    pass
        
        if stuck_count == 0:
            print("\n✓ No stuck jobs detected")
        else:
            print(f"\n⚠️  Found {stuck_count} potentially stuck job(s)")
            print("\nTo recover stuck jobs, you can:")
            print("1. Check the external service (NCA/GoAPI) for actual status")
            print("2. Run manual recovery scripts if job completed externally")
            print("3. Cancel and retry if job truly failed")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching jobs from Airtable: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    check_recent_jobs()