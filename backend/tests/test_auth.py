def test_login_requires_valid_credentials(client):
    client.post(
        "/api/users",
        json={"username": "bob", "email": "b@example.com", "password": "supersecret"},
    )

    ok = client.post("/api/auth/login", json={"username": "bob", "password": "supersecret"})
    assert ok.status_code == 200
    assert ok.json["user"]["username"] == "bob"

    bad = client.post("/api/auth/login", json={"username": "bob", "password": "wrong"})
    assert bad.status_code == 401
    assert bad.json["error"] == "Invalid credentials"

