import asyncio
from playwright.async_api import async_playwright
import json
import re

async def scrape_store(store_url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            viewport={"width": 1366, "height": 768}
        )
        page = await context.new_page()
        
        print(f"[*] Navigating to store: {store_url}")
        await page.goto(store_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)
        
        # Scroll smoothly to load all lazy-loaded store products
        for _ in range(8):
            await page.mouse.wheel(0, 800)
            await page.wait_for_timeout(1000)
            
        products = await page.evaluate("""() => {
            const items = [];
            const links = Array.from(document.querySelectorAll('a[href*="/products/"]'));
            for (const a of links) {
                let href = a.href || '';
                if (href.startsWith('//')) {
                    href = 'https:' + href;
                }
                const cleanUrl = href.split('?')[0];
                const text = (a.innerText || a.getAttribute('title') || '').trim().replace(/\\n+/g, ' ');
                if (cleanUrl.includes('/products/') && !items.find(i => i.url === cleanUrl)) {
                    // extract title or heading if available
                    let title = text;
                    if (!title && a.parentElement) {
                        title = (a.parentElement.innerText || '').trim().replace(/\\n+/g, ' ');
                    }
                    items.push({ url: cleanUrl, title: title });
                }
            }
            return items;
        }""")
        
        print(f"[+] Total unique products extracted: {len(products)}")
        for idx, p in enumerate(products, 1):
            print(f"  {idx}. {p['url']} | {p['title'][:60]}")
            
        with open("store_products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
            
        await browser.close()
        return products

if __name__ == "__main__":
    store = "https://www.daraz.pk/shop/8itypm6b"
    asyncio.run(scrape_store(store))
