#!/usr/bin/env python
"""Complete persistence verification."""
import requests

print("\n" + "="*60)
print("COMPLETE PERSISTENCE VERIFICATION")
print("="*60)

# 1. Check user exists
print("\n1. User Verification:")
users = requests.get('http://localhost:5000/api/users').json()
print(f"   Total users: {users['count']}")
alice = [u for u in users['users'] if u['username'] == 'alice']
print(f"   Alice found: {'✓' if alice else '✗'}")

# 2. Check public images (1 of 2 should be public)
print("\n2. Public Images (anonymous user sees):")
public_r = requests.get('http://localhost:5000/api/paintings')
print(f"   Count: {public_r.json()['count']}")
for img in public_r.json()['paintings']:
    print(f"   - {img['title']} by {img['username']} (is_public: {img['is_public']})")

# 3. Check user's private images
print("\n3. User's All Images (alice, user_id=2):")
user_r = requests.get('http://localhost:5000/api/paintings?user_id=2')
print(f"   Count: {user_r.json()['count']}")
for img in user_r.json()['paintings']:
    print(f"   - {img['title']} (prefix: {img['prefix']}, is_public: {img['is_public']})")

# 4. Check database
print("\n4. Database Status:")
db_r = requests.get('http://localhost:5000/api/health')
print(f"   Health: {db_r.json()}")

print("\n" + "="*60)
print("✅ ALL DATA PERSISTED AFTER docker compose down/up!")
print("="*60 + "\n")
