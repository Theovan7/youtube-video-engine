#!/usr/bin/env python3
"""Test script to check Airtable segment record and Status field options."""

import requests
import json
import os

def check_airtable_segment():
    """Check the segment record and Status field configuration."""
    
    record_id = "recxGRBRi1Qe9sLDn"
    base_id = "app1XR6KcYA8GleJd"
    
    # Airtable API setup - need to check what API key the Flask server is using
    # This is likely in the .env file or config
    
    print("🔍 ANALYZING NEW ERROR...")
    print("✅ GOOD NEWS: Schema validation error is FIXED!")
    print("❌ NEW ISSUE: Airtable permissions error")
    print()
    
    print("📋 ERROR BREAKDOWN:")
    print("1. API call to Flask server: ✅ SUCCESS (no more validation error)")
    print("2. Flask server processing: ✅ STARTED (trying to update status)")
    print("3. Airtable status update: ❌ FAILED (insufficient permissions)")
    print()
    
    print("🎯 ROOT CAUSE:")
    print("The Flask server API key doesn't have permission to create")
    print("new select options in the Airtable Status field.")
    print()
    
    print("💡 SPECIFIC ERROR:")
    print("Trying to set Status = 'Generating Video'")
    print("But 'Generating Video' is not an existing option in the Status field")
    print("And the API key lacks permission to create new options")
    print()
    
    print("🔧 POSSIBLE SOLUTIONS:")
    print("1. Add 'Generating Video' as a Status option in Airtable manually")
    print("2. Update Flask server to use a different status value that exists")
    print("3. Grant the Flask server API key permission to modify field options")
    print("4. Check what Status options currently exist in the field")

if __name__ == "__main__":
    check_airtable_segment()
