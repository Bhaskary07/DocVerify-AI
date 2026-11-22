import hashlib
import io
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel
from pypdf import PdfReader

app = FastAPI(title="DocVerify AI API", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

USERS_DB = {
    "admin@docverify.ai": {
        "email": "admin@docverify.ai",
        "password_hash": hashlib.sha256(b"admin123").hexdigest(),
        "role": "Admin",
    },
    "reviewer@docverify.ai": {
        "email": "reviewer@docverify.ai",
        "password_hash": hashlib.sha256(b"review123").hexdigest(),
        "role": "Reviewer",
    },
    "applicant@docverify.ai": {
        "email": "applicant@docverify.ai",
        "password_hash": hashlib.sha256(b"apply123").hexdigest(),
        "role": "Applicant",
    },
}
DOCUMENTS_DB = {}


class UserAuth(BaseModel):
    email: str
    password: str
    role: Optional[str] = "Applicant"


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "docverify-backend"}


@app.post("/api/auth/register")
def register_user(user: UserAuth):
    if user.email in USERS_DB:
        raise HTTPException(status_code=400, detail="Email already registered.")
    if user.role not in ["Applicant", "Reviewer", "Admin"]:
        raise HTTPException(status_code=400, detail="Invalid role.")
    USERS_DB[user.email] = {
        "email": user.email,
        "password_hash": hashlib.sha256(user.password.encode()).hexdigest(),
        "role": user.role,
    }
    return {"message": "User registered successfully", "email": user.email, "role": user.role}


@app.post("/api/auth/login")
def login_user(user: UserAuth):
    record = USERS_DB.get(user.email)
    if not record or record["password_hash"] != hashlib.sha256(user.password.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"email": record["email"], "role": record["role"], "token": f"session-{uuid.uuid4()}"}


@app.post("/api/documents/upload")
async def upload_document(
    applicant_email: str = Form("applicant@docverify.ai"),
    doc_type: str = Form("Passport"),
    file: UploadFile = File(...),
):
    allowed_ext = {".pdf", ".jpg", ".jpeg", ".png"}
    filename = file.filename or "upload.bin"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: PDF, JPG, PNG.")

    content = await file.read()
    size_bytes = len(content)

    if size_bytes < 1024:
        raise HTTPException(status_code=400, detail="File corrupted or too small (<1KB).")
    if size_bytes > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 25MB limit.")

    extracted_text = ""
    legibility_status = "Readable (High Quality)"
    confidence = 0.96

    if ext == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise HTTPException(status_code=400, detail="Password-protected PDFs are rejected.")
            for page in reader.pages:
                extracted_text += (page.extract_text() or "") + "\n"
            if not extracted_text.strip():
                extracted_text = "[Scanned PDF detected — needs visual check]"
                legibility_status = "Low Text Density - Needs Visual Check"
                confidence = 0.72
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Corrupted PDF file.")
    else:
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()
            img_info = Image.open(io.BytesIO(content))
            width, height = img_info.size
            if width < 300 or height < 300:
                legibility_status = f"Blurry / Low Resolution ({width}x{height}px). Re-upload >= 300x300px."
                confidence = 0.55
            extracted_text = f"Image ({width}x{height}px, {img_info.format})"
        except Exception:
            raise HTTPException(status_code=400, detail="Corrupted image file.")

    doc_id = str(uuid.uuid4())[:8]
    saved_name = f"{doc_id}_{filename}"
    with open(os.path.join(UPLOAD_DIR, saved_name), "wb") as f:
        f.write(content)

    record = {
        "id": doc_id,
        "applicant_email": applicant_email,
        "doc_type": doc_type,
        "filename": filename,
        "file_url": f"/files/{saved_name}",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "status": "Pending Review",
        "legibility": legibility_status,
        "confidence": confidence,
        "extracted_fields": {
            "candidate_name": applicant_email.split("@")[0].replace(".", " ").title(),
            "document_number": f"DOC-{doc_id.upper()}",
            "raw_snippet": extracted_text[:300].strip() or "No embedded text extracted",
        },
        "reviewer_note": "",
    }
    DOCUMENTS_DB[doc_id] = record
    return record


@app.get("/api/documents")
def list_documents(applicant_email: Optional[str] = None):
    docs = list(DOCUMENTS_DB.values())
    if applicant_email:
        docs = [d for d in docs if d["applicant_email"] == applicant_email]
    return docs
