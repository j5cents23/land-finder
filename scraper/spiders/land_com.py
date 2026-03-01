import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.spiders.base import BaseSpider
from scraper.spiders.browser import (
    create_stealth_browser,
    create_stealth_page,
    human_delay,
    human_scroll,
)

logger = logging.getLogger(__name__)


class LandComSpider(BaseSpider):
    name = "land_com"

    BASE_URL = "https://www.land.com"

    SEARCH_PATHS = [
        # Idaho
        "/Idaho/all-land/for-sale/",
        # Colorado
        "/Colorado/all-land/for-sale/",
        # Utah
        "/Utah/all-land/for-sale/",
        # Montana
        "/Montana/all-land/for-sale/",
        # Michigan
        "/Michigan/all-land/for-sale/",
        # New Hampshire
        "/New-Hampshire/all-land/for-sale/",
        # Pennsylvania
        "/Pennsylvania/all-land/for-sale/",
        # West Virginia
        "/West-Virginia/all-land/for-sale/",
        # Wyoming
        "/Wyoming/all-land/for-sale/",
    ]

    def _search_url(self, path: str, page: int = 1) -> str:
        if page <= 1:
            return f"{self.BASE_URL}{path}"
        return f"{self.BASE_URL}{path}?page={page}"

    def parse_results(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[dict] = []

        for card in soup.select(".listing-card"):
            link = card.select_one(".listing-card__link")
            if not link:
                continue

            href = link.get("href", "")
            source_id = card.get("data-id", href)

            title_el = card.select_one(".listing-card__title")
            title = title_el.get_text(strip=True) if title_el else ""

            price_el = card.select_one(".listing-card__price")
            price = price_el.get_text(strip=True) if price_el else ""

            acres_el = card.select_one(".listing-card__acres")
            acreage = acres_el.get_text(strip=True) if acres_el else ""

            county_el = card.select_one(".listing-card__county")
            county = county_el.get_text(strip=True) if county_el else ""

            state_el = card.select_one(".listing-card__state")
            state = state_el.get_text(strip=True) if state_el else ""

            description_el = card.select_one(".listing-card__description")
            description = (
                description_el.get_text(strip=True) if description_el else ""
            )

            listings.append({
                "source_id": source_id,
                "url": urljoin(base_url, href),
                "title": title,
                "price": price,
                "acreage": acreage,
                "county": county,
                "state": state,
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

            for path in self.SEARCH_PATHS:
                url = self._search_url(path)
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
                    logger.warning("[land_com] Error scraping %s: %s", url, exc)

        except Exception as exc:
            logger.error("[land_com] Browser error: %s", exc)
        finally:
            if browser:
                await browser.close()
            if pw:
                await pw.stop()

        return all_listings
