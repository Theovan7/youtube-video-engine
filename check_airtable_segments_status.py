#!/usr/bin/env python3
"""
Check Airtable Segments table status options and structure.
This script helps verify if all required status values are available in the Airtable segments table.
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

def check_segments_table_structure():
    """Check the current structure of the segments table and available status options."""
    try:
        # Initialize services
        config = get_config()()
        airtable = AirtableService()
        
        print("🔍 Checking Airtable Segments table structure...")
        print(f"📊 Base ID: {config.AIRTABLE_BASE_ID}")
        print(f"📋 Segments Table: {config.SEGMENTS_TABLE}")
        
        # Get a few sample records to understand the structure
        try:
            sample_records = airtable.segments_table.all(max_records=5)
            
            if not sample_records:
                print("⚠️  No records found in segments table")
                return
            
            print(f"\n📈 Found {len(sample_records)} sample records")
            
            # Analyze field structure from sample records
            all_fields = set()
            status_values = set()
            
            for i, record in enumerate(sample_records):
                print(f"\n📝 Record {i+1} (ID: {record['id']}):")
                fields = record.get('fields', {})
                all_fields.update(fields.keys())
                
                # Look for status field
                for field_name, field_value in fields.items():
                    if 'status' in field_name.lower():
                        print(f"   🏷️  {field_name}: {field_value}")
                        if field_value:
                            status_values.add(str(field_value))
                
            print(f"\n📋 All available fields in segments table:")
            for field in sorted(all_fields):
                print(f"   • {field}")
            
            print(f"\n🏷️  Status values found in sample data:")
            if status_values:
                for status in sorted(status_values):
                    print(f"   • {status}")
            else:
                print("   ⚠️  No status values found in sample data")
            
            # Check if Status field exists
            status_field_exists = any('status' in field.lower() for field in all_fields)
            print(f"\n📊 Status field exists: {'✅' if status_field_exists else '❌'}")
            
            return {
                'fields': sorted(all_fields),
                'status_values': sorted(status_values),
                'status_field_exists': status_field_exists,
                'sample_count': len(sample_records)
            }
            
        except Exception as e:
            print(f"❌ Error accessing segments table: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        return None

def get_required_status_values():
    """Get all status values that should be available based on the codebase."""
    
    # Status values from config
    config_statuses = [
        'pending',
        'processing', 
        'completed',
        'failed'
    ]
    
    # Additional status values found in the codebase
    workflow_statuses = [
        'combined',
        'combination_failed',
        'concatenation_failed',
        'music_addition_failed',
        'music_generation_failed', 
        'voiceover_ready',
        'combining_media',
        'segments_combined',
        'adding_music',
        'generating_music',
        'generating_voice',
        'Video Ready',
        'Video Generation Failed'
    ]
    
    all_required = config_statuses + workflow_statuses
    
    print("📋 Required status values based on codebase analysis:")
    print("\n🔧 Basic config statuses:")
    for status in config_statuses:
        print(f"   • {status}")
    
    print("\n🔄 Workflow-specific statuses:")
    for status in workflow_statuses:
        print(f"   • {status}")
    
    print(f"\n📊 Total required status options: {len(all_required)}")
    
    return all_required

def compare_status_options(current_structure, required_statuses):
    """Compare current Airtable structure with required status values."""
    
    if not current_structure:
        print("❌ Cannot compare - unable to read current table structure")
        return
    
    current_statuses = current_structure.get('status_values', [])
    
    print(f"\n🔄 Comparison Results:")
    print(f"   Current status options: {len(current_statuses)}")
    print(f"   Required status options: {len(required_statuses)}")
    
    # Find missing statuses
    missing_statuses = set(required_statuses) - set(current_statuses)
    extra_statuses = set(current_statuses) - set(required_statuses)
    
    if missing_statuses:
        print(f"\n❌ Missing status options ({len(missing_statuses)}):")
        for status in sorted(missing_statuses):
            print(f"   • {status}")
    else:
        print(f"\n✅ All required status options are available!")
    
    if extra_statuses:
        print(f"\n📝 Extra status options in Airtable ({len(extra_statuses)}):")
        for status in sorted(extra_statuses):
            print(f"   • {status}")
    
    return {
        'missing': sorted(missing_statuses),
        'extra': sorted(extra_statuses),
        'has_missing': len(missing_statuses) > 0
    }

def main():
    """Main function to check Airtable segments table status options."""
    
    print("🚀 YouTube Video Engine - Airtable Segments Status Check")
    print("=" * 60)
    
    # Check current table structure
    current_structure = check_segments_table_structure()
    
    print("\n" + "=" * 60)
    
    # Get required status values
    required_statuses = get_required_status_values()
    
    print("\n" + "=" * 60)
    
    # Compare and provide recommendations
    if current_structure:
        comparison = compare_status_options(current_structure, required_statuses)
        
        print("\n🎯 Recommendations:")
        if comparison['has_missing']:
            print("   1. ❌ Add missing status options to the Segments table Status field")
            print("   2. 🔧 Update Airtable field to include all required statuses")
            print("   3. ✅ Test the app functions with new status options")
        else:
            print("   ✅ Segments table has all required status options!")
            print("   🎯 The app should function correctly with current status setup")
    
    print(f"\n📋 Summary:")
    if current_structure:
        print(f"   • Table structure: ✅ Accessible")
        print(f"   • Status field: {'✅' if current_structure['status_field_exists'] else '❌'}")
        print(f"   • Sample records: {current_structure['sample_count']}")
        if 'missing' in locals():
            print(f"   • Missing statuses: {len(comparison['missing'])}")
    else:
        print(f"   • Table structure: ❌ Not accessible")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
