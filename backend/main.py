import os
import io
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
from PIL import Image

app = FastAPI(title="DocVerify AI API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

DOCUMENTS_DB = {}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "docverify-backend"}


@app.post("/api/documents/upload")
async def upload_document(
    applicant_email: str = Form("applicant@docverify.ai"),
    doc_type: str = Form("Passport"),
    file: UploadFile = File(...)
):
    allowed_ext = {".pdf", ".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: PDF, JPG, PNG.")

    content = await file.read()
    size_bytes = len(content)

    if size_bytes < 1024:
        raise HTTPException(status_code=400, detail="File corrupted or too small (<1KB).")
    if size_bytes > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 25MB limit.")

    if ext == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise HTTPException(status_code=400, detail="Password-protected PDFs are rejected.")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Corrupted PDF file.")
    else:
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Corrupted image file.")

    doc_id = str(uuid.uuid4())[:8]
    saved_name = f"{doc_id}_{file.filename}"
    with open(os.path.join(UPLOAD_DIR, saved_name), "wb") as f:
        f.write(content)

    record = {
        "id": doc_id,
        "applicant_email": applicant_email,
        "doc_type": doc_type,
        "filename": file.filename,
        "file_url": f"/files/{saved_name}",
        "uploaded_at": datetime.utcnow().isoformat(),
        "status": "Health Check Passed",
    }
    DOCUMENTS_DB[doc_id] = record
    return record


@app.get("/api/documents")
def list_documents(applicant_email: Optional[str] = None):
    docs = list(DOCUMENTS_DB.values())
    if applicant_email:
        docs = [d for d in docs if d["applicant_email"] == applicant_email]
    return docs
