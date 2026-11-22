from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200


def test_reject_small_file():
    files = {"file": ("tiny.pdf", b"bad", "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400
    assert "too small" in res.json()["detail"].lower()


def test_register_and_login():
    res = client.post(
        "/api/auth/register",
        json={
            "email": "student1@docverify.ai",
            "password": "secret123",
            "role": "Applicant",
        },
    )
    assert res.status_code == 200
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "student1@docverify.ai",
            "password": "secret123",
        },
    )
    assert login_res.status_code == 200
    assert login_res.json()["role"] == "Applicant"
