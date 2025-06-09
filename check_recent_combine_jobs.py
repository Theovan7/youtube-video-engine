#!/usr/bin/env python3
"""
Check for recent combine jobs and their status.
"""

import os
from datetime import datetime, timedelta
from services.airtable_service import AirtableService
from services.job_monitor import JobMonitor
import ast

# Initialize services
airtable = AirtableService()
monitor = JobMonitor()

def check_recent_jobs():
    """Check for jobs created in the last 30 minutes."""
    print("Checking for recent combine jobs...")
    print("=" * 70)
    
    try:
        # Get all jobs
        jobs_table = airtable.jobs_table
        all_jobs = jobs_table.all()
        
        # Filter for recent jobs
        recent_jobs = []
        current_time = datetime.utcnow()
        
        for job in all_jobs:
            fields = job.get('fields', {})
            created_time = fields.get('Created Time', '')
            
            if created_time:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', ''))
                    age_minutes = (current_time - created_dt).total_seconds() / 60
                    
                    # Check if job is recent (last 30 minutes) and is a combine operation
                    if age_minutes <= 30:
                        # Check if it's a combine job
                        request_payload = fields.get('Request Payload', '{}')
                        is_combine = False
                        
                        try:
                            if request_payload and request_payload != '{}':
                                payload_data = ast.literal_eval(request_payload)
                                operation = payload_data.get('operation', '')
                                is_combine = operation == 'combine'
                        except:
                            pass
                        
                        # Also check job type
                        job_type = fields.get('Job Type', '')
                        if 'combin' in job_type.lower() or is_combine:
                            recent_jobs.append({
                                'id': job['id'],
                                'fields': fields,
                                'age_minutes': age_minutes,
                                'created_dt': created_dt
                            })
                except Exception as e:
                    print(f"Error parsing date for job {job['id']}: {e}")
        
        # Sort by creation time
        recent_jobs.sort(key=lambda x: x['created_dt'], reverse=True)
        
        print(f"\nFound {len(recent_jobs)} recent combine jobs:\n")
        
        for idx, job in enumerate(recent_jobs[:10], 1):  # Show up to 10 most recent
            fields = job['fields']
            job_id = job['id']
            
            print(f"{idx}. Job ID: {job_id}")
            print(f"   Age: {job['age_minutes']:.1f} minutes")
            print(f"   Status: {fields.get('Status', 'Unknown')}")
            print(f"   Type: {fields.get('Job Type', 'Unknown')}")
            print(f"   External ID: {fields.get('External Job ID', 'None')}")
            print(f"   Webhook URL: {fields.get('Webhook URL', 'None')}")
            
            # Check if external job exists
            external_id = fields.get('External Job ID')
            if external_id:
                # Check if file exists on DO Spaces
                output_url = monitor.construct_output_url(external_id)
                file_exists = monitor.check_file_exists(output_url)
                print(f"   Output URL: {output_url}")
                print(f"   File Exists: {'YES ✓' if file_exists else 'NO ✗'}")
                
                # If file exists but job is still processing, it should be picked up by polling
                if file_exists and fields.get('Status') == 'processing':
                    print(f"   ⚠️  File exists but job still in processing - polling should pick this up!")
            else:
                print(f"   ⚠️  No External Job ID - cannot check for output file")
            
            # Check segment status
            request_payload = fields.get('Request Payload', '{}')
            try:
                if request_payload and request_payload != '{}':
                    payload_data = ast.literal_eval(request_payload)
                    segment_id = payload_data.get('segment_id') or payload_data.get('record_id')
                    
                    if segment_id:
                        try:
                            segment = airtable.get_segment(segment_id)
                            if segment:
                                seg_fields = segment['fields']
                                print(f"   Segment {segment_id}:")
                                print(f"     Status: {seg_fields.get('Status')}")
                                print(f"     Has Combined: {'Yes' if seg_fields.get('Voiceover + Video') else 'No'}")
                        except:
                            pass
            except:
                pass
            
            print("-" * 70)
            
    except Exception as e:
        print(f"Error checking jobs: {e}")

def trigger_manual_check():
    """Trigger a manual polling check."""
    print("\nTriggering manual polling check...")
    try:
        monitor.run_check_cycle()
        print("Manual check completed!")
    except Exception as e:
        print(f"Error during manual check: {e}")

if __name__ == "__main__":
    check_recent_jobs()
    print("\n" + "=" * 70)
    trigger_manual_check()