#!/usr/bin/env python3
"""
Test script to verify correct GoAPI endpoints and capabilities.
This will help us determine the right configuration and service offerings.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_goapi_endpoints():
    """Test different GoAPI endpoint configurations."""
    
    api_key = os.getenv('GOAPI_API_KEY')
    if not api_key:
        print("❌ No GOAPI_API_KEY found in environment")
        return
    
    print("🔍 Testing GoAPI Endpoint Configurations")
    print("="*60)
    
    # Test configurations
    configs = [
        {
            'name': 'Current Config (api.goapi.ai)',
            'base_url': 'https://api.goapi.ai',
            'endpoints': ['/api/v1/task', '/api/v1/generate/credit']
        },
        {
            'name': 'Corrected Config (goapi.ai)',
            'base_url': 'https://goapi.ai',
            'endpoints': ['/api/midjourney/imagine', '/api/midjourney/fetch']
        }
    ]
    
    for config in configs:
        print(f"\n📋 Testing: {config['name']}")
        print(f"   Base URL: {config['base_url']}")
        
        for endpoint in config['endpoints']:
            full_url = f"{config['base_url']}{endpoint}"
            print(f"\n🚀 Testing: {full_url}")
            
            try:
                # Test with GET first
                response = requests.get(
                    full_url,
                    headers={
                        'X-API-Key': api_key,
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                print(f"   ✅ GET Response: {response.status_code}")
                if response.status_code != 404:
                    print(f"   📄 Response: {response.text[:200]}...")
                
                # If GET fails with 405 (Method Not Allowed), try POST
                if response.status_code == 405:
                    post_response = requests.post(
                        full_url,
                        headers={
                            'X-API-Key': api_key,
                            'Authorization': f'Bearer {api_key}',
                            'Content-Type': 'application/json'
                        },
                        json={'test': True},
                        timeout=10
                    )
                    print(f"   ✅ POST Response: {post_response.status_code}")
                    if post_response.status_code != 404:
                        print(f"   📄 POST Response: {post_response.text[:200]}...")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")

def test_kling_alternatives():
    """Test alternative Kling video generation services."""
    print("\n\n🎬 Testing Alternative Kling Video Services")
    print("="*60)
    
    # Test PiAPI
    print("\n📋 Testing PiAPI Kling endpoints:")
    piapi_endpoints = [
        'https://api.piapi.ai/kling/videogen',
        'https://api.piapi.ai/kling/fetch'
    ]
    
    for endpoint in piapi_endpoints:
        print(f"🚀 Testing: {endpoint}")
        try:
            response = requests.post(
                endpoint,
                headers={'Content-Type': 'application/json'},
                json={'test': True},
                timeout=10
            )
            print(f"   ✅ Response: {response.status_code}")
            if response.status_code not in [404, 401]:
                print(f"   📄 Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_goapi_documentation():
    """Test for GoAPI documentation or help endpoints."""
    print("\n\n📚 Testing GoAPI Documentation Endpoints")
    print("="*60)
    
    doc_urls = [
        'https://goapi.ai/docs',
        'https://goapi.ai/api/docs',
        'https://doc.goapi.ai',
        'https://goapi.ai/help',
        'https://api.goapi.ai/docs'
    ]
    
    for url in doc_urls:
        print(f"🚀 Testing: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"   ✅ Response: {response.status_code}")
            if response.status_code == 200:
                print(f"   📄 Found documentation at: {url}")
                # Check if it mentions video or Kling
                content = response.text.lower()
                if 'video' in content:
                    print("   🎬 Contains 'video' references")
                if 'kling' in content:
                    print("   🎯 Contains 'kling' references")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 GoAPI Endpoint Verification Script")
    print("="*60)
    
    test_goapi_endpoints()
    test_kling_alternatives()  
    test_goapi_documentation()
    
    print("\n" + "="*60)
    print("🎯 SUMMARY:")
    print("Check the responses above to determine:")
    print("1. Which GoAPI endpoints actually exist")
    print("2. Whether GoAPI supports Kling video generation")
    print("3. Alternative services for Kling video generation")
    print("="*60)
