#!/usr/bin/env python3
"""
Test script to verify the corrected GoAPI payload structure.
This script creates the payload that would be sent to GoAPI and prints it
to verify it matches the working n8n example structure.
"""

import json
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.goapi_service import GoAPIService


def test_corrected_payload():
    """Test the corrected payload structure."""
    
    print("🎬 TESTING CORRECTED GOAPI PAYLOAD STRUCTURE")
    print("=" * 60)
    
    try:
        # Initialize GoAPI service
        service = GoAPIService()
        
        # Test parameters
        test_params = {
            'image_url': 'https://example.com/test-image.jpg',
            'duration': 10,
            'aspect_ratio': '1:1',  # Using same as n8n example
            'quality': 'standard',
            'webhook_url': 'https://example.com/webhook'
        }
        
        print("📋 Test Parameters:")
        print(f"   Image URL: {test_params['image_url']}")
        print(f"   Duration: {test_params['duration']} seconds")
        print(f"   Aspect Ratio: {test_params['aspect_ratio']}")
        print(f"   Quality: {test_params['quality']}")
        print(f"   Webhook URL: {test_params['webhook_url']}")
        print()
        
        # Build the payload manually to show structure
        mode_mapping = {
            'standard': 'std',
            'high': 'pro',
            'pro': 'pro'
        }
        mode = mode_mapping.get(test_params['quality'], 'std')
        
        # This is the CORRECTED payload structure
        corrected_payload = {
            'model': 'kling',
            'task_type': 'video_generation',
            'input': {  # ← KEY FIX: 'input' wrapper
                'prompt': 'animate the video',
                'cfg_scale': 0.5,
                'duration': test_params['duration'],
                'aspect_ratio': test_params['aspect_ratio'],
                'version': '1.6',  # ← Inside 'input'
                'mode': mode,      # ← Inside 'input'
                'image_url': test_params['image_url'],
                'effect': 'expansion',  # ← Inside 'input'
                'camera_control': {
                    'type': 'simple',
                    'config': {  # ← KEY FIX: 'config' wrapper for camera params
                        'horizontal': 0,
                        'vertical': 2,
                        'pan': -10,
                        'tilt': 0,
                        'roll': 0,
                        'zoom': 0
                    }
                }
            },
            'config': {  # ← KEY FIX: 'config' section
                'service_mode': 'public',
                'webhook_config': {  # ← Webhook inside config
                    'endpoint': test_params['webhook_url']
                }
            }
        }
        
        print("🎯 CORRECTED PAYLOAD STRUCTURE:")
        print("=" * 40)
        print(json.dumps(corrected_payload, indent=2))
        print()
        
        # Compare with the n8n working structure (from payload_comparison.txt)
        n8n_working_structure = {
            "model": "kling",
            "task_type": "video_generation",
            "input": {
                "prompt": "animate the video",
                "cfg_scale": 0.5,
                "duration": 10,
                "aspect_ratio": "1:1",
                "version": "1.6",
                "mode": "std",
                "image_url": "...",
                "effect": "expansion",
                "camera_control": {
                    "type": "simple",
                    "config": {
                        "horizontal": 0,
                        "vertical": 2,
                        "pan": -10,
                        "tilt": 0,
                        "roll": 0,
                        "zoom": 0
                    }
                }
            },
            "config": {
                "webhook_config": {
                    "endpoint": "webhook_url"
                },
                "service_mode": "public"
            }
        }
        
        print("✅ N8N WORKING STRUCTURE (for comparison):")
        print("=" * 40)
        print(json.dumps(n8n_working_structure, indent=2))
        print()
        
        # Verify structure matches
        structure_matches = True
        issues = []
        
        # Check top level keys
        if set(corrected_payload.keys()) != set(n8n_working_structure.keys()):
            structure_matches = False
            issues.append("Top level keys don't match")
        
        # Check input section keys
        if set(corrected_payload['input'].keys()) != set(n8n_working_structure['input'].keys()):
            structure_matches = False
            issues.append("Input section keys don't match")
        
        # Check config section
        if 'webhook_config' not in corrected_payload['config']:
            structure_matches = False
            issues.append("webhook_config not in config section")
        
        # Check camera_control structure
        if 'config' not in corrected_payload['input']['camera_control']:
            structure_matches = False
            issues.append("camera_control missing 'config' wrapper")
        
        print("🔍 STRUCTURE VALIDATION:")
        print("=" * 30)
        if structure_matches:
            print("✅ PAYLOAD STRUCTURE MATCHES N8N WORKING EXAMPLE!")
            print("✅ All required sections present:")
            print("   ✅ 'input' wrapper around main parameters")
            print("   ✅ 'config' wrapper around camera control parameters")
            print("   ✅ 'config' section with service_mode and webhook_config")
            print("   ✅ webhook_config properly nested in config section")
        else:
            print("❌ PAYLOAD STRUCTURE ISSUES FOUND:")
            for issue in issues:
                print(f"   ❌ {issue}")
        
        print()
        print("🚀 NEXT STEPS:")
        print("=" * 15)
        if structure_matches:
            print("✅ Payload structure is correct!")
            print("✅ Ready to test video generation with corrected payload")
            print("✅ This should resolve the 400/500 validation errors")
        else:
            print("❌ Fix the structure issues above before testing")
        
        return structure_matches
        
    except Exception as e:
        print(f"❌ Error testing payload structure: {e}")
        return False


if __name__ == '__main__':
    success = test_corrected_payload()
    sys.exit(0 if success else 1)
