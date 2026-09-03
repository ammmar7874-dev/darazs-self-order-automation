// Daraz Store Booster & Auto-Scraper Frontend Logic
let currentStoreProducts = [
  {
    id: "598756764",
    url: "https://www.daraz.pk/products/3rd-tws-i598756764-s2766588828.html",
    title: "Airpods Air Pro TwS Bluetooth Earbuds",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["airpods pro", "tws earbuds", "bluetooth handfree", "wireless earphones"],
    selected: true
  },
  {
    id: "621540685",
    url: "https://www.daraz.pk/products/tws-10-i621540685-s2904136294.html",
    title: "Airpods pro TwS Airbuds Super Sound",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["airpods pro tws", "airbuds", "wireless earbuds bluetooth", "bluetooth earbuds"],
    selected: true
  },
  {
    id: "1971002021",
    url: "https://www.daraz.pk/products/2-i1971002021-s14056277835.html",
    title: "Air Pro 2nd Gen TWS Wireless Bluetooth Earbuds",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["air pro 2nd gen", "tws wireless earbuds", "bluetooth earphones", "noise reduction earbuds"],
    selected: true
  },
  {
    id: "1970986896",
    url: "https://www.daraz.pk/products/-i1970986896-s14056746013.html",
    title: "Pro Wireless TWS Bluetooth Earbuds",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["wireless earbuds", "pro tws earbuds", "bluetooth airpods", "wireless earphones"],
    selected: true
  },
  {
    id: "1970297081",
    url: "https://www.daraz.pk/products/-i1970297081-s14056295397.html",
    title: "Pro TWS In-Ear Wireless Earphones",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["pro tws bluetooth", "in ear earbuds", "wireless earphones", "airpods"],
    selected: true
  },
  {
    id: "1970984905",
    url: "https://www.daraz.pk/products/-i1970984905-s14056722911.html",
    title: "Universal Pro TWS Wireless Earbuds Bluetooth 5.2 Super Bass",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["universal pro tws", "wireless earbuds bluetooth 5.2", "super bass earphones", "tws earbuds"],
    selected: true
  },
  {
    id: "1970301002",
    url: "https://www.daraz.pk/products/-i1970301002-s14056736598.html",
    title: "Pro TWS Wireless Earbuds Bluetooth 5.3 Deep Bass",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["pro tws wireless earbuds", "bluetooth 5.3 earphones", "deep bass airbuds", "stereo earbuds"],
    selected: true
  },
  {
    id: "1970303004",
    url: "https://www.daraz.pk/products/-i1970303004-s14056722913.html",
    title: "Pro High Bass Bluetooth Earbuds Noise Isolation",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["pro high bass earbuds", "noise isolation earphones", "type c bluetooth earbuds", "wireless earbuds"],
    selected: true
  },
  {
    id: "598791145",
    url: "https://www.daraz.pk/products/tws-169-ra-i598791145-s2766617090.html",
    title: "Airpro TwS Airpods Touch Sensor Headset",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["airpro tws airpods", "wireless earbuds", "bluetooth handfree", "touch sensor airbuds"],
    selected: true
  },
  {
    id: "667064561",
    url: "https://www.daraz.pk/products/tws-10-i667064561-s3146768410.html",
    title: "Original TwS Airpods with Super Sound & Touch Sensor",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["original tws airpods", "wireless airbuds", "bluetooth earphones", "airpods tws"],
    selected: true
  },
  {
    id: "1970984906",
    url: "https://www.daraz.pk/products/2-i1970984906-s14056287634.html",
    title: "Pro 2 TWS Bluetooth Earphones In-Ear Wireless Earbuds",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["pro 2 tws", "bluetooth earphones in ear", "silicone tips earbuds", "wireless airbuds"],
    selected: true
  },
  {
    id: "1970291629",
    url: "https://www.daraz.pk/products/-i1970291629-s14056722908.html",
    title: "AP Pro TWS Wireless Earbuds Heavy Subwoofer Bass",
    img: "https://static-01.daraz.pk/p/3c7bbdebe29158cf5f98cf7c899c9ef4.jpg",
    keywords: ["ap pro tws", "wireless earbuds bluetooth", "pubg calling earbuds", "heavy bass airpods"],
    selected: true
  }
];

function renderStoreProductsGrid() {
  const container = document.getElementById("store-products-grid");
  const countLabel = document.getElementById("store-products-count-label");
  if (!container) return;

  if (!currentStoreProducts || currentStoreProducts.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem;">
        No products loaded. Paste a store link and click <b>Scrape Store Products</b>!
      </div>
    `;
    if (countLabel) countLabel.innerText = "0 products loaded";
    return;
  }

  if (countLabel) {
    const selCount = currentStoreProducts.filter(p => p.selected).length;
    countLabel.innerText = `Selected ${selCount} of ${currentStoreProducts.length} products for ranking boost`;
  }

  container.innerHTML = currentStoreProducts.map((p, idx) => `
    <div class="glass-panel" style="padding: 1rem; border: 1px solid ${p.selected ? 'var(--accent-daraz)' : 'rgba(255,255,255,0.08)'}; background: ${p.selected ? 'rgba(249, 115, 22, 0.04)' : 'rgba(20,25,40,0.6)'}; border-radius: var(--radius-md); display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease;">
      <div>
        <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.5rem;">
          <label style="display: flex; align-items: center; gap: 0.5rem; font-weight: 700; font-size: 0.88rem; cursor: pointer;">
            <input type="checkbox" ${p.selected ? 'checked' : ''} onchange="toggleStoreProduct(${idx})" style="accent-color: var(--accent-daraz); width: 16px; height: 16px;">
            <span>#${idx + 1} SKU: ${p.id || 'N/A'}</span>
          </label>
          <span class="nav-badge" style="font-size: 0.7rem; background: rgba(34,197,94,0.1); color: var(--accent-green);">10x ATC/Wish</span>
        </div>
        
        <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-primary); line-height: 1.35; margin-bottom: 0.5rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="${p.title}">
          ${p.title}
        </div>

        <div style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 0.5rem; word-break: break-all;">
          ${p.url.substring(0, 50)}...
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.75rem;">
          ${(p.keywords || []).slice(0, 3).map(kw => `
            <span style="font-size: 0.7rem; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; color: var(--accent-cyan);">
              🔍 ${kw}
            </span>
          `).join('')}
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.5rem; font-size: 0.75rem; color: var(--text-secondary);">
        <span>Target: <b>10 Cart / 10 Wish</b></span>
        <a href="${p.url}" target="_blank" style="color: var(--accent-primary); text-decoration: none; display: flex; align-items: center; gap: 2px;">
          View <i data-lucide="external-link" style="width: 12px; height: 12px;"></i>
        </a>
      </div>
    </div>
  `).join('');

  if (window.lucide) lucide.createIcons();
}

function toggleStoreProduct(idx) {
  if (currentStoreProducts[idx]) {
    currentStoreProducts[idx].selected = !currentStoreProducts[idx].selected;
    renderStoreProductsGrid();
  }
}

async function scrapeStoreCatalog() {
  const inputEl = document.getElementById("store-url-input");
  const storeUrl = inputEl ? inputEl.value.trim() : "";
  if (!storeUrl) {
    showToast("Please enter a valid Daraz Store URL", "warning");
    return;
  }

  const btn = document.getElementById("btn-scrape-store");
  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<i data-lucide="loader-2" class="spin" style="width: 16px; height: 16px;"></i> Scraping Store...`;
  btn.disabled = true;
  if (window.lucide) lucide.createIcons();

  try {
    showToast("Scraping store catalog in real-time. Please wait...", "info");
    const res = await fetch("/api/campaigns/scrape-store", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ store_url: storeUrl })
    });
    const data = await res.json();
    if (res.ok && data.products && data.products.length > 0) {
      currentStoreProducts = data.products.map(p => ({
        ...p,
        keywords: [p.title.split(" ").slice(0, 3).join(" "), "wireless earbuds", "airpods"],
        selected: true
      }));
      renderStoreProductsGrid();
      showToast(`Successfully extracted ${data.products.length} products!`, "success");
    } else {
      showToast(data.detail || "Could not extract products automatically. Loaded cached products.", "warning");
      renderStoreProductsGrid();
    }
  } catch (err) {
    console.error("Scrape error:", err);
    showToast("Server error during store scrape. Using verified store listings.", "warning");
    renderStoreProductsGrid();
  } finally {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
    if (window.lucide) lucide.createIcons();
  }
}

async function launchStoreBoostCampaign() {
  const selected = currentStoreProducts.filter(p => p.selected);
  if (selected.length === 0) {
    showToast("Please select at least 1 product to boost!", "warning");
    return;
  }

  const targetAtc = parseInt(document.getElementById("store-target-atc").value) || 10;
  const targetWishlist = parseInt(document.getElementById("store-target-wishlist").value) || 10;
  const followStore = document.getElementById("store-opt-follow")?.checked || true;
  const collectVouchers = document.getElementById("store-opt-vouchers")?.checked || true;
  const upvoteReviews = document.getElementById("store-opt-upvotes")?.checked || true;
  const isHeadless = document.getElementById("store-opt-headless")?.checked || false;

  const btn = document.getElementById("btn-launch-store-boost");
  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<i data-lucide="loader-2" class="spin" style="width: 18px; height: 18px;"></i> Launching 10x Boost...`;
  btn.disabled = true;
  if (window.lucide) lucide.createIcons();

  try {
    const payload = {
      store_url: document.getElementById("store-url-input")?.value || "https://www.daraz.pk/shop/8itypm6b",
      products: selected,
      target_atc: targetAtc,
      target_wishlist: targetWishlist,
      follow_store: followStore,
      collect_vouchers: collectVouchers,
      upvote_reviews: upvoteReviews,
      headless: isHeadless
    };

    const res = await fetch("/api/campaigns/bulk-store-boost", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`🔥 Store 10x Deep Ranking Campaign launched for ${selected.length} products!`, "success");
      
      // Trigger all created campaigns
      if (data.campaign_ids && data.campaign_ids.length > 0) {
        for (const cid of data.campaign_ids) {
          fetch(`/api/campaigns/${cid}/start`, { method: "POST" }).catch(() => {});
        }
      }
      
      // Switch to dashboard view
      setTimeout(() => {
        if (typeof switchTab === 'function') {
          switchTab('dashboard-view');
        }
      }, 1200);
    } else {
      showToast(data.detail || "Failed to launch store boost.", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Error starting store boost: " + err.message, "error");
  } finally {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
    if (window.lucide) lucide.createIcons();
  }
}

// Event Listeners Initialization
document.addEventListener("DOMContentLoaded", () => {
  renderStoreProductsGrid();

  const scrapeBtn = document.getElementById("btn-scrape-store");
  if (scrapeBtn) scrapeBtn.addEventListener("click", scrapeStoreCatalog);

  const sampleBtn = document.getElementById("btn-load-sample-store");
  if (sampleBtn) sampleBtn.addEventListener("click", () => {
    renderStoreProductsGrid();
    showToast("Loaded 12 store products from catalog!", "success");
  });

  const selectAllBtn = document.getElementById("btn-store-select-all");
  if (selectAllBtn) selectAllBtn.addEventListener("click", () => {
    currentStoreProducts.forEach(p => p.selected = true);
    renderStoreProductsGrid();
  });

  const deselectAllBtn = document.getElementById("btn-store-deselect-all");
  if (deselectAllBtn) deselectAllBtn.addEventListener("click", () => {
    currentStoreProducts.forEach(p => p.selected = false);
    renderStoreProductsGrid();
  });

  const launchBtn = document.getElementById("btn-launch-store-boost");
  if (launchBtn) launchBtn.addEventListener("click", launchStoreBoostCampaign);
});
