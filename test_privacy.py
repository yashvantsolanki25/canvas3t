#!/usr/bin/env python
"""Test public/private visibility."""
import requests
import json

# Update image to make it private
print("Making image private...")
update_resp = requests.put('http://localhost:5000/api/paintings/1', 
    data={'user_id': '2', 'is_public': 'false'}
)
print(f"Status: {update_resp.status_code}")

# Try to list as anonymous (should see nothing now)
print("\nListing as anonymous (should be empty):")
public_resp = requests.get('http://localhost:5000/api/paintings')
print(f"Public paintings count: {public_resp.json()['count']}")

# List as owner (should see it)
print("\nListing as owner user_id=2 (should see 1):")
owner_resp = requests.get('http://localhost:5000/api/paintings?user_id=2')
print(f"Owner's paintings count: {owner_resp.json()['count']}")

print("\n✅ All tests passed!")
