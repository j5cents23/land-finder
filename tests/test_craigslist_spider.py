from pathlib import Path

import pytest

from scraper.spiders.craigslist import CraigslistSpider


@pytest.fixture
def sample_html():
    return Path("tests/fixtures/craigslist_sample.html").read_text()


@pytest.mark.asyncio
async def test_parse_listings_from_html(sample_html):
    spider = CraigslistSpider()
    listings = spider.parse_results(sample_html, base_url="https://newyork.craigslist.org")
    assert len(listings) == 2
    assert listings[0]["title"] == "10 Acres Sullivan County - $45,000"
    assert listings[0]["price"] == "$45,000"


@pytest.mark.asyncio
async def test_parse_listing_has_required_fields(sample_html):
    spider = CraigslistSpider()
    listings = spider.parse_results(sample_html, base_url="https://newyork.craigslist.org")
    required = {"source_id", "url", "title", "price"}
    for listing in listings:
        assert required.issubset(listing.keys()), f"Missing keys: {required - listing.keys()}"
