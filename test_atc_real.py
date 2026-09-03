import asyncio
from playwright.async_api import async_playwright
from backend.core.daraz_bot import DarazBotEngine

async def test_atc_real():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768}
        )
        page = await context.new_page()
        
        all_reqs = []
        page.on("request", lambda req: all_reqs.append((req.method, req.url)))
        
        print("Navigating to product 667064561...")
        await page.goto("https://www.daraz.pk/products/i667064561.html", timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(4)
        
        # Click SKU if needed
        sku_opts = await page.locator(".sku-variable-item:not(.disabled), .sku-prop-content-item:not(.disabled)").all()
        print(f"SKU options count: {len(sku_opts)}")
        if sku_opts:
            await sku_opts[0].click()
            await asyncio.sleep(1)
            
        atc_btn = page.locator("button.pdp-button_skin_orange, button:has-text('Add to Cart')").first
        count = await atc_btn.count()
        print(f"ATC Button count: {count}")
        
        if count > 0:
            print("Clicking Add to Cart button...")
            req_before = len(all_reqs)
            await atc_btn.click()
            await asyncio.sleep(5)
            
            req_after = len(all_reqs)
            print(f"New requests fired after click: {req_after - req_before}")
            
            # Check for cart counter or modal
            cart_num = await page.locator("#topActionHeader .cart-num, .lzd-nav-cart-num, .cart-icon-num").all_text_contents()
            print(f"Cart Counter Badge: {cart_num}")
            
            # Check for success toast or popup
            dialog = await page.locator(".next-dialog, .cart-dialog, .pdp-cart-success").all_text_contents()
            print(f"Dialog contents: {dialog}")
            
            # List relevant API requests
            for method, url in all_reqs[req_before:]:
                if any(k in url.lower() for k in ["cart", "add", "log", "goldlog", "event", "track", "daraz"]):
                    print(f"  [{method}] {url[:120]}")
                    
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_atc_real())
