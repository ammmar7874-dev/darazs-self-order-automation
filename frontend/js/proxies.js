// Proxies & Free IP Rotator Controller

async function loadProxies() {
  await Promise.all([loadProxiesTable(), fetchNetworkStatus()]);
}

// 1. Fetch & Render Proxies Table
async function loadProxiesTable() {
  const tbody = document.querySelector("#proxies-table tbody");
  const countBadge = document.getElementById("proxies-count-badge");
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/api/proxies`);
    const proxies = await res.json();

    if (countBadge) countBadge.innerText = `${proxies.length} Proxies in Pool`;

    if (!proxies || proxies.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            No proxies in pool. Click <b>⚡ Auto-Harvest 15+ Free Working Proxies</b> above!
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = proxies.map(p => `
      <tr>
        <td>#${p.id}</td>
        <td style="font-family: var(--font-mono); font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">${escapeHtml(p.proxy_url)}</td>
        <td><span class="badge ${p.proxy_type.includes('free') ? 'badge-info' : 'badge-primary'}">${escapeHtml(p.proxy_type)}</span></td>
        <td style="font-family: var(--font-mono); color: var(--accent-cyan);">${p.last_ip || 'Tested on launch'}</td>
        <td><span class="badge ${p.is_active ? 'badge-success' : 'badge-danger'}">${p.is_active ? 'Active' : 'Inactive'}</span></td>
        <td>
          <button class="btn btn-danger btn-sm" onclick="deleteProxy(${p.id})">
            <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
          </button>
        </td>
      </tr>
    `).join('');

    if (window.lucide) lucide.createIcons();
  } catch (e) {
    console.error("Error loading proxies:", e);
  }
}

// 2. Fetch Full Network & ADB Status
async function fetchNetworkStatus() {
  const diagIp = document.getElementById("diag-ip");
  const diagGeo = document.getElementById("diag-geo");
  const diagIsp = document.getElementById("diag-isp");
  const diagAdb = document.getElementById("diag-adb");
  const navIp = document.getElementById("nav-ip-text");

  try {
    const res = await fetch(`${API_BASE}/api/proxies/current-ip`);
    const data = await res.json();
    if (data.ip) {
      if (diagIp) diagIp.innerText = data.ip;
      if (navIp) navIp.innerText = `IP: ${data.ip}`;
      if (diagGeo) diagGeo.innerText = `${data.city || 'Unknown'}, ${data.country || 'Pakistan'}`;
      if (diagIsp) diagIsp.innerText = data.isp || 'Direct ISP';
    }
  } catch (e) {
    if (diagIp) diagIp.innerText = "Check Failed";
  }

  // Check ADB devices
  try {
    const adbRes = await fetch(`${API_BASE}/api/proxies/adb-devices`);
    const adbData = await adbRes.json();
    if (diagAdb) {
      if (adbData.count > 0) {
        diagAdb.innerHTML = `<span style="color: var(--accent-green); font-weight: 700;">✓ Connected (${adbData.connected_devices[0]})</span>`;
      } else {
        diagAdb.innerHTML = `<span style="color: var(--text-muted);">No phone connected via USB</span>`;
      }
    }
  } catch (e) {}
}

// 3. Auto-Harvest 15+ Free Working Worldwide Proxies
document.getElementById("btn-harvest-free-proxies")?.addEventListener("click", async () => {
  const btn = document.getElementById("btn-harvest-free-proxies");
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader" class="spin" style="width: 16px; height: 16px;"></i> Scraping & Validating Worldwide Proxies...`;
  if (window.lucide) lucide.createIcons();

  showToast("Harvesting & testing thousands of free global proxies in parallel...", "info");

  try {
    const res = await fetch(`${API_BASE}/api/proxies/harvest-free?max_valid=15`, {
      method: "POST"
    });
    const data = await res.json();

    if (data.status === "success" && data.found_valid > 0) {
      showToast(`Found ${data.found_valid} live verified proxies! Added ${data.added_to_database} to pool.`, "success");
      await loadProxiesTable();
    } else {
      showToast("Could not find active public proxies right now. Try again shortly.", "warning");
    }
  } catch (e) {
    showToast("Error harvesting proxies. Check your internet connection.", "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
    if (window.lucide) lucide.createIcons();
  }
});

// 4. Trigger Dynamic IP Rotation
document.getElementById("btn-trigger-rotation")?.addEventListener("click", async () => {
  const method = document.getElementById("rotation-method-select")?.value || "auto";
  const targetParam = document.getElementById("rotation-param-input")?.value.trim() || null;

  showToast(`Triggering IP rotation (${method})...`, "info");

  try {
    const res = await fetch(`${API_BASE}/api/proxies/rotate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method: method, target_param: targetParam })
    });
    const data = await res.json();

    if (data.success) {
      showToast(`[✓] ${data.message}`, "success");
      setTimeout(() => {
        fetchNetworkStatus();
      }, 3500);
    } else {
      showToast(`[!] Rotation Failed: ${data.message}`, "error");
    }
  } catch (e) {
    showToast("Error communicating with rotation service", "error");
  }
});

// 5. Add Custom Proxy Manually
document.getElementById("proxy-config-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("proxy-url-input");
  const proxyUrl = input?.value.trim();
  if (!proxyUrl) return;

  try {
    const res = await fetch(`${API_BASE}/api/proxies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        proxy_url: proxyUrl,
        proxy_type: "custom"
      })
    });

    if (res.ok) {
      showToast("Custom proxy added to pool!", "success");
      input.value = "";
      await loadProxiesTable();
    }
  } catch (e) {
    showToast("Error adding proxy", "error");
  }
});

// 6. Delete Proxy
async function deleteProxy(proxyId) {
  if (!confirm("Are you sure you want to remove this proxy?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/proxies/${proxyId}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Proxy removed", "info");
      await loadProxiesTable();
    }
  } catch (e) {
    showToast("Error deleting proxy", "error");
  }
}

// 7. Refresh Button
document.getElementById("btn-refresh-ip-status")?.addEventListener("click", () => {
  fetchNetworkStatus();
  showToast("Network diagnostics refreshed", "info");
});

document.addEventListener("DOMContentLoaded", () => {
  loadProxies();
});
