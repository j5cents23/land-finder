# Land Finder — Design Document

**Date:** 2026-03-01
**Status:** Approved

A personal land listing aggregator that scrapes multiple listing sites on a schedule, filters against configurable criteria, and surfaces matches via a web dashboard with email alerts.

## Architecture

**Approach:** Modular Scraper Pipeline — each listing site gets its own spider module. A central orchestrator runs them on schedule, normalizes data into a common schema, deduplicates, filters against saved search criteria, stores in SQLite, and alerts on new matches.

**Stack:**
- Scraping: Python, `httpx`, `BeautifulSoup`, Playwright (JS-rendered sites only)
- Pipeline: Custom normalizer, deduplicator, alerter
- Scheduling: APScheduler (every 4 hours, configurable)
- Database: SQLite + SQLAlchemy (portable to Postgres later)
- Dashboard: Next.js (App Router), Leaflet maps
- Alerts: Resend (email), Twilio SMS optional/later
- Hosting: Local (Mac) initially, cloud migration later

## Project Structure

```
land-finder/
├── scraper/
│   ├── spiders/
│   │   ├── zillow.py           # Playwright-based
│   │   ├── landwatch.py        # HTTP + BeautifulSoup
│   │   ├── land_com.py         # HTTP + BeautifulSoup
│   │   ├── craigslist.py       # HTTP + BeautifulSoup
│   │   └── facebook.py         # Playwright-based
│   ├── pipeline/
│   │   ├── normalizer.py       # Raw data → ListingSchema
│   │   ├── deduplicator.py     # Cross-site duplicate detection
│   │   └── alerter.py          # Email/SMS for new matches
│   ├── models.py               # SQLAlchemy models
│   ├── config.py               # Search criteria, schedule, site toggles
│   ├── scheduler.py            # APScheduler entry
│   └── main.py                 # Entry point
├── dashboard/                  # Next.js frontend
├── db/                         # SQLite file, migrations
└── pyproject.toml
```

## Data Model

### Listing

| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| source | enum | zillow, landwatch, land_com, craigslist, facebook |
| source_id | str | Unique per source |
| url | str | Original listing URL |
| title | str | |
| description | text | Nullable |
| price | int | Stored in cents |
| acreage | float | |
| price_per_acre | float | Computed on insert |
| address | str | |
| city | str | |
| county | str | |
| state | str | 2-letter code |
| zip_code | str | |
| latitude | float | Nullable |
| longitude | float | Nullable |
| zoning | str | Nullable |
| has_water | bool | Nullable |
| has_utilities | bool | Nullable |
| has_road_access | bool | Nullable |
| image_urls | JSON | Array of URLs |
| raw_data | JSON | Original scraped payload |
| first_seen_at | datetime | |
| last_seen_at | datetime | |
| is_active | bool | False after 3 missed runs |
| notified | bool | Prevents duplicate alerts |

**Uniqueness constraint:** `source` + `source_id`

### SearchCriteria

| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| name | str | User-friendly label |
| min_acreage | float | Nullable |
| max_price | int | Nullable |
| max_ppa | float | Max price per acre, nullable |
| states | JSON | Array of 2-letter codes |
| counties | JSON | Array of county names |
| center_lat | float | Nullable, for radius search |
| center_lng | float | Nullable |
| radius_miles | float | Nullable |
| require_water | bool | |
| require_utils | bool | |
| require_road | bool | |
| zoning_types | JSON | Array of allowed zoning types |
| is_active | bool | |

## Pipeline Flow

1. **Scheduler** — APScheduler triggers all active spiders every 4 hours. Spiders run concurrently via `asyncio.gather`.
2. **Spider Runner** — Each spider yields raw dicts. HTTP spiders paginate through results. Playwright spiders handle JS-rendered pages with realistic delays.
3. **Normalizer** — Each spider's `normalize(raw) → Listing` maps site-specific fields to common schema. Parses acreage, price, and extracts features from description text via keyword matching.
4. **Deduplicator** — Same-site: skip if `source` + `source_id` exists (update `last_seen_at`). Cross-site: fuzzy match on address + acreage within 5%.
5. **Filter** — Match new listings against all active SearchCriteria. A listing matches if it passes every non-null criterion. Radius uses haversine distance.
6. **Store** — Insert new listings, update existing. Mark listings not seen in 3 consecutive runs as inactive.
7. **Alerter** — Batch new matches into email digest via Resend. Hot deals (below price/acre threshold) get instant alerts.

## Dashboard

### Pages

- `/` — Map view (Leaflet) with color-coded pins + recent matches card grid
- `/listings` — Sortable, filterable table of all listings
- `/listings/[id]` — Detail page with images, map, data, similar listings
- `/saved` — Favorited listings
- `/criteria` — Manage search criteria
- `/settings` — Alert preferences, last run status

### Pin colors

- Green: new (last 24h)
- Blue: previously seen
- Red: hot deal (below price/acre threshold)

### API routes

- `GET /api/listings` — filtered, paginated listing query
- `GET /api/listings/[id]` — single listing detail
- `GET /api/criteria` — list saved searches
- `POST /api/criteria` — create search criteria
- `PATCH /api/favorites/[id]` — toggle favorite

No auth — personal tool running locally.

## Alerts

- **Email via Resend** (free tier: 100/day) — digest after each run, instant for hot deals
- **SMS via Twilio** — optional, hot deals only, add later
- **Price drop detection** — re-alert if a listing's price decreases
- **Deduplication** — `notified` flag prevents repeat alerts

## Error Handling & Operations

- Each spider runs in `try/except` — one failure doesn't stop others
- Retry with exponential backoff (3 attempts) for 429/503 errors
- User-agent rotation (5-10 agents), 2s minimum between requests per site
- Playwright spiders: random delays (1-3s), randomized viewport, realistic scroll
- `robots.txt` honored where present
- Run log written to `runs.json` after each scrape
- Dashboard shows last run status and next scheduled run
- Self-alert email if all spiders fail in a run
- No automatic data deletion — inactive listings hidden but preserved
