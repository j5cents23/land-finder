"""Pipeline orchestrator that wires normalize, dedupe, filter, and store."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from scraper.models import Listing, SearchCriteria, SourceEnum
from scraper.pipeline.deduplicator import deduplicate
from scraper.pipeline.filter import matches_criteria
from scraper.pipeline.normalizer import detect_features, parse_acreage, parse_price


def _raw_to_listing(raw: dict) -> Listing | None:
    """Convert a raw result dict into a Listing model instance.

    Returns None when price or acreage cannot be parsed, acreage is zero,
    or the source string is not a valid SourceEnum value.
    """
    price = parse_price(raw.get("price", ""))
    acreage = parse_acreage(raw.get("acreage", ""))
    if price is None or acreage is None or acreage == 0:
        return None

    features = detect_features(raw.get("description", ""))
    now = datetime.now(timezone.utc)

    source_str = raw.get("source", "craigslist")
    try:
        source = SourceEnum(source_str)
    except ValueError:
        return None

    return Listing(
        id=uuid.uuid4(),
        source=source,
        source_id=raw.get("source_id", ""),
        url=raw.get("url", ""),
        title=raw.get("title", ""),
        description=raw.get("description"),
        price=price,
        acreage=acreage,
        price_per_acre=price / acreage if acreage else 0,
        address=raw.get("address", ""),
        city=raw.get("city", ""),
        county=raw.get("county", ""),
        state=raw.get("state", ""),
        zip_code=raw.get("zip_code", ""),
        latitude=raw.get("latitude"),
        longitude=raw.get("longitude"),
        zoning=raw.get("zoning"),
        has_water=features["has_water"],
        has_utilities=features["has_utilities"],
        has_road_access=features["has_road_access"],
        image_urls=raw.get("image_urls", []),
        raw_data=raw,
        first_seen_at=now,
        last_seen_at=now,
        is_active=True,
        notified=False,
    )


async def run_pipeline(session: Session, raw_results: list[dict]) -> list[Listing]:
    """Process raw scraper results through the full pipeline.

    For each raw dict:
      1. Normalize into a Listing object
      2. Deduplicate against existing listings
      3. Filter against active search criteria
      4. Store matches in the database

    Returns the list of newly stored Listing objects.
    """
    new_listings: list[Listing] = []

    all_criteria = (
        session.query(SearchCriteria)
        .filter(SearchCriteria.is_active == True)  # noqa: E712
        .all()
    )

    for raw in raw_results:
        listing = _raw_to_listing(raw)
        if listing is None:
            continue

        result = deduplicate(session, listing)
        if not result.is_new:
            continue

        matched = not all_criteria or any(
            matches_criteria(listing, c) for c in all_criteria
        )
        if not matched:
            continue

        session.add(listing)
        session.flush()
        new_listings.append(listing)

    session.commit()
    return new_listings
