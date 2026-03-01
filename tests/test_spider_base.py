import pytest

from scraper.spiders.base import BaseSpider


class FakeSpider(BaseSpider):
    name = "fake"

    async def scrape(self, criteria):
        return [
            {"id": "1", "title": "Lot A", "price": "$10,000", "acres": "5"},
            {"id": "2", "title": "Lot B", "price": "$20,000", "acres": "10"},
        ]


class IncompleteSpider(BaseSpider):
    name = "incomplete"


@pytest.mark.asyncio
async def test_spider_scrape_returns_raw_dicts():
    spider = FakeSpider()
    results = await spider.scrape(criteria={})
    assert len(results) == 2
    assert results[0]["title"] == "Lot A"


def test_spider_has_name():
    spider = FakeSpider()
    assert spider.name == "fake"


def test_incomplete_spider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        IncompleteSpider()
