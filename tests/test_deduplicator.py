import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from scraper.models import Base, Listing, SourceEnum
from scraper.pipeline.deduplicator import deduplicate


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def make_listing(**overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        source=SourceEnum.CRAIGSLIST,
        source_id="abc",
        url="https://example.com/1",
        title="Land",
        price=5000000,
        acreage=10.0,
        price_per_acre=500000.0,
        address="123 Mountain Rd",
        city="Liberty",
        county="Sullivan",
        state="NY",
        zip_code="12754",
        image_urls=[],
        raw_data={},
        first_seen_at=now,
        last_seen_at=now,
        is_active=True,
        notified=False,
    )
    defaults.update(overrides)
    return Listing(**defaults)


def test_new_listing_is_not_duplicate():
    session = make_session()
    listing = make_listing()
    result = deduplicate(session, listing)
    assert result.is_new is True


def test_same_source_same_id_is_duplicate():
    session = make_session()
    existing = make_listing(source_id="dup1")
    session.add(existing)
    session.commit()

    incoming = make_listing(source_id="dup1")
    result = deduplicate(session, incoming)
    assert result.is_new is False
    assert result.existing_id == existing.id


def test_cross_site_fuzzy_match():
    session = make_session()
    existing = make_listing(
        source=SourceEnum.LANDWATCH,
        source_id="lw1",
        address="123 Mountain Road",
        acreage=10.0,
    )
    session.add(existing)
    session.commit()

    incoming = make_listing(
        source=SourceEnum.CRAIGSLIST,
        source_id="cl1",
        address="123 Mountain Rd",
        acreage=10.2,  # within 5%
    )
    result = deduplicate(session, incoming)
    assert result.is_new is True
    assert result.possible_cross_site_match == existing.id
