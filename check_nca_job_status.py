#!/usr/bin/env python3
"""Check NCA job status directly."""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# NCA configuration
NCA_API_KEY = os.getenv('NCA_API_KEY')
NCA_BASE_URL = os.getenv('NCA_BASE_URL', 'https://api.ncatoolkit.com')

def check_nca_job(job_id):
    """Check the status of an NCA job."""
    
    url = f"{NCA_BASE_URL}/v1/job/status/{job_id}"
    headers = {
        'x-api-key': NCA_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def main():
    """Check the two processing jobs found."""
    
    jobs_to_check = [
        {
            'airtable_id': 'rec1SGPYaLvliXLmU',
            'nca_job_id': '6f147c49-52f8-499d-93a7-0394964b4ac1',
            'type': 'combine'
        },
        {
            'airtable_id': 'rec2YOaDXxVarrn55',
            'nca_job_id': '6e420e8c-c382-4467-bf49-7cafa0dc72f3',
            'type': 'combine'
        }
    ]
    
    print("=" * 80)
    print("CHECKING NCA JOB STATUS")
    print("=" * 80)
    
    for job in jobs_to_check:
        print(f"\nAirtable Job: {job['airtable_id']}")
        print(f"NCA Job ID: {job['nca_job_id']}")
        print(f"Type: {job['type']}")
        
        result = check_nca_job(job['nca_job_id'])
        
        if 'error' in result:
            print(f"❌ Error checking job: {result['error']}")
        else:
            status = result.get('status', 'Unknown')
            state = result.get('state', 'Unknown')
            
            print(f"Status: {status}")
            print(f"State: {state}")
            
            if status == 'completed':
                print("✅ Job completed successfully!")
                output = result.get('output', {})
                if output:
                    print(f"Output URL: {output.get('url', 'N/A')}")
                print("\n⚠️  This job is marked as 'processing' in Airtable but is actually completed!")
                print("   The webhook likely failed. Consider running a recovery script.")
                
            elif status == 'failed':
                print("❌ Job failed!")
                error = result.get('error', 'Unknown error')
                print(f"Error: {error}")
                
            elif status in ['pending', 'processing']:
                print("⏳ Job is still processing...")
                created_at = result.get('created_at', '')
                if created_at:
                    print(f"Created at: {created_at}")
            
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()