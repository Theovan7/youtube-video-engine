#!/usr/bin/env python3
"""
Check the status of the missing NCA job recm8Ycr5coKYs62G
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, '/Users/theovandermerwe/Dropbox/CODING2/ClaudeDesktop/ProjectHI/youtube_video_engine')

# Load environment variables
load_dotenv()

def check_nca_job_status():
    """Check the status of job recm8Ycr5coKYs62G"""
    
    print("🔍 CHECKING NCA JOB STATUS")
    print("=" * 40)
    
    # Get API credentials
    api_key = os.getenv('NCA_API_KEY')
    base_url = os.getenv('NCA_BASE_URL', 'https://no-code-architect-app-gpxhq.ondigitalocean.app')
    
    if not api_key:
        print("❌ ERROR: NCA_API_KEY not found in environment variables")
        return False
    
    job_id = "recm8Ycr5coKYs62G"  # From your test output
    
    print(f"📋 Checking job: {job_id}")
    print(f"🌐 Base URL: {base_url}")
    print()
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Check job status using the NCA endpoint
    url = f"{base_url}/v1/job/status/{job_id}"
    
    print(f"🔍 Checking status at: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Job Status Response:")
                print(f"   Job ID: {result.get('job_id', 'N/A')}")
                print(f"   Status: {result.get('status', 'N/A')}")
                print(f"   Progress: {result.get('progress', 'N/A')}")
                print(f"   Message: {result.get('message', 'N/A')}")
                
                if 'output' in result:
                    print(f"   Output: {result['output']}")
                
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                
                return True
            except Exception as e:
                print(f"❌ Error parsing JSON response: {e}")
                print(f"Raw response: {response.text}")
                return False
                
        elif response.status_code == 404:
            print("❌ JOB NOT FOUND")
            print("This could mean:")
            print("   1. Job was never submitted to NCA")
            print("   2. Job ID is incorrect")
            print("   3. Job was cleaned up/expired")
            return False
            
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking job status: {e}")
        return False

def check_webhook_endpoint():
    """Verify the webhook endpoint is accessible"""
    
    print("\n🔗 CHECKING WEBHOOK ENDPOINT")
    print("=" * 30)
    
    webhook_url = "https://youtube-video-engine.fly.dev/webhooks/nca-toolkit"
    
    try:
        # Just check if the endpoint responds
        response = requests.get(webhook_url, timeout=10)
        print(f"📡 Webhook endpoint status: {response.status_code}")
        
        if response.status_code in [200, 405]:  # 405 = Method Not Allowed is OK for GET on POST endpoint
            print("✅ Webhook endpoint is accessible")
            return True
        else:
            print(f"⚠️  Webhook endpoint returned: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook endpoint check failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 NCA JOB STATUS INVESTIGATION")
    print("=" * 50)
    
    # Check the specific job
    job_found = check_nca_job_status()
    
    # Check webhook accessibility 
    webhook_ok = check_webhook_endpoint()
    
    print("\n📊 INVESTIGATION SUMMARY:")
    print("=" * 25)
    print(f"🔍 Job Status Check: {'✅ FOUND' if job_found else '❌ NOT FOUND'}")
    print(f"🔗 Webhook Endpoint: {'✅ ACCESSIBLE' if webhook_ok else '❌ ISSUE'}")
    
    if not job_found:
        print("\n🎯 LIKELY CAUSES:")
        print("1. NCA Toolkit never received or processed the job")
        print("2. Job failed immediately and was cleaned up")
        print("3. Different job ID system than expected")
        print("4. NCA API endpoint or authentication issue")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Check NCA Toolkit logs for job submission")
    print("2. Verify NCA API key and base URL are correct")
    print("3. Test with a fresh job submission")
    print("4. Check if webhook URL format matches NCA expectations")
