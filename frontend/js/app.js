// Global State & Core WebSocket Controller
const API_BASE = window.location.origin;
let socket = null;

// Sound Effects Synthesizer using Web Audio API (No external sound files required)
const SoundFX = {
  enabled: true,
  ctx: null,
  init() {
    if (!this.ctx) {
      try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) this.ctx = new AudioContext();
      } catch (e) {}
    }
  },
  playTone(freq, type = "sine", duration = 0.12, gainVal = 0.08) {
    if (!this.enabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      if (this.ctx.state === "suspended") this.ctx.resume();
      
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);
      
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {}
  },
  click() {
    this.playTone(800, "sine", 0.05, 0.04);
  },
  success() {
    this.playTone(587.33, "triangle", 0.08, 0.06);
    setTimeout(() => this.playTone(880, "sine", 0.16, 0.08), 80);
  },
  action() {
    this.playTone(440, "sine", 0.08, 0.05);
    setTimeout(() => this.playTone(659.25, "sine", 0.12, 0.06), 60);
  },
  error() {
    this.playTone(250, "sawtooth", 0.2, 0.08);
  }
};

// Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  
  let icon = "info";
  if (type === "success") {
    icon = "check-circle";
    SoundFX.success();
  } else if (type === "error") {
    icon = "alert-triangle";
    SoundFX.error();
  } else {
    SoundFX.click();
  }
  
  toast.innerHTML = `<i data-lucide="${icon}" style="width: 18px; height: 18px;"></i> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);
  
  if (window.lucide) lucide.createIcons();
  
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4200);
}

// Modal Helpers
function openModal(id) {
  SoundFX.action();
  const modal = document.getElementById(id);
  if (modal) modal.classList.add("active");
  if (window.lucide) lucide.createIcons();
}

function closeModal(id) {
  SoundFX.click();
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove("active");
}

// Tab Switching (Desktop & Mobile App Bar)
function switchTab(targetTabId) {
  SoundFX.click();
  document.querySelectorAll(".tab-btn, .mobile-nav-item").forEach(b => {
    if (b.getAttribute("data-tab") === targetTabId) {
      b.classList.add("active");
    } else {
      b.classList.remove("active");
    }
  });

  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
  const targetPane = document.getElementById(targetTabId);
  if (targetPane) {
    targetPane.classList.add("active");
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
  if (window.lucide) lucide.createIcons();
}

// Desktop Bridge & Native Folder Handlers
async function openDesktopFolder(target) {
  SoundFX.action();
  showToast(`Opening ${target} folder...`, "info");
  
  // Try PyWebView Native Bridge
  if (window.pywebview && window.pywebview.api) {
    try {
      if (target === "data") await window.pywebview.api.open_data_dir();
      else if (target === "screenshots") await window.pywebview.api.open_screenshots_dir();
      return;
    } catch (e) {}
  }
  
  // Fallback to Backend REST API
  try {
    const res = await fetch(`${API_BASE}/api/system/open-folder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target: target })
    });
    if (res.ok) {
      showToast(`Opened ${target} in Windows File Explorer!`, "success");
    } else {
      showToast(`Could not open ${target} folder`, "error");
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
}

async function createDesktopShortcut() {
  SoundFX.action();
  showToast("Creating Windows Desktop Shortcut...", "info");
  
  if (window.pywebview && window.pywebview.api) {
    try {
      await window.pywebview.api.create_desktop_shortcut();
      showToast("Desktop shortcut created successfully!", "success");
      return;
    } catch (e) {}
  }

  try {
    const res = await fetch(`${API_BASE}/api/system/create-desktop-shortcut`, { method: "POST" });
    const data = await res.json();
    if (res.ok && data.status === "ok") {
      showToast("Shortcut 'DarazBot Pro' pinned to your Desktop!", "success");
    } else {
      showToast("Shortcut creation skipped or unavailable.", "info");
    }
  } catch (err) {
    showToast("Failed to create desktop shortcut", "error");
  }
}

function toggleAppFullscreen() {
  SoundFX.click();
  if (window.pywebview && window.pywebview.api) {
    try {
      window.pywebview.api.toggle_fullscreen();
      return;
    } catch (e) {}
  }

  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  } else {
    document.exitFullscreen().catch(() => {});
  }
}

async function loadSystemDiagnostics() {
  try {
    const res = await fetch(`${API_BASE}/api/system/info`);
    if (res.ok) {
      const info = await res.json();
      const diagModalBody = document.getElementById("diagnostics-modal-body");
      if (diagModalBody) {
        diagModalBody.innerHTML = `
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
            <div class="glass-panel" style="padding: 1rem;">
              <div style="font-size: 0.78rem; color: var(--text-muted);">HOST OS</div>
              <div style="font-size: 1.1rem; font-weight: 700; color: #fff;">${escapeHtml(info.os)} ${escapeHtml(info.os_release)}</div>
            </div>
            <div class="glass-panel" style="padding: 1rem;">
              <div style="font-size: 0.78rem; color: var(--text-muted);">PYTHON RUNTIME</div>
              <div style="font-size: 1.1rem; font-weight: 700; color: var(--accent-cyan); font-family: var(--font-mono);">v${escapeHtml(info.python_version)}</div>
            </div>
            <div class="glass-panel" style="padding: 1rem;">
              <div style="font-size: 0.78rem; color: var(--text-muted);">DATABASE STORAGE</div>
              <div style="font-size: 1.1rem; font-weight: 700; color: var(--accent-green);">${info.db_size_kb} KB</div>
            </div>
            <div class="glass-panel" style="padding: 1rem;">
              <div style="font-size: 0.78rem; color: var(--text-muted);">SCREENSHOTS CACHE</div>
              <div style="font-size: 1.1rem; font-weight: 700; color: var(--accent-daraz);">${info.screenshots_count} Captures</div>
            </div>
          </div>
          <div style="font-size: 0.85rem; color: var(--text-secondary); background: rgba(0,0,0,0.3); padding: 0.85rem; border-radius: var(--radius-sm); font-family: var(--font-mono);">
            <div>📂 Data Path: ${escapeHtml(info.data_dir)}</div>
            <div style="margin-top: 0.35rem;">📸 Screen Path: ${escapeHtml(info.screenshots_dir)}</div>
          </div>
        `;
      }
      openModal("diagnostics-modal");
    }
  } catch (err) {
    showToast("Failed to load system diagnostics", "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Navigation Tabs Handlers
  const allNavBtns = document.querySelectorAll(".tab-btn, .mobile-nav-item");
  allNavBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");
      if (target) switchTab(target);
    });
  });

  // Modal Triggers
  document.getElementById("btn-quick-new-campaign")?.addEventListener("click", () => {
    document.querySelector('[data-tab="campaigns-view"]')?.click();
  });

  document.getElementById("btn-quick-batch")?.addEventListener("click", () => {
    openModal("batch-campaigns-modal");
  });

  document.getElementById("btn-open-batch-modal")?.addEventListener("click", () => {
    openModal("batch-campaigns-modal");
  });

  document.getElementById("btn-open-bulk-accounts-modal")?.addEventListener("click", () => {
    openModal("bulk-accounts-modal");
  });

  document.getElementById("current-ip-btn")?.addEventListener("click", () => {
    SoundFX.action();
    checkCurrentNetworkIP();
  });

  // Desktop Bar Action Triggers
  document.getElementById("btn-desktop-data-folder")?.addEventListener("click", () => openDesktopFolder("data"));
  document.getElementById("btn-desktop-screens-folder")?.addEventListener("click", () => openDesktopFolder("screenshots"));
  document.getElementById("btn-desktop-shortcut")?.addEventListener("click", createDesktopShortcut);
  document.getElementById("btn-desktop-fullscreen")?.addEventListener("click", toggleAppFullscreen);
  document.getElementById("btn-desktop-diagnostics")?.addEventListener("click", loadSystemDiagnostics);

  // Settings Modal Triggers
  document.getElementById("btn-open-settings-modal")?.addEventListener("click", () => {
    loadSettings();
    openModal("settings-modal");
  });

  document.getElementById("btn-save-settings")?.addEventListener("click", saveSettings);

  document.getElementById("marketplace-selector")?.addEventListener("change", async (e) => {
    const country = e.target.value;
    try {
      await fetch(`${API_BASE}/api/logs/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active_country: country })
      });
      showToast(`Marketplace switched to ${country}!`, "success");
      loadStats();
    } catch (err) {
      showToast("Failed to change marketplace", "error");
    }
  });

  // Initialize App
  initWebSocket();
  checkCurrentNetworkIP();
  loadStats();
  if (window.lucide) lucide.createIcons();
});

// WebSocket Setup
function initWebSocket() {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
  
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("[WS] Connected to backend daemon");
    const wsText = document.getElementById("ws-status-text");
    if (wsText) wsText.innerText = "Connected";
    const wsInd = document.querySelector(".ws-indicator");
    if (wsInd) wsInd.style.color = "var(--accent-green)";
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "log") {
        if (window.handleLiveLog) window.handleLiveLog(data);
        if (data.level === "success") {
          loadStats();
          if (window.loadCampaigns) window.loadCampaigns();
        }
      } else if (data.type === "campaign_progress") {
        if (window.loadCampaigns) window.loadCampaigns();
        loadStats();
      }
    } catch (e) {
      console.error("[WS] Parse error", e);
    }
  };

  socket.onclose = () => {
    const wsText = document.getElementById("ws-status-text");
    if (wsText) wsText.innerText = "Reconnecting...";
    const wsInd = document.querySelector(".ws-indicator");
    if (wsInd) wsInd.style.color = "var(--accent-yellow)";
    setTimeout(initWebSocket, 3000);
  };
}

// Check Network IP via Backend (No CORS issues)
async function checkCurrentNetworkIP() {
  const badgeText = document.getElementById("nav-ip-text");
  const diagIp = document.getElementById("diag-ip");
  const diagGeo = document.getElementById("diag-geo");
  const diagIsp = document.getElementById("diag-isp");
  
  if (badgeText) badgeText.innerText = "IP: Checking...";
  try {
    const res = await fetch(`${API_BASE}/api/proxies/current-ip`);
    if (res.ok) {
      const data = await res.json();
      const ip = data.ip || 'Unknown';
      if (badgeText) badgeText.innerText = `IP: ${ip}`;
      if (diagIp) diagIp.innerText = ip;
      if (diagGeo) diagGeo.innerText = `${data.city || ''} ${data.country || ''}`.trim() || 'Online';
      if (diagIsp) diagIsp.innerText = data.org || 'Direct Telecom / Jazz / ISP';
      return;
    }
  } catch (e) {
    if (badgeText) badgeText.innerText = "IP: Connected";
  }
}

// Load Global Statistics
async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/api/logs/stats`);
    if (!res.ok) return;
    const stats = await res.json();
    
    if (document.getElementById("stat-active-accounts")) document.getElementById("stat-active-accounts").innerText = stats.active_accounts;
    if (document.getElementById("stat-total-accounts")) document.getElementById("stat-total-accounts").innerText = `Total: ${stats.total_accounts} in Pool`;
    if (document.getElementById("stat-orders-placed")) document.getElementById("stat-orders-placed").innerText = stats.total_orders_placed;
    if (document.getElementById("stat-atc-done")) document.getElementById("stat-atc-done").innerText = stats.total_atc_done;
    if (document.getElementById("stat-wishlist-done")) document.getElementById("stat-wishlist-done").innerText = stats.total_wishlist_done;
    if (document.getElementById("stat-running-campaigns")) document.getElementById("stat-running-campaigns").innerText = stats.running_campaigns;
    if (document.getElementById("stat-total-campaigns")) document.getElementById("stat-total-campaigns").innerText = `Total: ${stats.total_campaigns} Targets`;

    // Sync marketplace selector
    const marketSelect = document.getElementById("marketplace-selector");
    if (marketSelect && stats.active_country) {
      marketSelect.value = stats.active_country;
    }
  } catch (e) {
    console.error("Error loading stats:", e);
  }
}

// Settings & Preferences Manager
async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/logs/settings`);
    if (!res.ok) return;
    const data = await res.json();

    const countrySelect = document.getElementById("setting-country-select");
    const humanSelect = document.getElementById("setting-human-profile");
    const safeMode = document.getElementById("setting-safe-mode");

    if (countrySelect) countrySelect.value = data.active_country;
    if (humanSelect) humanSelect.value = data.human_profile;
    if (safeMode) safeMode.checked = data.safe_order_mode;
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

async function saveSettings() {
  const country = document.getElementById("setting-country-select")?.value;
  const profile = document.getElementById("setting-human-profile")?.value;
  const safeMode = document.getElementById("setting-safe-mode")?.checked;

  try {
    const res = await fetch(`${API_BASE}/api/logs/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        active_country: country,
        human_profile: profile,
        safe_order_mode: safeMode
      })
    });
    if (res.ok) {
      showToast("Engine settings saved successfully!", "success");
      closeModal("settings-modal");
      loadStats();
    }
  } catch (err) {
    showToast("Failed to save settings", "error");
  }
}

// Utility: HTML Escape
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
