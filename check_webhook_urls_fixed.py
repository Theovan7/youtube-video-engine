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

def check_jobs_table():
    """Check all jobs in the Jobs table."""
    print("Checking Jobs table...")
    
    try:
        # Use the get_jobs_by_status method to get processing jobs
        processing_jobs = airtable.get_jobs_by_status('processing')
        
        print(f"\nFound {len(processing_jobs)} jobs in 'processing' status:\n")
        
        for job in processing_jobs:
            fields = job.get('fields', {})
            print(f"Job ID: {job['id']}")
            print(f"Status: {fields.get('Status', 'Unknown')}")
            print(f"Type: {fields.get('Job Type', 'Unknown')}")
            print(f"External Job ID: {fields.get('External Job ID', 'None')}")
            print(f"Webhook URL: {fields.get('Webhook URL', 'None')}")
            print(f"Created: {fields.get('Created Time', 'Unknown')}")
            print(f"Response Payload: {fields.get('Response Payload', 'None')}")
            
            # Check if this is an old job
            created_time = fields.get('Created Time', '')
            if created_time:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    age = datetime.now(created_dt.tzinfo) - created_dt
                    print(f"Age: {age}")
                except:
                    pass
            
            print("-" * 60)
            
    except Exception as e:
        print(f"Error checking jobs: {e}")

def check_webhook_events():
    """Check webhook events table for any received webhooks."""
    print("\n\nChecking Webhook Events table...")
    
    try:
        # Get the webhook events table
        webhook_table = airtable.client.table(airtable.config.AIRTABLE_BASE_ID, 'Webhook Events')
        
        # Get recent webhook events
        events = webhook_table.all(formula="DATETIME_DIFF(NOW(), CREATED_TIME(), 'hours') < 24")
        
        print(f"\nFound {len(events)} webhook events in last 24 hours:\n")
        
        for event in events:
            fields = event.get('fields', {})
            print(f"Event ID: {event['id']}")
            print(f"Service: {fields.get('Service', 'Unknown')}")
            print(f"Endpoint: {fields.get('Endpoint', 'Unknown')}")
            print(f"Related Job: {fields.get('Related Job', 'None')}")
            print(f"Processed: {fields.get('Processed Successfully', 'Unknown')}")
            print(f"Created: {fields.get('Created Time', 'Unknown')}")
            
            # Check payload
            payload = fields.get('Payload', '{}')
            try:
                if payload:
                    payload_data = json.loads(payload) if isinstance(payload, str) else payload
                    print(f"Payload Keys: {list(payload_data.keys()) if isinstance(payload_data, dict) else 'Not a dict'}")
            except:
                print(f"Could not parse payload")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"Error checking webhook events: {e}")

def check_segment_videos():
    """Check segment videos that might be stuck."""
    print("\n\nChecking Segment Videos for stuck combinations...")
    
    try:
        # Get segments that might be stuck in combining
        segments_table = airtable.client.table(airtable.config.AIRTABLE_BASE_ID, 'Segments')
        
        # Look for segments in 'Combining Media' status
        stuck_segments = segments_table.all(formula="Status = 'Combining Media'")
        
        print(f"\nFound {len(stuck_segments)} segments in 'Combining Media' status:\n")
        
        for segment in stuck_segments:
            fields = segment.get('fields', {})
            print(f"Segment ID: {segment['id']}")
            print(f"Status: {fields.get('Status', 'Unknown')}")
            print(f"Has Voiceover: {'Yes' if fields.get('Voiceover') else 'No'}")
            print(f"Has Video: {'Yes' if fields.get('Video') else 'No'}")
            print(f"Has Combined: {'Yes' if fields.get('Voiceover + Video') else 'No'}")
            
            # Check related jobs
            jobs = fields.get('Jobs', [])
            if jobs:
                print(f"Related Jobs: {jobs}")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"Error checking segments: {e}")

if __name__ == "__main__":
    check_jobs_table()
    check_webhook_events()
    check_segment_videos()