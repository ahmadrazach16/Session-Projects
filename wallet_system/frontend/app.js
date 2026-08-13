// ============================================================
// Ledger — frontend application logic
// Talks only to the API layer (/api/...). No business rules here;
// this file just renders state and forwards user actions.
// ============================================================

const API_BASE = "/api";

const state = {
  token: localStorage.getItem("ledger_token") || null,
  user: null,
  wallets: [],
};

// ---------------- API helper ----------------
async function api(path, { method = "GET", body, idempotencyKey } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let json;
  try {
    json = await res.json();
  } catch {
    throw new Error("Unexpected server response.");
  }

  if (!res.ok || json.success === false) {
    const message = json?.error?.message || "Something went wrong.";
    const err = new Error(message);
    err.code = json?.error?.code;
    throw err;
  }
  return json.data;
}

function uuid() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function money(n) {
  const num = Number(n || 0);
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso.replace(" ", "T") + "Z");
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.remove("hidden");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.add("hidden"), 3200);
}

// ============================================================
// Auth screen
// ============================================================
const authScreen = document.getElementById("auth-screen");
const appShell = document.getElementById("app-shell");

document.querySelectorAll(".auth-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const target = tab.dataset.tab;
    document.getElementById("login-form").classList.toggle("hidden", target !== "login");
    document.getElementById("register-form").classList.toggle("hidden", target !== "register");
  });
});

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("login-error");
  errorEl.textContent = "";
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: {
        email: document.getElementById("login-email").value,
        password: document.getElementById("login-password").value,
      },
    });
    state.token = data.token;
    state.user = data.user;
    localStorage.setItem("ledger_token", data.token);
    await bootApp();
  } catch (err) {
    errorEl.textContent = err.message;
  }
});

document.getElementById("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("register-error");
  errorEl.textContent = "";
  try {
    await api("/auth/register", {
      method: "POST",
      body: {
        name: document.getElementById("register-name").value,
        email: document.getElementById("register-email").value,
        password: document.getElementById("register-password").value,
      },
    });
    // Auto login after registering
    const data = await api("/auth/login", {
      method: "POST",
      body: {
        email: document.getElementById("register-email").value,
        password: document.getElementById("register-password").value,
      },
    });
    state.token = data.token;
    state.user = data.user;
    localStorage.setItem("ledger_token", data.token);
    await bootApp();
  } catch (err) {
    errorEl.textContent = err.message;
  }
});

document.getElementById("logout-btn").addEventListener("click", () => {
  state.token = null;
  state.user = null;
  localStorage.removeItem("ledger_token");
  appShell.classList.add("hidden");
  authScreen.classList.remove("hidden");
});

// ============================================================
// Navigation
// ============================================================
document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", () => switchView(item.dataset.view));
});
document.querySelectorAll("[data-goto]").forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.goto));
});

function switchView(view) {
  document.querySelectorAll(".nav-item").forEach((i) => i.classList.toggle("active", i.dataset.view === view));
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  document.getElementById(`view-${view}`).classList.remove("hidden");
  if (view === "history") loadHistory(1);
  if (view === "admin") loadAdminWallets();
}

// ============================================================
// App boot
// ============================================================
async function bootApp() {
  authScreen.classList.add("hidden");
  appShell.classList.remove("hidden");

  document.getElementById("user-name").textContent = state.user.name;
  document.getElementById("user-role").textContent = state.user.role;
  document.getElementById("user-avatar").textContent = state.user.name.charAt(0).toUpperCase();
  document.querySelectorAll(".admin-only").forEach((el) => el.classList.toggle("hidden", state.user.role !== "ADMIN"));

  await loadWallets();
  await loadRecentActivity();
  switchView("dashboard");
}

async function tryRestoreSession() {
  if (!state.token) return;
  try {
    state.user = await api("/auth/me");
    await bootApp();
  } catch {
    state.token = null;
    localStorage.removeItem("ledger_token");
  }
}

// ============================================================
// Wallets (dashboard)
// ============================================================
async function loadWallets() {
  state.wallets = await api("/wallet");
  renderWalletStubs();
  populateWalletSelects();
}

function renderWalletStubs() {
  const container = document.getElementById("wallet-stubs");
  if (state.wallets.length === 0) {
    container.innerHTML = `<div class="wallet-stub-empty">You don't have any wallets yet. Create one to start depositing and sending money.</div>`;
    return;
  }
  container.innerHTML = state.wallets.map((w) => {
    const [whole, cents] = money(w.balance).split(".");
    return `
    <div class="wallet-stub">
      <div class="wallet-stub-top">
        <div>
          <div class="wallet-currency">${w.currency} WALLET</div>
          <div class="wallet-id">ID #${w.id}</div>
        </div>
        <span class="wallet-status ${w.status}">${w.status}</span>
      </div>
      <div class="wallet-balance">${whole}<span class="wallet-balance-cents">.${cents}</span></div>
      <div class="wallet-stub-foot">
        <span>Opened ${fmtDate(w.created_at)}</span>
        <span>${w.currency}</span>
      </div>
    </div>`;
  }).join("");
}

function populateWalletSelects() {
  const options = state.wallets
    .filter((w) => w.status === "ACTIVE")
    .map((w) => `<option value="${w.id}">#${w.id} — ${w.currency} (${money(w.balance)})</option>`)
    .join("");
  const empty = `<option value="">No active wallets</option>`;
  ["deposit-wallet", "withdraw-wallet", "transfer-from"].forEach((id) => {
    document.getElementById(id).innerHTML = options || empty;
  });
}

document.getElementById("open-create-wallet").addEventListener("click", () => {
  openModal(`
    <h3>New wallet</h3>
    <p class="panel-sub">Choose a currency. You can only have one active wallet per currency.</p>
    <label style="margin-bottom:14px;">Currency
      <select id="new-wallet-currency">
        <option value="USD">USD — US Dollar</option>
        <option value="PKR">PKR — Pakistani Rupee</option>
        <option value="EUR">EUR — Euro</option>
        <option value="GBP">GBP — British Pound</option>
      </select>
    </label>
    <div class="form-error" id="new-wallet-error"></div>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="modal-cancel">Cancel</button>
      <button class="btn btn-primary" id="modal-confirm">Create wallet</button>
    </div>
  `);
  document.getElementById("modal-cancel").addEventListener("click", closeModal);
  document.getElementById("modal-confirm").addEventListener("click", async () => {
    const currency = document.getElementById("new-wallet-currency").value;
    const errorEl = document.getElementById("new-wallet-error");
    try {
      await api("/wallet", { method: "POST", body: { currency } });
      closeModal();
      showToast(`${currency} wallet created.`);
      await loadWallets();
    } catch (err) {
      errorEl.textContent = err.message;
    }
  });
});

// ---------------- Deposit ----------------
document.getElementById("deposit-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("deposit-error");
  errorEl.textContent = "";
  const walletId = document.getElementById("deposit-wallet").value;
  const amount = document.getElementById("deposit-amount").value;
  const note = document.getElementById("deposit-note").value;
  if (!walletId) { errorEl.textContent = "Create a wallet first."; return; }
  try {
    await api("/wallet/deposit", {
      method: "POST",
      body: { wallet_id: Number(walletId), amount: Number(amount), description: note },
      idempotencyKey: uuid(),
    });
    showToast("Deposit completed.");
    document.getElementById("deposit-form").reset();
    await loadWallets();
    await loadRecentActivity();
  } catch (err) {
    errorEl.textContent = err.message;
  }
});

// ---------------- Withdraw ----------------
document.getElementById("withdraw-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("withdraw-error");
  errorEl.textContent = "";
  const walletId = document.getElementById("withdraw-wallet").value;
  const amount = document.getElementById("withdraw-amount").value;
  const note = document.getElementById("withdraw-note").value;
  if (!walletId) { errorEl.textContent = "Create a wallet first."; return; }
  try {
    await api("/wallet/withdraw", {
      method: "POST",
      body: { wallet_id: Number(walletId), amount: Number(amount), description: note },
      idempotencyKey: uuid(),
    });
    showToast("Withdrawal completed.");
    document.getElementById("withdraw-form").reset();
    await loadWallets();
    await loadRecentActivity();
  } catch (err) {
    errorEl.textContent = err.message;
  }
});

// ---------------- Transfer ----------------
document.getElementById("transfer-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("transfer-error");
  const successEl = document.getElementById("transfer-success");
  errorEl.textContent = "";
  successEl.textContent = "";
  const fromWallet = document.getElementById("transfer-from").value;
  const toWallet = document.getElementById("transfer-to").value;
  const amount = document.getElementById("transfer-amount").value;
  const note = document.getElementById("transfer-note").value;
  if (!fromWallet) { errorEl.textContent = "Create a wallet first."; return; }
  try {
    const tx = await api("/wallet/transfer", {
      method: "POST",
      body: {
        sender_wallet_id: Number(fromWallet),
        recipient_wallet_id: Number(toWallet),
        amount: Number(amount),
        description: note,
      },
      idempotencyKey: uuid(),
    });
    successEl.textContent = `Sent. Reference ${tx.reference}.`;
    showToast("Transfer completed.");
    document.getElementById("transfer-form").reset();
    await loadWallets();
    await loadRecentActivity();
  } catch (err) {
    errorEl.textContent = err.message;
  }
});

// ============================================================
// Transaction rendering helpers
// ============================================================
function txDirectionForUser(tx) {
  const myWalletIds = new Set(state.wallets.map((w) => w.id));
  if (tx.type === "DEPOSIT") return "in";
  if (tx.type === "WITHDRAWAL") return "out";
  if (tx.type === "ADJUSTMENT") return tx.destination_wallet_id ? "in" : "out";
  if (tx.type === "TRANSFER") {
    if (myWalletIds.has(tx.destination_wallet_id) && !myWalletIds.has(tx.source_wallet_id)) return "in";
    return "out";
  }
  return "out";
}

function txIcon(tx, direction) {
  if (tx.type === "ADJUSTMENT") return { cls: "adj", glyph: "±" };
  return direction === "in" ? { cls: "in", glyph: "↓" } : { cls: "out", glyph: "↑" };
}

function renderTxRow(tx) {
  const direction = txDirectionForUser(tx);
  const icon = txIcon(tx, direction);
  const label = {
    DEPOSIT: "Deposit",
    WITHDRAWAL: "Withdrawal",
    TRANSFER: direction === "in" ? "Received transfer" : "Sent transfer",
    ADJUSTMENT: "Balance adjustment",
  }[tx.type] || tx.type;

  return `
  <div class="tx-row">
    <div class="tx-icon ${icon.cls}">${icon.glyph}</div>
    <div class="tx-main">
      <div class="tx-title">${label}${tx.description ? " · " + escapeHtml(tx.description) : ""}</div>
      <div class="tx-ref">${tx.reference} · ${fmtDate(tx.created_at)}</div>
    </div>
    <div class="tx-amount ${direction}">${direction === "in" ? "+" : "−"}${money(tx.amount)} ${tx.currency}</div>
    <div class="tx-status ${tx.status}">${tx.status}</div>
  </div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function loadRecentActivity() {
  try {
    const result = await api("/wallet/transactions?page=1&page_size=5");
    const container = document.getElementById("recent-tx");
    container.innerHTML = result.items.length
      ? result.items.map(renderTxRow).join("")
      : `<div class="tx-empty">No transactions yet. Make a deposit to get started.</div>`;
  } catch (err) {
    showToast(err.message, true);
  }
}

// ============================================================
// History / statement view
// ============================================================
let historyPage = 1;

document.getElementById("apply-filters").addEventListener("click", () => loadHistory(1));

async function loadHistory(page) {
  historyPage = page;
  const params = new URLSearchParams({
    page: String(page),
    page_size: "10",
  });
  const type = document.getElementById("filter-type").value;
  const status = document.getElementById("filter-status").value;
  const reference = document.getElementById("filter-reference").value;
  if (type) params.set("type", type);
  if (status) params.set("status", status);
  if (reference) params.set("reference", reference);

  try {
    const result = await api(`/wallet/transactions?${params.toString()}`);
    const container = document.getElementById("history-tx");
    container.innerHTML = result.items.length
      ? result.items.map(renderTxRow).join("")
      : `<div class="tx-empty">No matching transactions.</div>`;
    renderPagination(result);
  } catch (err) {
    showToast(err.message, true);
  }
}

function renderPagination(result) {
  const container = document.getElementById("history-pagination");
  if (result.total_pages <= 1) { container.innerHTML = ""; return; }
  let html = "";
  for (let p = 1; p <= result.total_pages; p++) {
    html += `<button class="btn btn-sm ${p === result.page ? "btn-primary" : "btn-ghost"}" data-page="${p}">${p}</button>`;
  }
  container.innerHTML = html;
  container.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => loadHistory(Number(btn.dataset.page)));
  });
}

// ============================================================
// Admin
// ============================================================
document.querySelectorAll(".admin-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".admin-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    document.querySelectorAll(".admin-pane").forEach((p) => p.classList.add("hidden"));
    document.getElementById(`admin-${tab.dataset.admintab}`).classList.remove("hidden");
    if (tab.dataset.admintab === "wallets") loadAdminWallets();
    if (tab.dataset.admintab === "users") loadAdminUsers();
    if (tab.dataset.admintab === "failed") loadAdminFailed();
  });
});

async function loadAdminWallets() {
  try {
    const wallets = await api("/admin/wallets?page=1&page_size=100");
    const container = document.getElementById("admin-wallets-table");
    container.innerHTML = `
      <table>
        <thead><tr><th>ID</th><th>Owner</th><th>Currency</th><th>Balance</th><th>Status</th><th></th></tr></thead>
        <tbody>
          ${wallets.map((w) => `
            <tr>
              <td>#${w.id}</td>
              <td>${escapeHtml(w.owner_name)}<br><span style="color:var(--text-low);font-size:11px;">${escapeHtml(w.owner_email)}</span></td>
              <td>${w.currency}</td>
              <td style="font-family:var(--font-mono);">${money(w.balance)}</td>
              <td><span class="badge ${w.status}">${w.status}</span></td>
              <td>
                <div class="row-actions">
                  ${w.status === "FROZEN"
                    ? `<button class="btn btn-sm btn-ghost" data-unfreeze="${w.id}">Unfreeze</button>`
                    : `<button class="btn btn-sm btn-ghost" data-freeze="${w.id}">Freeze</button>`}
                  <button class="btn btn-sm btn-ghost" data-adjust="${w.id}">Adjust</button>
                </div>
              </td>
            </tr>`).join("")}
        </tbody>
      </table>`;

    container.querySelectorAll("[data-freeze]").forEach((btn) =>
      btn.addEventListener("click", () => adminFreezeWallet(btn.dataset.freeze, true)));
    container.querySelectorAll("[data-unfreeze]").forEach((btn) =>
      btn.addEventListener("click", () => adminFreezeWallet(btn.dataset.unfreeze, false)));
    container.querySelectorAll("[data-adjust]").forEach((btn) =>
      btn.addEventListener("click", () => openAdjustModal(btn.dataset.adjust)));
  } catch (err) {
    showToast(err.message, true);
  }
}

async function adminFreezeWallet(walletId, freeze) {
  try {
    await api(`/admin/wallets/${walletId}/${freeze ? "freeze" : "unfreeze"}`, { method: "POST" });
    showToast(freeze ? "Wallet frozen." : "Wallet unfrozen.");
    await loadAdminWallets();
  } catch (err) {
    showToast(err.message, true);
  }
}

function openAdjustModal(walletId) {
  openModal(`
    <h3>Adjust balance — wallet #${walletId}</h3>
    <p class="panel-sub">Use a negative amount to deduct. Every adjustment is recorded as an auditable transaction.</p>
    <label style="margin-bottom:12px;">Amount
      <input type="number" id="adjust-amount" step="0.01" placeholder="e.g. 500 or -200">
    </label>
    <label style="margin-bottom:12px;">Reason
      <input type="text" id="adjust-reason" placeholder="e.g. Manual correction after investigation">
    </label>
    <div class="form-error" id="adjust-error"></div>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="modal-cancel">Cancel</button>
      <button class="btn btn-primary" id="modal-confirm">Apply adjustment</button>
    </div>
  `);
  document.getElementById("modal-cancel").addEventListener("click", closeModal);
  document.getElementById("modal-confirm").addEventListener("click", async () => {
    const errorEl = document.getElementById("adjust-error");
    try {
      await api(`/admin/wallets/${walletId}/adjust-balance`, {
        method: "POST",
        body: {
          amount: Number(document.getElementById("adjust-amount").value),
          reason: document.getElementById("adjust-reason").value,
        },
      });
      closeModal();
      showToast("Balance adjusted.");
      await loadAdminWallets();
    } catch (err) {
      errorEl.textContent = err.message;
    }
  });
}

async function loadAdminUsers() {
  try {
    const users = await api("/admin/users?page=1&page_size=100");
    const container = document.getElementById("admin-users-table");
    container.innerHTML = `
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th></tr></thead>
        <tbody>
          ${users.map((u) => `
            <tr>
              <td>#${u.id}</td>
              <td>${escapeHtml(u.name)}</td>
              <td>${escapeHtml(u.email)}</td>
              <td>${u.role}</td>
              <td><span class="badge ACTIVE">${u.status}</span></td>
              <td>${fmtDate(u.created_at)}</td>
            </tr>`).join("")}
        </tbody>
      </table>`;
  } catch (err) {
    showToast(err.message, true);
  }
}

async function loadAdminFailed() {
  try {
    const result = await api("/admin/transactions/failed?page=1&page_size=50");
    const container = document.getElementById("admin-failed-table");
    container.innerHTML = result.items.length
      ? `<table>
          <thead><tr><th>Reference</th><th>Type</th><th>Amount</th><th>Reason</th><th>When</th></tr></thead>
          <tbody>
            ${result.items.map((tx) => `
              <tr>
                <td style="font-family:var(--font-mono);">${tx.reference}</td>
                <td>${tx.type}</td>
                <td>${money(tx.amount)} ${tx.currency}</td>
                <td>${escapeHtml(tx.failure_reason || "—")}</td>
                <td>${fmtDate(tx.created_at)}</td>
              </tr>`).join("")}
          </tbody>
        </table>`
      : `<div class="tx-empty">No failed transactions. Everything's clean.</div>`;
  } catch (err) {
    showToast(err.message, true);
  }
}

// ============================================================
// Modal helpers
// ============================================================
function openModal(html) {
  document.getElementById("modal-content").innerHTML = html;
  document.getElementById("modal-backdrop").classList.remove("hidden");
}
function closeModal() {
  document.getElementById("modal-backdrop").classList.add("hidden");
}
document.getElementById("modal-backdrop").addEventListener("click", (e) => {
  if (e.target.id === "modal-backdrop") closeModal();
});

// ============================================================
// Boot
// ============================================================
tryRestoreSession();
