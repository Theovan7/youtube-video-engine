#!/usr/bin/env python3
"""
Check the status of the combine jobs we just created.
"""

from datetime import datetime
from services.airtable_service import AirtableService
from services.job_monitor import JobMonitor
from services.nca_service import NCAService
import requests

# Initialize services
airtable = AirtableService()
monitor = JobMonitor()
nca = NCAService()

# The job IDs we created
job_ids = [
    'reccDAlHMgYDxAH4G',
    'recYfcfAMT0YazzpA',
    'recutnS27eKodv5sZ',
    'recpAn4qqMAw555T1',
    'recaZfbnNuNgJsArP'
]

def check_jobs_and_files():
    """Check the status of combine jobs and their output files."""
    print("Checking status of combine jobs...")
    print("=" * 80)
    
    current_time = datetime.utcnow()
    
    for job_id in job_ids:
        print(f"\nJob ID: {job_id}")
        print("-" * 40)
        
        try:
            # Get job from Airtable
            job = airtable.get_job(job_id)
            if not job:
                print("  ❌ Job not found in Airtable!")
                continue
                
            fields = job['fields']
            
            # Basic info
            status = fields.get('Status', 'Unknown')
            external_id = fields.get('External Job ID')
            created_time = fields.get('Created Time', '')
            
            age_minutes = 'Unknown'
            if created_time:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', ''))
                    age_minutes = (current_time - created_dt).total_seconds() / 60
                except:
                    pass
            
            print(f"  Status: {status}")
            print(f"  Age: {age_minutes:.1f} minutes" if isinstance(age_minutes, float) else f"  Age: {age_minutes}")
            print(f"  External ID: {external_id or 'MISSING ⚠️'}")
            
            # Check segment
            request_payload = fields.get('Request Payload', '{}')
            segment_id = None
            try:
                import ast
                if request_payload and request_payload != '{}':
                    payload_data = ast.literal_eval(request_payload)
                    segment_id = payload_data.get('segment_id') or payload_data.get('record_id')
            except:
                pass
                
            if segment_id:
                print(f"  Segment ID: {segment_id}")
                
                # Check segment status
                try:
                    segment = airtable.get_segment(segment_id)
                    if segment:
                        seg_fields = segment['fields']
                        seg_status = seg_fields.get('Status')
                        has_combined = bool(seg_fields.get('Voiceover + Video'))
                        
                        print(f"  Segment Status: {seg_status}")
                        print(f"  Has Combined Video: {'YES ✓' if has_combined else 'NO ✗'}")
                        
                        if has_combined:
                            combined_urls = seg_fields.get('Voiceover + Video', [])
                            if combined_urls:
                                print(f"  Combined URL: {combined_urls[0].get('url', 'N/A')[:60]}...")
                except Exception as e:
                    print(f"  Error checking segment: {e}")
            
            # If we have external ID, check file and NCA status
            if external_id:
                # Check if file exists on DO Spaces
                output_url = monitor.construct_output_url(external_id)
                print(f"  Expected URL: {output_url[:60]}...")
                
                file_exists = monitor.check_file_exists(output_url)
                print(f"  File Exists on DO Spaces: {'YES ✓' if file_exists else 'NO ✗'}")
                
                if file_exists and status == 'processing':
                    print(f"  🔧 FILE EXISTS BUT JOB STILL PROCESSING - Polling should fix this!")
                
                # Check NCA job status
                try:
                    print(f"  Checking NCA status...")
                    nca_status = nca.get_job_status(external_id)
                    if nca_status:
                        nca_job_status = nca_status.get('status', 'Unknown')
                        print(f"  NCA Status: {nca_job_status}")
                        
                        if nca_job_status == 'failed':
                            print(f"  NCA Error: {nca_status.get('error', 'Unknown error')}")
                        elif nca_job_status == 'completed':
                            nca_output = nca_status.get('output', {})
                            if isinstance(nca_output, dict):
                                nca_url = nca_output.get('url')
                                if nca_url:
                                    print(f"  NCA Output URL: {nca_url[:60]}...")
                except Exception as e:
                    print(f"  ❌ NCA Status Check Failed: {str(e)[:100]}")
            else:
                print(f"  ⚠️  No External Job ID - Cannot check NCA or file status")
                
        except Exception as e:
            print(f"  ❌ Error checking job: {e}")
    
    print("\n" + "=" * 80)
    print("TRIGGERING MANUAL POLLING CHECK...")
    
    # Trigger manual polling
    try:
        monitor.run_check_cycle()
        print("✓ Manual polling check completed")
    except Exception as e:
        print(f"❌ Polling check failed: {e}")

if __name__ == "__main__":
    check_jobs_and_files()