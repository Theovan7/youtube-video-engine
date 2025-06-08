#!/usr/bin/env python3
"""
Check webhook URLs in stuck jobs to verify format.
"""

import os
import json
from datetime import datetime, timedelta
from services.airtable_service import AirtableService
from config import get_config

# Initialize services
config = get_config()()
airtable = AirtableService()

def check_stuck_jobs():
    """Check stuck jobs and their webhook URLs."""
    print("Checking stuck jobs...")
    
    # Get jobs in processing state
    try:
        jobs = airtable.get_all_jobs()
        stuck_jobs = []
        
        for job in jobs:
            fields = job.get('fields', {})
            status = fields.get('Status', '')
            created_time = fields.get('Created Time', '')
            
            if status == 'processing':
                # Check if job is older than 10 minutes
                if created_time:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    age = datetime.now(created_dt.tzinfo) - created_dt
                    if age > timedelta(minutes=10):
                        stuck_jobs.append({
                            'id': job['id'],
                            'fields': fields,
                            'age': age
                        })
        
        print(f"\nFound {len(stuck_jobs)} stuck jobs:\n")
        
        for job in stuck_jobs:
            print(f"Job ID: {job['id']}")
            print(f"Age: {job['age']}")
            print(f"Type: {job['fields'].get('Job Type', 'Unknown')}")
            print(f"External Job ID: {job['fields'].get('External Job ID', 'None')}")
            print(f"Webhook URL: {job['fields'].get('Webhook URL', 'None')}")
            
            # Check request payload for more details
            request_payload = job['fields'].get('Request Payload', '{}')
            try:
                if request_payload and request_payload != '{}':
                    payload_data = json.loads(request_payload) if request_payload.startswith('{') else eval(request_payload)
                    print(f"Request Payload Keys: {list(payload_data.keys())}")
                    if 'webhook_url' in payload_data:
                        print(f"Webhook URL from payload: {payload_data['webhook_url']}")
            except Exception as e:
                print(f"Could not parse request payload: {e}")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"Error: {e}")

def check_specific_jobs():
    """Check specific job IDs mentioned by user."""
    job_ids = ['reci0gT2LhNaIaFtp', 'recphkqVVvJEwM19c']
    
    print("\nChecking specific jobs:\n")
    
    for job_id in job_ids:
        try:
            job = airtable.get_job(job_id)
            if job:
                fields = job.get('fields', {})
                print(f"Job ID: {job_id}")
                print(f"Status: {fields.get('Status', 'Unknown')}")
                print(f"Type: {fields.get('Job Type', 'Unknown')}")
                print(f"External Job ID: {fields.get('External Job ID', 'None')}")
                print(f"Webhook URL: {fields.get('Webhook URL', 'None')}")
                print(f"Created: {fields.get('Created Time', 'Unknown')}")
                print(f"Error Details: {fields.get('Error Details', 'None')}")
                print(f"Notes: {fields.get('Notes', 'None')}")
                
                # Check if external job exists
                external_id = fields.get('External Job ID')
                if external_id:
                    print(f"\nChecking if NCA job {external_id} exists...")
                    # Would need NCA service to check status
                    
                print("-" * 60)
            else:
                print(f"Job {job_id} not found")
                
        except Exception as e:
            print(f"Error checking job {job_id}: {e}")

if __name__ == "__main__":
    check_stuck_jobs()
    check_specific_jobs()