"""Shared stealth browser helpers for Playwright-based spiders."""

import asyncio
import logging
import random

from playwright.async_api import Browser, Page, Playwright, async_playwright

logger = logging.getLogger("land-finder.browser")


async def create_stealth_browser() -> tuple[Playwright, Browser]:
    """Launch a stealth Chromium browser.

    Returns a ``(playwright, browser)`` pair.  The caller is responsible
    for calling ``browser.close()`` and ``pw.stop()`` when finished.
    """
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ],
    )
    return pw, browser


async def create_stealth_page(browser: Browser) -> Page:
    """Create a new page with stealth patches applied."""
    from playwright_stealth import stealth_async

    context = await browser.new_context(
        viewport={
            "width": random.randint(1200, 1920),
            "height": random.randint(800, 1080),
        },
        user_agent=random.choice([
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36",
        ]),
        locale="en-US",
        timezone_id="America/Denver",
        geolocation=None,
        permissions=[],
    )
    page = await context.new_page()
    await stealth_async(page)
    return page


async def human_scroll(page: Page, scrolls: int = 3) -> None:
    """Simulate human-like scrolling."""
    for _ in range(scrolls):
        await page.evaluate("window.scrollBy(0, window.innerHeight * 0.7)")
        await asyncio.sleep(random.uniform(0.8, 2.0))


async def human_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Random delay to appear human."""
    await asyncio.sleep(random.uniform(min_s, max_s))
