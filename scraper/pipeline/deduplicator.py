import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from scraper.models import Listing


@dataclass(frozen=True)
class DedupeResult:
    is_new: bool
    existing_id: uuid.UUID | None = None
    possible_cross_site_match: uuid.UUID | None = None


def _normalize_address(address: str) -> str:
    """Normalize an address for fuzzy comparison.

    Lowercases, strips whitespace, and replaces full street-type
    words with standard abbreviations.
    """
    addr = address.lower().strip()
    replacements = {
        "road": "rd",
        "street": "st",
        "avenue": "ave",
        "drive": "dr",
        "lane": "ln",
        "court": "ct",
        "boulevard": "blvd",
        "place": "pl",
    }
    for full, abbr in replacements.items():
        addr = re.sub(rf"\b{full}\b", abbr, addr)
    return re.sub(r"\s+", " ", addr)


def _acreage_within_tolerance(
    a: float, b: float, tolerance: float = 0.05
) -> bool:
    """Return True if two acreage values are within the given tolerance."""
    if a == 0 or b == 0:
        return False
    return abs(a - b) / max(a, b) <= tolerance


def deduplicate(session: Session, listing: Listing) -> DedupeResult:
    """Check whether a listing is a duplicate.

    Performs two checks:
    1. Same-site: exact match on (source, source_id). If found, updates
       last_seen_at on the existing row and returns is_new=False.
    2. Cross-site: fuzzy match on normalized address + acreage within 5%
       for listings from a different source in the same state/county.
       Returns is_new=True with the possible_cross_site_match id.
    """
    # Same-site exact match
    stmt = select(Listing).where(
        Listing.source == listing.source,
        Listing.source_id == listing.source_id,
    )
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        existing.last_seen_at = listing.last_seen_at
        return DedupeResult(is_new=False, existing_id=existing.id)

    # Cross-site fuzzy match
    normalized_addr = _normalize_address(listing.address)
    stmt = select(Listing).where(
        Listing.source != listing.source,
        Listing.state == listing.state,
        Listing.county == listing.county,
    )
    candidates = session.execute(stmt).scalars().all()
    for candidate in candidates:
        if (
            _normalize_address(candidate.address) == normalized_addr
            and _acreage_within_tolerance(candidate.acreage, listing.acreage)
        ):
            return DedupeResult(
                is_new=True,
                possible_cross_site_match=candidate.id,
            )

    return DedupeResult(is_new=True)
