const API_BASE = "http://localhost:8000";
let currentUser = null;

function updateAuthUI() {
  const authSec = document.getElementById("auth-section");
  const appSec = document.getElementById("applicant-section");
  if (!currentUser) {
    authSec.classList.remove("hidden");
    appSec.classList.add("hidden");
    return;
  }
  authSec.classList.add("hidden");
  appSec.classList.remove("hidden");
  document.getElementById("user-bar").innerText =
    `Signed in as ${currentUser.email} (${currentUser.role})`;
  loadApplicantDocs();
}

async function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (!res.ok) {
    document.getElementById("auth-msg").innerText = data.detail || "Login failed.";
    return;
  }
  currentUser = data;
  updateAuthUI();
}

async function register() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const role = document.getElementById("role").value;
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, role })
  });
  const data = await res.json();
  if (!res.ok) {
    document.getElementById("auth-msg").innerText = data.detail || "Registration failed.";
    return;
  }
  currentUser = { email: data.email, role: data.role };
  updateAuthUI();
}

function logout() {
  currentUser = null;
  updateAuthUI();
}

async function uploadDocument() {
  const fileInput = document.getElementById("file-input");
  const docType = document.getElementById("doc-type").value;
  const msgEl = document.getElementById("upload-msg");
  if (!fileInput.files.length) return;

  const formData = new FormData();
  formData.append("applicant_email", currentUser.email);
  formData.append("doc_type", docType);
  formData.append("file", fileInput.files[0]);

  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: "POST",
    body: formData
  });
  const data = await res.json();
  if (!res.ok) {
    msgEl.innerText = `Error: ${data.detail}`;
    return;
  }
  msgEl.innerText = `Extracted ${data.extracted_fields.candidate_name} (${data.extracted_fields.document_number})`;
  loadApplicantDocs();
}

async function loadApplicantDocs() {
  const res = await fetch(`${API_BASE}/api/documents?applicant_email=${encodeURIComponent(currentUser.email)}`);
  const docs = await res.json();
  document.getElementById("applicant-docs").innerHTML = docs.map(d => {
    const f = d.extracted_fields || {};
    return `<div class="doc-item">
      <strong>${d.doc_type}</strong> — ${d.filename} (${d.status})<br/>
      <small>Name: ${f.candidate_name || "-"} | Doc #: ${f.document_number || "-"}</small><br/>
      <small>Snippet: ${f.raw_snippet || ""}</small>
    </div>`;
  }).join("") || "<p>No documents yet.</p>";
}
