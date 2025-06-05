#!/usr/bin/env python3
"""
Check the current state of the stuck segment and related jobs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.airtable_service import AirtableService
from config import get_config
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_stuck_segment():
    """Check the current state of segment recXwiLcbFPcIQxI7."""
    try:
        # Initialize services
        config = get_config()()
        airtable = AirtableService()
        
        stuck_segment_id = "recXwiLcbFPcIQxI7"
        
        print("🔍 Checking stuck segment...")
        print(f"📊 Segment ID: {stuck_segment_id}")
        
        # Get segment details
        try:
            segment = airtable.get_segment(stuck_segment_id)
            if not segment:
                print(f"❌ Segment {stuck_segment_id} not found")
                return
            
            fields = segment.get('fields', {})
            
            print(f"\n📝 Segment Details:")
            print(f"   ID: {segment['id']}")
            print(f"   Content: {fields.get('Content', 'N/A')}")
            print(f"   Status: {fields.get('Status', 'N/A')}")
            print(f"   Duration: {fields.get('Duration (seconds)', 'N/A')} seconds")
            print(f"   Last Modified: {segment.get('createdTime', 'N/A')}")
            
            # Check for media resources
            print(f"\n📋 Available Resources:")
            print(f"   Video: {'✅' if fields.get('Video') else '❌'}")
            print(f"   Voiceover: {'✅' if fields.get('Voiceover') else '❌'}")
            print(f"   Images: {'✅' if fields.get('Images') else '❌'}")
            print(f"   Voiceover + Video: {'✅' if fields.get('Voiceover + Video') else '❌'}")
            
            if fields.get('Images'):
                print(f"      Image count: {len(fields['Images'])}")
            
            # Get related jobs
            print(f"\n🔍 Searching for related jobs...")
            jobs = airtable.jobs_table.all(formula=f"FIND('{stuck_segment_id}', {{Segments}})")
            
            if jobs:
                print(f"   Found {len(jobs)} related jobs:")
                for i, job in enumerate(jobs):
                    job_fields = job.get('fields', {})
                    print(f"\n   Job {i+1}:")
                    print(f"      ID: {job['id']}")
                    print(f"      Type: {job_fields.get('Job Type', 'N/A')}")
                    print(f"      Status: {job_fields.get('Status', 'N/A')}")
                    print(f"      External Job ID: {job_fields.get('External Job ID', 'N/A')}")
                    print(f"      Error: {job_fields.get('Error', 'N/A')}")
                    print(f"      Created: {job.get('createdTime', 'N/A')}")
            else:
                print("   ❌ No related jobs found")
            
            return {
                'segment': segment,
                'jobs': jobs,
                'stuck': fields.get('Status') == 'Combining Media'
            }
            
        except Exception as e:
            print(f"❌ Error accessing segment: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        return None

def check_missing_job():
    """Check for the missing NCA job mentioned in troubleshooting notes."""
    try:
        config = get_config()()
        airtable = AirtableService()
        
        missing_job_id = "recm8Ycr5coKYs62G"
        
        print(f"\n🔍 Checking for missing job...")
        print(f"📊 Job ID: {missing_job_id}")
        
        # Try to find the job
        try:
            job = airtable.get_job(missing_job_id)
            if job:
                print(f"✅ Job found!")
                job_fields = job.get('fields', {})
                print(f"   Type: {job_fields.get('Job Type', 'N/A')}")
                print(f"   Status: {job_fields.get('Status', 'N/A')}")
                print(f"   External Job ID: {job_fields.get('External Job ID', 'N/A')}")
            else:
                print(f"❌ Job {missing_job_id} not found in database")
                print("   This confirms the 'missing job' issue from troubleshooting notes")
        except Exception as e:
            print(f"❌ Error checking job: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_successful_job_with_wrong_status():
    """Check the job that was successful but marked as failed."""
    try:
        config = get_config()()
        airtable = AirtableService()
        
        # Search for job with external ID 025c2adc-710c-431e-9779-a055cc1bea43
        external_job_id = "025c2adc-710c-431e-9779-a055cc1bea43"
        
        print(f"\n🔍 Checking successful job marked as failed...")
        print(f"📊 External Job ID: {external_job_id}")
        
        # Search for job by external ID
        jobs = airtable.jobs_table.all(formula=f"{{External Job ID}} = '{external_job_id}'")
        
        if jobs:
            job = jobs[0]  # Should be only one
            job_fields = job.get('fields', {})
            
            print(f"✅ Job found!")
            print(f"   ID: {job['id']}")
            print(f"   Type: {job_fields.get('Job Type', 'N/A')}")
            print(f"   Status: {job_fields.get('Status', 'N/A')}")
            print(f"   Error: {job_fields.get('Error', 'N/A')}")
            print(f"   Created: {job.get('createdTime', 'N/A')}")
            
            # Check if the output URL was actually generated
            output_url = "https://phi-bucket.nyc3.digitaloceanspaces.com/phi-bucket/025c2adc-710c-431e-9779-a055cc1bea43_output_0.mp4"
            print(f"\n📋 Expected output URL: {output_url}")
            print("   This job was actually successful but webhook handler marked it as failed")
            
        else:
            print(f"❌ Job with external ID {external_job_id} not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function to check the current issue state."""
    
    print("🚀 YouTube Video Engine - Stuck Segment Analysis")
    print("=" * 60)
    
    # Check the stuck segment
    segment_data = check_stuck_segment()
    
    print("\n" + "=" * 60)
    
    # Check for missing job
    check_missing_job()
    
    print("\n" + "=" * 60)
    
    # Check successful job marked as failed
    check_successful_job_with_wrong_status()
    
    print("\n" + "=" * 60)
    
    print("\n🎯 Summary:")
    if segment_data:
        if segment_data['stuck']:
            print("   ❌ Segment is stuck in 'Combining Media' status")
            print("   🔧 Manual recovery needed")
        else:
            print("   ✅ Segment status appears normal")
    
    print("   📋 Next steps:")
    print("   1. Fix webhook status parsing logic")
    print("   2. Add NCA job validation") 
    print("   3. Manually recover stuck segment")
    print("   4. Test fixes with new job")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
