#!/usr/bin/env python
"""Test persistence after restart."""
import requests

print("=== Checking images after docker compose down/up ===\n")

# Check user's images
r = requests.get('http://localhost:5000/api/paintings?user_id=2')
count = r.json()['count']
print(f"Images for user_id=2: {count}")

if count > 0:
    print("\nImage details:")
    for img in r.json()['paintings']:
        print(f"  - {img['title']} (prefix: {img['prefix']})")
        print(f"    Path: {img['filename']}")
        print(f"    Public: {img['is_public']}\n")

print(f"\n✅ SUCCESS! Images persisted after container restart" if count > 0 else "\n❌ FAILED! Images lost")
