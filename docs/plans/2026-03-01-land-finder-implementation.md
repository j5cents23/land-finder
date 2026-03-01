# Land Finder Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a personal land listing aggregator that scrapes 5 sites every 4 hours, filters against saved criteria, and surfaces matches via a Next.js dashboard with email alerts.

**Architecture:** Modular scraper pipeline — each site gets an independent Python spider. A scheduler runs all spiders concurrently, pipes results through normalize → deduplicate → filter → store → alert. Next.js dashboard reads from the shared SQLite DB.

**Tech Stack:** Python 3.12, httpx, BeautifulSoup4, Playwright, SQLAlchemy, APScheduler, Next.js 14 (App Router), Leaflet, Resend, SQLite.

**Design doc:** `docs/plans/2026-03-01-land-finder-design.md`

---

## Phase 1: Python Project Scaffolding + Database Models

### Task 1: Initialize Python project with pyproject.toml

**Files:**
- Create: `pyproject.toml`
- Create: `scraper/__init__.py`
- Create: `scraper/spiders/__init__.py`
- Create: `scraper/pipeline/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "land-finder-scraper"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "sqlalchemy>=2.0",
    "httpx>=0.27",
    "beautifulsoup4>=4.12",
    "playwright>=1.40",
    "apscheduler>=3.10",
    "resend>=2.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Step 2: Create empty `__init__.py` files**

Create empty files at:
- `scraper/__init__.py`
- `scraper/spiders/__init__.py`
- `scraper/pipeline/__init__.py`
- `tests/__init__.py`

**Step 3: Create virtual environment and install deps**

Run: `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && playwright install chromium`

**Step 4: Create .gitignore**

```gitignore
.venv/
__pycache__/
*.pyc
.env
db/*.db
runs.json
.pytest_cache/
node_modules/
.next/
```

**Step 5: Commit**

```bash
git add pyproject.toml scraper/ tests/__init__.py .gitignore
git commit -m "chore(scraper): scaffold python project with dependencies"
```

---

### Task 2: Define SQLAlchemy models

**Files:**
- Create: `scraper/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scraper.models'` or `ImportError`

**Step 3: Write the models**

```python
# scraper/models.py
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SourceEnum(str, enum.Enum):
    ZILLOW = "zillow"
    LANDWATCH = "landwatch"
    LAND_COM = "land_com"
    CRAIGSLIST = "craigslist"
    FACEBOOK = "facebook"


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_source_listing"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    source: Mapped[SourceEnum] = mapped_column(Enum(SourceEnum))
    source_id: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer)
    acreage: Mapped[float] = mapped_column(Float)
    price_per_acre: Mapped[float] = mapped_column(Float)
    address: Mapped[str] = mapped_column(String(512))
    city: Mapped[str] = mapped_column(String(255))
    county: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(2))
    zip_code: Mapped[str] = mapped_column(String(10))
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    zoning: Mapped[str | None] = mapped_column(String(100), nullable=True)
    has_water: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_utilities: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_road_access: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    image_urls: Mapped[list] = mapped_column(JSON, default=list)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)


class SearchCriteria(Base):
    __tablename__ = "search_criteria"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    min_acreage: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_ppa: Mapped[float | None] = mapped_column(Float, nullable=True)
    states: Mapped[list] = mapped_column(JSON, default=list)
    counties: Mapped[list] = mapped_column(JSON, default=list)
    center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    require_water: Mapped[bool] = mapped_column(Boolean, default=False)
    require_utils: Mapped[bool] = mapped_column(Boolean, default=False)
    require_road: Mapped[bool] = mapped_column(Boolean, default=False)
    zoning_types: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add scraper/models.py tests/test_models.py
git commit -m "feat(models): add Listing and SearchCriteria SQLAlchemy models"
```

---

### Task 3: Database session helper and config

**Files:**
- Create: `scraper/db.py`
- Create: `scraper/config.py`
- Create: `tests/test_db.py`

**Step 1: Write the failing test**

```python
# tests/test_db.py
from scraper.db import get_engine, get_session
from scraper.models import Base, Listing


def test_get_engine_creates_tables():
    engine = get_engine(":memory:")
    Base.metadata.create_all(engine)
    # Should not raise — tables exist
    with get_session(engine) as session:
        result = session.query(Listing).all()
        assert result == []


def test_get_session_is_usable():
    engine = get_engine(":memory:")
    Base.metadata.create_all(engine)
    with get_session(engine) as session:
        assert session.is_active
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write db.py and config.py**

```python
# scraper/db.py
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


def get_engine(db_path: str = "db/land_finder.db") -> Engine:
    if db_path == ":memory:":
        url = "sqlite:///:memory:"
    else:
        url = f"sqlite:///{db_path}"
    return create_engine(url)


@contextmanager
def get_session(engine: Engine) -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

```python
# scraper/config.py
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / "db" / "land_finder.db")


@dataclass(frozen=True)
class SpiderConfig:
    enabled: bool = True
    interval_hours: float = 4.0
    max_pages: int = 10
    delay_seconds: float = 2.0


@dataclass(frozen=True)
class AlertConfig:
    email_enabled: bool = True
    email_to: str = os.getenv("ALERT_EMAIL", "")
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    hot_deal_ppa_threshold: int = 200000  # cents — $2,000/acre


@dataclass(frozen=True)
class AppConfig:
    db_path: str = DB_PATH
    spiders: dict[str, SpiderConfig] = field(default_factory=lambda: {
        "zillow": SpiderConfig(),
        "landwatch": SpiderConfig(),
        "land_com": SpiderConfig(),
        "craigslist": SpiderConfig(),
        "facebook": SpiderConfig(),
    })
    alerts: AlertConfig = field(default_factory=AlertConfig)
    user_agents: list[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add scraper/db.py scraper/config.py tests/test_db.py
git commit -m "feat(db): add database session helper and app config"
```

---

## Phase 2: Spider Base Class + Pipeline Infrastructure

### Task 4: Create abstract spider base class

**Files:**
- Create: `scraper/spiders/base.py`
- Create: `tests/test_spider_base.py`

**Step 1: Write the failing test**

```python
# tests/test_spider_base.py
import pytest

from scraper.spiders.base import BaseSpider


class FakeSpider(BaseSpider):
    name = "fake"

    async def scrape(self, criteria):
        return [
            {"id": "1", "title": "Lot A", "price": "$10,000", "acres": "5"},
            {"id": "2", "title": "Lot B", "price": "$20,000", "acres": "10"},
        ]


class IncompleteSpider(BaseSpider):
    name = "incomplete"


@pytest.mark.asyncio
async def test_spider_scrape_returns_raw_dicts():
    spider = FakeSpider()
    results = await spider.scrape(criteria={})
    assert len(results) == 2
    assert results[0]["title"] == "Lot A"


def test_spider_has_name():
    spider = FakeSpider()
    assert spider.name == "fake"


def test_incomplete_spider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        IncompleteSpider()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_spider_base.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the base spider**

```python
# scraper/spiders/base.py
import random
from abc import ABC, abstractmethod

import httpx


class BaseSpider(ABC):
    name: str = ""

    def __init__(self, user_agents: list[str] | None = None, delay: float = 2.0):
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]
        self.delay = delay

    def _random_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=self._random_headers(),
            follow_redirects=True,
            timeout=30.0,
        )

    @abstractmethod
    async def scrape(self, criteria: dict) -> list[dict]:
        """Scrape listings and return raw dicts."""
        ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_spider_base.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add scraper/spiders/base.py tests/test_spider_base.py
git commit -m "feat(spiders): add abstract BaseSpider class"
```

---

### Task 5: Build the normalizer

**Files:**
- Create: `scraper/pipeline/normalizer.py`
- Create: `tests/test_normalizer.py`

**Step 1: Write the failing test**

```python
# tests/test_normalizer.py
from scraper.pipeline.normalizer import parse_price, parse_acreage, detect_features


def test_parse_price_with_dollar_sign():
    assert parse_price("$45,000") == 4500000


def test_parse_price_plain_number():
    assert parse_price("45000") == 4500000


def test_parse_price_with_k_suffix():
    assert parse_price("$45K") == 4500000


def test_parse_price_none_on_invalid():
    assert parse_price("Call for price") is None


def test_parse_price_none_on_empty():
    assert parse_price("") is None


def test_parse_acreage_with_acres():
    assert parse_acreage("10 acres") == 10.0


def test_parse_acreage_decimal():
    assert parse_acreage("2.5 ac") == 2.5


def test_parse_acreage_plain_number():
    assert parse_acreage("15") == 15.0


def test_parse_acreage_none_on_invalid():
    assert parse_acreage("N/A") is None


def test_detect_features_water():
    features = detect_features("Beautiful property with well water and creek access")
    assert features["has_water"] is True


def test_detect_features_utilities():
    features = detect_features("Electric and gas available at the road")
    assert features["has_utilities"] is True


def test_detect_features_road():
    features = detect_features("Paved road frontage, easy access")
    assert features["has_road_access"] is True


def test_detect_features_none_when_missing():
    features = detect_features("Nice wooded lot, very private")
    assert features["has_water"] is None
    assert features["has_utilities"] is None
    assert features["has_road_access"] is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_normalizer.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the normalizer**

```python
# scraper/pipeline/normalizer.py
import re


def parse_price(raw: str) -> int | None:
    if not raw:
        return None
    cleaned = raw.strip().upper()
    # Handle K suffix: "$45K" -> 45000
    k_match = re.search(r"[\$]?\s*([\d,]+\.?\d*)\s*K", cleaned)
    if k_match:
        value = float(k_match.group(1).replace(",", ""))
        return int(value * 1000 * 100)
    # Standard: "$45,000" or "45000"
    match = re.search(r"[\$]?\s*([\d,]+\.?\d*)", cleaned)
    if match:
        value = float(match.group(1).replace(",", ""))
        return int(value * 100)
    return None


def parse_acreage(raw: str) -> float | None:
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
    if not description:
        return {"has_water": None, "has_utilities": None, "has_road_access": None}
    return {
        "has_water": True if _WATER_PATTERNS.search(description) else None,
        "has_utilities": True if _UTILITY_PATTERNS.search(description) else None,
        "has_road_access": True if _ROAD_PATTERNS.search(description) else None,
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_normalizer.py -v`
Expected: All passed

**Step 5: Commit**

```bash
git add scraper/pipeline/normalizer.py tests/test_normalizer.py
git commit -m "feat(pipeline): add price, acreage, and feature normalizers"
```

---

### Task 6: Build the deduplicator

**Files:**
- Create: `scraper/pipeline/deduplicator.py`
- Create: `tests/test_deduplicator.py`

**Step 1: Write the failing test**

```python
# tests/test_deduplicator.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_deduplicator.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the deduplicator**

```python
# scraper/pipeline/deduplicator.py
import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from scraper.models import Listing, SourceEnum


@dataclass(frozen=True)
class DedupeResult:
    is_new: bool
    existing_id: uuid.UUID | None = None
    possible_cross_site_match: uuid.UUID | None = None


def _normalize_address(address: str) -> str:
    addr = address.lower().strip()
    replacements = {
        "road": "rd", "street": "st", "avenue": "ave", "drive": "dr",
        "lane": "ln", "court": "ct", "boulevard": "blvd", "place": "pl",
    }
    for full, abbr in replacements.items():
        addr = re.sub(rf"\b{full}\b", abbr, addr)
    return re.sub(r"\s+", " ", addr)


def _acreage_within_tolerance(a: float, b: float, tolerance: float = 0.05) -> bool:
    if a == 0 or b == 0:
        return False
    return abs(a - b) / max(a, b) <= tolerance


def deduplicate(session: Session, listing: Listing) -> DedupeResult:
    # Same-site check
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_deduplicator.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add scraper/pipeline/deduplicator.py tests/test_deduplicator.py
git commit -m "feat(pipeline): add same-site and cross-site deduplicator"
```

---

### Task 7: Build the criteria filter

**Files:**
- Create: `scraper/pipeline/filter.py`
- Create: `tests/test_filter.py`

**Step 1: Write the failing test**

```python
# tests/test_filter.py
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
    # Center is far away
    criteria = make_criteria(center_lat=35.0, center_lng=-80.0, radius_miles=50.0)
    assert matches_criteria(listing, criteria) is False


def test_radius_filter_passes():
    listing = make_listing(latitude=41.8, longitude=-74.7)
    criteria = make_criteria(center_lat=41.85, center_lng=-74.65, radius_miles=10.0)
    assert matches_criteria(listing, criteria) is True


def test_haversine_known_distance():
    # NYC to LA is roughly 2,451 miles
    d = haversine_miles(40.7128, -74.0060, 34.0522, -118.2437)
    assert 2440 < d < 2460
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_filter.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the filter**

```python
# scraper/pipeline/filter.py
import math

from scraper.models import Listing, SearchCriteria


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_filter.py -v`
Expected: All passed

**Step 5: Commit**

```bash
git add scraper/pipeline/filter.py tests/test_filter.py
git commit -m "feat(pipeline): add criteria filter with haversine radius support"
```

---

## Phase 3: First Spider (Craigslist)

### Task 8: Build the Craigslist spider

**Files:**
- Create: `scraper/spiders/craigslist.py`
- Create: `tests/test_craigslist_spider.py`
- Create: `tests/fixtures/craigslist_sample.html`

**Step 1: Create a sample HTML fixture**

Save a representative Craigslist land listing search results page to `tests/fixtures/craigslist_sample.html`. Inspect the actual page at `https://newyork.craigslist.org/search/rea?query=land+acres` and save the HTML structure. The test fixture should contain 2-3 sample listing cards.

Create a minimal fixture:

```html
<!-- tests/fixtures/craigslist_sample.html -->
<html>
<body>
<div class="cl-search-result">
  <a href="/bnm/rea/d/liberty-10-acres-sullivan-county/7890123456.html"
     class="posting-title">
    <span class="label">10 Acres Sullivan County - $45,000</span>
  </a>
  <span class="priceinfo">$45,000</span>
  <div class="meta">
    <span class="posting-hood"> (Liberty, NY)</span>
  </div>
</div>
<div class="cl-search-result">
  <a href="/bnm/rea/d/ellenville-5-acres-wooded/7890123457.html"
     class="posting-title">
    <span class="label">5 Acres Wooded Lot - $28,000</span>
  </a>
  <span class="priceinfo">$28,000</span>
  <div class="meta">
    <span class="posting-hood"> (Ellenville, NY)</span>
  </div>
</div>
</body>
</html>
```

**Step 2: Write the failing test**

```python
# tests/test_craigslist_spider.py
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from scraper.spiders.craigslist import CraigslistSpider


@pytest.fixture
def sample_html():
    return Path("tests/fixtures/craigslist_sample.html").read_text()


@pytest.mark.asyncio
async def test_parse_listings_from_html(sample_html):
    spider = CraigslistSpider()
    listings = spider.parse_results(sample_html, base_url="https://newyork.craigslist.org")
    assert len(listings) == 2
    assert listings[0]["title"] == "10 Acres Sullivan County - $45,000"
    assert listings[0]["price"] == "$45,000"


@pytest.mark.asyncio
async def test_parse_listing_has_required_fields(sample_html):
    spider = CraigslistSpider()
    listings = spider.parse_results(sample_html, base_url="https://newyork.craigslist.org")
    required = {"source_id", "url", "title", "price"}
    for listing in listings:
        assert required.issubset(listing.keys()), f"Missing keys: {required - listing.keys()}"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_craigslist_spider.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write the Craigslist spider**

```python
# scraper/spiders/craigslist.py
import asyncio
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.spiders.base import BaseSpider


class CraigslistSpider(BaseSpider):
    name = "craigslist"

    REGIONS = [
        "newyork", "hudsonvalley", "catskills", "albany", "potsdam",
    ]

    def _search_url(self, region: str, offset: int = 0) -> str:
        return f"https://{region}.craigslist.org/search/rea?query=land+acres&s={offset}"

    def parse_results(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        listings = []
        for result in soup.select(".cl-search-result"):
            link = result.select_one("a.posting-title")
            if not link:
                continue
            href = link.get("href", "")
            source_id_match = re.search(r"/(\d+)\.html", href)
            source_id = source_id_match.group(1) if source_id_match else href
            title_el = link.select_one(".label")
            title = title_el.get_text(strip=True) if title_el else ""
            price_el = result.select_one(".priceinfo")
            price = price_el.get_text(strip=True) if price_el else ""
            hood_el = result.select_one(".posting-hood")
            hood = hood_el.get_text(strip=True).strip("() ") if hood_el else ""

            listings.append({
                "source_id": source_id,
                "url": urljoin(base_url, href),
                "title": title,
                "price": price,
                "hood": hood,
            })
        return listings

    async def scrape(self, criteria: dict) -> list[dict]:
        all_listings = []
        async with self._client() as client:
            for region in self.REGIONS:
                try:
                    url = self._search_url(region)
                    response = await client.get(url)
                    response.raise_for_status()
                    base_url = f"https://{region}.craigslist.org"
                    results = self.parse_results(response.text, base_url)
                    all_listings.extend(results)
                    await asyncio.sleep(self.delay)
                except Exception as e:
                    print(f"[craigslist] Error scraping {region}: {e}")
        return all_listings
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_craigslist_spider.py -v`
Expected: 2 passed

**Step 6: Commit**

```bash
git add scraper/spiders/craigslist.py tests/test_craigslist_spider.py tests/fixtures/
git commit -m "feat(spiders): add Craigslist spider with HTML parser"
```

---

## Phase 4: Pipeline Orchestrator

### Task 9: Build the pipeline orchestrator

**Files:**
- Create: `scraper/pipeline/orchestrator.py`
- Create: `tests/test_orchestrator.py`

**Step 1: Write the failing test**

```python
# tests/test_orchestrator.py
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from scraper.models import Base, Listing, SearchCriteria, SourceEnum
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the orchestrator**

```python
# scraper/pipeline/orchestrator.py
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from scraper.models import Listing, SearchCriteria, SourceEnum
from scraper.pipeline.deduplicator import deduplicate
from scraper.pipeline.filter import matches_criteria
from scraper.pipeline.normalizer import detect_features, parse_acreage, parse_price


def _raw_to_listing(raw: dict) -> Listing | None:
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
    new_listings = []

    all_criteria = (
        session.query(SearchCriteria)
        .filter(SearchCriteria.is_active == True)
        .all()
    )

    for raw in raw_results:
        listing = _raw_to_listing(raw)
        if listing is None:
            continue

        result = deduplicate(session, listing)
        if not result.is_new:
            continue

        # Check if listing matches any criteria
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_orchestrator.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add scraper/pipeline/orchestrator.py tests/test_orchestrator.py
git commit -m "feat(pipeline): add orchestrator to wire normalize-dedupe-filter-store"
```

---

## Phase 5: Alerter

### Task 10: Build the email alerter

**Files:**
- Create: `scraper/pipeline/alerter.py`
- Create: `tests/test_alerter.py`

**Step 1: Write the failing test**

```python
# tests/test_alerter.py
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from scraper.models import Listing, SourceEnum
from scraper.pipeline.alerter import build_email_html, send_digest


def make_listing(**overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        source=SourceEnum.CRAIGSLIST,
        source_id="1",
        url="https://example.com/1",
        title="10 Acres in Sullivan County",
        price=5000000,
        acreage=10.0,
        price_per_acre=500000.0,
        address="123 Rd",
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


def test_build_email_html_contains_listing():
    listings = [make_listing(title="Amazing 10 Acres")]
    html = build_email_html(listings)
    assert "Amazing 10 Acres" in html
    assert "$50,000" in html  # 5000000 cents = $50,000


def test_build_email_html_multiple_listings():
    listings = [make_listing(title="Lot A"), make_listing(title="Lot B")]
    html = build_email_html(listings)
    assert "Lot A" in html
    assert "Lot B" in html


@patch("scraper.pipeline.alerter.resend")
def test_send_digest_calls_resend(mock_resend):
    mock_resend.Emails.send.return_value = {"id": "123"}
    listings = [make_listing()]
    send_digest(listings, to_email="test@example.com", api_key="re_test")
    mock_resend.Emails.send.assert_called_once()
    call_args = mock_resend.Emails.send.call_args[0][0]
    assert call_args["to"] == ["test@example.com"]


@patch("scraper.pipeline.alerter.resend")
def test_send_digest_skips_when_no_listings(mock_resend):
    send_digest([], to_email="test@example.com", api_key="re_test")
    mock_resend.Emails.send.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_alerter.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the alerter**

```python
# scraper/pipeline/alerter.py
import resend

from scraper.models import Listing


def _format_price(cents: int) -> str:
    return f"${cents // 100:,}"


def build_email_html(listings: list[Listing]) -> str:
    rows = []
    for listing in listings:
        rows.append(f"""
        <tr>
            <td><a href="{listing.url}">{listing.title}</a></td>
            <td>{_format_price(listing.price)}</td>
            <td>{listing.acreage:.1f} ac</td>
            <td>{_format_price(int(listing.price_per_acre))}/ac</td>
            <td>{listing.county}, {listing.state}</td>
            <td>{listing.source.value}</td>
        </tr>""")

    return f"""
    <html>
    <body>
        <h2>Land Finder: {len(listings)} New Match{"es" if len(listings) != 1 else ""}</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
            <tr>
                <th>Title</th><th>Price</th><th>Acreage</th>
                <th>Price/Acre</th><th>Location</th><th>Source</th>
            </tr>
            {"".join(rows)}
        </table>
    </body>
    </html>
    """


def send_digest(
    listings: list[Listing],
    to_email: str,
    api_key: str,
) -> None:
    if not listings:
        return

    resend.api_key = api_key
    html = build_email_html(listings)
    resend.Emails.send({
        "from": "Land Finder <landfinder@resend.dev>",
        "to": [to_email],
        "subject": f"Land Finder: {len(listings)} new listing{"s" if len(listings) != 1 else ""}",
        "html": html,
    })
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_alerter.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add scraper/pipeline/alerter.py tests/test_alerter.py
git commit -m "feat(alerter): add email digest via Resend"
```

---

## Phase 6: Scheduler + Main Entry Point

### Task 11: Build the scheduler and main entry point

**Files:**
- Create: `scraper/scheduler.py`
- Create: `scraper/main.py`
- Create: `.env.example`

**Step 1: Write the scheduler**

```python
# scraper/scheduler.py
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from scraper.config import AppConfig
from scraper.db import get_engine, get_session
from scraper.models import Base, Listing
from scraper.pipeline.alerter import send_digest
from scraper.pipeline.orchestrator import run_pipeline
from scraper.spiders.craigslist import CraigslistSpider

logger = logging.getLogger("land-finder")

SPIDERS = {
    "craigslist": CraigslistSpider,
    # "landwatch": LandWatchSpider,
    # "land_com": LandComSpider,
    # "zillow": ZillowSpider,
    # "facebook": FacebookSpider,
}


async def _run_spider(name: str, spider, config: AppConfig) -> list[dict]:
    try:
        logger.info(f"Running spider: {name}")
        results = await spider.scrape(criteria={})
        for r in results:
            r["source"] = name
        logger.info(f"Spider {name} returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Spider {name} failed: {e}")
        return []


async def run_scrape(config: AppConfig) -> dict:
    engine = get_engine(config.db_path)
    Base.metadata.create_all(engine)

    all_results = []
    tasks = []

    for name, spider_cls in SPIDERS.items():
        spider_config = config.spiders.get(name)
        if spider_config and not spider_config.enabled:
            continue
        spider = spider_cls(
            user_agents=config.user_agents,
            delay=spider_config.delay_seconds if spider_config else 2.0,
        )
        tasks.append(_run_spider(name, spider, config))

    spider_results = await asyncio.gather(*tasks)
    for results in spider_results:
        all_results.extend(results)

    run_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_raw": len(all_results),
        "spiders": {name: "ok" for name in SPIDERS},
        "new_matches": 0,
    }

    with get_session(engine) as session:
        new_listings = await run_pipeline(session, all_results)
        run_summary["new_matches"] = len(new_listings)

        if new_listings and config.alerts.email_enabled and config.alerts.email_to:
            try:
                send_digest(
                    new_listings,
                    to_email=config.alerts.email_to,
                    api_key=config.alerts.resend_api_key,
                )
                for listing in new_listings:
                    listing.notified = True
                session.commit()
                logger.info(f"Sent digest with {len(new_listings)} listings")
            except Exception as e:
                logger.error(f"Failed to send digest: {e}")

    # Write run log
    log_path = Path("runs.json")
    runs = []
    if log_path.exists():
        runs = json.loads(log_path.read_text())
    runs.append(run_summary)
    # Keep last 100 runs
    runs = runs[-100:]
    log_path.write_text(json.dumps(runs, indent=2))

    logger.info(f"Run complete: {run_summary['new_matches']} new matches from {run_summary['total_raw']} raw")
    return run_summary
```

**Step 2: Write main.py**

```python
# scraper/main.py
import asyncio
import logging
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scraper.config import AppConfig
from scraper.scheduler import run_scrape

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("land-finder.log"),
    ],
)


async def main():
    config = AppConfig()

    # Run once immediately
    await run_scrape(config)

    # Then schedule
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_scrape,
        "interval",
        hours=4,
        args=[config],
    )
    scheduler.start()

    # Keep alive
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 3: Create .env.example**

```env
ALERT_EMAIL=your@email.com
RESEND_API_KEY=re_your_key_here
```

**Step 4: Commit**

```bash
git add scraper/scheduler.py scraper/main.py .env.example
git commit -m "feat(scheduler): add APScheduler runner and main entry point"
```

---

## Phase 7: Additional Spiders

### Task 12: Build the LandWatch spider

Same pattern as Task 8. Create `scraper/spiders/landwatch.py` with:
- HTTP-based (`httpx` + `BeautifulSoup`)
- Target URL: `https://www.landwatch.com/land/for-sale` with state/county params
- Parse listing cards for: source_id, url, title, price, acreage, location
- Test with saved HTML fixture at `tests/fixtures/landwatch_sample.html`
- Register in `scraper/scheduler.py` SPIDERS dict

### Task 13: Build the Land.com spider

Same pattern. Create `scraper/spiders/land_com.py`:
- HTTP-based
- Target: `https://www.land.com/property/` with filters
- Parse listing results
- Test with fixture
- Register in SPIDERS

### Task 14: Build the Zillow spider

Create `scraper/spiders/zillow.py`:
- **Playwright-based** — Zillow requires JS rendering
- Navigate to search results, scroll to load listings, extract from rendered DOM
- Random delays (1-3s) between actions
- Randomized viewport size
- Test with fixture (saved rendered HTML)
- Register in SPIDERS

### Task 15: Build the Facebook Marketplace spider

Create `scraper/spiders/facebook.py`:
- **Playwright-based** — requires JS rendering
- May require login cookies (document in README)
- Navigate to Marketplace → Property → Land
- Extract listings from rendered page
- Test with fixture
- Register in SPIDERS

> **Note for Tasks 12-15:** Each spider follows the exact same pattern as the Craigslist spider (Task 8). The real work is inspecting each site's HTML structure, saving a fixture, writing the parser, and testing against the fixture. The spider class structure, base class usage, and pipeline integration are identical.

---

## Phase 8: Next.js Dashboard — Scaffolding + API

### Task 16: Scaffold Next.js dashboard

**Step 1: Create Next.js app**

Run: `cd /Users/jln/Desktop/Code/land-finder && npx create-next-app@latest dashboard --typescript --tailwind --app --src-dir --no-eslint --import-alias "@/*"`

**Step 2: Install dashboard dependencies**

Run: `cd dashboard && npm install better-sqlite3 leaflet react-leaflet && npm install -D @types/better-sqlite3 @types/leaflet`

**Step 3: Commit**

```bash
git add dashboard/
git commit -m "chore(dashboard): scaffold Next.js app with Tailwind"
```

---

### Task 17: Build API route — GET /api/listings

**Files:**
- Create: `dashboard/src/app/api/listings/route.ts`
- Create: `dashboard/src/lib/db.ts`
- Create: `dashboard/src/lib/types.ts`

**Step 1: Create shared types**

```typescript
// dashboard/src/lib/types.ts
export interface Listing {
  id: string
  source: string
  source_id: string
  url: string
  title: string
  description: string | null
  price: number
  acreage: number
  price_per_acre: number
  address: string
  city: string
  county: string
  state: string
  zip_code: string
  latitude: number | null
  longitude: number | null
  zoning: string | null
  has_water: boolean | null
  has_utilities: boolean | null
  has_road_access: boolean | null
  image_urls: string[]
  first_seen_at: string
  last_seen_at: string
  is_active: boolean
  is_favorited: boolean
}

export interface SearchCriteria {
  id: string
  name: string
  min_acreage: number | null
  max_price: number | null
  max_ppa: number | null
  states: string[]
  counties: string[]
  center_lat: number | null
  center_lng: number | null
  radius_miles: number | null
  require_water: boolean
  require_utils: boolean
  require_road: boolean
  zoning_types: string[]
  is_active: boolean
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}
```

**Step 2: Create DB helper**

```typescript
// dashboard/src/lib/db.ts
import Database from "better-sqlite3"
import path from "path"

const DB_PATH = path.join(process.cwd(), "..", "db", "land_finder.db")

export function getDb(): Database.Database {
  return new Database(DB_PATH, { readonly: true })
}

export function getWritableDb(): Database.Database {
  return new Database(DB_PATH)
}
```

**Step 3: Create listings API route**

```typescript
// dashboard/src/app/api/listings/route.ts
import { NextRequest, NextResponse } from "next/server"

import { getDb } from "@/lib/db"
import type { ApiResponse, Listing } from "@/lib/types"

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams
  const page = parseInt(params.get("page") ?? "1", 10)
  const limit = parseInt(params.get("limit") ?? "50", 10)
  const offset = (page - 1) * limit

  const state = params.get("state")
  const county = params.get("county")
  const minAcreage = params.get("min_acreage")
  const maxPrice = params.get("max_price")
  const source = params.get("source")
  const activeOnly = params.get("active") !== "false"

  const db = getDb()

  try {
    const conditions: string[] = []
    const values: unknown[] = []

    if (activeOnly) {
      conditions.push("is_active = 1")
    }
    if (state) {
      conditions.push("state = ?")
      values.push(state)
    }
    if (county) {
      conditions.push("county = ?")
      values.push(county)
    }
    if (minAcreage) {
      conditions.push("acreage >= ?")
      values.push(parseFloat(minAcreage))
    }
    if (maxPrice) {
      conditions.push("price <= ?")
      values.push(parseInt(maxPrice, 10))
    }
    if (source) {
      conditions.push("source = ?")
      values.push(source)
    }

    const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : ""

    const countRow = db.prepare(`SELECT COUNT(*) as total FROM listings ${where}`).get(...values) as { total: number }
    const rows = db.prepare(
      `SELECT * FROM listings ${where} ORDER BY first_seen_at DESC LIMIT ? OFFSET ?`
    ).all(...values, limit, offset)

    const response: ApiResponse<Listing[]> = {
      success: true,
      data: rows as Listing[],
      meta: {
        total: countRow.total,
        page,
        limit,
      },
    }
    return NextResponse.json(response)
  } finally {
    db.close()
  }
}
```

**Step 4: Commit**

```bash
git add dashboard/src/lib/ dashboard/src/app/api/
git commit -m "feat(api): add GET /api/listings with filtering and pagination"
```

---

### Task 18: Build remaining API routes

**Files:**
- Create: `dashboard/src/app/api/listings/[id]/route.ts` — GET single listing
- Create: `dashboard/src/app/api/criteria/route.ts` — GET all, POST new
- Create: `dashboard/src/app/api/favorites/[id]/route.ts` — PATCH toggle

Each follows the same pattern as Task 17. The criteria POST route uses `getWritableDb()` since it writes. The favorites route toggles a `is_favorited` column (add this to the Listing model in the Python side too — or use a separate `favorites` table with just `listing_id`).

**Commit:**

```bash
git add dashboard/src/app/api/
git commit -m "feat(api): add listing detail, criteria CRUD, and favorites toggle"
```

---

## Phase 9: Dashboard UI

### Task 19: Build the map + listing card layout (home page)

**Files:**
- Create: `dashboard/src/components/map.tsx` — Leaflet map with color-coded pins
- Create: `dashboard/src/components/listing-card.tsx` — Compact card with price, acreage, county
- Modify: `dashboard/src/app/page.tsx` — Compose map + card grid

Key details:
- Leaflet map with `react-leaflet` — use dynamic import (`next/dynamic`) with `ssr: false` since Leaflet needs `window`
- Green pins for listings < 24h old, blue for older, red for hot deals
- Click pin → popup with title, price, acreage, link to detail page
- Below map: responsive card grid (CSS grid, 1-3 columns)
- Each card: title, price, acreage, price/acre, county + state, source badge, heart icon

**Commit:**

```bash
git add dashboard/src/components/ dashboard/src/app/page.tsx
git commit -m "feat(dashboard): add map view and listing card grid"
```

---

### Task 20: Build the listings table page

**Files:**
- Create: `dashboard/src/app/listings/page.tsx`
- Create: `dashboard/src/components/listings-table.tsx`
- Create: `dashboard/src/components/filter-sidebar.tsx`

Key details:
- Sortable HTML table (click column headers to sort)
- Filter sidebar: price range inputs, acreage range, state dropdown, county dropdown, source checkboxes, feature checkboxes
- Pagination controls at bottom
- Heart icon per row for favorites
- External link icon to open original listing

**Commit:**

```bash
git add dashboard/src/app/listings/ dashboard/src/components/
git commit -m "feat(dashboard): add filterable listings table page"
```

---

### Task 21: Build the listing detail page

**Files:**
- Create: `dashboard/src/app/listings/[id]/page.tsx`

Key details:
- Image gallery (simple grid, click to enlarge)
- All listing fields in a clean two-column layout
- Small Leaflet map showing parcel pin
- Link to original listing
- Heart/favorite toggle
- "Similar listings" section — query API for same county + similar acreage

**Commit:**

```bash
git add dashboard/src/app/listings/
git commit -m "feat(dashboard): add listing detail page with map and gallery"
```

---

### Task 22: Build the criteria management page

**Files:**
- Create: `dashboard/src/app/criteria/page.tsx`
- Create: `dashboard/src/components/criteria-form.tsx`

Key details:
- List existing criteria with edit/delete/toggle active
- Form to create new criteria: name, min acreage, max price, max price/acre, states (multi-select), counties (multi-select), radius (center point + miles), feature requirements, zoning
- Save hits POST `/api/criteria`

**Commit:**

```bash
git add dashboard/src/app/criteria/ dashboard/src/components/criteria-form.tsx
git commit -m "feat(dashboard): add search criteria management page"
```

---

### Task 23: Build the saved/favorites page

**Files:**
- Create: `dashboard/src/app/saved/page.tsx`

Key details:
- Same card grid as home page, but filtered to favorites only
- Remove from favorites button on each card

**Commit:**

```bash
git add dashboard/src/app/saved/
git commit -m "feat(dashboard): add saved/favorites page"
```

---

### Task 24: Build the settings page

**Files:**
- Create: `dashboard/src/app/settings/page.tsx`

Key details:
- Alert preferences: email toggle, email address, hot deal threshold
- Last run status: read from `runs.json` via API
- Next scheduled run time
- Spider status toggles (enable/disable per site)

**Commit:**

```bash
git add dashboard/src/app/settings/
git commit -m "feat(dashboard): add settings page with alert prefs and run status"
```

---

## Phase 10: Integration + Polish

### Task 25: Add navigation layout

**Files:**
- Create: `dashboard/src/components/nav.tsx`
- Modify: `dashboard/src/app/layout.tsx`

Key details:
- Top nav bar with links: Home, Listings, Saved, Criteria, Settings
- Active link highlighting
- App title "Land Finder"

**Commit:**

```bash
git add dashboard/src/components/nav.tsx dashboard/src/app/layout.tsx
git commit -m "feat(dashboard): add navigation bar"
```

---

### Task 26: End-to-end smoke test

**Step 1: Create the DB directory**

Run: `mkdir -p db`

**Step 2: Run the scraper once manually**

Run: `cd /Users/jln/Desktop/Code/land-finder && source .venv/bin/activate && python -c "import asyncio; from scraper.scheduler import run_scrape; from scraper.config import AppConfig; asyncio.run(run_scrape(AppConfig()))"`

Expected: Creates `db/land_finder.db`, logs spider results, writes `runs.json`

**Step 3: Start the dashboard**

Run: `cd dashboard && npm run dev`

**Step 4: Verify**

- Open `http://localhost:3000` — should see map and any found listings
- Open `http://localhost:3000/listings` — should see table
- Open `http://localhost:3000/criteria` — should be able to create a search
- Open `http://localhost:3000/settings` — should see last run status

**Step 5: Commit any fixes**

```bash
git add -A
git commit -m "fix(integration): resolve issues from end-to-end smoke test"
```

---

### Task 27: Run full test suite and verify coverage

Run: `cd /Users/jln/Desktop/Code/land-finder && source .venv/bin/activate && pytest --cov=scraper --cov-report=term-missing -v`

Expected: All tests pass, coverage > 80% on pipeline modules.

Fix any gaps by adding tests, then commit:

```bash
git commit -m "test(scraper): achieve 80%+ coverage on pipeline modules"
```
