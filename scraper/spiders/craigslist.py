import asyncio
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.spiders.base import BaseSpider


class CraigslistSpider(BaseSpider):
    name = "craigslist"

    REGIONS = [
        "newyork",
        "hudsonvalley",
        "catskills",
        "albany",
        "potsdam",
    ]

    def _search_url(self, region: str, offset: int = 0) -> str:
        return (
            f"https://{region}.craigslist.org/search/rea"
            f"?query=land+acres&s={offset}"
        )

    def parse_results(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[dict] = []

        for result in soup.select(".cl-search-result"):
            link = result.select_one("a.posting-title")
            if not link:
                continue

            href = link.get("href", "")
            source_id_match = re.search(r"/(\d+)\.html", href)
            source_id = source_id_match.group(1) if source_id_match else href

            title_el = link.select_one(".label")
            title = title_el.get_text(strip=True) if title_el else ""

            price_el = result.select_one(".priceinfo")
            price = price_el.get_text(strip=True) if price_el else ""

            hood_el = result.select_one(".posting-hood")
            hood = hood_el.get_text(strip=True).strip("() ") if hood_el else ""

            listings.append({
                "source_id": source_id,
                "url": urljoin(base_url, href),
                "title": title,
                "price": price,
                "hood": hood,
            })

        return listings

    async def scrape(self, criteria: dict) -> list[dict]:
        all_listings: list[dict] = []

        async with self._client() as client:
            for region in self.REGIONS:
                try:
                    url = self._search_url(region)
                    response = await client.get(url)
                    response.raise_for_status()
                    base_url = f"https://{region}.craigslist.org"
                    results = self.parse_results(response.text, base_url)
                    all_listings.extend(results)
                    await asyncio.sleep(self.delay)
                except Exception as exc:
                    self._log_error(region, exc)

        return all_listings

    @staticmethod
    def _log_error(region: str, exc: Exception) -> None:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning("[craigslist] Error scraping %s: %s", region, exc)
