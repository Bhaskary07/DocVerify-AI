const API_BASE = "http://localhost:8000";
let currentUser = null;
let selectedDocId = null;

function updateAuthUI() {
  document.getElementById("auth-section").classList.add("hidden");
  document.getElementById("applicant-section").classList.add("hidden");
  document.getElementById("reviewer-section").classList.add("hidden");
  document.getElementById("admin-section").classList.add("hidden");

  if (!currentUser) {
    document.getElementById("auth-section").classList.remove("hidden");
    return;
  }
  if (currentUser.role === "Reviewer") {
    document.getElementById("reviewer-section").classList.remove("hidden");
    document.getElementById("reviewer-bar").innerText = `Reviewer: ${currentUser.email}`;
    loadReviewerQueue();
  } else if (currentUser.role === "Admin") {
    document.getElementById("admin-section").classList.remove("hidden");
    document.getElementById("admin-bar").innerText = `Admin: ${currentUser.email}`;
    loadAdminUsers();
  } else {
    document.getElementById("applicant-section").classList.remove("hidden");
    document.getElementById("applicant-bar").innerText = `Applicant: ${currentUser.email}`;
    loadApplicantDocs();
  }
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
  selectedDocId = null;
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
  const pct = Math.round((data.confidence || 0) * 100);
  msgEl.innerText = `Uploaded — Legibility: ${data.legibility} (${pct}% confidence)`;
  loadApplicantDocs();
}

async function loadApplicantDocs() {
  const res = await fetch(`${API_BASE}/api/documents?applicant_email=${encodeURIComponent(currentUser.email)}`);
  const docs = await res.json();
  document.getElementById("applicant-docs").innerHTML = docs.map(d => {
    const f = d.extracted_fields || {};
    return `<div class="doc-item">
      <div><strong>${d.doc_type}</strong> — ${d.filename} (${d.status})<br/>
      <small>Legibility: ${d.legibility} | Name: ${f.candidate_name || "-"} | Note: ${d.reviewer_note || "None"}</small></div>
    </div>`;
  }).join("") || "<p>No documents yet.</p>";
}

async function loadReviewerQueue() {
  const res = await fetch(`${API_BASE}/api/documents`);
  const docs = await res.json();
  document.getElementById("reviewer-queue").innerHTML = docs.map(d => {
    const encoded = encodeURIComponent(JSON.stringify(d));
    return `<div class="doc-item">
      <div><strong>[${d.id}] ${d.doc_type}</strong> — ${d.applicant_email} (${d.status})</div>
      <button onclick="openWorkspace('${encoded}')">Open Split-Screen</button>
    </div>`;
  }).join("") || "<p>No documents in queue.</p>";
}

function openWorkspace(encoded) {
  const doc = JSON.parse(decodeURIComponent(encoded));
  selectedDocId = doc.id;
  document.getElementById("split-workspace").classList.remove("hidden");
  document.getElementById("doc-preview").src = `${API_BASE}${doc.file_url}`;
  const pct = Math.round((doc.confidence || 0) * 100);
  document.getElementById("legibility-banner").innerText = `${doc.legibility} (${pct}%)`;
  document.getElementById("edit-name").value = doc.extracted_fields.candidate_name || "";
  document.getElementById("edit-docnum").value = doc.extracted_fields.document_number || "";
  document.getElementById("edit-note").value = doc.reviewer_note || "";
}

async function submitReview(status) {
  if (!selectedDocId) return;
  await fetch(`${API_BASE}/api/documents/${selectedDocId}/review`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      status,
      edited_name: document.getElementById("edit-name").value,
      edited_doc_number: document.getElementById("edit-docnum").value,
      reviewer_note: document.getElementById("edit-note").value
    })
  });
  loadReviewerQueue();
}

async function loadAdminUsers() {
  const res = await fetch(`${API_BASE}/api/admin/users`);
  const users = await res.json();
  document.getElementById("admin-users").innerHTML = users.map(u => `
    <tr>
      <td>${u.email}</td>
      <td>${u.role}</td>
      <td>
        <button onclick="changeRole('${u.email}', 'Reviewer')">Make Reviewer</button>
        <button onclick="changeRole('${u.email}', 'Applicant')">Make Applicant</button>
      </td>
    </tr>
  `).join("");
}

async function changeRole(email, role) {
  await fetch(`${API_BASE}/api/admin/users/${encodeURIComponent(email)}/role`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role })
  });
  loadAdminUsers();
}
