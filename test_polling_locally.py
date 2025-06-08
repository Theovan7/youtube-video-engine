#!/usr/bin/env python3
"""
Test the job polling functionality locally.
"""

import os
import time
from services.job_monitor import JobMonitor
from services.airtable_service import AirtableService
from config import get_config

# Initialize services
config = get_config()()
monitor = JobMonitor()
airtable = AirtableService()

def test_polling():
    """Test the polling functionality."""
    print("Testing Job Polling System")
    print("=" * 50)
    
    # Test 1: Check for stuck jobs
    print("\n1. Checking for stuck jobs...")
    try:
        stuck_jobs = monitor.check_stuck_jobs(older_than_minutes=5)
        print(f"   Found {len(stuck_jobs)} stuck jobs")
        
        for job in stuck_jobs[:3]:  # Show first 3
            print(f"\n   Job ID: {job['id']}")
            print(f"   Age: {job['age_minutes']:.1f} minutes")
            print(f"   External ID: {job['fields'].get('External Job ID', 'None')}")
            print(f"   Status: {job['fields'].get('Status', 'Unknown')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Check file existence
    print("\n2. Testing file existence check...")
    test_urls = [
        "https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket/test_file.mp4",
        "https://google.com",  # Should exist
        "https://nonexistent-domain-12345.com/file.mp4"  # Should not exist
    ]
    
    for url in test_urls:
        exists = monitor.check_file_exists(url)
        print(f"   {url}: {'EXISTS' if exists else 'NOT FOUND'}")
    
    # Test 3: URL construction
    print("\n3. Testing URL construction...")
    test_job_ids = [
        "abc123-def456-ghi789",
        "test_job_id_12345"
    ]
    
    for job_id in test_job_ids:
        url = monitor.construct_output_url(job_id)
        print(f"   Job ID: {job_id}")
        print(f"   URL: {url}")
    
    # Test 4: Run a check cycle
    print("\n4. Running a full check cycle...")
    try:
        start_time = time.time()
        monitor.run_check_cycle()
        elapsed = time.time() - start_time
        print(f"   Check cycle completed in {elapsed:.2f} seconds")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Check specific stuck jobs
    print("\n5. Checking specific known stuck jobs...")
    known_job_ids = ['reci0gT2LhNaIaFtp', 'recphkqVVvJEwM19c']
    
    for job_id in known_job_ids:
        try:
            job = airtable.get_job(job_id)
            if job:
                fields = job['fields']
                print(f"\n   Job: {job_id}")
                print(f"   Status: {fields.get('Status', 'Unknown')}")
                print(f"   External ID: {fields.get('External Job ID', 'None')}")
                
                # Check if file exists
                external_id = fields.get('External Job ID')
                if external_id:
                    url = monitor.construct_output_url(external_id)
                    exists = monitor.check_file_exists(url)
                    print(f"   Output file exists: {exists}")
                    print(f"   URL: {url}")
            else:
                print(f"   Job {job_id} not found")
        except Exception as e:
            print(f"   Error checking job {job_id}: {e}")

if __name__ == "__main__":
    test_polling()