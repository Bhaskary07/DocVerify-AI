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
