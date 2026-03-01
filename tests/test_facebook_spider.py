from pathlib import Path

import pytest

from scraper.spiders.facebook import FacebookSpider


@pytest.fixture
def sample_html():
    return Path("tests/fixtures/facebook_sample.html").read_text()


@pytest.mark.asyncio
async def test_parse_listings_from_html(sample_html):
    spider = FacebookSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.facebook.com")
    assert len(listings) == 2
    assert listings[0]["title"] == "15 Acres - Vacant Land Sullivan County NY"
    assert listings[0]["price"] == "$52,000"
    assert listings[0]["location"] == "Liberty, NY"


@pytest.mark.asyncio
async def test_parse_second_listing(sample_html):
    spider = FacebookSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.facebook.com")
    assert listings[1]["title"] == "3 Acres Wooded Lot - Catskills Area"
    assert listings[1]["price"] == "$25,000"
    assert listings[1]["location"] == "Saugerties, NY"


@pytest.mark.asyncio
async def test_parse_listing_has_required_fields(sample_html):
    spider = FacebookSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.facebook.com")
    required = {"source_id", "url", "title", "price"}
    for listing in listings:
        assert required.issubset(listing.keys()), f"Missing keys: {required - listing.keys()}"


@pytest.mark.asyncio
async def test_parse_listing_urls_are_absolute(sample_html):
    spider = FacebookSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.facebook.com")
    for listing in listings:
        assert listing["url"].startswith("https://"), f"URL not absolute: {listing['url']}"


@pytest.mark.asyncio
async def test_parse_listing_source_ids(sample_html):
    spider = FacebookSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.facebook.com")
    assert listings[0]["source_id"] == "fb-mp-901234567"
    assert listings[1]["source_id"] == "fb-mp-901234568"


@pytest.mark.asyncio
async def test_parse_listing_descriptions(sample_html):
    spider = FacebookSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.facebook.com")
    assert "road frontage" in listings[0]["description"]
    assert "Perc tested" in listings[1]["description"]


@pytest.mark.asyncio
async def test_parse_empty_html():
    spider = FacebookSpider()
    listings = spider.parse_results("<html><body></body></html>", base_url="https://www.facebook.com")
    assert listings == []
