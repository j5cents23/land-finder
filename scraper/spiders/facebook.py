import asyncio
import logging
import random
import re

from bs4 import BeautifulSoup

from scraper.spiders.base import BaseSpider

logger = logging.getLogger(__name__)


class FacebookSpider(BaseSpider):
    name = "facebook"

    BASE_URL = "https://www.facebook.com"

    SEARCH_URLS = [
        "https://www.facebook.com/marketplace/nyc/search?query=land%20acres%20sullivan%20county&exact=false",
        "https://www.facebook.com/marketplace/nyc/search?query=land%20acres%20ulster%20county&exact=false",
        "https://www.facebook.com/marketplace/nyc/search?query=land%20acres%20catskills&exact=false",
        "https://www.facebook.com/marketplace/nyc/search?query=vacant%20land%20upstate%20ny&exact=false",
    ]

    def parse_results(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[dict] = []

        for card in soup.select("[data-testid='marketplace-listing-card']"):
            link = card.select_one("a.listing-link")
            if not link:
                continue

            href = link.get("href", "")
            source_id = card.get("data-listing-id", "")
            if not source_id:
                item_match = re.search(r"/item/(\d+)", href)
                source_id = item_match.group(1) if item_match else href

            title_el = card.select_one("[data-testid='listing-title']")
            title = title_el.get_text(strip=True) if title_el else ""

            price_el = card.select_one("[data-testid='listing-price']")
            price = price_el.get_text(strip=True) if price_el else ""

            location_el = card.select_one("[data-testid='listing-location']")
            location = location_el.get_text(strip=True) if location_el else ""

            description_el = card.select_one(".listing-description")
            description = description_el.get_text(strip=True) if description_el else ""

            url = href if href.startswith("http") else f"{base_url}{href}"

            listings.append({
                "source_id": source_id,
                "url": url,
                "title": title,
                "price": price,
                "location": location,
                "description": description,
            })

        return listings

    async def scrape(self, criteria: dict) -> list[dict]:
        all_listings: list[dict] = []

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("[facebook] playwright is not installed")
            return all_listings

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )

            for search_url in self.SEARCH_URLS:
                try:
                    page = await context.new_page()
                    await page.goto(search_url, wait_until="networkidle")
                    await asyncio.sleep(random.uniform(2.0, 4.0))

                    # Simulate human scrolling to trigger lazy-load
                    for _ in range(3):
                        await page.evaluate("window.scrollBy(0, 400)")
                        await asyncio.sleep(random.uniform(0.8, 1.5))

                    html = await page.content()
                    results = self.parse_results(html, self.BASE_URL)
                    all_listings.extend(results)
                    await page.close()
                    await asyncio.sleep(self.delay + random.uniform(1.0, 3.0))
                except Exception as exc:
                    logger.warning("[facebook] Error scraping %s: %s", search_url, exc)

            await browser.close()

        return all_listings
