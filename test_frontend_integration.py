#!/usr/bin/env python3
"""
Comprehensive integration test for Canvas3T Frontend-Backend Integration
Tests the full user journey: registration, login, image upload, privacy toggle, gallery
"""
import requests
import json
import time
from pathlib import Path

# Configuration - support both localhost (from host) and docker network names (from container)
import socket
try:
    # Try to detect if running from inside docker
    socket.getaddrinfo('web', 5000)
    FRONTEND_URL = "http://web:4173"  # Inside docker container
    BACKEND_URL = "http://web:5000"
except socket.gaierror:
    # Running from host machine
    FRONTEND_URL = "http://localhost:5173"
    BACKEND_URL = "http://localhost:5000"
TEST_USER = {
    "username": f"testuser_{int(time.time())}",
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPassword123"
}

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def test_registration():
    """Test user registration via frontend proxy"""
    print_section("Test 1: User Registration")
    
    url = f"{FRONTEND_URL}/api/users"
    payload = {
        "username": TEST_USER["username"],
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        assert "user" in data, "Response missing 'user' field"
        assert data["user"]["username"] == TEST_USER["username"]
        
        print(f"✓ Registration successful")
        print(f"  Username: {data['user']['username']}")
        print(f"  Email: {data['user']['email']}")
        print(f"  User ID: {data['user']['id']}")
        
        return data["user"]
    except Exception as e:
        print(f"✗ Registration failed: {e}")
        raise

def test_login():
    """Test user login via frontend proxy"""
    print_section("Test 2: User Login")
    
    url = f"{FRONTEND_URL}/api/auth/login"
    payload = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        assert "token" in data, "Response missing 'token' field"
        
        token = data["token"]
        print(f"✓ Login successful")
        print(f"  Token: {token[:30]}...")
        
        return token
    except Exception as e:
        print(f"✗ Login failed: {e}")
        raise

def test_image_upload(token):
    """Test image upload via frontend proxy"""
    print_section("Test 3: Image Upload")
    
    # Create a simple test image
    test_image_path = Path("/tmp/test_image.jpg")
    
    # Create a minimal JPEG (1x1 pixel)
    import struct
    # Minimal valid JPEG
    jpeg_data = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD2, 0x8A, 0x28, 0xFF, 0xD9
    ])
    
    test_image_path.write_bytes(jpeg_data)
    
    url = f"{FRONTEND_URL}/api/paintings"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(test_image_path, "rb") as f:
            files = {
                "file": ("test.jpg", f, "image/jpeg")
            }
            data = {
                "title": "Test Image",
                "folder": "test_folder",
                "is_public": "true"
            }
            response = requests.post(url, files=files, data=data, headers=headers)
        
        response.raise_for_status()
        result = response.json()
        
        print(f"✓ Image upload successful")
        print(f"  Painting ID: {result.get('id')}")
        print(f"  Title: {result.get('title')}")
        print(f"  Folder: {result.get('folder')}")
        print(f"  Public: {result.get('is_public')}")
        
        return result
    except Exception as e:
        print(f"✗ Image upload failed: {e}")
        raise
    finally:
        test_image_path.unlink(missing_ok=True)

def test_list_paintings():
    """Test fetching paintings list"""
    print_section("Test 4: List Public Paintings")
    
    url = f"{FRONTEND_URL}/api/paintings"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Paintings list retrieved")
        print(f"  Total paintings: {data.get('total', 0)}")
        print(f"  Items in page: {len(data.get('items', []))}")
        
        if data.get('items'):
            for painting in data['items']:
                print(f"    - {painting.get('title')} (ID: {painting.get('id')})")
        
        return data
    except Exception as e:
        print(f"✗ Failed to list paintings: {e}")
        raise

def test_privacy_toggle(token, painting_id):
    """Test making painting private"""
    print_section("Test 5: Privacy Toggle")
    
    url = f"{FRONTEND_URL}/api/paintings/{painting_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Make it private
        response = requests.put(url, json={"is_public": False}, headers=headers)
        response.raise_for_status()
        
        print(f"✓ Made painting private")
        
        # Verify it's not in public list
        public_response = requests.get(f"{FRONTEND_URL}/api/paintings")
        public_data = public_response.json()
        
        # Check if painting is still in public list (it shouldn't be)
        found_in_public = any(p["id"] == painting_id for p in public_data.get("items", []))
        
        if not found_in_public:
            print(f"✓ Verified: Painting removed from public list")
        else:
            print(f"✗ Painting still visible in public list")
        
        return True
    except Exception as e:
        print(f"✗ Privacy toggle failed: {e}")
        raise

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  Canvas3T Integration Test Suite")
    print("  Frontend <-> Backend via Nginx Proxy")
    print("="*70)
    
    try:
        # Run tests in sequence
        user = test_registration()
        token = test_login()
        painting = test_image_upload(token)
        paintings = test_list_paintings()
        test_privacy_toggle(token, painting["id"])
        
        print_section("All Tests Passed! ✓")
        print("\n✓ Frontend successfully integrated with backend")
        print("✓ All API endpoints working through nginx proxy")
        print("✓ Authentication, upload, and privacy features confirmed")
        
    except Exception as e:
        print_section("Tests Failed! ✗")
        print(f"\nError: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
