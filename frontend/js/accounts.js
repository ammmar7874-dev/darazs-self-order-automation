// Accounts Pool Manager

async function loadAccounts() {
  const tbody = document.querySelector("#accounts-table tbody");
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/api/accounts`);
    const accounts = await res.json();

    if (!accounts || accounts.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 3rem;">
            No Daraz buyer accounts in pool. Click <b>Bulk Import Accounts</b> above to add accounts.
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = accounts.map(acc => {
      let statusBadge = `<span class="badge badge-success"><i data-lucide="check-circle" style="width: 12px; height: 12px;"></i> Active</span>`;
      if (acc.status === "cooldown") {
        statusBadge = `<span class="badge badge-warning"><i data-lucide="clock" style="width: 12px; height: 12px;"></i> Quota Full (${acc.daily_orders_count}/${acc.max_daily_orders} Done)</span>`;
      } else if (acc.status === "needs_otp") {
        statusBadge = `<span class="badge badge-danger"><i data-lucide="alert-triangle" style="width: 12px; height: 12px;"></i> Needs OTP/Verify</span>`;
      }

      const lastUsed = acc.last_used_at 
        ? new Date(acc.last_used_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
        : "Never";

      return `
        <tr>
          <td style="font-family: var(--font-mono); color: var(--text-muted);">#${acc.id}</td>
          <td style="font-weight: 600;">${escapeHtml(acc.email)}</td>
          <td>
            <span style="font-family: var(--font-mono); font-weight: 700; color: ${acc.daily_orders_count >= acc.max_daily_orders ? 'var(--accent-yellow)' : 'var(--text-primary)'};">
              ${acc.daily_orders_count} / ${acc.max_daily_orders}
            </span>
          </td>
          <td style="font-family: var(--font-mono);">${acc.total_orders_placed}</td>
          <td>${statusBadge}</td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">${lastUsed}</td>
          <td>
            <div style="display: flex; gap: 0.4rem;">
              <button class="btn btn-primary btn-sm" onclick="openAccountBrowser(${acc.id})" title="Open visual Chrome window">
                <i data-lucide="external-link" style="width: 13px; height: 13px;"></i> Browser
              </button>
              <button class="btn btn-secondary btn-sm" onclick="checkAccountSession(${acc.id})" title="Check if cookies are still valid headlessly">
                <i data-lucide="shield-check" style="width: 13px; height: 13px;"></i> Check
              </button>
              <button class="btn btn-secondary btn-sm" onclick="resetAccountQuota(${acc.id})" title="Reset daily counter to 0">
                <i data-lucide="rotate-ccw" style="width: 13px; height: 13px;"></i> Reset
              </button>
              <button class="btn btn-danger btn-sm" onclick="deleteAccount(${acc.id})" title="Delete account">
                <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
              </button>
            </div>
          </td>
        </tr>`;
    }).join("");

    if (window.lucide) lucide.createIcons();
  } catch (e) {
    console.error("Error loading accounts:", e);
  }
}

async function openAccountBrowser(id) {
  showToast(`Opening visible browser window for Account #${id}...`, "info");
  try {
    const res = await fetch(`${API_BASE}/api/accounts/${id}/open-browser`, { method: "POST" });
    if (res.ok) {
      showToast("Browser window opened! You can view login status directly on your screen.", "success");
    }
  } catch (e) {
    showToast("Error opening account browser", "error");
  }
}

async function checkAccountSession(id) {
  showToast(`Checking active session for Account #${id}...`, "info");
  try {
    const res = await fetch(`${API_BASE}/api/accounts/${id}/check-session`, { method: "POST" });
    const data = await res.json();
    if (data.is_logged_in) {
      showToast(`[✓] Account #${id} has an ACTIVE valid login session!`, "success");
    } else {
      showToast(`[!] Account #${id} needs OTP or login credentials.`, "warning");
    }
    loadAccounts();
  } catch (e) {
    showToast("Error checking account session", "error");
  }
}

async function resetAccountQuota(id) {
  try {
    const res = await fetch(`${API_BASE}/api/accounts/${id}/reset-quota`, { method: "POST" });
    if (res.ok) {
      showToast(`Account #${id} quota reset! Ready for orders.`, "success");
      loadAccounts();
      loadStats();
    }
  } catch (e) {
    showToast("Error resetting quota", "error");
  }
}

async function deleteAccount(id) {
  if (!confirm(`Delete Account #${id}?`)) return;
  try {
    const res = await fetch(`${API_BASE}/api/accounts/${id}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Account removed", "info");
      loadAccounts();
      loadStats();
    }
  } catch (e) {
    showToast("Error deleting account", "error");
  }
}

// Single Account Creation
document.getElementById("single-account-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    email: document.getElementById("acc-email").value.trim(),
    password: document.getElementById("acc-password").value.trim(),
    phone: document.getElementById("acc-phone").value.trim() || null,
    full_name: document.getElementById("acc-name").value.trim() || "Customer",
    shipping_address: document.getElementById("acc-address").value.trim() || null,
    city: document.getElementById("acc-city").value.trim() || "Karachi",
    max_daily_orders: 1
  };

  try {
    const res = await fetch(`${API_BASE}/api/accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      showToast("Account added to pool!", "success");
      document.getElementById("single-account-form").reset();
      loadAccounts();
      loadStats();
    } else {
      const err = await res.json();
      showToast(`Error: ${err.detail || 'Could not add account'}`, "error");
    }
  } catch (err) {
    showToast("Network error adding account", "error");
  }
});

// Bulk Text Import
document.getElementById("btn-submit-bulk-accounts")?.addEventListener("click", async () => {
  const textarea = document.getElementById("bulk-accounts-textarea");
  const text = textarea.value.trim();
  if (!text) {
    showToast("Please enter account lines", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/accounts/bulk-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text_data: text })
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`Imported ${data.imported} new accounts (Updated: ${data.updated})`, "success");
      textarea.value = "";
      closeModal("bulk-accounts-modal");
      loadAccounts();
      loadStats();
    }
  } catch (e) {
    showToast("Error during bulk import", "error");
  }
});

// Export CSV handler
function exportAccountsCSV() {
  window.open(`${API_BASE}/api/accounts/export-csv`, '_blank');
}
window.exportAccountsCSV = exportAccountsCSV;

// Set Global Daily Order Limit across all accounts
async function setGlobalDailyLimit(limit) {
  try {
    const res = await fetch(`${API_BASE}/api/accounts/set-global-limit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ max_daily_orders: parseInt(limit) })
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`Daily order limit set to ${limit} orders/day for all ${data.updated_count} accounts!`, "success");
      loadAccounts();
    }
  } catch (e) {
    showToast("Error setting global limit", "error");
  }
}
window.setGlobalDailyLimit = setGlobalDailyLimit;

// Reset All Quotas
document.getElementById("btn-reset-all-quotas")?.addEventListener("click", async () => {
  if (!confirm("Are you sure you want to reset daily order quotas back to 0 for ALL accounts in the pool?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/accounts/reset-all-quotas`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      showToast(`Successfully reset quotas back to 0 for all accounts!`, "success");
      loadAccounts();
    }
  } catch (e) {
    showToast("Error resetting quotas", "error");
  }
});

document.addEventListener("DOMContentLoaded", () => {
  loadAccounts();
});
