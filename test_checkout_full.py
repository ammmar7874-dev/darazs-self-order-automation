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
        print("Clicked Buy Now, waiting 6 seconds...")
        await asyncio.sleep(6)
        
    print("1. SHIPPING URL:", page.url)
    
    # Click Proceed to Pay using text selector
    proceed = page.locator("text='Proceed to Pay'").first
    count = await proceed.count()
    print("Proceed to Pay locator count:", count)
    if count > 0:
        await proceed.scroll_into_view_if_needed()
        await proceed.click()
        print("CLICKED Proceed to Pay! Waiting 8 seconds...")
        await asyncio.sleep(8)
        
    print("2. PAYMENT URL:", page.url)
    await page.screenshot(path="data/payment_step_snapshot.png", full_page=True)
    
    # Select Cash on Delivery
    cod = page.locator("text='Cash on Delivery'").first
    cod_count = await cod.count()
    print("COD locator count:", cod_count)
    if cod_count > 0:
        await cod.click()
        print("CLICKED Cash on Delivery! Waiting 3 seconds...")
        await asyncio.sleep(3)
        
    # Check Confirm Order button
    confirm = page.locator("text='Confirm Order', text='CONFIRM ORDER', text='Place Order', text='Pay Now'").first
    confirm_count = await confirm.count()
    print("Confirm button count:", confirm_count)
    await page.screenshot(path="data/final_step_snapshot.png", full_page=True)

    await context.close()
    await browser_pool.stop()

if __name__ == "__main__":
    asyncio.run(main())
