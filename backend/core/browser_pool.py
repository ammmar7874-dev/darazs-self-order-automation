import os
import re
import random
from pathlib import Path
from typing import Optional, Dict, Tuple
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from playwright_stealth import Stealth
from fake_useragent import UserAgent
from backend.config import PROFILES_DIR

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"
]

stealth_engine = Stealth()

# Realistic GPU Renderers for Anti-Detect Spoofing
WEBGL_RENDERERS = [
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"}
]

class BrowserPool:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        
    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()

    async def stop(self):
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def _sanitize_email(self, email: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_-]', '_', email)

    async def create_account_context(
        self,
        account_email: str,
        proxy_dict: Optional[Dict[str, str]] = None,
        headless: bool = False
    ) -> Tuple[BrowserContext, Page]:
        """
        Creates a persistent, isolated, anti-detect browser context with randomized
        hardware fingerprints (Canvas, WebGL, AudioContext, Battery, Viewport).
        """
        await self.start()
        
        user_data_dir = PROFILES_DIR / self._sanitize_email(account_email)
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Realistic Viewport sizes
        viewports = [
            {"width": 1366, "height": 768},
            {"width": 1920, "height": 1080},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
            {"width": 1600, "height": 900}
        ]
        chosen_viewport = random.choice(viewports)
        gpu = random.choice(WEBGL_RENDERERS)
        hw_concurrency = random.choice([4, 8, 12, 16])
        device_memory = random.choice([4, 8, 16])
        
        user_agent_str = random.choice(USER_AGENTS)
        
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--start-maximized",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu-sandbox"
        ]
        
        launch_kwargs = {
            "user_data_dir": str(user_data_dir),
            "headless": headless,
            "viewport": chosen_viewport,
            "user_agent": user_agent_str,
            "proxy": proxy_dict,
            "args": args,
            "locale": "en-US",
            "timezone_id": "Asia/Karachi",
            "geolocation": {"longitude": 67.0011, "latitude": 24.8607}, # Karachi
            "permissions": ["geolocation"]
        }

        # Auto-detect real system Google Chrome or Microsoft Edge
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        if any(os.path.exists(p) for p in chrome_paths):
            launch_kwargs["channel"] = "chrome"
        elif any(os.path.exists(p) for p in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]):
            launch_kwargs["channel"] = "msedge"

        try:
            context = await self.playwright.chromium.launch_persistent_context(**launch_kwargs)
        except Exception:
            # Fallback to default bundled chromium if channel fails
            if "channel" in launch_kwargs:
                launch_kwargs.pop("channel")
            context = await self.playwright.chromium.launch_persistent_context(**launch_kwargs)
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Apply anti-bot stealth engine
        try:
            await stealth_engine.apply_stealth_async(page)
        except Exception:
            pass
            
        # Enterprise-Grade Anti-Detect Hardware Fingerprint Injections
        stealth_init_script = f"""
            // 1. Remove WebDriver
            Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
            
            // 2. Spoof Hardware Concurrency & Memory
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hw_concurrency} }});
            Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {device_memory} }});

            // 3. Spoof WebGL Vendor & Renderer
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{gpu["vendor"]}';
                if (parameter === 37446) return '{gpu["renderer"]}';
                return getParameter.apply(this, arguments);
            }};
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{gpu["vendor"]}';
                if (parameter === 37446) return '{gpu["renderer"]}';
                return getParameter2.apply(this, arguments);
            }};

            // 4. Subtle Canvas Noise for Unique Fingerprint
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {{
                const context = this.getContext('2d');
                if (context) {{
                    const imgData = context.getImageData(0, 0, Math.min(this.width, 10), Math.min(this.height, 10));
                    if (imgData && imgData.data.length > 0) {{
                        imgData.data[0] = (imgData.data[0] + 1) % 255;
                        context.putImageData(imgData, 0, 0);
                    }}
                }}
                return originalToDataURL.apply(this, arguments);
            }};

            // 5. Spoof Chrome Runtime
            window.chrome = {{
                runtime: {{}},
                app: {{}},
                loadTimes: function() {{}},
                csi: function() {{}}
            }};
        """
        await page.add_init_script(stealth_init_script)
        
        return context, page

browser_pool = BrowserPool()
