import asyncio
import sys
import re

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine

async def audit_live_daraz_selectors():
    print("==================================================================")
    print("🌐 DARAZ.PK LIVE DOM & SELECTOR COMPATIBILITY AUDIT")
    print("==================================================================")
    
    context = None
    page = None
    results = {}
    
    try:
        context, page = await browser_pool.create_account_context(
            account_email="live_audit_test@daraz.pk",
            headless=True
        )
        
        # 1. Homepage & Search Box
        print("\n[Step 1] Auditing Homepage & Search Bar...")
        await page.goto("https://www.daraz.pk", timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        search_selectors = [
            "#q",
            "input[type='search']",
            "input.search-box__input--O34g",
            "input[placeholder*='Search in Daraz']",
            "input[placeholder*='Search']"
        ]
        found_search = None
        for sel in search_selectors:
            if await page.locator(sel).count() > 0:
                found_search = sel
                break
        print(f"  ✔ Search Input Selector: {found_search} (Count: {await page.locator(found_search).count() if found_search else 0})")
        results["Homepage_Search"] = "WORKING" if found_search else "BROKEN"

        # 2. Search Catalog & Product Cards
        print("\n[Step 2] Auditing Search Results Catalog & Product Cards...")
        await page.goto("https://www.daraz.pk/catalog/?q=wireless+earbuds", timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(4)
        
        card_selectors = [
            "div[data-tracking='product-card']",
            "div[data-item-id]",
            ".box--ujueT",
            ".gridItem--Yd0sa",
            "a[href*='-i']",
            ".product-card"
        ]
        cards_found = {}
        first_product_url = None
        for sel in card_selectors:
            cnt = await page.locator(sel).count()
            if cnt > 0:
                cards_found[sel] = cnt
                if not first_product_url and sel == "a[href*='-i']":
                    try:
                        first_product_url = await page.locator(sel).first.get_attribute("href")
                    except Exception:
                        pass
                        
        print(f"  ✔ Found Product Card Selectors: {cards_found}")
        results["Search_Catalog"] = f"WORKING (Found {sum(cards_found.values())} elements)" if cards_found else "BROKEN"

        # 3. Product Detail Page (PDP) & Add to Cart
        print("\n[Step 3] Auditing Product Detail Page (PDP) & ATC Buttons...")
        test_pdp_url = "https://www.daraz.pk" + first_product_url if (first_product_url and first_product_url.startswith("/")) else (first_product_url or "https://www.daraz.pk/products/m10-tws-wireless-earbuds-bluetooth-53-i424426543.html")
        print(f"  --> Navigating to PDP: {test_pdp_url[:70]}...")
        await page.goto(test_pdp_url, timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(4)
        
        atc_selectors = [
            "button.pdp-button_skin_orange",
            "button:has-text('Add to Cart')",
            ".add-to-cart-buy-now-btn button",
            "button.pdp-button_theme_orange"
        ]
        found_atc = None
        for sel in atc_selectors:
            if await page.locator(sel).count() > 0:
                found_atc = sel
                break
                
        buy_now_selectors = [
            "button.pdp-button_skin_red",
            "button:has-text('Buy Now')",
            "button.buy-now-btn"
        ]
        found_buy_now = None
        for sel in buy_now_selectors:
            if await page.locator(sel).count() > 0:
                found_buy_now = sel
                break

        print(f"  ✔ Add to Cart Button: {found_atc} (Count: {await page.locator(found_atc).count() if found_atc else 0})")
        print(f"  ✔ Buy Now Button: {found_buy_now} (Count: {await page.locator(found_buy_now).count() if found_buy_now else 0})")
        results["PDP_ATC_Button"] = "WORKING" if found_atc else "BROKEN"
        results["PDP_Buy_Now"] = "WORKING" if found_buy_now else "BROKEN"

        # 4. Login Page Selectors
        print("\n[Step 4] Auditing Daraz Member Login Page...")
        await page.goto("https://member.daraz.pk/user/login", timeout=45000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        email_field = None
        for sel in ["input[placeholder*='Phone Number or Email']", "input[placeholder*='Email']", ".mod-login-input-loginName input", "input[type='text']"]:
            if await page.locator(sel).count() > 0:
                email_field = sel
                break
                
        pwd_field = None
        for sel in ["input[placeholder*='password']", "input[placeholder*='Password']", "input[type='password']", ".mod-login-input-password input"]:
            if await page.locator(sel).count() > 0:
                pwd_field = sel
                break
                
        login_btn = None
        for sel in ["button.mod-login-btn", "button.next-btn-primary", "button:has-text('LOGIN')", "button:has-text('Login')"]:
            if await page.locator(sel).count() > 0:
                login_btn = sel
                break

        print(f"  ✔ Login Email Field: {email_field}")
        print(f"  ✔ Login Password Field: {pwd_field}")
        print(f"  ✔ Login Submit Button: {login_btn}")
        results["Login_Page"] = "WORKING" if (email_field and pwd_field and login_btn) else "BROKEN"

    except Exception as e:
        print(f"❌ Exception in Live Audit: {e}")
        results["Live_Audit"] = f"FAILED: {e}"
    finally:
        if context:
            await context.close()
        await browser_pool.stop()

    print("\n" + "=" * 66)
    print("📊 LIVE DARAZ.PK SELECTOR AUDIT RESULTS:")
    for k, v in results.items():
        print(f"  • {k.ljust(20)}: {v}")
    print("==================================================================")

if __name__ == "__main__":
    asyncio.run(audit_live_daraz_selectors())
