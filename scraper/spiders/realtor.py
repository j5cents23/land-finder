"""Realtor.com spider using HomeHarvest API — no scraping needed."""

import logging
import math

from scraper.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

SQFT_PER_ACRE = 43_560

TARGET_STATES = [
    "Idaho",
    "Colorado",
    "Utah",
    "Montana",
    "Michigan",
    "New Hampshire",
    "Pennsylvania",
    "West Virginia",
    "Wyoming",
]

STATE_ABBREV = {
    "Idaho": "ID",
    "Colorado": "CO",
    "Utah": "UT",
    "Montana": "MT",
    "Michigan": "MI",
    "New Hampshire": "NH",
    "Pennsylvania": "PA",
    "West Virginia": "WV",
    "Wyoming": "WY",
}


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else int(f)
    except (ValueError, TypeError):
        return None


def _safe_str(val) -> str:
    if val is None:
        return ""
    s = str(val)
    return "" if s == "nan" or s == "<NA>" else s


def _lot_sqft_to_acres(lot_sqft) -> str:
    val = _safe_float(lot_sqft)
    if val is None or val <= 0:
        return ""
    return str(round(val / SQFT_PER_ACRE, 2))


def _photos_to_list(primary_photo, alt_photos) -> list[str]:
    photos = []
    p = _safe_str(primary_photo)
    if p:
        photos.append(p)
    alt = _safe_str(alt_photos)
    if alt:
        photos.extend(url.strip() for url in alt.split(",") if url.strip())
    return photos[:10]


def _row_to_raw(row) -> dict:
    price_val = _safe_int(row.get("list_price"))
    lot_sqft = _safe_float(row.get("lot_sqft"))

    return {
        "source_id": _safe_str(row.get("property_id")),
        "url": _safe_str(row.get("property_url")),
        "title": _safe_str(row.get("formatted_address")),
        "description": _safe_str(row.get("text")),
        "price": str(price_val) if price_val is not None else "",
        "acreage": _lot_sqft_to_acres(lot_sqft),
        "address": _safe_str(row.get("full_street_line")),
        "city": _safe_str(row.get("city")),
        "county": _safe_str(row.get("county")),
        "state": _safe_str(row.get("state")),
        "zip_code": _safe_str(row.get("zip_code")),
        "latitude": _safe_float(row.get("latitude")),
        "longitude": _safe_float(row.get("longitude")),
        "image_urls": _photos_to_list(
            row.get("primary_photo"), row.get("alt_photos")
        ),
        "source": "realtor",
    }


class RealtorSpider(BaseSpider):
    name = "realtor"

    async def scrape(self, criteria: dict) -> list[dict]:
        from homeharvest import scrape_property

        all_listings: list[dict] = []

        for state in TARGET_STATES:
            try:
                logger.info("Fetching land listings for %s", state)
                df = scrape_property(
                    location=state,
                    listing_type="for_sale",
                    property_type=["land"],
                )
                count = len(df)
                logger.info("Got %d listings from %s", count, state)

                for _, row in df.iterrows():
                    raw = _row_to_raw(row)
                    if raw["source_id"] and raw["price"]:
                        all_listings.append(raw)

            except Exception as exc:
                logger.warning("Failed to fetch %s: %s", state, exc)

        logger.info("Total realtor listings: %d", len(all_listings))
        return all_listings
