// ============================================================================
// DARAZBOT PRO - LIVE VISUAL BROWSER MONITOR & WORKER INSPECTOR
// ============================================================================

let monitorInterval = null;
let isMonitorActive = false;
let monitorFps = 2000; // default 2 seconds

function startVisualStream() {
  stopVisualStream();
  isMonitorActive = true;
  fetchLiveScreenshot();
  monitorInterval = setInterval(fetchLiveScreenshot, monitorFps);
  updateMonitorStatusUI(true);
}

function stopVisualStream() {
  if (monitorInterval) {
    clearInterval(monitorInterval);
    monitorInterval = null;
  }
  isMonitorActive = false;
  updateMonitorStatusUI(false);
}

function toggleVisualStream() {
  if (isMonitorActive) {
    stopVisualStream();
    showToast('Visual browser monitor paused', 'info');
  } else {
    startVisualStream();
    showToast('Live visual stream started', 'success');
  }
}

async function fetchLiveScreenshot() {
  const imgEl = document.getElementById('visual-monitor-img');
  const placeholder = document.getElementById('visual-monitor-placeholder');
  const timestampEl = document.getElementById('visual-monitor-timestamp');
  if (!imgEl) return;

  try {
    const timestamp = new Date().getTime();
    const res = await fetch(`/api/logs/live-screenshot?t=${timestamp}`);
    if (res.status === 200) {
      const blob = await res.blob();
      if (blob && blob.size > 0) {
        const url = URL.createObjectURL(blob);
        imgEl.src = url;
        imgEl.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';
        if (timestampEl) timestampEl.innerText = `Live Frame: ${new Date().toLocaleTimeString()}`;
      }
    } else if (res.status === 204) {
      if (!imgEl.src || imgEl.src.length === 0) {
        imgEl.style.display = 'none';
        if (placeholder) placeholder.style.display = 'flex';
        if (timestampEl) timestampEl.innerText = 'Standby (No active worker browser running)';
      }
    }
  } catch (err) {
    console.debug('Monitor stream poll:', err);
  }
}

function updateMonitorStatusUI(running) {
  const statusBadge = document.getElementById('visual-monitor-badge');
  const btnToggle = document.getElementById('btn-toggle-visual-stream');
  if (statusBadge) {
    statusBadge.className = running ? 'badge badge-success' : 'badge badge-warning';
    statusBadge.innerHTML = running ? '🔴 LIVE STREAMING' : '⏸️ PAUSED';
  }
  if (btnToggle) {
    btnToggle.innerHTML = running 
      ? '<i data-lucide="pause" style="width:15px;height:15px;"></i> Pause Stream'
      : '<i data-lucide="play" style="width:15px;height:15px;"></i> Resume Stream';
    if (window.lucide) lucide.createIcons();
  }
}

function setStreamInterval(ms) {
  monitorFps = parseInt(ms);
  if (isMonitorActive) {
    startVisualStream();
  }
  showToast(`Stream refresh rate set to ${monitorFps / 1000}s`, 'info');
}

// Automatically start stream when visual monitor tab is active
document.addEventListener('DOMContentLoaded', () => {
  const tabButtons = document.querySelectorAll('.tab-btn, .mobile-nav-item');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabTarget = btn.getAttribute('data-tab');
      if (tabTarget === 'visual-monitor-view') {
        startVisualStream();
      }
    });
  });

  const btnToggle = document.getElementById('btn-toggle-visual-stream');
  if (btnToggle) {
    btnToggle.addEventListener('click', toggleVisualStream);
  }

  const btnSnap = document.getElementById('btn-snap-visual-stream');
  if (btnSnap) {
    btnSnap.addEventListener('click', () => {
      fetchLiveScreenshot();
      showToast('Frame updated!', 'success');
    });
  }
});
