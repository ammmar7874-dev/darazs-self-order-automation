import asyncio
import random
import re
from typing import Optional, Dict, Any, Callable, List
from playwright.async_api import Page, BrowserContext
from backend.core.human_behavior import human_delay, human_type, human_scroll, human_mouse_move
from backend.config import settings

class DarazBotEngine:
    def __init__(self, page: Page, context: BrowserContext, log_callback: Optional[Callable] = None):
        self.page = page
        self.context = context
        self.log = log_callback or self._default_log
        self.base_url = settings.daraz_base_url
        self.login_url = "https://member.daraz.pk/user/login"


    async def _default_log(self, level: str, message: str):
        try:
            print(f"[{level.upper()}] {message}")
        except Exception:
            try:
                print(f"[{level.upper()}] {message.encode('ascii', 'ignore').decode('ascii')}")
            except Exception:
                pass

    async def navigate_home(self):
        """Navigates to Daraz homepage with humanized timeout and loading checks."""
        await self.log("info", f"Navigating to {self.base_url}...")
        try:
            await self.page.goto(self.base_url, timeout=45000, wait_until="domcontentloaded")
            await human_delay(2.0, 4.0)
            
            # Dismiss any popup banners or close buttons if present
            close_selectors = [
                ".lzd-popup-close",
                "img[src*='close']",
                ".close-btn",
                "button[aria-label='Close']",
                ".next-dialog-close"
            ]
            for sel in close_selectors:
                try:
                    if await self.page.locator(sel).count() > 0:
                        await self.page.locator(sel).first.click(timeout=2000)
                        await human_delay(0.5, 1.0)
                except Exception:
                    pass
        except Exception as e:
            await self.log("warning", f"Page load took longer or had minor issues: {e}")

    async def check_and_login(self, email: str, password: str, phone: Optional[str] = None) -> bool:
        """
        Checks if account is logged in; if not, performs stealth login.
        Supports both Phone number and Email address login.
        """
        await self.log("info", f"Checking login session for {phone or email} (Account: {email})...")
        
        try:
            # First check if user is already logged in on daraz.pk
            await self.page.goto(self.base_url, wait_until="domcontentloaded")
            await human_delay(1.5, 2.5)
            
            member_nav = self.page.locator("a[href*='member.daraz.pk'], #topActionUserAccount, #myAccountTrigger, span:has-text('ACCOUNT')").first
            if await member_nav.count() > 0:
                txt = (await member_nav.inner_text()).lower()
                if "login" not in txt and "sign" not in txt and len(txt.strip()) > 0:
                    await self.log("success", f"Active session already logged in for: {email}")
                    return True

            # If not logged in, proceed to login page
            await self.page.goto(self.login_url, wait_until="domcontentloaded")
            await human_delay(2.0, 3.5)

            
            # Check for logged-in profile icon/text
            is_logged_in = await self.page.locator("a[href*='customer/account'], #myAccount, .lzd-nav-account, span:has-text('Account')").count() > 0
            if is_logged_in:
                await self.log("success", f"Account {email} is already logged in with active session!")
                return True

            # Navigate to member login URL
            login_url = "https://member.daraz.pk/user/login"
            await self.page.goto(login_url, timeout=40000, wait_until="domcontentloaded")
            await human_delay(2.5, 4.0)
            
            # Locate login input field
            email_selectors = [
                "input[placeholder*='Phone Number or Email']",
                "input[placeholder*='Phone Number']",
                "input[placeholder*='Email']",
                ".mod-login-input-loginName input",
                ".mod-login-col2 input[type='text']",
                "input[type='text']:not(#q)",
                "#account"
            ]
            email_field = None
            for sel in email_selectors:
                if await self.page.locator(sel).count() > 0:
                    email_field = sel
                    break
                    
            login_id = phone.strip() if (phone and len(phone.strip()) >= 10) else email.strip()
            await self.log("info", f"Typing login identifier ({login_id})...")
            # Clear field first
            await self.page.locator(email_field).first.fill("")
            await human_type(self.page, email_field, login_id)
            await human_delay(0.8, 1.5)

            
            # Password field
            pwd_selectors = [
                "input[placeholder*='password']",
                "input[placeholder*='Password']",
                "input[type='password']",
                ".mod-login-input-password input",
                "#password"
            ]
            pwd_field = None
            for sel in pwd_selectors:
                if await self.page.locator(sel).count() > 0:
                    pwd_field = sel
                    break
                    
            if pwd_field:
                await self.page.locator(pwd_field).first.fill("")
                await human_type(self.page, pwd_field, password)
                await human_delay(1.0, 2.0)
                
            # Click Login button
            login_btn_selectors = [
                "button.mod-login-btn",
                "button.next-btn-primary",
                "button:has-text('LOGIN')",
                "button:has-text('Login')",
                ".mod-login-btn button"
            ]
            for btn_sel in login_btn_selectors:
                if await self.page.locator(btn_sel).count() > 0:
                    await self.page.locator(btn_sel).first.click()
                    break
                    
            await self.log("info", "Submitted login credentials. Waiting for authentication...")
            await human_delay(6.0, 10.0)
            
            # Check for verification / slider captcha
            captcha_selectors = [
                "#nc_1_n1z",
                ".nc_scale",
                "div[id*='nocaptcha']",
                "iframe[src*='captcha']"
            ]
            for c_sel in captcha_selectors:
                if await self.page.locator(c_sel).count() > 0:
                    await self.log("warning", f"Security verification / Captcha detected for {email}. Manual review or OTP may be needed.")
                    return False
                    
            # Check if navigated away or account elements are visible
            current_url = self.page.url.lower()
            if "user/login" not in current_url:
                await self.log("success", f"Successfully logged into account: {email}")
                return True
            else:
                # One more check for active cookies/session
                cookies = await self.context.cookies()
                has_token = any("token" in c.get("name", "").lower() or "user" in c.get("name", "").lower() for c in cookies)
                if has_token:
                    await self.log("success", f"Session token detected for {email}!")
                    return True
                await self.log("warning", f"Login did not redirect away from login page for {email}.")
                return False

                
        except Exception as e:
            await self.log("error", f"Error during login process for {email}: {e}")
            return False

    async def organic_search_and_browse(
        self,
        keyword: str,
        target_url: str,
        seller_name: Optional[str] = None
    ) -> bool:
        """
        Simulates Advanced Organic Buyer Journey:
        1. Selects dynamic keyword from multi-keyword list (if comma separated).
        2. Types in Daraz search with autocomplete suggestion detection.
        3. 25% chance of Competitor Inspection (Pogo-sticking) to boost conversion win-rate.
        4. Locates target listing in organic search results.
        5. Performs deep dwell: scrolls reviews, clicks product images, and inspects specs.
        """
        # 1. Multi-keyword selection & smart cleaning
        active_kw = keyword.strip()
        if "," in keyword or "|" in keyword:
            kw_list = [k.strip() for k in re.split(r'[,|]', keyword) if k.strip()]
            if kw_list:
                active_kw = random.choice(kw_list)

        # Clean breadcrumbs or noise if user pasted a long title
        if ">" in active_kw:
            active_kw = active_kw.split(">")[0].strip()
        active_kw = re.sub(r'[_~#%&*()]+', ' ', active_kw).strip()
        words = active_kw.split()
        if len(words) > 6:
            active_kw = " ".join(words[:5])

        await self.log("info", f"Initiating organic search for keyword: '{active_kw}'...")
        await self.navigate_home()
        await human_delay(1.5, 3.0)
        
        # Locate search input
        search_selectors = [
            "#q",
            "input[type='search']",
            "input.search-box__input--O34g",
            "input[placeholder*='Search in Daraz']",
            "input[placeholder*='Search']"
        ]
        search_box = None
        for sel in search_selectors:
            if await self.page.locator(sel).count() > 0:
                search_box = sel
                break
                
        if search_box:
            await human_mouse_move(self.page, search_box)
            await human_type(self.page, search_box, active_kw)
            await human_delay(0.8, 1.5)
            
            # Check for autocomplete suggestion dropdown click
            try:
                suggest_items = await self.page.locator(".search-suggest-item, .suggest-item, .search-box__suggest li").all()
                if suggest_items:
                    await suggest_items[0].click()
                    await self.log("info", f"Clicked Daraz autocomplete suggestion for maximum buyer intent signal.")
                else:
                    await self.page.keyboard.press("Enter")
            except Exception:
                await self.page.keyboard.press("Enter")
        else:
            await self.log("info", "Navigating directly to keyword search catalog...")
            try:
                await self.page.goto(f"{self.base_url}/catalog/?q={active_kw.replace(' ', '+')}", timeout=60000, wait_until="domcontentloaded")
            except Exception:
                try:
                    await self.page.goto(f"{self.base_url}/catalog/?q={active_kw.replace(' ', '+')}", timeout=60000, wait_until="commit")
                except Exception:
                    pass
            
        await self.log("info", "Search results loaded. Simulating buyer browsing and scrolling...")
        await human_delay(2.5, 4.5)
        await human_scroll(self.page, min_scrolls=2, max_scrolls=5)
        
        # Extract target item ID or path from target_url
        target_id_match = re.search(r'-i(\d+)', target_url) or re.search(r'products/([a-zA-Z0-9_-]+)', target_url)
        target_token = target_id_match.group(1) if target_id_match else None
        
        # 2. Competitor Pogo-Sticking (Comparative Warmup Traffic - 25% Chance)
        if random.random() < 0.25:
            try:
                competitor_links = await self.page.locator("a[href*='-i']:not([href*='" + (target_token or "none") + "'])").all()
                if competitor_links:
                    comp_choice = random.choice(competitor_links[:4])
                    await self.log("info", "Simulating competitor comparison browsing (pogo-sticking to boost our win-rate)...")
                    await comp_choice.click()
                    await human_delay(3.0, 6.0)
                    await human_scroll(self.page, min_scrolls=2, max_scrolls=3)
                    await human_delay(2.0, 4.0)
                    await self.page.go_back(wait_until="commit")
                    await human_delay(2.0, 3.5)
            except Exception:
                pass

        # 3. Locate Target Product
        found_target = False
        try:
            product_links = await self.page.locator("a[href*='-i'], div[data-item-id] a, a[href*='products/']").all()
            for link in product_links:
                href = await link.get_attribute("href") or ""
                if target_token and target_token in href:
                    await self.log("success", f"Target product identified organically in search results!")
                    await human_mouse_move(self.page, f"a[href*='{target_token}']")
                    await human_delay(0.8, 1.8)
                    await link.click()
                    found_target = True
                    break
        except Exception:
            pass
                
        if not found_target:
            await self.log("info", f"Visiting target product with organic search referrer...")
            try:
                await self.page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            except Exception:
                try:
                    await self.page.goto(target_url, timeout=60000, wait_until="commit")
                except Exception:
                    pass
            
        await human_delay(3.0, 5.0)
        
        # 4. Interactive Product Page Inspection (Image gallery clicks + Review Scrolling)
        await self.log("info", "Simulating natural buyer dwell (inspecting product gallery pictures & reviews)...")
        try:
            # Click 2nd and 3rd gallery images if available
            gallery_thumbs = await self.page.locator(".item-gallery__thumbnail-image, .pdp-item-gallery img, .next-slick-slide").all()
            if len(gallery_thumbs) > 1:
                await gallery_thumbs[1].click()
                await human_delay(1.0, 2.0)
            if len(gallery_thumbs) > 2:
                await gallery_thumbs[2].click()
                await human_delay(1.0, 2.0)
        except Exception:
            pass

        # Deep scroll into reviews and specifications
        await human_scroll(self.page, min_scrolls=4, max_scrolls=7)
        await human_delay(4.0, 7.0)
        return True

    async def add_to_cart(self) -> bool:
        """Clicks 'Add to Cart' and handles any variant selections if present."""
        await self.log("info", "Attempting to Add Product to Cart...")
        
        # Handle variant selection if required (e.g. Size/Color)
        try:
            sku_options = await self.page.locator(".sku-variable-item:not(.disabled), .sku-prop-content-item:not(.disabled)").all()
            if sku_options:
                await sku_options[0].click()
                await human_delay(0.5, 1.0)
        except Exception:
            pass
            
        atc_selectors = [
            "button.pdp-button_skin_orange",
            "button:has-text('Add to Cart')",
            "button:has-text('Add To Cart')",
            ".add-to-cart-buy-now-btn button",
            "button.add-to-cart-btn",
            ".pdp-add-to-cart",
            "div.pdp-cart-btn button",
            "button[class*='pdp-button']:has-text('Cart')"
        ]
        
        for sel in atc_selectors:
            if await self.page.locator(sel).count() > 0:
                await human_mouse_move(self.page, sel)
                await human_delay(0.5, 1.0)
                await self.page.locator(sel).first.click()
                await self.log("success", "Clicked 'Add to Cart' successfully!")
                await human_delay(2.5, 4.5)
                return True
                
        await self.log("warning", "Add to Cart button was not found or was unavailable (e.g. out of stock).")
        return False

    async def add_to_wishlist(self) -> bool:
        """Adds product to wishlist/favorites with full selector and JS fallback support."""
        await self.log("info", "Attempting to Add Product to Wishlist (Favorite)...")
        
        wishlist_selectors = [
            ".pdp-mod-action .pdp-mod-icon-wishlist",
            "i.pdp-mod-icon-wishlist",
            ".pdp-mod-action i",
            ".pdp-wishlist",
            "[class*='pdp-mod-icon-wishlist']",
            "[class*='pdp-mod-action'] span",
            "[class*='wishlist']",
            "span:has-text('Wishlist')",
            "span:has-text('Favorite')",
            "i[class*='heart']",
            "span[class*='heart']",
            ".pdp-button_skin_wishlist",
            "button[aria-label*='wishlist']",
            "span[title*='Wishlist']",
            "span[title*='Favorite']"
        ]
        
        for sel in wishlist_selectors:
            try:
                if await self.page.locator(sel).count() > 0:
                    target_el = self.page.locator(sel).first
                    await target_el.scroll_into_view_if_needed()
                    await human_delay(0.5, 1.0)
                    await target_el.click(force=True)
                    await self.log("success", f"Product added to Wishlist & favorites via selector: {sel}")
                    await human_delay(1.5, 2.5)
                    return True
            except Exception:
                pass

        # Robust JavaScript Fallback
        try:
            clicked_js = await self.page.evaluate('''() => {
                const candidates = Array.from(document.querySelectorAll('.pdp-mod-action, .pdp-mod-action span, .pdp-mod-action i, [class*="wishlist"], [class*="fav"], [class*="heart"], [data-spm-click*="wishlist"], [data-spm-click*="fav"]'));
                for (const el of candidates) {
                    const cls = (el.className || '').toString().toLowerCase();
                    const spm = (el.getAttribute('data-spm-click') || '').toLowerCase();
                    const title = (el.getAttribute('title') || '').toLowerCase();
                    if (cls.includes('wishlist') || cls.includes('fav') || cls.includes('heart') || spm.includes('wishlist') || title.includes('wishlist') || title.includes('favorite')) {
                        el.click();
                        return true;
                    }
                }
                const actionIcons = document.querySelectorAll('.pdp-mod-action .pdp-mod-icon, .pdp-mod-action > span, .pdp-mod-action > i');
                if (actionIcons.length > 0) {
                    actionIcons[actionIcons.length - 1].click();
                    return true;
                }
                return false;
            }''')
            if clicked_js:
                await self.log("success", "Product added to Wishlist & favorites via smart JS fallback!")
                await human_delay(1.5, 2.5)
                return True
        except Exception:
            pass

        await self.log("warning", "Wishlist button could not be located on this page.")
        return False

    async def checkout_and_place_order(self, payment_method: str = "cod") -> Dict[str, Any]:
        """
        Full 2-Step Checkout:
        1. PDP: Select SKU & Click 'Buy Now' -> navigates to /shipping
        2. Shipping Page: Confirms address & Clicks 'Proceed to Pay' -> navigates to /payment
        3. Payment Page: Selects 'Cash on Delivery' & Clicks 'Confirm Order' -> /order/success
        """
        await self.log("info", "Proceeding to checkout (Buy Now)...")
        
        # Handle variant selection if needed
        try:
            sku_options = await self.page.locator(".sku-variable-item:not(.disabled), .sku-prop-content-item:not(.disabled)").all()
            if sku_options:
                await sku_options[0].click()
                await human_delay(0.5, 1.0)
        except Exception:
            pass

        buy_now_selectors = [
            "button.pdp-button_skin_red",
            "button:has-text('Buy Now')",
            "button:has-text('BUY NOW')",
            ".pdp-buy-now",
            ".add-to-cart-buy-now-btn button:last-child"
        ]
        
        clicked_buy = False
        for sel in buy_now_selectors:
            if await self.page.locator(sel).count() > 0:
                await human_mouse_move(self.page, sel)
                await human_delay(0.5, 1.2)
                await self.page.locator(sel).first.click()
                clicked_buy = True
                break
                
        if not clicked_buy:
            # Fallback to Cart page -> Checkout
            await self.page.goto(f"{self.base_url}/cart", wait_until="domcontentloaded")
            await human_delay(2.0, 3.5)
            checkout_btn = self.page.locator("button:has-text('CHECK OUT'), button:has-text('Proceed to Checkout')").first
            if await checkout_btn.count() > 0:
                await checkout_btn.click()
                clicked_buy = True
                
        if not clicked_buy:
            return {"success": False, "error": "Could not locate Buy Now or Checkout button."}
            
        await self.log("info", "Navigating to Shipping & Address Review page...")
        await human_delay(4.0, 7.0)
        
        # --- STEP 1: SHIPPING REVIEW & PROCEED TO PAY ---
        if "shipping" in self.page.url.lower() or "checkout" in self.page.url.lower():
            await self.log("info", "On Shipping page. Checking address status...")
            await human_delay(2.0, 3.5)
            
            # A. Check if an address card already exists on page and click it
            address_cards = self.page.locator(".address-item, .mod-address-item, .item-container, div[data-spm*='address'], .mod-address-card")
            card_count = await address_cards.count()
            
            # Check if address form is open or if no address card is selected
            needs_address_fill = False
            if card_count == 0:
                needs_address_fill = True
            else:
                try:
                    await address_cards.first.click()
                    await human_delay(1.0, 2.0)
                except Exception:
                    pass

            # B. If no address or "+ Add Address" exists, auto-fill full Daraz PK form
            add_addr_btn = self.page.locator("button:has-text('Add Address'), button:has-text('Add New Address'), .mod-address-add-btn, a:has-text('Add Address'), .add-new-address").first
            if await add_addr_btn.count() > 0:
                await add_addr_btn.click()
                needs_address_fill = True
                await human_delay(1.5, 2.5)

            if needs_address_fill or await self.page.locator("input[placeholder*='Full Name'], input[name*='name'], input[placeholder*='House no']").count() > 0:
                await self.log("info", "Filling complete Daraz delivery address (Punjab / Lahore / Gulberg)...")
                
                # 1. Fill Name
                name_inputs = self.page.locator("input[placeholder*='Full Name'], input[name*='name'], input[name='fullName'], .mod-address-form input[type='text']").first
                if await name_inputs.count() > 0:
                    await name_inputs.fill("Ammar Buyer")
                    await human_delay(0.4, 0.8)

                # 2. Fill Phone
                phone_inputs = self.page.locator("input[placeholder*='Phone Number'], input[name*='phone'], input[type='tel']").first
                if await phone_inputs.count() > 0:
                    await phone_inputs.fill("03165915989")
                    await human_delay(0.4, 0.8)

                # 3. Fill Street Address
                addr_inputs = self.page.locator("input[placeholder*='House no'], input[placeholder*='Street'], input[placeholder*='Address'], textarea").first
                if await addr_inputs.count() > 0:
                    await addr_inputs.fill("House 25, Main Gulberg 3, Near Liberty Market")
                    await human_delay(0.4, 0.8)

                # 4. Handle Daraz Fusion UI Dropdowns (Province -> City -> Area)
                select_triggers = await self.page.locator(".next-select, .mod-select-location, div[role='combobox']").all()
                if select_triggers:
                    # Select Province (Punjab)
                    try:
                        await select_triggers[0].click()
                        await human_delay(0.8, 1.5)
                        punjab_opt = self.page.locator(".next-menu-item:has-text('Punjab'), li:has-text('Punjab')").first
                        if await punjab_opt.count() > 0:
                            await punjab_opt.click()
                            await human_delay(0.8, 1.5)
                    except Exception:
                        pass
                        
                    # Select City (Lahore / Vehari)
                    if len(select_triggers) > 1:
                        try:
                            await select_triggers[1].click()
                            await human_delay(0.8, 1.5)
                            city_opt = self.page.locator(".next-menu-item:has-text('Lahore'), .next-menu-item:has-text('Vehari'), .next-menu-item").first
                            if await city_opt.count() > 0:
                                await city_opt.click()
                                await human_delay(0.8, 1.5)
                        except Exception:
                            pass
                            
                    # Select Area
                    if len(select_triggers) > 2:
                        try:
                            await select_triggers[2].click()
                            await human_delay(0.8, 1.5)
                            area_opt = self.page.locator(".next-menu-item:has-text('Gulberg'), .next-menu-item").first
                            if await area_opt.count() > 0:
                                await area_opt.click()
                                await human_delay(0.8, 1.5)
                        except Exception:
                            pass

                # 5. Select Tag (Home / Office)
                home_tag = self.page.locator("button:has-text('Home'), button:has-text('HOME'), span:has-text('Home'), .mod-address-tag").first
                if await home_tag.count() > 0:
                    try:
                        await home_tag.click()
                    except Exception:
                        pass

                # 6. Click Save Button
                save_btn = self.page.locator("button:has-text('Save'), button:has-text('SAVE'), button.mod-address-form-btn, button.next-btn-primary").first
                if await save_btn.count() > 0:
                    await save_btn.click()
                    await self.log("info", "Saved Delivery Address in Daraz profile.")
                    await human_delay(3.0, 5.0)


            # C. Click Proceed to Payment button
            proceed_btn = self.page.locator("text='Proceed to Pay', button:has-text('Proceed to Pay'), .checkout-order-total-button, .checkout-order-total-button button").first
            clicked_proceed = False
            
            if await proceed_btn.count() > 0:
                try:
                    await proceed_btn.scroll_into_view_if_needed()
                    await human_delay(0.5, 1.0)
                    await proceed_btn.click(force=True)
                    clicked_proceed = True
                except Exception:
                    pass
                    
            if not clicked_proceed:
                clicked_proceed = await self.page.evaluate('''() => {
                    const btn = Array.from(document.querySelectorAll('button, div[role="button"], a')).find(b => (b.innerText || '').toLowerCase().includes('proceed to pay'));
                    if (btn) {
                        btn.scrollIntoView();
                        btn.click();
                        return true;
                    }
                    return false;
                }''')

            if clicked_proceed:
                await self.log("info", "Clicked 'Proceed to Pay'! Navigating to Payment selection...")
                # Wait for navigation away from /shipping to payment-cashier
                for _ in range(25):
                    await asyncio.sleep(1)
                    curr = self.page.url.lower()
                    if "payment" in curr or "cashier" in curr or "pay" in curr or "shipping" not in curr:
                        break
                        
            await human_delay(3.0, 5.0)

        # --- STEP 2: PAYMENT METHOD SELECTION (COD) ---
        await self.log("info", f"Selecting payment method: {payment_method.upper()}...")
        
        cod_selectors = [
            "text='Cash on Delivery'",
            "div:has-text('Cash on Delivery')",
            "span:has-text('Cash on Delivery')",
            "p:has-text('Cash on Delivery')",
            "div[data-spm*='cod']",
            ".payment-item-cod"
        ]
        
        selected_cod = False
        for cod_sel in cod_selectors:
            if await self.page.locator(cod_sel).count() > 0:
                try:
                    await self.page.locator(cod_sel).first.scroll_into_view_if_needed()
                    await human_delay(0.5, 1.0)
                    await self.page.locator(cod_sel).first.click(force=True)
                    selected_cod = True
                    await self.log("success", "Selected 'Cash on Delivery' (COD) option!")
                    await human_delay(2.5, 4.0)
                    break
                except Exception:
                    pass
                
        if not selected_cod:
            # JS Fallback for COD Selection
            selected_cod = await self.page.evaluate('''() => {
                const items = Array.from(document.querySelectorAll('div, span, li, button, p, label'));
                const codEl = items.find(el => (el.innerText || '').trim() === 'Cash on Delivery');
                if (codEl) {
                    codEl.click();
                    return true;
                }
                return false;
            }''')
            if selected_cod:
                await self.log("success", "Selected 'Cash on Delivery' (COD) option!")
                await human_delay(2.5, 4.0)
                
        # --- STEP 3: CONFIRM & PLACE ORDER FINAL BUTTON ---
        confirm_order_selectors = [
            "text='Confirm Order'",
            "button:has-text('Confirm Order')",
            "button:has-text('CONFIRM ORDER')",
            "button:has-text('Place Order')",
            "button:has-text('Pay Now')",
            ".automation-btn-confirm-order",
            "button.next-btn-primary"
        ]
        
        confirmed = False
        for c_sel in confirm_order_selectors:
            if await self.page.locator(c_sel).count() > 0:
                try:
                    await self.page.locator(c_sel).first.scroll_into_view_if_needed()
                    await human_delay(0.5, 1.0)
                    await self.page.locator(c_sel).first.click(force=True)
                    confirmed = True
                    await self.log("info", "Clicked 'Confirm Order'! Awaiting order generation from Daraz...")
                    await human_delay(6.0, 10.0)
                    break
                except Exception:
                    pass
                
        if not confirmed:
            # JS Fallback for Confirm Order
            confirmed = await self.page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                const confirmBtn = btns.find(b => (b.innerText || '').trim().toLowerCase() === 'confirm order' || (b.innerText || '').includes('Confirm Order'));
                if (confirmBtn) {
                    confirmBtn.click();
                    return true;
                }
                return false;
            }''')
            if confirmed:
                await self.log("info", "Clicked 'Confirm Order'! Awaiting order confirmation...")
                await human_delay(6.0, 10.0)


        # Verify final confirmation by URL / Success page
        current_url = self.page.url.lower()
        if "success" in current_url or "result" in current_url or "pay/success" in current_url or confirmed:
            await self.log("success", "ORDER CONFIRMED & PLACED SUCCESSFULLY ON DARAZ!")
            return {"success": True, "url": self.page.url}
        else:
            await self.log("warning", f"Checkout reached URL: {self.page.url}")
            return {"success": False, "url": self.page.url, "error": "Could not complete COD confirmation step"}

    async def follow_store(self) -> bool:
        """Follows the seller store on Daraz (boosts store credibility score)."""
        await self.log("info", "Attempting to Follow Seller Store...")
        follow_selectors = [
            ".seller-name__follow",
            "button:has-text('FOLLOW')",
            "button:has-text('Follow')",
            "span:has-text('FOLLOW')",
            "span:has-text('Follow')",
            ".store-follow-btn",
            "[data-spm-click*='follow']",
            ".seller-im-follow-btn"
        ]
        for sel in follow_selectors:
            try:
                if await self.page.locator(sel).count() > 0:
                    btn = self.page.locator(sel).first
                    txt = (await btn.inner_text()).strip().upper()
                    if "FOLLOWING" in txt or "FOLLOWED" in txt:
                        await self.log("info", "Store is already followed by this account.")
                        return True
                    await btn.scroll_into_view_if_needed()
                    await human_delay(0.5, 1.0)
                    await btn.click(force=True)
                    await self.log("success", "Successfully followed seller store!")
                    await human_delay(1.5, 2.5)
                    return True
            except Exception:
                pass
        
        # JS Fallback
        try:
            followed = await self.page.evaluate('''() => {
                const candidates = Array.from(document.querySelectorAll('button, a, span, div[role="button"]'));
                for (const el of candidates) {
                    const txt = (el.innerText || '').trim().toUpperCase();
                    if (txt === 'FOLLOW' || (txt.includes('FOLLOW') && !txt.includes('FOLLOWING') && !txt.includes('FOLLOWER'))) {
                        el.click();
                        return true;
                    }
                }
                return false;
            }''')
            if followed:
                await self.log("success", "Store followed via smart JS fallback!")
                await human_delay(1.5, 2.5)
                return True
        except Exception:
            pass

        await self.log("info", "Store follow button not present or already followed.")
        return False

    async def collect_vouchers(self) -> int:
        """Collects all available vouchers on the store/product page (triggers algorithm reward)."""
        await self.log("info", "Scanning for collectible Daraz vouchers & coupons...")
        collected_count = 0
        voucher_selectors = [
            "button:has-text('Collect')",
            "button:has-text('COLLECT')",
            "span:has-text('Collect')",
            "span:has-text('COLLECT')",
            ".voucher-item__btn:has-text('Collect')",
            "[class*='voucher'] button",
            ".voucher-btn"
        ]
        for sel in voucher_selectors:
            try:
                buttons = await self.page.locator(sel).all()
                for btn in buttons:
                    txt = (await btn.inner_text()).strip().upper()
                    if "COLLECT" in txt and "COLLECTED" not in txt:
                        await btn.scroll_into_view_if_needed()
                        await human_delay(0.5, 1.0)
                        await btn.click(force=True)
                        collected_count += 1
                        await self.log("success", f"Claimed voucher #{collected_count}!")
                        await human_delay(1.0, 2.0)
            except Exception:
                pass

        if collected_count > 0:
            await self.log("success", f"Total {collected_count} voucher(s) successfully collected!")
        else:
            await self.log("info", "No unclaimed vouchers found on this page.")
        return collected_count

    async def upvote_positive_reviews(self, max_upvotes: int = 3) -> int:
        """Finds 5-star positive reviews and upvotes them to boost listing conversion rate."""
        await self.log("info", f"Scanning for 5-star reviews to upvote (Target: up to {max_upvotes})...")
        upvoted = 0
        try:
            # Scroll to reviews section
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.7);")
            await human_delay(1.5, 3.0)

            helpful_btns = await self.page.locator(".review-item .helpfull, .review-item [class*='helpful'], .review-item i[class*='like'], .item-rating .helpful").all()
            for btn in helpful_btns[:max_upvotes]:
                try:
                    await btn.scroll_into_view_if_needed()
                    await human_delay(0.5, 1.0)
                    await btn.click(force=True)
                    upvoted += 1
                    await self.log("success", f"Upvoted positive review #{upvoted}!")
                    await human_delay(1.0, 2.0)
                except Exception:
                    pass
        except Exception as e:
            await self.log("warning", f"Review upvoting check completed: {e}")

        return upvoted

    async def scrape_store_catalog(self, store_url: str) -> List[Dict[str, Any]]:
        """Extracts all product URLs, titles, images, and prices from a Daraz store."""
        await self.log("info", f"Scraping store catalog from: {store_url}...")
        try:
            await self.page.goto(store_url, timeout=60000, wait_until="domcontentloaded")
            await human_delay(3.0, 5.0)

            for _ in range(7):
                await self.page.mouse.wheel(0, 800)
                await human_delay(0.8, 1.2)

            products = await self.page.evaluate('''() => {
                const items = [];
                const links = Array.from(document.querySelectorAll('a[href*="/products/"]'));
                for (const a of links) {
                    let href = a.href || '';
                    if (href.startsWith('//')) {
                        href = 'https:' + href;
                    }
                    const cleanUrl = href.split('?')[0];
                    const text = (a.innerText || a.getAttribute('title') || '').trim().replace(/\\n+/g, ' ');
                    const imgEl = a.querySelector('img');
                    const img = imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || '') : '';
                    if (cleanUrl.includes('/products/') && !items.find(i => i.url === cleanUrl)) {
                        let title = text;
                        if (!title && a.parentElement) {
                            title = (a.parentElement.innerText || '').trim().replace(/\\n+/g, ' ');
                        }
                        const idMatch = cleanUrl.match(/-i(\\d+)/) || cleanUrl.match(/i(\\d+)\\.html/);
                        const pId = idMatch ? idMatch[1] : '';
                        items.push({
                            id: pId,
                            url: cleanUrl,
                            title: title,
                            img: img
                        });
                    }
                }
                return items;
            }''')
            await self.log("success", f"Extracted {len(products)} products from store catalog!")
            return products
        except Exception as e:
            await self.log("error", f"Failed to scrape store catalog: {e}")
            return []

    async def capture_live_screenshot(self, filename: str = "live_stream.png") -> Optional[str]:
        """Captures real-time screenshot of current browser page for live desktop monitor stream."""
        try:
            from backend.config import SCREENSHOTS_DIR
            out_path = SCREENSHOTS_DIR / filename
            await self.page.screenshot(path=str(out_path), full_page=False)
            return str(out_path)
        except Exception:
            return None

    async def check_keyword_serp_rank(
        self,
        keyword: str,
        target_id_or_url: str,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Deep Organic SERP Scanner:
        Searches Daraz keyword catalog page 1 to max_pages, finds exact rank position of product,
        detects organic vs sponsored slots, competitors count, and price/ratings.
        """
        clean_kw = keyword.strip()
        # Extract product ID if full URL provided
        target_id = ""
        id_match = re.search(r'-i(\d+)', target_id_or_url) or re.search(r'i(\d+)\.html', target_id_or_url)
        if id_match:
            target_id = id_match.group(1)
        elif target_id_or_url.isdigit():
            target_id = target_id_or_url
        else:
            target_id = target_id_or_url.strip()

        await self.log("info", f"Scanning SERP ranking for '{clean_kw}' (Target Product ID: {target_id})...")
        
        total_items_scanned = 0
        target_found = False
        result_details = {
            "keyword": clean_kw,
            "target_id": target_id,
            "found": False,
            "page": None,
            "position_on_page": None,
            "overall_rank": None,
            "is_sponsored": False,
            "product_title": None,
            "product_price": None,
            "product_url": None,
            "total_scanned": 0,
            "top_competitors": []
        }

        for page_num in range(1, max_pages + 1):
            serp_url = f"{self.base_url}/catalog/?q={clean_kw.replace(' ', '+')}&page={page_num}"
            await self.log("info", f"Checking SERP Page {page_num}/{max_pages}: {serp_url}")
            
            try:
                await self.page.goto(serp_url, timeout=45000, wait_until="domcontentloaded")
                await human_delay(2.5, 4.0)
                await self.capture_live_screenshot()

                # Scroll down slightly to trigger lazy-loaded cards
                for _ in range(3):
                    await self.page.mouse.wheel(0, 700)
                    await human_delay(0.5, 0.8)

                # Extract all product cards on page
                card_data = await self.page.evaluate('''() => {
                    const cards = [];
                    // Match standard Daraz desktop catalog cards
                    const items = document.querySelectorAll('div[data-qa-locator="product-item"], .gridItem--Yd0sa, div[data-tracking="product-card"], .Bm3ON');
                    items.forEach((item, index) => {
                        const linkEl = item.querySelector('a[href*="/products/"]');
                        const href = linkEl ? (linkEl.href || '') : '';
                        const titleEl = item.querySelector('.title--wFj93, .RfADt a, ._95X4G a, a[title]');
                        const title = titleEl ? (titleEl.innerText || titleEl.getAttribute('title') || '').trim() : '';
                        const priceEl = item.querySelector('.price--NVB62, .aBrP0, .currency--GViewer, span:has-text("Rs.")');
                        const price = priceEl ? priceEl.innerText.trim() : '';
                        const sponsoredEl = item.querySelector('.sponsor-tag, [class*="sponsored"], [class*="AdTag"], span:has-text("AD")');
                        const isSponsored = !!sponsoredEl;
                        
                        const idMatch = href.match(/-i(\\d+)/) || href.match(/i(\\d+)\\.html/);
                        const itemId = idMatch ? idMatch[1] : '';

                        cards.push({
                            id: itemId,
                            url: href.split('?')[0],
                            title: title,
                            price: price,
                            is_sponsored: isSponsored,
                            pos_on_page: index + 1
                        });
                    });
                    return cards;
                }''')

                total_items_scanned += len(card_data)

                # Save top 3 competitors from page 1
                if page_num == 1 and not result_details["top_competitors"]:
                    result_details["top_competitors"] = card_data[:3]

                for card in card_data:
                    # Match target
                    if (target_id and target_id == card["id"]) or (target_id_or_url in card["url"]):
                        target_found = True
                        result_details.update({
                            "found": True,
                            "page": page_num,
                            "position_on_page": card["pos_on_page"],
                            "overall_rank": total_items_scanned - (len(card_data) - card["pos_on_page"]),
                            "is_sponsored": card["is_sponsored"],
                            "product_title": card["title"],
                            "product_price": card["price"],
                            "product_url": card["url"],
                            "total_scanned": total_items_scanned
                        })
                        await self.log("success", f"🎯 Found Target Product on Page {page_num}, Slot #{card['pos_on_page']} (Overall Rank: #{result_details['overall_rank']})!")
                        return result_details

            except Exception as e:
                await self.log("warning", f"Page {page_num} scan warning: {e}")

        result_details["total_scanned"] = total_items_scanned
        if not target_found:
            await self.log("info", f"Target product not found in top {max_pages} pages ({total_items_scanned} listings scanned). Consider running ATC & Store Booster to increase SERP rank.")
        return result_details




