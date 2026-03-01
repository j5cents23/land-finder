from pathlib import Path

import pytest

from scraper.spiders.zillow import ZillowSpider


@pytest.fixture
def sample_html():
    return Path("tests/fixtures/zillow_sample.html").read_text()


@pytest.mark.asyncio
async def test_parse_listings_from_html(sample_html):
    spider = ZillowSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.zillow.com")
    assert len(listings) == 2
    assert listings[0]["price"] == "$39,900"
    assert listings[0]["address"] == "0 County Road 42, Liberty, NY 12754"
    assert listings[0]["acreage"] == "12 ac lot"


@pytest.mark.asyncio
async def test_parse_second_listing(sample_html):
    spider = ZillowSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.zillow.com")
    assert listings[1]["price"] == "$74,500"
    assert listings[1]["address"] == "Lot 7 Mountain View Rd, Phoenicia, NY 12464"
    assert listings[1]["acreage"] == "6.5 ac lot"


@pytest.mark.asyncio
async def test_parse_listing_has_required_fields(sample_html):
    spider = ZillowSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.zillow.com")
    required = {"source_id", "url", "title", "price"}
    for listing in listings:
        assert required.issubset(listing.keys()), f"Missing keys: {required - listing.keys()}"


@pytest.mark.asyncio
async def test_parse_listing_urls_are_absolute(sample_html):
    spider = ZillowSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.zillow.com")
    for listing in listings:
        assert listing["url"].startswith("https://"), f"URL not absolute: {listing['url']}"


@pytest.mark.asyncio
async def test_parse_listing_source_ids_are_zpids(sample_html):
    spider = ZillowSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.zillow.com")
    assert listings[0]["source_id"] == "2080456321"
    assert listings[1]["source_id"] == "2080456322"


@pytest.mark.asyncio
async def test_title_uses_address(sample_html):
    spider = ZillowSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.zillow.com")
    assert listings[0]["title"] == listings[0]["address"]


@pytest.mark.asyncio
async def test_parse_empty_html():
    spider = ZillowSpider()
    listings = spider.parse_results("<html><body></body></html>", base_url="https://www.zillow.com")
    assert listings == []
