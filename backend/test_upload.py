#!/usr/bin/env python
"""Test script for image upload."""
import requests
from PIL import Image
import os

# Create test image
print("Creating test image...")
img = Image.new("RGB", (100, 100), color="red")
img.save("/tmp/test_image.jpg")

# Upload image
print("Uploading image...")
with open("/tmp/test_image.jpg", "rb") as f:
    files = {"image": f}
    data = {
        "user_id": "2",
        "title": "Test Upload",
        "folder": "myimages",
        "is_public": "true",
        "description": "Test image from container"
    }
    response = requests.post("http://localhost:5000/api/paintings", files=files, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
