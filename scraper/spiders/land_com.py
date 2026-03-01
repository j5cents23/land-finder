import asyncio
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.spiders.base import BaseSpider

logger = logging.getLogger(__name__)


class LandComSpider(BaseSpider):
    name = "land_com"

    BASE_URL = "https://www.land.com"

    SEARCH_PATHS = [
        "/New-York/Sullivan-County/all-land/for-sale/",
        "/New-York/Ulster-County/all-land/for-sale/",
        "/New-York/Greene-County/all-land/for-sale/",
        "/New-York/Delaware-County/all-land/for-sale/",
        "/New-York/Orange-County/all-land/for-sale/",
    ]

    def _search_url(self, path: str, page: int = 1) -> str:
        return f"{self.BASE_URL}{path}" if page <= 1 else f"{self.BASE_URL}{path}?page={page}"

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
            description = description_el.get_text(strip=True) if description_el else ""

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

        async with self._client() as client:
            for path in self.SEARCH_PATHS:
                try:
                    url = self._search_url(path)
                    response = await client.get(url)
                    response.raise_for_status()
                    results = self.parse_results(response.text, self.BASE_URL)
                    all_listings.extend(results)
                    await asyncio.sleep(self.delay)
                except Exception as exc:
                    logger.warning("[land_com] Error scraping %s: %s", path, exc)

        return all_listings
