import asyncio
import random
import math

async def human_delay(min_sec: float = 1.0, max_sec: float = 3.5):
    """Wait for a randomized duration to simulate human thinking or reading time."""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)

async def human_type(page, selector: str, text: str, min_delay_ms: int = 50, max_delay_ms: int = 180):
    """Types text character by character with humanized random pauses and occasional typos."""
    element = page.locator(selector).first
    await element.click()
    await human_delay(0.3, 0.8)
    
    for char in text:
        # 3% chance of brief micro-pause
        if random.random() < 0.03:
            await asyncio.sleep(random.uniform(0.2, 0.5))
        await page.keyboard.type(char, delay=random.randint(min_delay_ms, max_delay_ms))
    
    await human_delay(0.4, 0.9)

async def human_scroll(page, min_scrolls: int = 3, max_scrolls: int = 7):
    """Simulates natural scrolling down the page with pauses and slight backtracking."""
    scroll_count = random.randint(min_scrolls, max_scrolls)
    for _ in range(scroll_count):
        # Scroll down by randomized amount
        scroll_amount = random.randint(250, 650)
        await page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}})")
        await human_delay(0.8, 2.2)
        
        # 25% chance of small scroll up (reading back something)
        if random.random() < 0.25:
            back_scroll = random.randint(80, 200)
            await page.evaluate(f"window.scrollBy({{top: -{back_scroll}, behavior: 'smooth'}})")
            await human_delay(0.5, 1.2)

async def human_mouse_move(page, target_selector: str):
    """Moves mouse towards element in curved steps to avoid robotic straight-line detection."""
    try:
        element = page.locator(target_selector).first
        box = await element.bounding_box()
        if not box:
            return
        
        target_x = box["x"] + box["width"] / 2 + random.uniform(-10, 10)
        target_y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
        
        # Current mouse pos approximation or random starting offset
        start_x = target_x + random.uniform(-200, 200)
        start_y = target_y + random.uniform(-200, 200)
        
        steps = random.randint(6, 12)
        for i in range(1, steps + 1):
            t = i / steps
            # Quadratic curve
            cur_x = (1 - t) * start_x + t * target_x + math.sin(t * math.pi) * random.uniform(-20, 20)
            cur_y = (1 - t) * start_y + t * target_y + math.cos(t * math.pi) * random.uniform(-15, 15)
            await page.mouse.move(cur_x, cur_y)
            await asyncio.sleep(random.uniform(0.02, 0.05))
            
    except Exception:
        # Fallback if bounding box isn't directly reachable
        pass
