import uuid
from datetime import datetime, timezone

from scraper.models import Listing, SearchCriteria, SourceEnum
from scraper.pipeline.filter import matches_criteria, haversine_miles


def make_listing(**overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        source=SourceEnum.CRAIGSLIST,
        source_id="test1",
        url="https://example.com",
        title="Test",
        price=5000000,
        acreage=10.0,
        price_per_acre=500000.0,
        address="123 Rd",
        city="Liberty",
        county="Sullivan",
        state="NY",
        zip_code="12754",
        latitude=41.8,
        longitude=-74.7,
        image_urls=[],
        raw_data={},
        first_seen_at=now,
        last_seen_at=now,
        is_active=True,
        notified=False,
    )
    defaults.update(overrides)
    return Listing(**defaults)


def make_criteria(**overrides):
    defaults = dict(
        id=uuid.uuid4(),
        name="Test",
        min_acreage=None,
        max_price=None,
        max_ppa=None,
        states=[],
        counties=[],
        center_lat=None,
        center_lng=None,
        radius_miles=None,
        require_water=False,
        require_utils=False,
        require_road=False,
        zoning_types=[],
        is_active=True,
    )
    defaults.update(overrides)
    return SearchCriteria(**defaults)


def test_empty_criteria_matches_everything():
    listing = make_listing()
    criteria = make_criteria()
    assert matches_criteria(listing, criteria) is True


def test_min_acreage_filters():
    listing = make_listing(acreage=3.0)
    criteria = make_criteria(min_acreage=5.0)
    assert matches_criteria(listing, criteria) is False


def test_max_price_filters():
    listing = make_listing(price=20000000)
    criteria = make_criteria(max_price=10000000)
    assert matches_criteria(listing, criteria) is False


def test_max_ppa_filters():
    listing = make_listing(price_per_acre=300000.0)
    criteria = make_criteria(max_ppa=200000.0)
    assert matches_criteria(listing, criteria) is False


def test_state_filter():
    listing = make_listing(state="NJ")
    criteria = make_criteria(states=["NY", "PA"])
    assert matches_criteria(listing, criteria) is False


def test_county_filter():
    listing = make_listing(county="Sullivan")
    criteria = make_criteria(counties=["Ulster", "Greene"])
    assert matches_criteria(listing, criteria) is False


def test_require_water_filters():
    listing = make_listing(has_water=None)
    criteria = make_criteria(require_water=True)
    assert matches_criteria(listing, criteria) is False


def test_radius_filter():
    listing = make_listing(latitude=42.5, longitude=-75.0)
    criteria = make_criteria(center_lat=35.0, center_lng=-80.0, radius_miles=50.0)
    assert matches_criteria(listing, criteria) is False


def test_radius_filter_passes():
    listing = make_listing(latitude=41.8, longitude=-74.7)
    criteria = make_criteria(center_lat=41.85, center_lng=-74.65, radius_miles=10.0)
    assert matches_criteria(listing, criteria) is True


def test_haversine_known_distance():
    d = haversine_miles(40.7128, -74.0060, 34.0522, -118.2437)
    assert 2440 < d < 2460
