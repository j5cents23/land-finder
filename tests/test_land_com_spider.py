from pathlib import Path

import pytest

from scraper.spiders.land_com import LandComSpider


@pytest.fixture
def sample_html():
    return Path("tests/fixtures/land_com_sample.html").read_text()


@pytest.mark.asyncio
async def test_parse_listings_from_html(sample_html):
    spider = LandComSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.land.com")
    assert len(listings) == 2
    assert listings[0]["title"] == "20 Acres in Catskill, New York"
    assert listings[0]["price"] == "$89,900"
    assert listings[0]["acreage"] == "20 acres"
    assert listings[0]["county"] == "Greene County"


@pytest.mark.asyncio
async def test_parse_second_listing(sample_html):
    spider = LandComSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.land.com")
    assert listings[1]["title"] == "8 Acres in Saugerties, New York"
    assert listings[1]["price"] == "$55,000"
    assert listings[1]["acreage"] == "8 acres"
    assert listings[1]["county"] == "Ulster County"
    assert listings[1]["state"] == "New York"


@pytest.mark.asyncio
async def test_parse_listing_has_required_fields(sample_html):
    spider = LandComSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.land.com")
    required = {"source_id", "url", "title", "price"}
    for listing in listings:
        assert required.issubset(listing.keys()), f"Missing keys: {required - listing.keys()}"


@pytest.mark.asyncio
async def test_parse_listing_urls_are_absolute(sample_html):
    spider = LandComSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.land.com")
    for listing in listings:
        assert listing["url"].startswith("https://"), f"URL not absolute: {listing['url']}"


@pytest.mark.asyncio
async def test_parse_listing_source_ids(sample_html):
    spider = LandComSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.land.com")
    assert listings[0]["source_id"] == "lc-220145"
    assert listings[1]["source_id"] == "lc-220146"


@pytest.mark.asyncio
async def test_parse_listing_descriptions(sample_html):
    spider = LandComSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.land.com")
    assert "Rolling meadows" in listings[0]["description"]
    assert "mountain views" in listings[1]["description"]


@pytest.mark.asyncio
async def test_parse_empty_html():
    spider = LandComSpider()
    listings = spider.parse_results("<html><body></body></html>", base_url="https://www.land.com")
    assert listings == []
