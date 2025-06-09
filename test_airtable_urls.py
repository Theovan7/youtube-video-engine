#!/usr/bin/env python3
"""
Test if Airtable URLs are accessible.
"""

import requests

def test_url_accessibility():
    """Test if we can access the Airtable URLs."""
    print("Testing Airtable URL Accessibility...")
    print("=" * 80)
    
    # URLs from the test
    urls = {
        "video": "https://v5.airtableusercontent.com/v3/u/41/41/1749398400000/-f4YcRHa6iHJmP-_PkCSkQ/OAtX8gyW4l4VGW9W1lgVnWHxKDLSa88S-Eoo1agyh2pBDMNs-l-9TNY2NpcDyaiQHUh86QNSXsTkKgvvTuVlTJIPGWGDys8Oj9qb4giZF56NDjhgxjIot1zEcltc1NFT-RRFHUEIDIvYZxAkYl4Hog/iuYJtS_mE1zOXqrXNPw0Nyn14Q0LXqzD9yZh99uB9Ek",
        "voiceover": "https://v5.airtableusercontent.com/v3/u/41/41/1749398400000/rdbEEy0w1C4iRVjEsItKAQ/JhSw-6dc33cKhYTlvwDRDCGmdhUlFFmKkDfleORwjTqaMu1LKSKhajxmciMzduORfAtGViHPMMVazhqMh9PrIPBfpBcQlahOTTFEMMGHPs9JOJanSDtCuFXO0Lga8ZMU24_oylygfIMmdyX4atNztA/Tc1r2rmJ4EjatpImvZv9wAIR_JMEDBvcfo1oXdUhpIs"
    }
    
    for file_type, url in urls.items():
        print(f"\nTesting {file_type} URL...")
        print(f"URL length: {len(url)} characters")
        
        try:
            # Try HEAD request first (faster)
            response = requests.head(url, timeout=10, allow_redirects=True)
            print(f"  HEAD Status: {response.status_code}")
            
            if response.status_code == 200:
                # Get content info
                content_type = response.headers.get('Content-Type', 'Unknown')
                content_length = response.headers.get('Content-Length', 'Unknown')
                print(f"  Content-Type: {content_type}")
                print(f"  Content-Length: {content_length}")
                print(f"  ✓ URL is accessible")
            else:
                print(f"  ✗ URL returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  ✗ Request timed out")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error: {e}")
    
    # Check URL expiration
    print("\n\nURL Analysis:")
    print("-" * 40)
    print("These Airtable URLs contain timestamps:")
    print("- The number '1749398400000' is a Unix timestamp")
    import datetime
    timestamp_ms = 1749398400000
    timestamp_s = timestamp_ms / 1000
    expiry_date = datetime.datetime.fromtimestamp(timestamp_s)
    print(f"- Expiry date: {expiry_date}")
    print(f"- Current date: {datetime.datetime.now()}")
    
    if datetime.datetime.now() > expiry_date:
        print("  ⚠️  URLs have EXPIRED!")
    else:
        time_left = expiry_date - datetime.datetime.now()
        print(f"  ✓ URLs valid for: {time_left}")

if __name__ == "__main__":
    test_url_accessibility()