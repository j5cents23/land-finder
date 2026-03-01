import asyncio
import logging
import random
import re

from bs4 import BeautifulSoup

from scraper.spiders.base import BaseSpider

logger = logging.getLogger(__name__)


class ZillowSpider(BaseSpider):
    name = "zillow"

    BASE_URL = "https://www.zillow.com"

    SEARCH_URLS = [
        # Idaho
        "https://www.zillow.com/id/land/",
        # Colorado
        "https://www.zillow.com/co/land/",
        # Utah
        "https://www.zillow.com/ut/land/",
        # Montana
        "https://www.zillow.com/mt/land/",
        # Michigan
        "https://www.zillow.com/mi/land/",
        # New Hampshire
        "https://www.zillow.com/nh/land/",
        # Pennsylvania
        "https://www.zillow.com/pa/land/",
        # West Virginia
        "https://www.zillow.com/wv/land/",
        # Wyoming
        "https://www.zillow.com/wy/land/",
    ]

    def parse_results(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[dict] = []

        for card in soup.select("article.list-card"):
            link = card.select_one("a.list-card-link")
            if not link:
                continue

            href = link.get("href", "")
            card_id = card.get("id", "")
            zpid_match = re.search(r"zpid_(\d+)", card_id)
            source_id = zpid_match.group(1) if zpid_match else href

            price_el = card.select_one(".list-card-price")
            price = price_el.get_text(strip=True) if price_el else ""

            acres_el = card.select_one(".list-card-acres")
            acreage = acres_el.get_text(strip=True) if acres_el else ""

            addr_el = card.select_one(".list-card-addr")
            address = addr_el.get_text(strip=True) if addr_el else ""

            url = href if href.startswith("http") else f"{base_url}{href}"

            listings.append({
                "source_id": source_id,
                "url": url,
                "title": address,
                "price": price,
                "acreage": acreage,
                "address": address,
            })

        return listings

    async def scrape(self, criteria: dict) -> list[dict]:
        all_listings: list[dict] = []

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("[zillow] playwright is not installed")
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
                    await asyncio.sleep(random.uniform(1.5, 3.0))

                    # Simulate human scrolling
                    await page.evaluate("window.scrollBy(0, 300)")
                    await asyncio.sleep(random.uniform(0.5, 1.0))

                    html = await page.content()
                    results = self.parse_results(html, self.BASE_URL)
                    all_listings.extend(results)
                    await page.close()
                    await asyncio.sleep(self.delay + random.uniform(0, 2.0))
                except Exception as exc:
                    logger.warning("[zillow] Error scraping %s: %s", search_url, exc)

            await browser.close()

        return all_listings
