#!/usr/bin/env python3
"""
Fix Jobs table Status field by documenting all required values.

The Jobs table Status field needs these values added:
- processed
- webhook_error  
- webhook_unknown_nca_status

Current values that should remain:
- pending
- processing
- completed
- failed
- Undefined (if it exists)

To fix this issue:
1. Go to your Airtable base: https://airtable.com/app1XR6KcYA8GleJd
2. Open the Jobs table
3. Click on the Status field header
4. Select "Customize field type"
5. Add these missing options:
   - processed
   - webhook_error
   - webhook_unknown_nca_status
6. Save the field

This will prevent the 422 errors when webhooks try to update job status.

Code locations using these statuses:
- api/webhooks.py:177 - Uses 'processed' for successful NCA operations
- api/webhooks.py:477 - Uses 'webhook_error' for webhook processing errors
- api/webhooks.py:509 - Uses 'webhook_unknown_nca_status' for unhandled NCA statuses

Consider also updating config.py to include all status values:
STATUS_PROCESSED = 'processed'
STATUS_WEBHOOK_ERROR = 'webhook_error'
STATUS_WEBHOOK_UNKNOWN = 'webhook_unknown_nca_status'
"""

import os
import sys
from pyairtable import Api

def check_current_status_values():
    """Check what status values currently exist in Jobs table."""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('AIRTABLE_API_KEY')
        base_id = os.getenv('AIRTABLE_BASE_ID', 'app1XR6KcYA8GleJd')
        
        if not api_key:
            print("Error: AIRTABLE_API_KEY not found in environment")
            return
        
        api = Api(api_key)
        base = api.base(base_id)
        jobs_table = base.table('Jobs')
        
        # Get a few records to see what status values are in use
        print("Checking current status values in Jobs table...")
        records = jobs_table.all(max_records=50)
        
        status_values = set()
        for record in records:
            status = record['fields'].get('Status')
            if status:
                status_values.add(status)
        
        print(f"\nFound {len(status_values)} unique status values currently in use:")
        for status in sorted(status_values):
            print(f"  - {status}")
        
        print("\n⚠️  Required status values that may be missing:")
        required_values = ['pending', 'processing', 'completed', 'failed', 'processed', 
                          'webhook_error', 'webhook_unknown_nca_status', 'Undefined']
        
        for required in required_values:
            if required not in status_values:
                print(f"  - {required} (MISSING - needs to be added)")
            else:
                print(f"  - {required} ✓")
        
        print("\n📝 To fix: Add the missing values to the Status field in Airtable")
        
    except Exception as e:
        print(f"Error checking status values: {e}")

if __name__ == "__main__":
    check_current_status_values()
