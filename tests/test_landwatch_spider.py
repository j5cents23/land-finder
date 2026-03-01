from pathlib import Path

import pytest

from scraper.spiders.landwatch import LandWatchSpider


@pytest.fixture
def sample_html():
    return Path("tests/fixtures/landwatch_sample.html").read_text()


@pytest.mark.asyncio
async def test_parse_listings_from_html(sample_html):
    spider = LandWatchSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.landwatch.com")
    assert len(listings) == 2
    assert listings[0]["title"] == "10 Acres in Sullivan County"
    assert listings[0]["price"] == "$65,000"
    assert listings[0]["acreage"] == "10 acres"
    assert listings[0]["location"] == "Liberty, Sullivan County, NY"


@pytest.mark.asyncio
async def test_parse_second_listing(sample_html):
    spider = LandWatchSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.landwatch.com")
    assert listings[1]["title"] == "5 Acre Wooded Lot Near Catskills"
    assert listings[1]["price"] == "$42,500"
    assert listings[1]["acreage"] == "5 acres"
    assert listings[1]["location"] == "Ellenville, Ulster County, NY"


@pytest.mark.asyncio
async def test_parse_listing_has_required_fields(sample_html):
    spider = LandWatchSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.landwatch.com")
    required = {"source_id", "url", "title", "price"}
    for listing in listings:
        assert required.issubset(listing.keys()), f"Missing keys: {required - listing.keys()}"


@pytest.mark.asyncio
async def test_parse_listing_urls_are_absolute(sample_html):
    spider = LandWatchSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.landwatch.com")
    for listing in listings:
        assert listing["url"].startswith("https://"), f"URL not absolute: {listing['url']}"


@pytest.mark.asyncio
async def test_parse_listing_source_ids(sample_html):
    spider = LandWatchSpider()
    listings = spider.parse_results(sample_html, base_url="https://www.landwatch.com")
    assert listings[0]["source_id"] == "lw-884201"
    assert listings[1]["source_id"] == "lw-884202"


@pytest.mark.asyncio
async def test_parse_empty_html():
    spider = LandWatchSpider()
    listings = spider.parse_results("<html><body></body></html>", base_url="https://www.landwatch.com")
    assert listings == []
