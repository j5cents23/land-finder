import math

from scraper.models import Listing, SearchCriteria


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def matches_criteria(listing: Listing, criteria: SearchCriteria) -> bool:
    """Check whether a listing satisfies all active search criteria filters.

    Returns True if the listing passes every non-None criterion,
    False as soon as any criterion rejects it.
    """
    if criteria.min_acreage is not None and listing.acreage < criteria.min_acreage:
        return False
    if criteria.max_price is not None and listing.price > criteria.max_price:
        return False
    if criteria.max_ppa is not None and listing.price_per_acre > criteria.max_ppa:
        return False
    if criteria.states and listing.state not in criteria.states:
        return False
    if criteria.counties and listing.county not in criteria.counties:
        return False
    if criteria.require_water and listing.has_water is not True:
        return False
    if criteria.require_utils and listing.has_utilities is not True:
        return False
    if criteria.require_road and listing.has_road_access is not True:
        return False
    if criteria.zoning_types and listing.zoning not in criteria.zoning_types:
        return False
    if (
        criteria.center_lat is not None
        and criteria.center_lng is not None
        and criteria.radius_miles is not None
    ):
        if listing.latitude is None or listing.longitude is None:
            return False
        dist = haversine_miles(
            criteria.center_lat, criteria.center_lng,
            listing.latitude, listing.longitude,
        )
        if dist > criteria.radius_miles:
            return False
    return True
