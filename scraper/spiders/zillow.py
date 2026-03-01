import logging
import re

from bs4 import BeautifulSoup

from scraper.spiders.base import BaseSpider
from scraper.spiders.browser import (
    create_stealth_browser,
    create_stealth_page,
    human_delay,
    human_scroll,
)

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
        pw = None
        browser = None
        try:
            pw, browser = await create_stealth_browser()
            page = await create_stealth_page(browser)

            for url in self.SEARCH_URLS:
                try:
                    logger.info("Navigating to %s", url)
                    await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=60_000,
                    )
                    await human_delay(2, 4)
                    await human_scroll(page)
                    await human_delay(1, 2)

                    html = await page.content()
                    results = self.parse_results(html, base_url=self.BASE_URL)
                    all_listings.extend(results)
                    logger.info("Found %d listings at %s", len(results), url)

                    await human_delay(3, 6)
                except Exception as exc:
                    logger.warning("[zillow] Error scraping %s: %s", url, exc)

        except Exception as exc:
            logger.error("[zillow] Browser error: %s", exc)
        finally:
            if browser:
                await browser.close()
            if pw:
                await pw.stop()

        return all_listings
