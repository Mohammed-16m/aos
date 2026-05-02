const API_URL = "http://localhost:8081/auth";
const FRONTEND_URL = "http://localhost:3000";
const RESERVATION_URL = "http://localhost:8083";
// ── TOKEN REFRESH ──
async function refreshAccessToken() {
    const refresh = localStorage.getItem("refresh");
    if (!refresh) return false;

    try {
        const res = await fetch(`${API_URL}/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh })
        });

        if (!res.ok) return false;

        const data = await res.json();
        localStorage.setItem("access", data.access);
        return true;
    } catch {
        return false;
    }
}

// ── authFetch: auto-retry with refresh on 401 ──
async function authFetch(url, options = {}) {
    const token = localStorage.getItem("access");
    if (!options.headers) options.headers = {};
    options.headers["Authorization"] = "Bearer " + token;
    if (!options.headers["Content-Type"] && options.body) {
        options.headers["Content-Type"] = "application/json";
    }

    let res = await fetch(url, options);

    // If 401, try to refresh the token once
    if (res.status === 401) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            // Retry original request with new token
            options.headers["Authorization"] = "Bearer " + localStorage.getItem("access");
            res = await fetch(url, options);
        } else {
            // Refresh also failed → log out
            localStorage.clear();
            window.location.href = "login.html";
            return;
        }
    }

    return res;
}

// ── checkAuth: validates token with server, not just existence ──
async function checkAuth() {
    const token = localStorage.getItem("access");
    if (!token) {
        window.location.href = "login.html";
        return;
    }

    try {
        const res = await authFetch(`${API_URL}/validate`);
        if (!res || !res.ok) {
            localStorage.clear();
            window.location.href = "login.html";
        }
    } catch {
        localStorage.clear();
        window.location.href = "login.html";
    }
}

// ── REGISTER ──
function register() {
    const first_name = document.getElementById("first_name").value.trim();
    const last_name  = document.getElementById("last_name").value.trim();
    const email      = document.getElementById("email").value.trim();
    const password   = document.getElementById("password").value.trim();

    if (!first_name || !last_name || !email || !password) {
        document.getElementById("message").innerText = "All fields are required";
        return;
    }

    fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ first_name, last_name, email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            localStorage.setItem("access", data.data.access);
            localStorage.setItem("refresh", data.data.refresh);
            localStorage.setItem("role", data.data.role);
            localStorage.setItem("user_id", data.data.user_id);

            // Redirection selon le rôle
            if (data.data.role === "ADMIN") {
                window.location.href = "http://localhost:3000/admin_table.html";
            } else {
                window.location.href = "http://localhost:3000/index.html";
            }
    })
    .catch(() => {
        document.getElementById("message").innerText = "Connection error";
    });
}

// ── LOGIN ──
function login() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
        document.getElementById("message").innerText = "All fields are required";
        return;
    }

    fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            localStorage.setItem("access", data.data.access);
            localStorage.setItem("refresh", data.data.refresh);
            if (data.data.role === "ADMIN") {
              window.location.href = RESERVATION_URL + "/dashboard-admin.html";
            } else {
                     window.location.href = "dashboard.html";
                   }
        } else {
            document.getElementById("message").innerText = data.message || "Login failed";
        }
    })
    .catch(() => {
        document.getElementById("message").innerText = "Connection error";
    });
}

// ── LOGOUT ──
function logout() {
    const refresh = localStorage.getItem("refresh");
    authFetch(`${API_URL}/logout`, {
        method: "POST",
        body: JSON.stringify({ refresh })
    }).finally(() => {
        localStorage.clear();
        window.location.href = "login.html";
    });
}

// ── GET USER INFO (for dashboard) ──
function getUser() {
    authFetch(`${API_URL}/me`)
        .then(res => res.json())
        .then(data => {
            if (data.status !== "success") return;
            const u = data.data;

            const fullName = (u.first_name && u.last_name)
                ? `${u.first_name} ${u.last_name}`
                : u.username;

            // Welcome banner
            document.getElementById('welcomeName').textContent = u.first_name || u.email;

            // Sidebar avatar
            document.getElementById('avatarInitial').textContent = (u.first_name || u.username)[0].toUpperCase();
            document.getElementById('sidebarUsername').textContent = fullName;

            // Sidebar role badge
            const roleBadge = document.getElementById('sidebarRole');
            roleBadge.textContent = u.role;
            roleBadge.className = 'role-badge ' + (u.role === 'ADMIN' ? 'admin' : 'client');
        });
}

function goToTables() {
    window.location.href = FRONTEND_URL + "/index.html";
}

function goToReservations() {
    window.location.href = RESERVATION_URL + "/dashboard_client.html";
}
// ── SIDEBAR / DROPDOWN ──
function toggleSidebar() {
    const sidebar  = document.getElementById('sidebar');
    const main     = document.getElementById('main');
    const topbar   = document.getElementById('topbar');

    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
        document.getElementById('overlay').classList.toggle('active');
    } else {
        sidebar.classList.toggle('collapsed');
        main.classList.toggle('expanded');
        topbar.classList.toggle('expanded');
    }
}

function toggleUserMenu() {
    const dropdown = document.getElementById("userDropdown");
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

// ── KEYBOARD ENTER ──
document.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        if (window.location.pathname.includes("login.html")) login();
        if (window.location.pathname.includes("register.html")) register();
    }
});

// ── AUTO-INIT on dashboard ──
if (window.location.pathname.includes("dashboard.html")) {
    checkAuth().then(() => getUser());
}

function showProfile() {
    // Pull whatever getUser() already loaded into localStorage or re-fetch
    authFetch(`${API_URL}/me`)
        .then(res => res.json())
        .then(data => {
            if (data.status !== "success") return;
            const u = data.data;

            const fullName = (u.first_name && u.last_name) ? `${u.first_name} ${u.last_name}` : u.email;
            document.getElementById('modalAvatar').textContent   = (u.first_name || u.email)[0].toUpperCase();
            document.getElementById('modalName').textContent     = fullName;
            document.getElementById('modalUsername').textContent = fullName;
            document.getElementById('modalEmail').textContent    = u.email;
            document.getElementById('modalId').textContent       = '#' + u.id;

            const badge = document.getElementById('modalRole');
            const badgeText = document.getElementById('modalRoleText');
            badge.textContent     = u.role;
            badgeText.textContent = u.role;
            badge.className = 'role-badge ' + (u.role === 'ADMIN' ? 'admin' : 'client');

            document.getElementById('profileModal').classList.add('open');
        });
}

function closeProfile() {
    document.getElementById('profileModal').classList.remove('open');
}

function closeProfileOnOverlay(event) {
    // Close only if clicking the dark overlay, not the modal itself
    if (event.target === document.getElementById('profileModal')) {
        closeProfile();
    }
}

function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2800);
}