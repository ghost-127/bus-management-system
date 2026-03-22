// ── LIVE CLOCK ──────────────────────────────────────────────────
const clockEl = document.getElementById('topbarTime');
function updateClock() {
    if (!clockEl) return;
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
setInterval(updateClock, 1000); updateClock();

// ── SIDEBAR TOGGLE ───────────────────────────────────────────────
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');
const sidebarToggle = document.getElementById('sidebarToggle');
if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('collapsed');
    });
}

// ── TOAST NOTIFICATIONS ─────────────────────────────────────────
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || '✅'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.style.animation = 'toastIn 0.3s ease reverse', 2700);
    setTimeout(() => toast.remove(), 3000);
}

// ── MODAL HELPERS ────────────────────────────────────────────────
function openModal(id) {
    const m = document.getElementById(id);
    m.style.display = 'flex'; m.classList.add('show');
}
function closeModal(id) {
    const m = document.getElementById(id);
    m.classList.remove('show');
    setTimeout(() => { m.style.display = 'none'; }, 200);
}
// Close modal on backdrop click
document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-backdrop')) {
        e.target.classList.remove('show');
        setTimeout(() => { e.target.style.display = 'none'; }, 200);
    }
});

// ── SEARCH FILTER ────────────────────────────────────────────────
function filterTable(inputId, tableBodyId) {
    const query = document.getElementById(inputId).value.toLowerCase();
    const rows = document.querySelectorAll(`#${tableBodyId} tr`);
    rows.forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
}

// ── API HELPERS ──────────────────────────────────────────────────
async function apiGet(url) {
    const separator = url.includes('?') ? '&' : '?';
    const res = await fetch(url + separator + '_t=' + Date.now(), { cache: 'no-store' });
    if (!res.ok) throw new Error('Request failed');
    return res.json();
}
async function apiPost(url, data) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return { ok: res.ok, data: await res.json() };
}
async function apiPut(url, data) {
    const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return { ok: res.ok, data: await res.json() };
}
async function apiDelete(url) {
    const res = await fetch(url, { method: 'DELETE' });
    return { ok: res.ok, data: await res.json() };
}

// ── CONFIRM DELETE ───────────────────────────────────────────────
function confirmDelete(message, onConfirm) {
    if (confirm(message || 'Are you sure you want to delete this item?')) {
        onConfirm();
    }
}

// ── BADGE HELPERS ────────────────────────────────────────────────
function statusBadge(status) {
    const map = { active: 'badge-success', inactive: 'badge-danger', 'on-route': 'badge-blue' };
    return `<span class="badge ${map[status] || 'badge-blue'}">${status}</span>`;
}
function roleBadge(role) {
    return `<span class="badge badge-${role}">${role.charAt(0).toUpperCase() + role.slice(1)}</span>`;
}
