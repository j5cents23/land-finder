import re


def parse_price(raw: str) -> int | None:
    """Convert a raw price string to cents (integer).

    Handles formats like "$45,000", "45000", "$45K".
    Returns None for unparseable strings or empty input.
    """
    if not raw:
        return None

    cleaned = raw.strip().upper()

    k_match = re.search(r"[\$]?\s*([\d,]+\.?\d*)\s*K", cleaned)
    if k_match:
        value = float(k_match.group(1).replace(",", ""))
        return int(value * 1000 * 100)

    match = re.search(r"[\$]?\s*([\d,]+\.?\d*)", cleaned)
    if match:
        value = float(match.group(1).replace(",", ""))
        return int(value * 100)

    return None


def parse_acreage(raw: str) -> float | None:
    """Convert a raw acreage string to a float.

    Handles formats like "10 acres", "2.5 ac", "15".
    Returns None for unparseable strings or empty input.
    """
    if not raw:
        return None

    match = re.search(r"([\d,]+\.?\d*)\s*(?:acres?|ac)?", raw.strip(), re.IGNORECASE)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None

    return None


_WATER_PATTERNS = re.compile(
    r"well\s*water|creek|stream|pond|lake|spring|water\s+available|river\s+front",
    re.IGNORECASE,
)

_UTILITY_PATTERNS = re.compile(
    r"electri|gas\s+available|utilit|power\s+available|sewer|septic\s+approved|public\s+water",
    re.IGNORECASE,
)

_ROAD_PATTERNS = re.compile(
    r"paved\s+road|road\s+frontage|road\s+access|county\s+road|state\s+road|highway\s+frontage|easy\s+access",
    re.IGNORECASE,
)


def detect_features(description: str) -> dict[str, bool | None]:
    """Detect land features from a description string.

    Scans for water, utility, and road access keywords.
    Returns True when detected, None when not found.
    """
    if not description:
        return {"has_water": None, "has_utilities": None, "has_road_access": None}

    return {
        "has_water": True if _WATER_PATTERNS.search(description) else None,
        "has_utilities": True if _UTILITY_PATTERNS.search(description) else None,
        "has_road_access": True if _ROAD_PATTERNS.search(description) else None,
    }
