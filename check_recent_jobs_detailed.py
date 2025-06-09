#!/usr/bin/env python3
"""
Check for recent jobs and analyze why they haven't been processed.
"""

import os
from datetime import datetime, timedelta
from services.airtable_service import AirtableService
from services.job_monitor import JobMonitor
from services.nca_service import NCAService
import ast
import requests

# Initialize services
airtable = AirtableService()
monitor = JobMonitor()
nca = NCAService()

def check_recent_and_stuck_jobs():
    """Check all recent and stuck jobs."""
    print("Checking for recent jobs and stuck processing jobs...")
    print("=" * 80)
    
    try:
        # Get all jobs
        jobs_table = airtable.jobs_table
        all_jobs = jobs_table.all()
        
        # Categorize jobs
        recent_jobs = []
        stuck_jobs = []
        current_time = datetime.utcnow()
        
        for job in all_jobs:
            fields = job.get('fields', {})
            created_time = fields.get('Created Time', '')
            status = fields.get('Status', '')
            
            if created_time:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', ''))
                    age_minutes = (current_time - created_dt).total_seconds() / 60
                    
                    # Recent jobs (last 30 minutes)
                    if age_minutes <= 30:
                        recent_jobs.append({
                            'id': job['id'],
                            'fields': fields,
                            'age_minutes': age_minutes,
                            'created_dt': created_dt
                        })
                    
                    # Stuck jobs (processing for more than 5 minutes)
                    if status == 'processing' and age_minutes > 5:
                        stuck_jobs.append({
                            'id': job['id'],
                            'fields': fields,
                            'age_minutes': age_minutes,
                            'created_dt': created_dt
                        })
                except Exception as e:
                    pass
        
        # Show recent jobs
        print(f"\nRECENT JOBS (last 30 minutes): {len(recent_jobs)}")
        print("-" * 80)
        
        if recent_jobs:
            recent_jobs.sort(key=lambda x: x['created_dt'], reverse=True)
            
            for job in recent_jobs[:10]:
                analyze_job(job)
        else:
            print("No jobs created in the last 30 minutes.")
        
        # Show stuck jobs
        print(f"\n\nSTUCK JOBS (processing > 5 minutes): {len(stuck_jobs)}")
        print("-" * 80)
        
        if stuck_jobs:
            stuck_jobs.sort(key=lambda x: x['age_minutes'], reverse=True)
            
            for job in stuck_jobs[:10]:
                analyze_job(job, check_file=True)
                
        # Check polling status
        print("\n\nPOLLING SYSTEM STATUS:")
        print("-" * 80)
        
        # Trigger manual check
        print("Triggering manual polling check...")
        response = requests.post(
            "https://youtube-video-engine.fly.dev/api/v2/check-stuck-jobs",
            json={"older_than_minutes": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Polling endpoint is working")
            print(f"Response: {response.json()}")
        else:
            print(f"✗ Polling endpoint error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def analyze_job(job_data, check_file=False):
    """Analyze a single job."""
    job_id = job_data['id']
    fields = job_data['fields']
    age = job_data['age_minutes']
    
    print(f"\nJob: {job_id}")
    print(f"  Age: {age:.1f} minutes")
    print(f"  Status: {fields.get('Status', 'Unknown')}")
    print(f"  Type: {fields.get('Job Type', 'Unknown')}")
    
    # Check external ID
    external_id = fields.get('External Job ID')
    print(f"  External ID: {external_id or 'MISSING ⚠️'}")
    
    # Parse operation
    request_payload = fields.get('Request Payload', '{}')
    operation = 'Unknown'
    segment_id = None
    
    try:
        if request_payload and request_payload != '{}':
            payload_data = ast.literal_eval(request_payload)
            operation = payload_data.get('operation', 'Unknown')
            segment_id = payload_data.get('segment_id') or payload_data.get('record_id')
    except:
        pass
    
    print(f"  Operation: {operation}")
    
    # Check webhook URL
    webhook_url = fields.get('Webhook URL', '')
    if webhook_url:
        print(f"  Webhook: Configured ✓")
    else:
        print(f"  Webhook: NOT CONFIGURED ⚠️")
    
    # If we have external ID, check file and NCA status
    if external_id and check_file:
        # Check file existence
        output_url = monitor.construct_output_url(external_id)
        print(f"  Expected URL: {output_url}")
        
        file_exists = monitor.check_file_exists(output_url)
        print(f"  File Exists: {'YES ✓' if file_exists else 'NO ✗'}")
        
        if file_exists and fields.get('Status') == 'processing':
            print(f"  🔧 POLLING SHOULD PROCESS THIS!")
        
        # Check NCA status
        try:
            nca_status = nca.get_job_status(external_id)
            if nca_status:
                print(f"  NCA Status: {nca_status.get('status', 'Unknown')}")
                if nca_status.get('error'):
                    print(f"  NCA Error: {nca_status.get('error')}")
        except Exception as e:
            print(f"  NCA Status Check Failed: {str(e)[:50]}")
    
    # Check segment if available
    if segment_id:
        try:
            segment = airtable.get_segment(segment_id)
            if segment:
                seg_fields = segment['fields']
                print(f"  Segment Status: {seg_fields.get('Status')}")
                print(f"  Has Combined: {'YES' if seg_fields.get('Voiceover + Video') else 'NO'}")
        except:
            pass

if __name__ == "__main__":
    check_recent_and_stuck_jobs()