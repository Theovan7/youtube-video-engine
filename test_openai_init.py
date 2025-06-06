#!/usr/bin/env python3
"""Test OpenAI initialization issue."""

import os
from openai import OpenAI

# Test basic initialization
print("Testing OpenAI client initialization...")

try:
    # Set a dummy API key for testing
    os.environ['OPENAI_API_KEY'] = 'sk-test-key'
    
    # Try to initialize the client
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    print("✅ OpenAI client initialized successfully")
    
except Exception as e:
    print(f"❌ Error initializing OpenAI client: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try to get more details
    import traceback
    traceback.print_exc()