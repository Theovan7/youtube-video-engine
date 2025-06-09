#!/usr/bin/env python3
"""
Extract real webhook payloads from Airtable for testing Pydantic models.
"""

import json
import os
from services.airtable_service import AirtableService
from config import get_config

def extract_webhook_payloads():
    """Extract recent webhook payloads from Airtable."""
    config = get_config()()
    airtable = AirtableService()
    
    print("Extracting webhook payloads from Airtable...")
    
    # Get recent webhook events
    webhook_events = airtable.webhook_events_table.all(max_records=50)
    print(f"Found {len(webhook_events)} webhook events")
    
    # Debug: Print first event structure if any
    if webhook_events:
        print(f"First event fields: {list(webhook_events[0]['fields'].keys())}")
    
    # Organize payloads by service
    payloads = {
        'nca': [],
        'goapi': [],
        'elevenlabs': []
    }
    
    for event in webhook_events:
        fields = event['fields']
        service = fields.get('Service', '').lower()
        print(f"Processing event: Service={fields.get('Service')}, Endpoint={fields.get('Endpoint')}")
        # Try both 'Payload' and 'Raw Payload' field names
        payload = fields.get('Payload') or fields.get('Raw Payload')
        processed = fields.get('Processed', 'No') == 'Yes'
        success = fields.get('Success', 'No') == 'Yes'
        
        if payload:
            # Parse payload if it's a string
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception as e:
                    # Try to parse as Python dict literal
                    try:
                        import ast
                        payload = ast.literal_eval(payload)
                    except:
                        print(f"Failed to parse payload for event {event['id']}: {e}")
                        continue
            
            # Add metadata
            payload_data = {
                'webhook_event_id': event['id'],
                'service': service,
                'processed': processed,
                'success': success,
                'endpoint': fields.get('Endpoint', ''),
                'related_job_id': fields.get('Related Job ID', ''),
                'notes': fields.get('Notes', ''),
                'payload': payload
            }
            
            # Categorize by service
            if 'nca' in service:
                payloads['nca'].append(payload_data)
                print(f"Added NCA payload from event {event['id']}")
            elif 'goapi' in service:
                payloads['goapi'].append(payload_data)
                print(f"Added GoAPI payload from event {event['id']}")
            elif 'elevenlabs' in service:
                payloads['elevenlabs'].append(payload_data)
                print(f"Added ElevenLabs payload from event {event['id']}")
    
    # Save payloads to files
    os.makedirs('testing_environment/test_inputs/webhook-simulations/real_payloads', exist_ok=True)
    
    for service, service_payloads in payloads.items():
        if service_payloads:
            filename = f'testing_environment/test_inputs/webhook-simulations/real_payloads/{service}_webhook_payloads.json'
            with open(filename, 'w') as f:
                json.dump(service_payloads, f, indent=2)
            print(f"Saved {len(service_payloads)} {service.upper()} webhook payloads to {filename}")
    
    # Also extract some completed jobs for reference
    print("\nExtracting completed jobs...")
    jobs = airtable.jobs_table.all(
        formula="{Status}='Completed'",
        max_records=20
    )
    
    job_data = []
    for job in jobs:
        fields = job['fields']
        job_info = {
            'job_id': job['id'],
            'job_type': fields.get('Job Type', ''),
            'status': fields.get('Status', ''),
            'external_job_id': fields.get('External Job ID', ''),
            'request_payload': fields.get('Request Payload', ''),
            'response_payload': fields.get('Response Payload', ''),
            'service': fields.get('Service', ''),
            'notes': fields.get('Notes', '')
        }
        job_data.append(job_info)
    
    with open('testing_environment/test_inputs/webhook-simulations/real_payloads/completed_jobs.json', 'w') as f:
        json.dump(job_data, f, indent=2)
    print(f"Saved {len(job_data)} completed jobs")
    
    return payloads

if __name__ == "__main__":
    payloads = extract_webhook_payloads()
    
    # Print summary
    print("\nSummary:")
    for service, service_payloads in payloads.items():
        print(f"- {service.upper()}: {len(service_payloads)} payloads")
        if service_payloads:
            # Show example structure
            print(f"  Example payload keys: {list(service_payloads[0]['payload'].keys())}")