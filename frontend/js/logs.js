// Live Console & Logs Viewer

function handleLiveLog(log) {
  const terminal = document.getElementById("terminal-output");
  const dashTerminal = document.getElementById("dashboard-live-log-container");

  const timeStr = log.timestamp 
    ? new Date(log.timestamp).toLocaleTimeString()
    : new Date().toLocaleTimeString();

  const levelClass = (log.level || "info").toLowerCase();
  const levelTag = (log.level || "INFO").toUpperCase();
  const accPrefix = log.account_email ? `[${log.account_email}] ` : "";

  const renderEntry = () => {
    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.style.padding = "3px 0";
    entry.style.borderBottom = "1px solid rgba(255,255,255,0.03)";
    entry.innerHTML = `
      <span class="log-time" style="color: var(--text-muted); margin-right: 6px;">[${timeStr}]</span>
      <span class="log-tag ${levelClass}">${levelTag}</span>
      <span class="log-msg" style="color: var(--text-primary); margin-left: 6px;">${accPrefix}${escapeHtml(log.message)}</span>
    `;
    return entry;
  };

  if (terminal) {
    terminal.appendChild(renderEntry());
    if (terminal.children.length > 250) {
      terminal.removeChild(terminal.firstElementChild);
    }
    terminal.scrollTop = terminal.scrollHeight;
  }

  if (dashTerminal) {
    // If placeholder is present, clear it
    if (dashTerminal.children.length === 1 && dashTerminal.children[0].innerText.includes("Connecting")) {
      dashTerminal.innerHTML = "";
    }
    dashTerminal.appendChild(renderEntry());
    if (dashTerminal.children.length > 100) {
      dashTerminal.removeChild(dashTerminal.firstElementChild);
    }
    dashTerminal.scrollTop = dashTerminal.scrollHeight;
  }
}

window.handleLiveLog = handleLiveLog;

async function loadInitialLogs() {
  try {
    const res = await fetch(`${API_BASE}/api/logs?limit=50`);
    const logs = await res.json();
    if (logs && logs.length > 0) {
      // Clear placeholders
      const dashTerminal = document.getElementById("dashboard-live-log-container");
      if (dashTerminal) dashTerminal.innerHTML = "";
      
      // Reverse to chronological order
      logs.reverse().forEach(handleLiveLog);
    }
  } catch (e) {
    console.error("Error loading logs:", e);
  }
}

document.getElementById("btn-clear-logs")?.addEventListener("click", async () => {
  const terminal = document.getElementById("terminal-output");
  const dashTerminal = document.getElementById("dashboard-live-log-container");
  if (terminal) terminal.innerHTML = "";
  if (dashTerminal) dashTerminal.innerHTML = "";
  try {
    await fetch(`${API_BASE}/api/logs`, { method: "DELETE" });
    showToast("Console logs cleared", "info");
  } catch (e) {
    console.error("Error clearing logs:", e);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  loadInitialLogs();
});
