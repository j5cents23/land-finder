import uuid

from scraper.models import ListingScore
from scraper.pipeline.enricher import (
    _find_nearest_ski,
    _get_county_data,
    _haversine_miles,
    compute_match_score,
)


def make_score(**overrides) -> ListingScore:
    """Build a ListingScore with sensible defaults for a near-perfect match."""
    defaults = dict(
        listing_id=uuid.uuid4(),
        nearest_hospital_miles=15.0,
        nearest_hospital_name="General Hospital",
        nearest_bigbox_miles=20.0,
        nearest_bigbox_name="Walmart",
        nearest_water_miles=0.5,
        nearest_water_type="river",
        nearest_trail_miles=3.0,
        nearest_trail_name="Mountain Trail",
        nearest_offroad_miles=10.0,
        nearest_ski_resort_miles=45.0,
        nearest_ski_resort_name="Bogus Basin",
        nearest_school_miles=5.0,
        nearest_school_name="Local Elementary",
        school_district_rating="Above Average",
        county_political_lean="R+20",
        county_property_tax_rate=0.65,
        county_mil_discount=True,
        county_population=150000,
        county_pop_growth_pct=15.0,
        county_median_age=34.0,
        avg_annual_snowfall_inches=35.0,
        avg_sunny_days=206,
        match_score=None,
        enriched_at=None,
    )
    merged = {**defaults, **overrides}
    return ListingScore(**merged)


def test_perfect_score():
    score = make_score()
    result = compute_match_score(score, acreage=4.0, price=15000000)
    assert result >= 90  # Should be near-perfect


def test_bad_location_low_score():
    score = make_score(
        nearest_hospital_miles=100.0,
        nearest_bigbox_miles=100.0,
        nearest_water_miles=20.0,
        nearest_trail_miles=50.0,
        county_political_lean="D+20",
        county_property_tax_rate=2.5,
        county_mil_discount=False,
        county_pop_growth_pct=-5.0,
        county_median_age=55.0,
        avg_annual_snowfall_inches=5.0,
        avg_sunny_days=120,
    )
    result = compute_match_score(score, acreage=4.0, price=15000000)
    assert result < 40


def test_mid_range_score():
    score = make_score(
        nearest_hospital_miles=30.0,
        nearest_bigbox_miles=40.0,
        nearest_water_miles=4.0,
        nearest_trail_miles=12.0,
        nearest_offroad_miles=25.0,
        nearest_ski_resort_miles=100.0,
        county_political_lean="R+5",
        county_property_tax_rate=1.0,
        county_mil_discount=True,
        county_pop_growth_pct=7.0,
        county_median_age=39.0,
        avg_annual_snowfall_inches=25.0,
        avg_sunny_days=180,
    )
    result = compute_match_score(score, acreage=4.0, price=15000000)
    assert 40 <= result <= 80


def test_score_with_no_data():
    score = make_score(
        nearest_hospital_miles=None,
        nearest_hospital_name=None,
        nearest_bigbox_miles=None,
        nearest_bigbox_name=None,
        nearest_water_miles=None,
        nearest_water_type=None,
        nearest_trail_miles=None,
        nearest_trail_name=None,
        nearest_offroad_miles=None,
        nearest_ski_resort_miles=None,
        nearest_ski_resort_name=None,
        nearest_school_miles=None,
        nearest_school_name=None,
        school_district_rating=None,
        county_political_lean=None,
        county_property_tax_rate=None,
        county_mil_discount=None,
        county_population=None,
        county_pop_growth_pct=None,
        county_median_age=None,
        avg_annual_snowfall_inches=None,
        avg_sunny_days=None,
    )
    result = compute_match_score(score, acreage=4.0, price=15000000)
    # Only acreage + price points should score
    assert result > 0
    assert result < 30


def test_find_nearest_ski_returns_result():
    result = _find_nearest_ski(43.6, -116.2)  # Near Boise
    assert result is not None
    assert result["name"] == "Bogus Basin"
    assert result["distance_miles"] < 20


def test_find_nearest_ski_utah():
    result = _find_nearest_ski(40.6, -111.55)  # Near Park City area
    assert result is not None
    assert result["name"] in ("Park City", "Brighton", "Snowbird")
    assert result["distance_miles"] < 15


def test_get_county_data_found():
    data = _get_county_data("ID", "Ada")
    assert data is not None
    assert data["lean"] == "R+8"
    assert data["pop"] == 510000
    assert data["tax"] == 0.69


def test_get_county_data_not_found():
    data = _get_county_data("XX", "Nowhere")
    assert data is None


def test_haversine_known_distance():
    # Boise, ID to Salt Lake City, UT is roughly 290 miles
    dist = _haversine_miles(43.615, -116.202, 40.760, -111.891)
    assert 280 < dist < 310


def test_haversine_same_point():
    dist = _haversine_miles(43.0, -116.0, 43.0, -116.0)
    assert dist == 0.0


def test_acreage_outside_ideal_range():
    score = make_score()
    # 15 acres is outside both ideal ranges
    result_big = compute_match_score(score, acreage=15.0, price=15000000)
    result_ideal = compute_match_score(score, acreage=4.0, price=15000000)
    assert result_ideal > result_big


def test_price_over_budget():
    score = make_score()
    result_expensive = compute_match_score(score, acreage=4.0, price=50000000)
    result_cheap = compute_match_score(score, acreage=4.0, price=15000000)
    assert result_cheap > result_expensive


def test_good_schools_boost_score():
    score_good = make_score(school_district_rating="Good")
    score_bad = make_score(school_district_rating="Below Average")
    score_none = make_score(school_district_rating=None)
    result_good = compute_match_score(score_good, acreage=4.0, price=15000000)
    result_bad = compute_match_score(score_bad, acreage=4.0, price=15000000)
    result_none = compute_match_score(score_none, acreage=4.0, price=15000000)
    assert result_good > result_bad
    assert result_good > result_none


def test_average_schools_partial_score():
    score_avg = make_score(school_district_rating="Average")
    score_above = make_score(school_district_rating="Above Average")
    result_avg = compute_match_score(score_avg, acreage=4.0, price=15000000)
    result_above = compute_match_score(score_above, acreage=4.0, price=15000000)
    assert result_above > result_avg


def test_county_data_has_schools():
    data = _get_county_data("ID", "Ada")
    assert data is not None
    assert data["schools"] == "Above Average"
    data_co = _get_county_data("CO", "El Paso")
    assert data_co is not None
    assert data_co["schools"] == "Good"
