#!/usr/bin/env python3
"""Test OpenAI service directly to check if it's working."""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Set environment to production to match deployed settings
os.environ['FLASK_ENV'] = 'production'

from services.openai_service import OpenAIService

# Test OpenAI service initialization
print("Testing OpenAI service initialization...")
try:
    openai_service = OpenAIService()
    print(f"✅ OpenAI service initialized successfully")
    print(f"   Client initialized: {openai_service.client is not None}")
    print(f"   API Key present: {openai_service.api_key is not None}")
    
    if openai_service.client:
        # Test markup generation
        print("\nTesting markup generation...")
        result = openai_service.generate_elevenlabs_markup(
            target_segment="This is a test segment with some emotion!",
            previous_segment="This was the previous segment.",
            following_segment="This will be the next segment."
        )
        print(f"✅ Markup generated successfully:")
        print(f"   Original: This is a test segment with some emotion!")
        print(f"   Marked up: {result}")
    else:
        print("❌ OpenAI client not initialized - check API key")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()