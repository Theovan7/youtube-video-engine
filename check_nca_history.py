#!/usr/bin/env python3
"""
Check historical NCA job success rates.
"""

from datetime import datetime, timedelta
from services.airtable_service import AirtableService
import ast

airtable = AirtableService()

def analyze_nca_history():
    """Analyze NCA job history to see when it stopped working."""
    print("NCA Historical Analysis")
    print("=" * 80)
    
    # Get all jobs
    jobs_table = airtable.jobs_table
    all_jobs = jobs_table.all()
    
    # Categorize by date and status
    jobs_by_day = {}
    nca_jobs = []
    
    for job in all_jobs:
        fields = job.get('fields', {})
        external_id = fields.get('External Job ID')
        
        # Only look at jobs that were sent to NCA
        if external_id:
            created_time = fields.get('Created Time', '')
            status = fields.get('Status', 'Unknown')
            job_type = fields.get('Job Type', 'Unknown')
            
            if created_time:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', ''))
                    date_key = created_dt.date()
                    
                    if date_key not in jobs_by_day:
                        jobs_by_day[date_key] = {
                            'total': 0,
                            'completed': 0,
                            'failed': 0,
                            'processing': 0
                        }
                    
                    jobs_by_day[date_key]['total'] += 1
                    
                    if status == 'completed':
                        jobs_by_day[date_key]['completed'] += 1
                    elif status == 'failed':
                        jobs_by_day[date_key]['failed'] += 1
                    elif status == 'processing':
                        jobs_by_day[date_key]['processing'] += 1
                    
                    nca_jobs.append({
                        'id': job['id'],
                        'created': created_dt,
                        'status': status,
                        'type': job_type,
                        'external_id': external_id
                    })
                    
                except:
                    pass
    
    # Show daily summary
    print("\nNCA Jobs by Day:")
    print("-" * 60)
    print("Date         | Total | Success | Failed | Processing")
    print("-" * 60)
    
    for date in sorted(jobs_by_day.keys(), reverse=True)[:10]:  # Last 10 days
        stats = jobs_by_day[date]
        success_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"{date} | {stats['total']:5} | {stats['completed']:7} | {stats['failed']:6} | {stats['processing']:10} ({success_rate:.0f}% success)")
    
    # Find the last successful job
    print("\n\nLast Successful NCA Jobs:")
    print("-" * 80)
    
    successful_jobs = [j for j in nca_jobs if j['status'] == 'completed']
    successful_jobs.sort(key=lambda x: x['created'], reverse=True)
    
    for job in successful_jobs[:5]:
        print(f"\nJob: {job['id']}")
        print(f"  Date: {job['created']}")
        print(f"  Type: {job['type']}")
        print(f"  External ID: {job['external_id']}")
    
    if successful_jobs:
        last_success = successful_jobs[0]['created']
        time_since = datetime.now(last_success.tzinfo) - last_success
        print(f"\n⚠️  Last successful NCA job was {time_since} ago")
    
    # Check recent failures
    print("\n\nRecent Failed/Stuck Jobs:")
    print("-" * 80)
    
    recent_jobs = [j for j in nca_jobs if j['created'] > datetime.now(j['created'].tzinfo) - timedelta(hours=24)]
    failed_recent = [j for j in recent_jobs if j['status'] in ['failed', 'processing']]
    
    for job in failed_recent[:5]:
        print(f"\nJob: {job['id']}")
        print(f"  Status: {job['status']}")
        print(f"  Type: {job['type']}")
        print(f"  Created: {job['created']}")
        print(f"  External ID: {job['external_id']}")
    
    # Summary
    print("\n\nSUMMARY:")
    print("=" * 80)
    
    if not successful_jobs:
        print("❌ No successful NCA jobs found in history")
    elif time_since > timedelta(hours=12):
        print(f"❌ NCA has been failing for at least {time_since}")
    else:
        print(f"⚠️  Some NCA jobs succeeded recently ({time_since} ago)")
    
    # Calculate overall success rate
    total_nca_jobs = len(nca_jobs)
    total_successful = len(successful_jobs)
    if total_nca_jobs > 0:
        overall_success_rate = (total_successful / total_nca_jobs) * 100
        print(f"\nOverall NCA Success Rate: {overall_success_rate:.1f}% ({total_successful}/{total_nca_jobs})")

if __name__ == "__main__":
    analyze_nca_history()