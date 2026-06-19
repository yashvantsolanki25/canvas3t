from io import BytesIO

import requests
from PIL import Image


def _fake_image(color="red"):
    img = Image.new("RGB", (32, 32), color=color)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"


def test_user_and_painting_flow(client):
    resp = client.post(
        "/api/users",
        json={"username": "alice", "email": "a@example.com", "password": "secret123"},
    )
    assert resp.status_code == 201
    user_id = resp.json["id"]

    login = client.post("/api/auth/login", json={"username": "alice", "password": "secret123"})
    assert login.status_code == 200

    img_buffer = _fake_image()
    data = {
        "user_id": str(user_id),
        "title": "Test Painting",
        "tags": "test, sample",
        "folder": "Drafts",
        "tools_used": "brush",
        "format": "webp",
    }
    response = client.post(
        "/api/paintings",
        data={**data, "image": (img_buffer, "test.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    painting_id = response.json["id"]
    assert response.json["format"] == "WEBP"

    get_resp = client.get(f"/api/paintings/{painting_id}")
    assert get_resp.status_code == 200
    assert get_resp.json["title"] == "Test Painting"
    assert get_resp.json["format"] == "WEBP"


def test_import_url_endpoint(client, monkeypatch):
    class FakeResponse:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            return None

    def fake_get(_url, timeout=15):
        buffer = _fake_image(color="blue")
        return FakeResponse(buffer.getvalue())

    monkeypatch.setattr(requests, "get", fake_get)

    resp = client.post(
        "/api/paintings/import-url",
        json={"image_url": "http://example.com/img.png", "format": "jpeg"},
    )
    assert resp.status_code == 200
    body = resp.json
    assert body["format"] == "JPEG"
    assert body["data_url"].startswith("data:image/jpeg;base64,")


def test_import_and_save_endpoint(client, monkeypatch):
    class FakeResponse:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            return None

    def fake_get(_url, timeout=15):
        buffer = _fake_image(color="green")
        return FakeResponse(buffer.getvalue())

    monkeypatch.setattr(requests, "get", fake_get)

    # create a user to own the imported painting
    resp = client.post(
        "/api/users",
        json={"username": "importer", "email": "i@example.com", "password": "importpass"},
    )
    assert resp.status_code == 201
    user_id = resp.json["id"]

    resp = client.post(
        "/api/paintings/import-url/save",
        json={"image_url": "http://example.com/img.png", "format": "jpeg", "user_id": user_id, "title": "Imported"},
    )
    assert resp.status_code == 201
    body = resp.json
    assert body["format"] == "JPEG"
    # verify painting can be fetched and image served
    painting_id = body["id"]
    get_resp = client.get(f"/api/paintings/{painting_id}")
    assert get_resp.status_code == 200
    image_url = body["image_url"]
    from urllib.parse import urlparse

    path = urlparse(image_url).path
    media_resp = client.get(path)
    assert media_resp.status_code == 200
