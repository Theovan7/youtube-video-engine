#!/usr/bin/env python3
"""
Test Pydantic webhook models using real payloads from Airtable.
This uses the testing framework to validate our Pydantic models with production data.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.webhooks.nca_models import NCAWebhookPayload
from models.webhooks.goapi_models import GoAPIWebhookPayload
from pydantic import ValidationError


class PydanticWebhookTester:
    """Test Pydantic webhook models with real payloads"""
    
    def __init__(self):
        self.base_path = Path("test_inputs/webhook-simulations/real_payloads")
        self.results = {
            'nca': {'success': 0, 'failed': 0, 'errors': []},
            'goapi': {'success': 0, 'failed': 0, 'errors': []}
        }
    
    def load_payloads(self, service: str) -> List[Dict]:
        """Load webhook payloads for a service"""
        file_path = self.base_path / f"{service}_webhook_payloads.json"
        if not file_path.exists():
            print(f"Warning: No payloads found at {file_path}")
            return []
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def test_nca_payload(self, payload_data: Dict) -> bool:
        """Test a single NCA payload"""
        try:
            # Extract the actual payload
            raw_payload = payload_data.get('payload', {})
            
            # Parse with Pydantic
            model = NCAWebhookPayload(**raw_payload)
            
            # Test model methods
            status = model.get_status()
            output_url = model.get_output_url()
            error_msg = model.get_error_message()
            
            # Log successful parsing
            webhook_id = payload_data.get('webhook_event_id', 'unknown')
            success = payload_data.get('success', False)
            
            print(f"✓ NCA Webhook {webhook_id}:")
            print(f"  - Status: {status}")
            print(f"  - Output URL: {output_url}")
            print(f"  - Error: {error_msg}")
            print(f"  - Webhook Success: {success}")
            
            # Validate consistency
            if success and status != 'completed':
                print(f"  ⚠️  Warning: Webhook marked as success but status is {status}")
            
            return True
            
        except ValidationError as e:
            webhook_id = payload_data.get('webhook_event_id', 'unknown')
            self.results['nca']['errors'].append({
                'webhook_id': webhook_id,
                'error': str(e),
                'payload': raw_payload
            })
            print(f"✗ NCA Webhook {webhook_id} failed validation: {e}")
            return False
        except Exception as e:
            webhook_id = payload_data.get('webhook_event_id', 'unknown')
            self.results['nca']['errors'].append({
                'webhook_id': webhook_id,
                'error': f"Unexpected error: {str(e)}",
                'payload': payload_data.get('payload', {})
            })
            print(f"✗ NCA Webhook {webhook_id} unexpected error: {e}")
            return False
    
    def test_goapi_payload(self, payload_data: Dict) -> bool:
        """Test a single GoAPI payload"""
        try:
            # Extract the actual payload
            raw_payload = payload_data.get('payload', {})
            
            # Parse with Pydantic
            model = GoAPIWebhookPayload(**raw_payload)
            
            # Test model methods
            status = model.get_status()
            video_url = model.get_video_url()
            music_url = model.get_music_url()
            error_msg = model.get_error_message()
            is_completed = model.is_completed()
            is_failed = model.is_failed()
            
            # Log successful parsing
            webhook_id = payload_data.get('webhook_event_id', 'unknown')
            success = payload_data.get('success', False)
            
            print(f"✓ GoAPI Webhook {webhook_id}:")
            print(f"  - Status: {status}")
            print(f"  - Video URL: {video_url}")
            print(f"  - Music URL: {music_url}")
            print(f"  - Error: {error_msg}")
            print(f"  - Is Completed: {is_completed}")
            print(f"  - Is Failed: {is_failed}")
            print(f"  - Webhook Success: {success}")
            
            # Validate consistency
            if success and not is_completed:
                print(f"  ⚠️  Warning: Webhook marked as success but not completed")
            
            return True
            
        except ValidationError as e:
            webhook_id = payload_data.get('webhook_event_id', 'unknown')
            self.results['goapi']['errors'].append({
                'webhook_id': webhook_id,
                'error': str(e),
                'payload': raw_payload
            })
            print(f"✗ GoAPI Webhook {webhook_id} failed validation: {e}")
            return False
        except Exception as e:
            webhook_id = payload_data.get('webhook_event_id', 'unknown')
            self.results['goapi']['errors'].append({
                'webhook_id': webhook_id,
                'error': f"Unexpected error: {str(e)}",
                'payload': payload_data.get('payload', {})
            })
            print(f"✗ GoAPI Webhook {webhook_id} unexpected error: {e}")
            return False
    
    def run_tests(self):
        """Run all tests"""
        print("=== Testing Pydantic Models with Real Webhook Payloads ===\n")
        
        # Test NCA payloads
        print("Testing NCA Webhook Payloads...")
        print("-" * 50)
        nca_payloads = self.load_payloads('nca')
        for payload in nca_payloads:
            if self.test_nca_payload(payload):
                self.results['nca']['success'] += 1
            else:
                self.results['nca']['failed'] += 1
        
        print(f"\nNCA Results: {self.results['nca']['success']} success, {self.results['nca']['failed']} failed\n")
        
        # Test GoAPI payloads
        print("Testing GoAPI Webhook Payloads...")
        print("-" * 50)
        goapi_payloads = self.load_payloads('goapi')
        for payload in goapi_payloads:
            if self.test_goapi_payload(payload):
                self.results['goapi']['success'] += 1
            else:
                self.results['goapi']['failed'] += 1
        
        print(f"\nGoAPI Results: {self.results['goapi']['success']} success, {self.results['goapi']['failed']} failed\n")
        
        # Summary
        self.print_summary()
        
        # Save error report if any failures
        if self.has_errors():
            self.save_error_report()
    
    def has_errors(self) -> bool:
        """Check if any tests failed"""
        return self.results['nca']['failed'] > 0 or self.results['goapi']['failed'] > 0
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        total_success = self.results['nca']['success'] + self.results['goapi']['success']
        total_failed = self.results['nca']['failed'] + self.results['goapi']['failed']
        
        print(f"Total Payloads Tested: {total_success + total_failed}")
        print(f"✓ Successful: {total_success}")
        print(f"✗ Failed: {total_failed}")
        
        if total_failed == 0:
            print("\n🎉 All webhook payloads validated successfully!")
            print("The Pydantic models correctly handle all real production payloads.")
        else:
            print(f"\n⚠️  {total_failed} payloads failed validation.")
            print("See pydantic_webhook_errors.json for details.")
    
    def save_error_report(self):
        """Save detailed error report"""
        report = {
            'summary': {
                'nca_success': self.results['nca']['success'],
                'nca_failed': self.results['nca']['failed'],
                'goapi_success': self.results['goapi']['success'],
                'goapi_failed': self.results['goapi']['failed']
            },
            'errors': {
                'nca': self.results['nca']['errors'],
                'goapi': self.results['goapi']['errors']
            }
        }
        
        with open('pydantic_webhook_errors.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nError report saved to pydantic_webhook_errors.json")


def main():
    """Run the tests"""
    tester = PydanticWebhookTester()
    tester.run_tests()
    
    # Return exit code based on results
    return 1 if tester.has_errors() else 0


if __name__ == "__main__":
    exit(main())