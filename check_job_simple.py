#!/usr/bin/env python3
"""
Simple script to check job status using direct Airtable API calls.
"""

import requests
import os
from pathlib import Path

def load_env_vars():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def check_job_status():
    """Check the job status directly via Airtable API."""
    
    # Load environment variables
    load_env_vars()
    
    # Get environment variables for Airtable
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key or not base_id:
        print("❌ Missing Airtable credentials")
        print(f"   API Key: {'✓' if api_key else '✗'}")
        print(f"   Base ID: {'✓' if base_id else '✗'}")
        return
    
    # Job ID from our test
    job_id = "recYughPfNurpuJek"
    
    # Airtable API endpoint (correct table name is "Jobs")
    url = f"https://api.airtable.com/v0/{base_id}/Jobs/{job_id}"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔍 Checking job status: {job_id}")
        print(f"   URL: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            job = response.json()
            fields = job.get('fields', {})
            
            print(f"📋 Job Status for {job_id}:")
            print(f"   Status: {fields.get('Status', 'N/A')}")
            print(f"   Type: {fields.get('Type', 'N/A')}")
            print(f"   External Job ID: {fields.get('External Job ID', 'N/A')}")
            print(f"   Created: {fields.get('Created Time', 'N/A')}")
            print(f"   Updated: {fields.get('Last Modified Time', 'N/A')}")
            
            video_url = fields.get('Video URL')
            if video_url:
                print(f"   Video URL: {video_url}")
            else:
                print(f"   Video URL: Not generated yet")
            
            error = fields.get('Error Details')
            if error:
                print(f"   Error: {error}")
                
            # Show response payload if available
            response_payload = fields.get('Response Payload')
            if response_payload:
                print(f"   Response Payload: {response_payload[:100]}...")
            
            # Show request payload if available  
            request_payload = fields.get('Request Payload')
            if request_payload:
                print(f"   Request Payload: {request_payload[:100]}...")
                
            print(f"\n🔗 External Task ID: {fields.get('External Job ID', 'N/A')}")
            
        elif response.status_code == 404:
            print(f"❌ Job {job_id} not found in Jobs table")
        else:
            print(f"❌ Error getting job: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking job: {e}")

if __name__ == "__main__":
    check_job_status()
