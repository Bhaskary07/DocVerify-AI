import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="DocVerify AI API", version="0.1.0")

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
        "status": "Uploaded",
    }
    DOCUMENTS_DB[doc_id] = record
    return record


@app.get("/api/documents")
def list_documents(applicant_email: Optional[str] = None):
    docs = list(DOCUMENTS_DB.values())
    if applicant_email:
        docs = [d for d in docs if d["applicant_email"] == applicant_email]
    return docs