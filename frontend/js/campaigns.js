// Campaigns & Dual-Mode Automation Manager

function switchCampaignMode(mode) {
  const typeInput = document.getElementById("camp-type");
  const btnAtc = document.getElementById("btn-mode-atc");
  const btnOrder = document.getElementById("btn-mode-order");
  const descCard = document.getElementById("mode-desc-card");
  const atcInputs = document.getElementById("atc-mode-inputs");
  const orderInputs = document.getElementById("order-mode-inputs");
  const submitBtn = document.getElementById("btn-submit-campaign");

  if (!typeInput) return;
  typeInput.value = mode;

  if (mode === "atc_rank_boost") {
    btnAtc.style.background = "var(--accent-primary)";
    btnAtc.style.color = "white";
    btnOrder.style.background = "transparent";
    btnOrder.style.color = "var(--text-muted)";

    descCard.innerHTML = `
      <b style="color: #ffffff;">⚡ Solution 4 (Infinite Organic Ranking):</b>
      Searches your keyword, scrolls & dwells on reviews, adds to cart & wishlist with rotating IPs. <b>Zero phone numbers or accounts required!</b>
    `;
    descCard.style.borderColor = "rgba(99, 102, 241, 0.3)";
    descCard.style.background = "rgba(99, 102, 241, 0.1)";

    atcInputs.style.display = "block";
    orderInputs.style.display = "none";
    submitBtn.className = "btn btn-daraz";
    submitBtn.innerHTML = `<i data-lucide="rocket" style="width: 16px; height: 16px;"></i> Launch Solution 4 Rank Booster`;
  } else {
    btnOrder.style.background = "var(--accent-daraz)";
    btnOrder.style.color = "white";
    btnAtc.style.background = "transparent";
    btnAtc.style.color = "var(--text-muted)";

    descCard.innerHTML = `
      <b style="color: #ffffff;">🛒 Dedicated Self-Orders Mode:</b>
      Places <b>1 Order per Account per Day</b> with automated address filling & COD checkout. Rotates accounts with safe 24-hour cooldowns.
    `;
    descCard.style.borderColor = "rgba(249, 115, 22, 0.3)";
    descCard.style.background = "rgba(249, 115, 22, 0.1)";

    atcInputs.style.display = "none";
    orderInputs.style.display = "block";
    submitBtn.className = "btn btn-primary";
    submitBtn.innerHTML = `<i data-lucide="shopping-cart" style="width: 16px; height: 16px;"></i> Launch Self-Order Campaign`;
  }

  if (window.lucide) lucide.createIcons();
}

window.switchCampaignMode = switchCampaignMode;

async function loadCampaigns() {
  const dashTbody = document.querySelector("#dashboard-campaigns-table tbody");
  const fullTbody = document.querySelector("#campaigns-full-table tbody");

  try {
    const res = await fetch(`${API_BASE}/api/campaigns`);
    const campaigns = await res.json();

    if (!campaigns || campaigns.length === 0) {
      const emptyHtml = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 3rem;">
            No campaigns active. Click <b>Launch Solution 4 Rank Booster</b> to start!
          </td>
        </tr>`;
      if (dashTbody) dashTbody.innerHTML = emptyHtml;
      if (fullTbody) fullTbody.innerHTML = emptyHtml;
      return;
    }

    const renderRow = (camp) => {
      let statusBadge = `<span class="badge badge-info"><i data-lucide="clock" style="width: 12px; height: 12px;"></i> Idle</span>`;
      if (camp.status === "running") {
        statusBadge = `<span class="badge badge-success"><div class="pulse-dot" style="width: 6px; height: 6px;"></div> Running</span>`;
      } else if (camp.status === "paused") {
        statusBadge = `<span class="badge badge-warning"><i data-lucide="pause-circle" style="width: 12px; height: 12px;"></i> Paused</span>`;
      } else if (camp.status === "completed") {
        statusBadge = `<span class="badge badge-purple"><i data-lucide="check-check" style="width: 12px; height: 12px;"></i> Completed</span>`;
      }

      const isATC = (camp.campaign_type || "atc_rank_boost") === "atc_rank_boost";
      const typeBadge = isATC 
        ? `<span class="badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.4);">🚀 Solution 4 (ATC)</span>`
        : `<span class="badge" style="background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4);">🛒 Orders (1/ID)</span>`;

      const orderPct = Math.min(100, Math.round((camp.completed_orders_count / (camp.target_orders_count || 1)) * 100));
      const atcPct = Math.min(100, Math.round((camp.completed_atc_count / (camp.target_atc_count || 1)) * 100));

      const isRunning = camp.status === "running";

      return `
        <tr>
          <td style="font-family: var(--font-mono); color: var(--text-muted);">#${camp.id}</td>
          <td>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 2px;">
              <span style="font-weight: 700; color: var(--text-primary);">${escapeHtml(camp.name)}</span>
              ${typeBadge}
            </div>
            <div style="font-size: 0.78rem; color: var(--accent-cyan);">
              <i data-lucide="search" style="width: 11px; height: 11px; display: inline;"></i> "${escapeHtml(camp.keyword)}"
            </div>
          </td>
          <td style="max-width: 200px;">
            <a href="${escapeHtml(camp.target_url)}" target="_blank" style="color: var(--text-secondary); text-decoration: none; font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; display: block; white-space: nowrap;">
              ${escapeHtml(camp.target_url)}
            </a>
          </td>
          <td>
            <div style="font-size: 0.82rem; font-weight: 600;">${camp.completed_orders_count} / ${camp.target_orders_count}</div>
            <div class="progress-bar-container">
              <div class="progress-bar-fill" style="width: ${orderPct}%;"></div>
            </div>
          </td>
          <td>
            <div style="font-size: 0.82rem; font-weight: 600;">${camp.completed_atc_count} / ${camp.target_atc_count}</div>
            <div class="progress-bar-container">
              <div class="progress-bar-fill" style="width: ${atcPct}%; background: linear-gradient(135deg, #f59e0b, #ec4899);"></div>
            </div>
          </td>
          <td>${statusBadge}</td>
          <td>
            <div style="display: flex; gap: 0.4rem;">
              ${isRunning ? `
                <button class="btn btn-secondary btn-sm" onclick="stopCampaign(${camp.id})" title="Pause Campaign">
                  <i data-lucide="pause" style="width: 13px; height: 13px;"></i> Pause
                </button>
              ` : `
                <button class="btn btn-daraz btn-sm" onclick="startCampaign(${camp.id})" title="Start / Resume Campaign">
                  <i data-lucide="play" style="width: 13px; height: 13px;"></i> Start
                </button>
              `}
              <button class="btn btn-danger btn-sm" onclick="deleteCampaign(${camp.id})" title="Delete Campaign">
                <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
              </button>
            </div>
          </td>
        </tr>`;
    };

    const rowsHtml = campaigns.map(renderRow).join("");
    if (dashTbody) dashTbody.innerHTML = rowsHtml;
    if (fullTbody) fullTbody.innerHTML = rowsHtml;

    if (window.lucide) lucide.createIcons();
  } catch (e) {
    console.error("Error loading campaigns:", e);
  }
}

window.loadCampaigns = loadCampaigns;

async function startCampaign(id) {
  try {
    const res = await fetch(`${API_BASE}/api/campaigns/${id}/start`, { method: "POST" });
    if (res.ok) {
      showToast(`Campaign #${id} started! Check Live Console for details.`, "success");
      loadCampaigns();
      loadStats();
    }
  } catch (e) {
    showToast("Error starting campaign", "error");
  }
}

async function stopCampaign(id) {
  try {
    const res = await fetch(`${API_BASE}/api/campaigns/${id}/stop`, { method: "POST" });
    if (res.ok) {
      showToast(`Campaign #${id} paused`, "info");
      loadCampaigns();
      loadStats();
    }
  } catch (e) {
    showToast("Error pausing campaign", "error");
  }
}

async function deleteCampaign(id) {
  if (!confirm(`Delete Campaign #${id}?`)) return;
  try {
    const res = await fetch(`${API_BASE}/api/campaigns/${id}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Campaign deleted", "info");
      loadCampaigns();
      loadStats();
    }
  } catch (e) {
    showToast("Error deleting campaign", "error");
  }
}

// Single Campaign Creation (Dual Mode)
document.getElementById("single-campaign-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  
  const mode = document.getElementById("camp-type")?.value || "atc_rank_boost";
  const isATC = mode === "atc_rank_boost";

  const payload = {
    name: document.getElementById("camp-name").value,
    campaign_type: mode,
    target_url: document.getElementById("camp-url").value,
    keyword: document.getElementById("camp-keyword").value,
    seller_name: document.getElementById("camp-seller")?.value || null,
    target_orders_count: isATC ? 0 : (parseInt(document.getElementById("camp-orders")?.value) || 1),
    target_atc_count: isATC ? (parseInt(document.getElementById("camp-atc")?.value) || 25) : 0,
    target_wishlist_count: isATC ? (parseInt(document.getElementById("camp-wishlist")?.value) || 10) : 0,
    delay_min_sec: parseInt(document.getElementById("camp-delay")?.value) || 12,
    delay_max_sec: (parseInt(document.getElementById("camp-delay")?.value) || 12) + 15,
    headless: document.getElementById("camp-headless")?.checked || false
  };

  try {
    const res = await fetch(`${API_BASE}/api/campaigns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const newCamp = await res.json();
      // Auto-start immediately!
      await fetch(`${API_BASE}/api/campaigns/${newCamp.id}/start`, { method: "POST" });
      showToast(isATC ? "🚀 Solution 4 Rank Booster started! Check Live Console for real-time progress." : "🛒 Self-Order Campaign launched!", "success");
      document.getElementById("single-campaign-form").reset();
      switchCampaignMode(mode);
      loadCampaigns();
      loadStats();
    } else {
      showToast("Failed to create campaign", "error");
    }
  } catch (err) {
    showToast("Network error creating campaign", "error");
  }
});

// Bulk Batch 200+ Products Submit
document.getElementById("btn-submit-batch-campaigns")?.addEventListener("click", async () => {
  const textarea = document.getElementById("batch-products-textarea");
  const batchText = textarea.value.trim();
  if (!batchText) {
    showToast("Please enter at least one product URL or formatted line", "error");
    return;
  }

  const payload = {
    batch_text: batchText,
    campaign_type: "atc_rank_boost",
    default_orders: 0,
    default_atc: 25,
    default_wishlist: 10,
    delay_min_sec: 12,
    delay_max_sec: 25,
    headless: false
  };

  try {
    const res = await fetch(`${API_BASE}/api/campaigns/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`Batch Generated! Created ${data.created_campaigns} Solution 4 Ranking campaigns.`, "success");
      textarea.value = "";
      closeModal("batch-campaigns-modal");
      loadCampaigns();
      loadStats();
    } else {
      showToast("Failed to generate batch campaigns", "error");
    }
  } catch (err) {
    showToast("Network error during batch generation", "error");
  }
});

// Quick Launch & Modal Event Listeners
document.getElementById("btn-quick-wizard-launch")?.addEventListener("click", () => openModal("single-campaign-modal"));
document.getElementById("btn-quick-new-campaign")?.addEventListener("click", () => openModal("single-campaign-modal"));
document.getElementById("btn-quick-batch")?.addEventListener("click", () => openModal("batch-campaigns-modal"));
document.getElementById("btn-open-single-campaign-modal")?.addEventListener("click", () => openModal("single-campaign-modal"));
document.getElementById("btn-open-batch-campaigns-modal")?.addEventListener("click", () => openModal("batch-campaigns-modal"));

document.addEventListener("DOMContentLoaded", () => {
  loadCampaigns();
});
