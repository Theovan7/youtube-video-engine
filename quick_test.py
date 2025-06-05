#!/usr/bin/env python3
"""Quick test of OpenAI gpt-image-1 API parameters"""

import os
import requests
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("❌ OPENAI_API_KEY not found")
    exit(1)

# Test minimal payload
payload = {
    'model': 'gpt-image-1',
    'prompt': 'Test image',
    'size': '1536x1024',
    'quality': 'high',
    'n': 1,
    'output_format': 'png',
    'moderation': 'auto'
}

headers = {
    'Authorization': f'Bearer {openai_api_key}',
    'Content-Type': 'application/json'
}

print("🧪 Testing gpt-image-1 API...")
print(f"📤 Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        'https://api.openai.com/v1/images/generations',
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"📥 Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS! API parameters are correct")
        print(f"📊 Generated {len(result['data'])} image(s)")
    else:
        print("❌ API Error:")
        try:
            error = response.json()
            print(json.dumps(error, indent=2))
        except:
            print(response.text)
            
except Exception as e:
    print(f"❌ Request failed: {e}")
