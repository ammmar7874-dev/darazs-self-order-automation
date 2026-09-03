import asyncio
import os
from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine

async def main():
    os.makedirs("data", exist_ok=True)
    context, page = await browser_pool.create_account_context('ammmar7874@gmail.com', headless=True)
    bot = DarazBotEngine(page, context)
    login_ok = await bot.check_and_login('ammmar7874@gmail.com', 'Ammar@7874', '03165915989')
    print("Login:", login_ok)
    print("Navigating to product...")
    await page.goto("https://www.daraz.pk/products/i605903921.html")
    await asyncio.sleep(4)
    
    # Handle variant selection
    try:
        sku = page.locator(".sku-variable-item, .sku-prop-content-item").first
        if await sku.count() > 0:
            await sku.click()
            await asyncio.sleep(1)
    except Exception:
        pass

    buy_btn = page.locator("button.pdp-button_skin_red, button:has-text('Buy Now'), button:has-text('BUY NOW')").first
    if await buy_btn.count() > 0:
        await buy_btn.click()
        print("Clicked Buy Now, waiting 5 seconds...")
        await asyncio.sleep(5)
        
    print("Current URL:", page.url)
    
    # Click Proceed to Pay
    btn = page.locator("button:has-text('Proceed to Pay'), button:has-text('PROCEED TO PAY'), button.checkout-order-total-button").first
    print("Proceed to Pay button count:", await btn.count())
    if await btn.count() > 0:
        await btn.scroll_into_view_if_needed()
        await btn.click()
        print("Clicked Proceed to Pay button! Waiting 8 seconds...")
        await asyncio.sleep(8)
        
    print("AFTER PROCEED URL:", page.url)
    await page.screenshot(path="data/payment_page_snapshot.png", full_page=True)
    print("Saved payment page screenshot to data/payment_page_snapshot.png")

    await context.close()
    await browser_pool.stop()

if __name__ == "__main__":
    asyncio.run(main())
