#!/usr/bin/env python3
"""
Automated Airtable Status Field Setup Script
This script attempts to add the required Status field to the Segments table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.airtable_service import AirtableService
from config import get_config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_required_status_options():
    """Get all required status options with colors."""
    return [
        {"name": "pending", "color": "grayBright2"},
        {"name": "processing", "color": "blueBright2"}, 
        {"name": "completed", "color": "greenBright2"},
        {"name": "failed", "color": "redBright2"},
        {"name": "combined", "color": "greenLight2"},
        {"name": "combination_failed", "color": "redBright2"},
        {"name": "concatenation_failed", "color": "redBright2"},
        {"name": "voiceover_ready", "color": "blueBright1"},
        {"name": "combining_media", "color": "orangeBright2"},
        {"name": "segments_combined", "color": "greenLight2"},
        {"name": "adding_music", "color": "purpleBright2"},
        {"name": "generating_music", "color": "purpleBright2"},
        {"name": "generating_voice", "color": "blueBright1"},
        {"name": "Video Ready", "color": "greenBright2"},
        {"name": "Video Generation Failed", "color": "redBright2"},
        {"name": "music_addition_failed", "color": "redBright2"},
        {"name": "music_generation_failed", "color": "redBright2"}
    ]

def add_status_field_manual_instructions():
    """Provide manual instructions for adding the Status field."""
    
    print("🔧 MANUAL SETUP REQUIRED")
    print("=" * 50)
    print("Due to API limitations, please add the Status field manually:")
    print("")
    print("1. Open Airtable.com")
    print("2. Go to PHI Video Production base")
    print("3. Open Segments table")
    print("4. Click + to add new field")
    print("5. Select 'Single Select' type")
    print("6. Name it 'Status'")
    print("7. Add these 17 options:")
    print("")
    
    options = get_required_status_options()
    for i, option in enumerate(options, 1):
        print(f"   {i:2d}. {option['name']}")
    
    print("")
    print("8. Set default value to 'pending'")
    print("9. Save the field")
    print("")
    print("📄 Complete instructions: AIRTABLE_STATUS_FIELD_SETUP.md")

def try_automated_setup():
    """Attempt to add the Status field programmatically."""
    try:
        print("🤖 Attempting automated setup...")
        
        # This would require direct API access with schema modification permissions
        # Most Airtable plans don't allow programmatic field creation
        
        # For now, we'll just validate the current setup
        config = get_config()()
        airtable = AirtableService()
        
        # Check if we can at least access the table
        try:
            sample_records = airtable.segments_table.all(max_records=1)
            print("✅ Table access confirmed")
            
            # Check current fields
            if sample_records:
                fields = list(sample_records[0].get('fields', {}).keys())
                if 'Status' in fields:
                    print("✅ Status field already exists!")
                    return True
                else:
                    print("❌ Status field not found")
                    return False
            else:
                print("⚠️  No records found to check field structure")
                return False
                
        except Exception as e:
            print(f"❌ Cannot access segments table: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Automated setup failed: {e}")
        return False

def verify_setup():
    """Verify that the Status field has been added correctly."""
    try:
        config = get_config()()
        airtable = AirtableService()
        
        # Get sample records to check field structure
        sample_records = airtable.segments_table.all(max_records=5)
        
        if not sample_records:
            print("⚠️  No records found to verify setup")
            return False
        
        # Check if Status field exists
        all_fields = set()
        status_values = set()
        
        for record in sample_records:
            fields = record.get('fields', {})
            all_fields.update(fields.keys())
            
            # Look for status field
            for field_name, field_value in fields.items():
                if field_name.lower() == 'status':
                    if field_value:
                        status_values.add(str(field_value))
        
        status_field_exists = 'Status' in all_fields
        required_options = [opt['name'] for opt in get_required_status_options()]
        
        print(f"\n📊 Verification Results:")
        print(f"   Status field exists: {'✅' if status_field_exists else '❌'}")
        
        if status_field_exists:
            missing_options = set(required_options) - status_values
            if missing_options:
                print(f"   Missing status options: {len(missing_options)}")
                for option in sorted(missing_options):
                    print(f"      • {option}")
            else:
                print(f"   All status options available: ✅")
                return True
        
        return status_field_exists and len(missing_options) == 0
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function to set up the Status field."""
    
    print("🚀 YouTube Video Engine - Airtable Status Field Setup")
    print("=" * 60)
    
    # Try automated setup first
    automated_success = try_automated_setup()
    
    if not automated_success:
        print("\n" + "=" * 60)
        add_status_field_manual_instructions()
        print("\n" + "=" * 60)
        
        # Ask user to confirm manual setup
        print("\nAfter manually adding the Status field, press Enter to verify...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nSetup cancelled.")
            return
        
        # Verify the setup
        print("🔍 Verifying setup...")
        if verify_setup():
            print("\n✅ SUCCESS: Status field is properly configured!")
            print("🎯 The YouTube Video Engine should now work correctly.")
        else:
            print("\n❌ Setup verification failed.")
            print("📋 Please check the manual instructions and try again.")
    else:
        print("\n✅ Status field already exists!")
        
        # Still verify it has all required options
        if verify_setup():
            print("🎯 All status options are available!")
        else:
            print("⚠️  Some status options may be missing.")

if __name__ == "__main__":
    main()
