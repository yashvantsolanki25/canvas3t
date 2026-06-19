#!/usr/bin/env python3
"""
Complete integration test: register → login → upload → persist
"""
import requests
import json
import time
from pathlib import Path
from io import BytesIO
from PIL import Image

FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://localhost:5000"

def test_health():
    """Test backend is healthy."""
    resp = requests.get(f"{BACKEND_URL}/api/health")
    print(f"[✓] Backend health: {resp.status_code}")
    assert resp.status_code == 200

def test_register():
    """Register a new user via frontend proxy."""
    username = f"user_{int(time.time())}"
    payload = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "TestPass123"
    }
    resp = requests.post(f"{FRONTEND_URL}/api/users", json=payload)
    print(f"[{'✓' if resp.status_code == 201 else '✗'}] Register: {resp.status_code}")
    assert resp.status_code == 201
    data = resp.json()
    assert "user" in data
    return username, payload["password"], data["user"]["id"]

def test_login(username, password):
    """Login and get token."""
    payload = {"username": username, "password": password}
    resp = requests.post(f"{FRONTEND_URL}/api/auth/login", json=payload)
    print(f"[{'✓' if resp.status_code == 200 else '✗'}] Login: {resp.status_code}")
    assert resp.status_code == 200
    data = resp.json()
    token = data["token"]
    return token

def create_test_image():
    """Create a minimal test image."""
    img = Image.new("RGB", (100, 100), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf, "test_image.png"

def test_upload(token, user_id):
    """Upload an image with auth token."""
    buf, filename = create_test_image()
    
    # Prepare form data
    files = {"image": (filename, buf, "image/png")}
    data = {
        "title": "Test Upload",
        "folder": "test_folder",
        "tags": "test,canvas",
        "is_public": "true"
    }
    
    # Add Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = requests.post(
        f"{FRONTEND_URL}/api/paintings",
        files=files,
        data=data,
        headers=headers
    )
    
    print(f"[{'✓' if resp.status_code == 201 else '✗'}] Upload: {resp.status_code}")
    if resp.status_code != 201:
        print(f"  Error: {resp.text}")
    assert resp.status_code == 201
    
    painting = resp.json()["painting"]
    return painting

def test_list_public():
    """List public paintings (no auth)."""
    resp = requests.get(f"{FRONTEND_URL}/api/paintings")
    print(f"[{'✓' if resp.status_code == 200 else '✗'}] List public: {resp.status_code}")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    print(f"  Found {data['total']} public paintings")
    return data

def test_list_user_paintings(token, user_id):
    """List user's own paintings."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id": user_id}
    resp = requests.get(f"{FRONTEND_URL}/api/paintings", params=params, headers=headers)
    print(f"[{'✓' if resp.status_code == 200 else '✗'}] List user: {resp.status_code}")
    assert resp.status_code == 200
    data = resp.json()
    print(f"  User has {data['total']} paintings")
    return data

def test_image_urls(painting):
    """Verify image URLs are accessible."""
    if painting.get("image_url"):
        resp = requests.head(f"{FRONTEND_URL}{painting['image_url']}")
        print(f"[{'✓' if resp.status_code == 200 else '✗'}] Image URL: {resp.status_code}")
    
    if painting.get("thumbnail_url"):
        resp = requests.head(f"{FRONTEND_URL}{painting['thumbnail_url']}")
        print(f"[{'✓' if resp.status_code == 200 else '✗'}] Thumbnail URL: {resp.status_code}")

def main():
    print("\n" + "="*70)
    print("  Canvas3T Full Integration Test")
    print("="*70 + "\n")
    
    try:
        test_health()
        username, password, user_id = test_register()
        token = test_login(username, password)
        painting = test_upload(token, user_id)
        list_public = test_list_public()
        list_user = test_list_user_paintings(token, user_id)
        test_image_urls(painting)
        
        print("\n" + "="*70)
        print("  ✓ All tests passed!")
        print("="*70 + "\n")
        
        print(f"Registered user: {username}")
        print(f"Uploaded painting: {painting.get('title')}")
        print(f"Public paintings: {list_public['total']}")
        print(f"User paintings: {list_user['total']}")
        print(f"Image saved to: {painting.get('filename')}")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
