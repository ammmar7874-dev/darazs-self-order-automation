# ⚡ DarazBot Pro — Self-Order, Organic Search & Ranking Suite

**DarazBot Pro** is a high-performance, enterprise-grade automation system engineered for Daraz store ranking optimization, organic search simulation, Add-To-Cart (ATC) volume boosting, and self-orders (Cash on Delivery / COD) with dynamic multi-account rotation and anti-detection proxy management.

---

## 🌟 Key Features

1. **Natural Human Search & Simulation**:
   - Types keywords dynamically with human pauses, mouse curves, and realistic typos.
   - Scrolls search result pages, locates the target product card organically to feed Daraz's ranking algorithm high-intent search signals.
   - Simulates authentic dwell time (scrolling reviews, specs, and questions).

2. **Custom Multi-Action Targeting**:
   - **Target Orders Count**: E.g. Place 5, 10, or 20 COD orders per product.
   - **Target Add-To-Cart (ATC) Count**: E.g. Add to cart 50 or 100 times to boost product CTR and conversion signals.
   - **Wishlist & Follow**: Increases store authority metrics.

3. **Multi-Account Pool & Automated Rotation**:
   - Import 10, 50, or 500+ Daraz buyer accounts via bulk text/CSV (`email:password` or `email:password:phone:address`).
   - Configurable daily order limit per account (e.g. 2 orders/day).
   - Once an account hits its limit, the bot **automatically switches to the next available account** and triggers an IP change.

4. **Intelligent IP & Proxy Rotation**:
   - Supports Residential, Mobile, and Datacenter proxies (HTTP / HTTPS / SOCKS5).
   - Dynamic IP rotation trigger via API / URL (ideal for 4G USB mobile dongles or rotating proxy endpoints).
   - IP Guard verifies the clean outbound IP before initiating browser sessions.

5. **Batch Processing (200+ Products)**:
   - 1-click batch generator to paste up to 200+ product links and launch automated campaigns.

6. **Real-time Glassmorphic Dashboard & Live Terminal**:
   - Live WebSocket feed showing exact browser steps in real time.
   - 1-click quota resets and real-time statistics.

---

## 🚀 Quick Start Guide

### 1. Launch with 1-Click
Double click `run.bat` in the project folder. It will:
1. Verify dependencies.
2. Launch the backend server at `http://127.0.0.1:8765`.
3. Automatically open the Web Dashboard in your browser.

### 2. Manual Startup (Terminal)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browser
playwright install chromium

# 3. Start Backend Server
python -m backend.main
```
Open **http://127.0.0.1:8765** in your browser.

---

## 📋 How to Use the Dashboard

### Step 1: Add Accounts
1. Go to the **Accounts Pool** tab.
2. Click **Bulk Import Accounts (CSV/Text)**.
3. Paste accounts in format:
   ```
   buyer1@gmail.com:SecretPassword123
   buyer2@gmail.com:SecretPassword456:03001234567:House 10, Block 4, Karachi
   ```

### Step 2: Configure Proxy (Optional but Recommended)
1. Go to the **Proxies & IP Rotator** tab.
2. Enter your proxy (e.g. `http://user:pass@gate.proxy.com:8080` or `127.0.0.1:9050`).
3. If using a 4G Dongle or rotating link, enter the **IP Rotation Trigger URL**.
4. Click **Test Connection**.

### Step 3: Launch Campaigns
1. Go to **Campaigns & Batch** tab.
2. **Single Product**: Fill in product URL, search keyword (e.g. `wireless earbuds`), target orders count, and ATC count.
3. **Batch (200+ Products)**: Click **Batch Upload (200+ Products)**, paste your links, and click **Generate All Batch Campaigns**.
4. Click **Start** on any campaign. Watch the live execution in the **Live Console** tab!

---

## 📁 System Architecture
- `backend/core/daraz_bot.py`: Main automation engine for search, dwell, ATC, and COD checkout.
- `backend/core/human_behavior.py`: Humanized bezier mouse curves, typing delays, and reading scrolls.
- `backend/core/browser_pool.py`: Playwright stealth profile manager with isolated cookies and sessions.
- `backend/core/proxy_rotator.py`: Proxy parsing, rotation webhook trigger, and outbound IP tester.
- `backend/core/task_scheduler.py`: Multi-account rotator and campaign queue runner.
- `backend/api/`: REST APIs for accounts, proxies, campaigns, and logs.
- `frontend/`: Modern glassmorphic web dashboard with real-time WebSockets.
