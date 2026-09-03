// ============================================================================
// DARAZBOT PRO - SERP KEYWORD RANK CHECKER & POSITION TRACKER
// ============================================================================

async function checkProductSerpRank() {
  const keyword = document.getElementById('rank-keyword-input')?.value.trim();
  const productUrl = document.getElementById('rank-product-input')?.value.trim();
  const maxPages = parseInt(document.getElementById('rank-max-pages')?.value || '5');

  if (!keyword || !productUrl) {
    showToast('Please enter both a Keyword and Product URL / ID', 'warning');
    return;
  }

  const btn = document.getElementById('btn-run-rank-check');
  const resultCard = document.getElementById('rank-result-container');

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader" class="spin" style="width:16px;height:16px;"></i> Scanning Daraz SERP...';
    if (window.lucide) lucide.createIcons();
  }

  if (resultCard) {
    resultCard.style.display = 'block';
    resultCard.innerHTML = `
      <div style="text-align: center; padding: 2.5rem; color: var(--text-secondary);">
        <div style="font-size: 1.05rem; font-weight: 600; color: #fff;">Searching Daraz Catalog for "${escapeHtml(keyword)}"...</div>
        <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.25rem;">Checking pages 1 to ${maxPages} and analyzing organic positions...</div>
      </div>
    `;
  }

  try {
    const res = await fetch('/api/campaigns/rank-checker/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword, target_url: productUrl, max_pages: maxPages })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to scan SERP');

    const r = data.result;
    renderRankResult(r);
    loadRankHistory();
    showToast(r.found ? `Found on Page ${r.page}, Slot #${r.position_on_page}!` : 'Scan complete. Product not found in scanned pages.', r.found ? 'success' : 'info');

  } catch (err) {
    console.error('Rank check failed:', err);
    showToast(err.message, 'error');
    if (resultCard) {
      resultCard.innerHTML = `
        <div style="padding: 1.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-sm); color: #fca5a5;">
          <b>Error Scanning SERP:</b> ${escapeHtml(err.message)}
        </div>
      `;
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="search" style="width:16px;height:16px;"></i> Check SERP Rank Now';
      if (window.lucide) lucide.createIcons();
    }
  }
}

function renderRankResult(r) {
  const container = document.getElementById('rank-result-container');
  if (!container) return;

  if (r.found) {
    const isPageOne = r.page === 1;
    const rankColor = isPageOne ? '#10b981' : (r.page <= 3 ? '#f59e0b' : '#6366f1');
    const badgeText = isPageOne ? '🌟 PAGE 1 WINNER' : `PAGE ${r.page} RANKED`;

    container.innerHTML = `
      <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius-md); padding: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
          <div>
            <span class="nav-badge" style="background: ${rankColor}20; color: ${rankColor}; border-color: ${rankColor}40; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; display: inline-block;">
              ${badgeText}
            </span>
            <h3 style="font-size: 1.25rem; font-weight: 700; margin: 0; color: #fff;">
              Position #${r.position_on_page} on Page ${r.page}
            </h3>
            <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.25rem;">
              Overall Organic Rank: <b>#${r.overall_rank}</b> out of ${r.total_scanned} listings scanned
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 1.75rem; font-weight: 800; color: ${rankColor}; font-family: var(--font-mono);">
              #${r.overall_rank}
            </div>
            <div style="font-size: 0.72rem; color: var(--text-muted);">${r.is_sponsored ? 'Sponsored Tag' : 'Organic Listing'}</div>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; background: rgba(0,0,0,0.3); padding: 1rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color); margin-bottom: 1.25rem;">
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">Product Title:</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(r.product_title || '')}">
              ${escapeHtml(r.product_title || 'Daraz Product')}
            </div>
          </div>
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">Catalog Price:</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: var(--accent-daraz); font-family: var(--font-mono);">
              ${escapeHtml(r.product_price || 'N/A')}
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 0.75rem;">
          <button class="btn btn-daraz btn-sm" onclick="quickLaunchRankBoostFromChecker('${escapeHtml(r.keyword)}', '${escapeHtml(r.product_url || r.target_id)}')">
            <i data-lucide="flame" style="width: 14px; height: 14px;"></i> Boost Rank to #1 With Solution 4
          </button>
          <a href="${escapeHtml(r.product_url || '#')}" target="_blank" class="btn btn-secondary btn-sm" style="text-decoration: none;">
            <i data-lucide="external-link" style="width: 14px; height: 14px;"></i> Open Listing
          </a>
        </div>
      </div>
    `;
  } else {
    container.innerHTML = `
      <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: var(--radius-md); padding: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
          <i data-lucide="alert-triangle" style="color: var(--accent-yellow); width: 28px; height: 28px;"></i>
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 700; margin: 0; color: #fff;">Product Not Found in Top ${r.total_scanned} Listings</h3>
            <div style="font-size: 0.82rem; color: var(--text-muted);">Scanned ${r.total_scanned} search results across ${document.getElementById('rank-max-pages')?.value || 5} pages.</div>
          </div>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.25rem; line-height: 1.5;">
          This product is currently deep in search results for keyword <b>"${escapeHtml(r.keyword)}"</b>. Launching the <b>10x Organic Rank Booster (ATC + Wishlist + Reviews)</b> will give it the organic velocity needed to rank on Page 1.
        </p>
        <button class="btn btn-daraz" onclick="quickLaunchRankBoostFromChecker('${escapeHtml(r.keyword)}', '${escapeHtml(document.getElementById('rank-product-input')?.value.trim())}')">
          <i data-lucide="rocket" style="width: 16px; height: 16px;"></i> Launch Solution 4 Rank Booster Now
        </button>
      </div>
    `;
  }
  if (window.lucide) lucide.createIcons();
}

async function loadRankHistory() {
  const tbody = document.querySelector('#rank-history-table tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/campaigns/rank-checker/history');
    if (!res.ok) return;
    const items = await res.json();

    if (!items || items.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            No rank check history yet. Scan your first keyword above!
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = items.map(h => {
      const isRanked = h.rank_position > 0;
      const rankBadge = isRanked 
        ? `<span class="badge badge-success">#${h.rank_position} (Pg ${h.page_number})</span>`
        : `<span class="badge badge-warning">> ${h.total_results_found}</span>`;

      return `
        <tr>
          <td><span style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-muted);">#${h.id}</span></td>
          <td><b>${escapeHtml(h.keyword)}</b></td>
          <td>
            <div style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.82rem;">
              <a href="${escapeHtml(h.product_url)}" target="_blank" style="color: var(--accent-cyan); text-decoration: none;">
                ${escapeHtml(h.product_title || h.product_id)}
              </a>
            </div>
          </td>
          <td>${rankBadge}</td>
          <td>${h.is_sponsored ? '<span class="badge badge-info">Sponsored</span>' : '<span class="badge badge-active">Organic</span>'}</td>
          <td><span style="font-size: 0.75rem; color: var(--text-muted);">${new Date(h.checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></td>
        </tr>
      `;
    }).join('');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Failed to load rank history:', err);
  }
}

function quickLaunchRankBoostFromChecker(kw, url) {
  const nameInput = document.getElementById('camp-name');
  const kwInput = document.getElementById('camp-keyword');
  const urlInput = document.getElementById('camp-url');

  if (nameInput) nameInput.value = `Rank Booster - ${kw.substring(0, 30)}`;
  if (kwInput) kwInput.value = kw;
  if (urlInput) urlInput.value = url;

  if (typeof switchTab === 'function') {
    switchTab('campaigns-view');
  }
  showToast('Pre-filled campaign form! Click Launch to begin.', 'success');
}

document.addEventListener('DOMContentLoaded', () => {
  const btnCheck = document.getElementById('btn-run-rank-check');
  if (btnCheck) {
    btnCheck.addEventListener('click', checkProductSerpRank);
  }
  loadRankHistory();
});
