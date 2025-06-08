#!/usr/bin/env python3
"""
Test NCA webhook connectivity by creating a simple test job.
"""

import os
import json
import time
import requests
from services.nca_service import NCAService
from services.airtable_service import AirtableService
from config import get_config

# Initialize services
config = get_config()()
nca = NCAService()
airtable = AirtableService()

def test_webhook_connectivity():
    """Test if NCA can reach our webhook endpoint."""
    print("Testing NCA webhook connectivity...\n")
    
    # First, test if our webhook endpoint is accessible
    webhook_base_url = config.WEBHOOK_BASE_URL
    test_webhook_url = f"{webhook_base_url}/webhooks/nca-toolkit?job_id=test123&operation=test"
    
    print(f"1. Testing webhook endpoint accessibility: {test_webhook_url}")
    try:
        response = requests.post(test_webhook_url, 
                               json={"id": "test123", "test": True},
                               timeout=5)
        print(f"   Response: {response.status_code}")
        if response.status_code == 500:
            print("   Note: 500 error is expected without proper authentication")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Creating a test job in Airtable...")
    try:
        # Create a test job
        test_job = airtable.create_job(
            job_type='test_webhook',
            request_payload={'test': True, 'purpose': 'webhook_connectivity_test'}
        )
        job_id = test_job['id']
        print(f"   Created job: {job_id}")
        
        # Construct webhook URL
        webhook_url = f"{webhook_base_url}/webhooks/nca-toolkit?job_id={job_id}&operation=test_connectivity"
        print(f"   Webhook URL: {webhook_url}")
        
        print("\n3. Sending a simple NCA request with webhook...")
        
        # Use a simple NCA endpoint that should return quickly
        # Let's try the health check first
        print("   Testing NCA health check...")
        if nca.check_health():
            print("   ✓ NCA service is healthy")
        else:
            print("   ✗ NCA service health check failed")
            
        # Try to submit a simple job with webhook
        print("\n4. Submitting a test job to NCA with webhook callback...")
        try:
            # Create a simple concat job with minimal inputs
            result = nca.concatenate_videos(
                video_urls=["https://example.com/test1.mp4", "https://example.com/test2.mp4"],
                output_filename="test_webhook_connectivity.mp4",
                webhook_url=webhook_url,
                custom_id=job_id
            )
            
            if 'job_id' in result:
                external_job_id = result['job_id']
                print(f"   ✓ NCA job created: {external_job_id}")
                
                # Update Airtable job with external ID
                airtable.update_job(job_id, {
                    'External Job ID': external_job_id,
                    'Webhook URL': webhook_url,
                    'Status': 'processing'
                })
                
                print("\n5. Waiting for webhook callback (30 seconds)...")
                time.sleep(30)
                
                # Check if job status was updated
                updated_job = airtable.get_job(job_id)
                final_status = updated_job['fields'].get('Status', 'Unknown')
                
                print(f"\n6. Final job status: {final_status}")
                
                if final_status == 'processing':
                    print("   ⚠️  Job still in processing - webhook likely not received")
                    
                    # Try to get status directly from NCA
                    print("\n7. Checking NCA job status directly...")
                    try:
                        nca_status = nca.get_job_status(external_job_id)
                        print(f"   NCA Status: {json.dumps(nca_status, indent=2)}")
                    except Exception as e:
                        print(f"   Error checking NCA status: {e}")
                        
                else:
                    print(f"   ✓ Job status updated to: {final_status}")
                    print("   Webhook was received successfully!")
                    
        except Exception as e:
            print(f"   Error creating NCA job: {e}")
            
    except Exception as e:
        print(f"Error in test: {e}")

def check_recent_webhook_events():
    """Check if any webhook events were recorded recently."""
    print("\n\n8. Checking for recent webhook events...")
    
    try:
        # Try to access webhook events table
        webhook_table = airtable.base.table('Webhook Events')
        
        # Get events from last hour
        recent_events = webhook_table.all(formula="DATETIME_DIFF(NOW(), {Created Time}, 'minutes') < 60")
        
        print(f"   Found {len(recent_events)} webhook events in last hour")
        
        for event in recent_events[:5]:  # Show first 5
            fields = event['fields']
            print(f"\n   Event: {event['id']}")
            print(f"   Service: {fields.get('Service', 'Unknown')}")
            print(f"   Created: {fields.get('Created Time', 'Unknown')}")
            print(f"   Processed: {fields.get('Processed Successfully', 'Unknown')}")
            
    except Exception as e:
        print(f"   Could not check webhook events: {e}")

if __name__ == "__main__":
    test_webhook_connectivity()
    check_recent_webhook_events()