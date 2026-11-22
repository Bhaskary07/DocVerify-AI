const API_BASE = "http://localhost:8000";
let currentUser = null;

function updateAuthUI() {
  const authSec = document.getElementById("auth-section");
  const sessSec = document.getElementById("session-section");
  if (!currentUser) {
    authSec.classList.remove("hidden");
    sessSec.classList.add("hidden");
    return;
  }
  authSec.classList.add("hidden");
  sessSec.classList.remove("hidden");
  document.getElementById("user-bar").innerText =
    `Signed in as ${currentUser.email} (${currentUser.role})`;
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
