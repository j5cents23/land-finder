import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from scraper.models import Base, Listing, SearchCriteria, SourceEnum


def make_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_create_listing():
    engine = make_engine()
    with Session(engine) as session:
        listing = Listing(
            id=uuid.uuid4(),
            source=SourceEnum.CRAIGSLIST,
            source_id="abc123",
            url="https://example.com/listing/abc123",
            title="10 Acres in Sullivan County",
            price=4500000,
            acreage=10.0,
            price_per_acre=450000.0,
            address="123 Mountain Rd",
            city="Liberty",
            county="Sullivan",
            state="NY",
            zip_code="12754",
            image_urls=[],
            raw_data={"original": "data"},
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
            is_active=True,
            notified=False,
        )
        session.add(listing)
        session.commit()

        result = session.get(Listing, listing.id)
        assert result is not None
        assert result.source == SourceEnum.CRAIGSLIST
        assert result.price == 4500000
        assert result.acreage == 10.0


def test_listing_unique_constraint():
    engine = make_engine()
    with Session(engine) as session:
        now = datetime.now(timezone.utc)
        base = dict(
            url="https://example.com/1",
            title="Land",
            price=100000,
            acreage=5.0,
            price_per_acre=20000.0,
            address="123 Rd",
            city="Town",
            county="County",
            state="NY",
            zip_code="12345",
            image_urls=[],
            raw_data={},
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            notified=False,
        )
        session.add(Listing(id=uuid.uuid4(), source=SourceEnum.ZILLOW, source_id="dup1", **base))
        session.commit()

        session.add(Listing(id=uuid.uuid4(), source=SourceEnum.ZILLOW, source_id="dup1", **base))
        try:
            session.commit()
            assert False, "Should have raised IntegrityError"
        except Exception:
            session.rollback()


def test_create_search_criteria():
    engine = make_engine()
    with Session(engine) as session:
        criteria = SearchCriteria(
            id=uuid.uuid4(),
            name="Upstate NY Deals",
            min_acreage=5.0,
            max_price=10000000,
            max_ppa=200000.0,
            states=["NY"],
            counties=["Sullivan", "Ulster"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        )
        session.add(criteria)
        session.commit()

        result = session.get(SearchCriteria, criteria.id)
        assert result is not None
        assert result.name == "Upstate NY Deals"
        assert result.states == ["NY"]
