from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200


def test_multi_format_upload():
    files = {"file": ("id_card.png", b"x" * 2048, "image/png")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 200
    assert res.json()["filename"] == "id_card.png"