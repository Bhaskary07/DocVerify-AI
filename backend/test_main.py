import io

from fastapi.testclient import TestClient
from main import app
from PIL import Image

client = TestClient(app)


def _png_bytes(width: int = 400, height: int = 400) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200


def test_reject_small_file():
    files = {"file": ("tiny.pdf", b"bad", "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 400


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


def test_extracted_fields_on_upload():
    png = _png_bytes(600, 400)
    files = {"file": ("diploma.png", png, "image/png")}
    data = {"applicant_email": "jane.doe@docverify.ai", "doc_type": "Diploma"}
    res = client.post("/api/documents/upload", files=files, data=data)
    assert res.status_code == 200
    fields = res.json()["extracted_fields"]
    assert fields["candidate_name"] == "Jane Doe"
    assert fields["document_number"].startswith("DOC-")
