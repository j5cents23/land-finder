import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from scraper.models import Base, Listing, SearchCriteria
from scraper.pipeline.orchestrator import run_pipeline


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine), engine


def make_criteria(session):
    c = SearchCriteria(
        id=uuid.uuid4(),
        name="Test",
        min_acreage=5.0,
        max_price=10000000,
        states=["NY"],
        counties=[],
        require_water=False,
        require_utils=False,
        require_road=False,
        zoning_types=[],
        is_active=True,
    )
    session.add(c)
    session.commit()
    return c


@pytest.mark.asyncio
async def test_pipeline_stores_new_listing():
    session, engine = make_session()
    make_criteria(session)

    raw_results = [
        {
            "source": "craigslist",
            "source_id": "123",
            "url": "https://example.com/123",
            "title": "10 Acres Sullivan County",
            "price": "$50,000",
            "acreage": "10",
            "address": "123 Mountain Rd",
            "city": "Liberty",
            "county": "Sullivan",
            "state": "NY",
            "zip_code": "12754",
            "description": "Well water, electric available, paved road",
        },
    ]

    new_listings = await run_pipeline(session, raw_results)
    assert len(new_listings) == 1
    assert session.query(Listing).count() == 1

    stored = session.query(Listing).first()
    assert stored.price == 5000000
    assert stored.acreage == 10.0
    assert stored.has_water is True


@pytest.mark.asyncio
async def test_pipeline_skips_duplicate():
    session, engine = make_session()
    make_criteria(session)

    raw = {
        "source": "craigslist",
        "source_id": "123",
        "url": "https://example.com/123",
        "title": "Land",
        "price": "$50,000",
        "acreage": "10",
        "address": "123 Rd",
        "city": "Liberty",
        "county": "Sullivan",
        "state": "NY",
        "zip_code": "12754",
        "description": "",
    }

    await run_pipeline(session, [raw])
    result = await run_pipeline(session, [raw])
    assert len(result) == 0
    assert session.query(Listing).count() == 1
