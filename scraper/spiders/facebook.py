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


class FacebookSpider(BaseSpider):
    name = "facebook"

    BASE_URL = "https://www.facebook.com"

    SEARCH_URLS = [
        # Idaho
        "https://www.facebook.com/marketplace/boise/search?query=land%20acres%20idaho&exact=false",
        # Colorado
        "https://www.facebook.com/marketplace/denver/search?query=land%20acres%20colorado&exact=false",
        "https://www.facebook.com/marketplace/108675895830498/search?query=land%20acres%20colorado%20springs&exact=false",
        # Utah
        "https://www.facebook.com/marketplace/saltlakecity/search?query=land%20acres%20utah&exact=false",
        # Montana
        "https://www.facebook.com/marketplace/billings/search?query=land%20acres%20montana&exact=false",
        "https://www.facebook.com/marketplace/bozeman/search?query=land%20acres%20montana&exact=false",
        # Michigan
        "https://www.facebook.com/marketplace/grandrapids/search?query=land%20acres%20michigan&exact=false",
        # New Hampshire
        "https://www.facebook.com/marketplace/manchester-nh/search?query=land%20acres%20new%20hampshire&exact=false",
        # Pennsylvania
        "https://www.facebook.com/marketplace/scranton/search?query=land%20acres%20poconos&exact=false",
        # West Virginia
        "https://www.facebook.com/marketplace/charleston-wv/search?query=land%20acres%20west%20virginia&exact=false",
        # Wyoming
        "https://www.facebook.com/marketplace/casper/search?query=land%20acres%20wyoming&exact=false",
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
            description = (
                description_el.get_text(strip=True) if description_el else ""
            )

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

                    # Check if Facebook redirected to login
                    current_url = page.url
                    if "/login" in current_url or "login.php" in current_url:
                        logger.warning(
                            "[facebook] Redirected to login page. "
                            "Facebook Marketplace requires authentication. "
                            "Skipping remaining URLs."
                        )
                        break

                    await human_scroll(page)
                    await human_delay(1, 2)

                    html = await page.content()
                    results = self.parse_results(html, base_url=self.BASE_URL)
                    all_listings.extend(results)
                    logger.info(
                        "Found %d listings at %s", len(results), url
                    )

                    await human_delay(3, 6)
                except Exception as exc:
                    logger.warning("[facebook] Error scraping %s: %s", url, exc)

        except Exception as exc:
            logger.error("[facebook] Browser error: %s", exc)
        finally:
            if browser:
                await browser.close()
            if pw:
                await pw.stop()

        return all_listings
