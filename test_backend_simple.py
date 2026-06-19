#!/usr/bin/env python3
"""Test backend via exec in running container"""
import subprocess
import sys

def run_test():
    """Run test inside backend container"""
    script = '''
import requests
import json
import time
from io import BytesIO
from PIL import Image

def log(prefix, msg):
    print(f"[{prefix}] {msg}")

# Test 1: Health
resp = requests.get("http://localhost:5000/api/health")
log("✓", f"Health check: {resp.status_code}")

# Test 2: Register
username = f"user_{int(time.time())}"
resp = requests.post("http://localhost:5000/api/users", json={
    "username": username,
    "email": f"{username}@test.local",
    "password": "TestPass123456"
})
if resp.status_code == 201:
    user_id = resp.json()["user"]["id"]
    log("✓", f"User registered: {username} (ID: {user_id})")
else:
    log("✗", f"Registration failed: {resp.status_code} - {resp.text}")
    exit(1)

# Test 3: Login
resp = requests.post("http://localhost:5000/api/auth/login", json={
    "username": username,
    "password": "TestPass123456"
})
if resp.status_code == 200:
    token = resp.json()["token"]
    log("✓", f"Login successful")
else:
    log("✗", f"Login failed: {resp.status_code}")
    exit(1)

# Test 4: Upload image
img = Image.new("RGB", (200, 200), color="red")
buf = BytesIO()
img.save(buf, format="PNG")
buf.seek(0)

files = {"image": ("test.png", buf, "image/png")}
data = {
    "title": "Test Image",
    "folder": "tests",
    "tags": "test",
    "is_public": "true"
}
headers = {"Authorization": f"Bearer {token}"}

resp = requests.post("http://localhost:5000/api/paintings", files=files, data=data, headers=headers)
if resp.status_code == 201:
    painting = resp.json()["painting"]
    log("✓", f"Image uploaded: {painting['title']}")
    log("ℹ", f"  Filename: {painting['filename']}")
    log("ℹ", f"  Thumbnail: {painting['thumbnail']}")
else:
    log("✗", f"Upload failed: {resp.status_code} - {resp.text}")
    exit(1)

# Test 5: List paintings
resp = requests.get(f"http://localhost:5000/api/paintings?user_id={user_id}", headers=headers)
if resp.status_code == 200:
    data = resp.json()
    log("✓", f"Gallery fetch: {data['total']} painting(s)")
else:
    log("✗", f"Failed to fetch gallery: {resp.status_code}")
    exit(1)

# Test 6: Check database
from app import create_app
from app.models import User, Painting
app = create_app()
with app.app_context():
    user_count = User.query.count()
    painting_count = Painting.query.count()
    log("✓", f"Database: {user_count} users, {painting_count} paintings")

log("✓", "All tests passed!")
'''
    
    cmd = f"docker exec canvas3t_api python3 -c '{script}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)
    return result.returncode

if __name__ == "__main__":
    exit(run_test())
