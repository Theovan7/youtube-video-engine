#!/usr/bin/env python3
"""Check segment details in Airtable to see if markup is being applied."""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
airtable_api_key = os.getenv('AIRTABLE_API_KEY')
airtable_base_id = os.getenv('AIRTABLE_BASE_ID')

headers = {
    'Authorization': f'Bearer {airtable_api_key}',
    'Content-Type': 'application/json'
}

# Get the most recent segments
print("Fetching recent segments from Airtable...")
response = requests.get(
    f'https://api.airtable.com/v0/{airtable_base_id}/Segments',
    headers=headers,
    params={
        'maxRecords': 20,
        'filterByFormula': "SEARCH('test script', {SRT Text}) > 0"
    }
)

if response.status_code == 200:
    segments = response.json()['records']
    print(f"Found {len(segments)} recent segments\n")
    
    for i, segment in enumerate(segments):
        fields = segment['fields']
        print(f"Segment {i+1} (ID: {segment['id']}):")
        print(f"  SRT Text: {fields.get('SRT Text', 'N/A')}")
        print(f"  Original SRT Text: {fields.get('Original SRT Text', 'N/A')}")
        print(f"  Created: {fields.get('Created', 'N/A')}")
        print(f"  Are they different? {fields.get('SRT Text') != fields.get('Original SRT Text')}")
        print()
else:
    print(f"Failed to fetch segments: {response.status_code}")
    print(response.text)