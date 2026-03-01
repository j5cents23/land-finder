"""Location enrichment module using Overpass API and static area data."""

import asyncio
import logging
import math
import uuid
from datetime import datetime, timezone

import httpx

from scraper.models import ListingScore

logger = logging.getLogger("land-finder.enricher")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two lat/lon points in miles."""
    R = 3958.8
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def _query_overpass(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
    query_tags: str,
    radius_meters: int = 80000,
) -> list[dict]:
    """Query Overpass API for nearby POIs.

    Returns a list of dicts sorted by distance, each containing
    name, distance_miles, lat, and lon.
    """
    query = f"""
    [out:json][timeout:25];
    (
      {query_tags}
    );
    out center;
    """
    query = (
        query.replace("{{lat}}", str(lat))
        .replace("{{lon}}", str(lon))
        .replace("{{radius}}", str(radius_meters))
    )
    try:
        resp = await client.post(OVERPASS_URL, data={"data": query}, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for el in data.get("elements", []):
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            name = el.get("tags", {}).get("name", "Unknown")
            if el_lat and el_lon:
                dist = _haversine_miles(lat, lon, el_lat, el_lon)
                results.append(
                    {"name": name, "distance_miles": dist, "lat": el_lat, "lon": el_lon}
                )
        results.sort(key=lambda x: x["distance_miles"])
        return results
    except Exception as e:
        logger.warning("Overpass query failed: %s", e)
        return []


async def find_nearest_hospital(
    client: httpx.AsyncClient, lat: float, lon: float
) -> dict | None:
    """Find the nearest hospital within ~50 miles."""
    results = await _query_overpass(
        client,
        lat,
        lon,
        'node["amenity"="hospital"](around:{{radius}},{{lat}},{{lon}});'
        'way["amenity"="hospital"](around:{{radius}},{{lat}},{{lon}});',
        radius_meters=80000,
    )
    return results[0] if results else None


async def find_nearest_bigbox(
    client: httpx.AsyncClient, lat: float, lon: float
) -> dict | None:
    """Find the nearest Costco, Sam's Club, or Walmart within ~75 miles."""
    results = await _query_overpass(
        client,
        lat,
        lon,
        'node["shop"="wholesale"]["name"~"Costco|Sam.*Club",i](around:{{radius}},{{lat}},{{lon}});'
        'way["shop"="wholesale"]["name"~"Costco|Sam.*Club",i](around:{{radius}},{{lat}},{{lon}});'
        'node["shop"="supermarket"]["name"~"Walmart",i](around:{{radius}},{{lat}},{{lon}});'
        'way["shop"="supermarket"]["name"~"Walmart",i](around:{{radius}},{{lat}},{{lon}});'
        'node["shop"="department_store"]["name"~"Walmart",i](around:{{radius}},{{lat}},{{lon}});'
        'way["shop"="department_store"]["name"~"Walmart",i](around:{{radius}},{{lat}},{{lon}});',
        radius_meters=120000,
    )
    return results[0] if results else None


async def find_nearest_water(
    client: httpx.AsyncClient, lat: float, lon: float
) -> dict | None:
    """Find the nearest lake, river, or creek within ~10 miles."""
    results = await _query_overpass(
        client,
        lat,
        lon,
        'way["natural"="water"](around:{{radius}},{{lat}},{{lon}});'
        'relation["natural"="water"](around:{{radius}},{{lat}},{{lon}});'
        'way["waterway"~"river|stream"](around:{{radius}},{{lat}},{{lon}});',
        radius_meters=16000,
    )
    return results[0] if results else None


async def find_nearest_trail(
    client: httpx.AsyncClient, lat: float, lon: float
) -> dict | None:
    """Find the nearest hiking trail within ~20 miles."""
    results = await _query_overpass(
        client,
        lat,
        lon,
        'way["highway"="path"]["sac_scale"](around:{{radius}},{{lat}},{{lon}});'
        'way["highway"="footway"]["name"](around:{{radius}},{{lat}},{{lon}});'
        'relation["route"="hiking"](around:{{radius}},{{lat}},{{lon}});',
        radius_meters=32000,
    )
    return results[0] if results else None


async def find_nearest_offroad(
    client: httpx.AsyncClient, lat: float, lon: float
) -> dict | None:
    """Find the nearest offroad / unpaved trail within ~30 miles."""
    results = await _query_overpass(
        client,
        lat,
        lon,
        'way["highway"="track"]["surface"~"unpaved|gravel|dirt"](around:{{radius}},{{lat}},{{lon}});'
        'way["highway"="track"]["tracktype"~"grade3|grade4|grade5"](around:{{radius}},{{lat}},{{lon}});',
        radius_meters=48000,
    )
    return results[0] if results else None


async def find_nearest_school(
    client: httpx.AsyncClient, lat: float, lon: float
) -> dict | None:
    """Find the nearest school within ~20 miles."""
    results = await _query_overpass(
        client,
        lat,
        lon,
        'node["amenity"="school"](around:{{radius}},{{lat}},{{lon}});'
        'way["amenity"="school"](around:{{radius}},{{lat}},{{lon}});',
        radius_meters=32000,
    )
    return results[0] if results else None


# ---------------------------------------------------------------------------
# Static county-level data
# Sources: 2020/2024 election results, Census ACS, BLS
# ---------------------------------------------------------------------------

COUNTY_DATA: dict[tuple[str, str], dict] = {
    # Idaho
    ("ID", "Ada"): {
        "lean": "R+8", "tax": 0.69, "mil": True,
        "pop": 510000, "growth": 18.2, "median_age": 35.3,
        "snow": 19, "sunny": 206, "schools": "Above Average",
    },
    ("ID", "Gem"): {
        "lean": "R+45", "tax": 0.63, "mil": True,
        "pop": 19000, "growth": 12.1, "median_age": 40.2,
        "snow": 25, "sunny": 204, "schools": "Average",
    },
    ("ID", "Boise"): {
        "lean": "R+42", "tax": 0.58, "mil": True,
        "pop": 8200, "growth": 8.5, "median_age": 42.0,
        "snow": 35, "sunny": 200, "schools": "Below Average",
    },
    ("ID", "Canyon"): {
        "lean": "R+35", "tax": 0.75, "mil": True,
        "pop": 230000, "growth": 20.1, "median_age": 31.5,
        "snow": 12, "sunny": 206, "schools": "Above Average",
    },
    ("ID", "Kootenai"): {
        "lean": "R+35", "tax": 0.65, "mil": True,
        "pop": 175000, "growth": 22.5, "median_age": 38.0,
        "snow": 45, "sunny": 170, "schools": "Average",
    },
    ("ID", "Bonner"): {
        "lean": "R+30", "tax": 0.55, "mil": True,
        "pop": 48000, "growth": 15.3, "median_age": 44.0,
        "snow": 55, "sunny": 165, "schools": "Below Average",
    },
    ("ID", "Bonneville"): {
        "lean": "R+40", "tax": 0.70, "mil": True,
        "pop": 120000, "growth": 10.2, "median_age": 31.0,
        "snow": 35, "sunny": 195, "schools": "Average",
    },
    # Colorado
    ("CO", "El Paso"): {
        "lean": "R+8", "tax": 0.49, "mil": True,
        "pop": 730000, "growth": 12.5, "median_age": 34.0,
        "snow": 38, "sunny": 243, "schools": "Good",
    },
    ("CO", "Teller"): {
        "lean": "R+25", "tax": 0.47, "mil": True,
        "pop": 25000, "growth": 5.8, "median_age": 48.0,
        "snow": 65, "sunny": 246, "schools": "Average",
    },
    ("CO", "Park"): {
        "lean": "R+18", "tax": 0.42, "mil": True,
        "pop": 18000, "growth": 8.2, "median_age": 46.0,
        "snow": 60, "sunny": 245, "schools": "Average",
    },
    ("CO", "Douglas"): {
        "lean": "R+5", "tax": 0.50, "mil": True,
        "pop": 370000, "growth": 15.0, "median_age": 38.5,
        "snow": 42, "sunny": 245, "schools": "Good",
    },
    ("CO", "Fremont"): {
        "lean": "R+30", "tax": 0.55, "mil": True,
        "pop": 48000, "growth": 3.1, "median_age": 45.0,
        "snow": 25, "sunny": 248, "schools": "Below Average",
    },
    # Utah
    ("UT", "Utah"): {
        "lean": "R+35", "tax": 0.55, "mil": True,
        "pop": 680000, "growth": 18.5, "median_age": 25.0,
        "snow": 35, "sunny": 222, "schools": "Good",
    },
    ("UT", "Wasatch"): {
        "lean": "R+15", "tax": 0.48, "mil": True,
        "pop": 36000, "growth": 25.0, "median_age": 30.0,
        "snow": 80, "sunny": 220, "schools": "Average",
    },
    ("UT", "Summit"): {
        "lean": "D+5", "tax": 0.45, "mil": True,
        "pop": 42000, "growth": 14.0, "median_age": 35.0,
        "snow": 90, "sunny": 225, "schools": "Average",
    },
    ("UT", "Cache"): {
        "lean": "R+30", "tax": 0.52, "mil": True,
        "pop": 133000, "growth": 10.5, "median_age": 25.5,
        "snow": 48, "sunny": 210, "schools": "Good",
    },
    # Montana
    ("MT", "Flathead"): {
        "lean": "R+30", "tax": 0.85, "mil": True,
        "pop": 108000, "growth": 16.0, "median_age": 41.0,
        "snow": 59, "sunny": 175, "schools": "Average",
    },
    ("MT", "Gallatin"): {
        "lean": "R+5", "tax": 0.82, "mil": True,
        "pop": 119000, "growth": 25.0, "median_age": 33.0,
        "snow": 72, "sunny": 185, "schools": "Good",
    },
    ("MT", "Missoula"): {
        "lean": "D+15", "tax": 0.83, "mil": True,
        "pop": 120000, "growth": 10.5, "median_age": 34.0,
        "snow": 47, "sunny": 180, "schools": "Average",
    },
    ("MT", "Lewis and Clark"): {
        "lean": "R+5", "tax": 0.80, "mil": True,
        "pop": 72000, "growth": 8.0, "median_age": 40.0,
        "snow": 45, "sunny": 188, "schools": "Average",
    },
    # Michigan
    ("MI", "Grand Traverse"): {
        "lean": "R+5", "tax": 1.15, "mil": True,
        "pop": 95000, "growth": 5.5, "median_age": 42.0,
        "snow": 75, "sunny": 170, "schools": "Good",
    },
    ("MI", "Kalamazoo"): {
        "lean": "D+5", "tax": 1.40, "mil": True,
        "pop": 265000, "growth": 2.0, "median_age": 33.5,
        "snow": 65, "sunny": 165, "schools": "Good",
    },
    ("MI", "Allegan"): {
        "lean": "R+20", "tax": 1.10, "mil": True,
        "pop": 120000, "growth": 6.0, "median_age": 37.5,
        "snow": 70, "sunny": 165, "schools": "Average",
    },
    # New Hampshire
    ("NH", "Grafton"): {
        "lean": "D+10", "tax": 1.86, "mil": True,
        "pop": 90000, "growth": 1.0, "median_age": 42.0,
        "snow": 60, "sunny": 158, "schools": "Good",
    },
    ("NH", "Coos"): {
        "lean": "R+5", "tax": 1.92, "mil": True,
        "pop": 30000, "growth": -5.0, "median_age": 48.0,
        "snow": 80, "sunny": 155, "schools": "Below Average",
    },
    ("NH", "Carroll"): {
        "lean": "R+5", "tax": 1.35, "mil": True,
        "pop": 49000, "growth": 3.0, "median_age": 50.0,
        "snow": 65, "sunny": 158, "schools": "Average",
    },
    # Pennsylvania
    ("PA", "Monroe"): {
        "lean": "D+5", "tax": 1.30, "mil": True,
        "pop": 170000, "growth": 5.0, "median_age": 42.0,
        "snow": 45, "sunny": 183, "schools": "Good",
    },
    ("PA", "Pike"): {
        "lean": "R+10", "tax": 1.20, "mil": True,
        "pop": 58000, "growth": 4.0, "median_age": 45.0,
        "snow": 40, "sunny": 180, "schools": "Average",
    },
    ("PA", "Wayne"): {
        "lean": "R+15", "tax": 1.25, "mil": True,
        "pop": 51000, "growth": 2.0, "median_age": 47.0,
        "snow": 42, "sunny": 178, "schools": "Average",
    },
    # New York
    ("NY", "Sullivan"): {
        "lean": "R+2", "tax": 2.15, "mil": False,
        "pop": 78000, "growth": 2.0, "median_age": 42.0,
        "snow": 45, "sunny": 175, "schools": "Below Average",
    },
    ("NY", "Ulster"): {
        "lean": "D+15", "tax": 2.10, "mil": False,
        "pop": 177000, "growth": 1.5, "median_age": 43.0,
        "snow": 42, "sunny": 178, "schools": "Below Average",
    },
    ("NY", "Greene"): {
        "lean": "R+5", "tax": 2.20, "mil": False,
        "pop": 47000, "growth": -1.0, "median_age": 46.0,
        "snow": 50, "sunny": 175, "schools": "Below Average",
    },
    # West Virginia
    ("WV", "Jefferson"): {
        "lean": "R+12", "tax": 0.58, "mil": True,
        "pop": 57000, "growth": 6.0, "median_age": 40.0,
        "snow": 25, "sunny": 195, "schools": "Good",
    },
    ("WV", "Berkeley"): {
        "lean": "R+20", "tax": 0.55, "mil": True,
        "pop": 120000, "growth": 12.0, "median_age": 37.0,
        "snow": 22, "sunny": 195, "schools": "Average",
    },
    # Tennessee
    ("TN", "Blount"): {
        "lean": "R+35", "tax": 0.60, "mil": True,
        "pop": 135000, "growth": 8.0, "median_age": 42.0,
        "snow": 8, "sunny": 204, "schools": "Average",
    },
    ("TN", "Sevier"): {
        "lean": "R+45", "tax": 0.45, "mil": True,
        "pop": 105000, "growth": 12.0, "median_age": 42.0,
        "snow": 10, "sunny": 204, "schools": "Average",
    },
    # Wyoming
    ("WY", "Teton"): {
        "lean": "D+15", "tax": 0.55, "mil": True,
        "pop": 24000, "growth": 8.0, "median_age": 36.0,
        "snow": 77, "sunny": 200, "schools": "Below Average",
    },
    ("WY", "Laramie"): {
        "lean": "R+20", "tax": 0.58, "mil": True,
        "pop": 100000, "growth": 2.5, "median_age": 34.0,
        "snow": 45, "sunny": 230, "schools": "Average",
    },
}

# ---------------------------------------------------------------------------
# Ski resorts / snowmobile areas with coordinates
# ---------------------------------------------------------------------------

SKI_AREAS: list[dict] = [
    {"name": "Bogus Basin", "lat": 43.76, "lon": -116.10, "state": "ID"},
    {"name": "Sun Valley", "lat": 43.70, "lon": -114.35, "state": "ID"},
    {"name": "Tamarack", "lat": 44.68, "lon": -116.10, "state": "ID"},
    {"name": "Brundage Mountain", "lat": 44.85, "lon": -116.15, "state": "ID"},
    {"name": "Schweitzer", "lat": 48.37, "lon": -116.62, "state": "ID"},
    {"name": "Lookout Pass", "lat": 47.45, "lon": -115.97, "state": "ID"},
    {"name": "Breckenridge", "lat": 39.48, "lon": -106.07, "state": "CO"},
    {"name": "Monarch Mountain", "lat": 38.51, "lon": -106.33, "state": "CO"},
    {"name": "Ski Cooper", "lat": 39.36, "lon": -106.30, "state": "CO"},
    {"name": "Park City", "lat": 40.65, "lon": -111.51, "state": "UT"},
    {"name": "Snowbird", "lat": 40.58, "lon": -111.66, "state": "UT"},
    {"name": "Brighton", "lat": 40.60, "lon": -111.58, "state": "UT"},
    {"name": "Beaver Mountain", "lat": 41.97, "lon": -111.54, "state": "UT"},
    {"name": "Whitefish Mountain", "lat": 48.48, "lon": -114.36, "state": "MT"},
    {"name": "Big Sky", "lat": 45.28, "lon": -111.40, "state": "MT"},
    {"name": "Crystal Mountain", "lat": 44.92, "lon": -84.68, "state": "MI"},
    {"name": "Boyne Mountain", "lat": 45.17, "lon": -84.93, "state": "MI"},
    {"name": "Cannon Mountain", "lat": 44.16, "lon": -71.70, "state": "NH"},
    {"name": "Loon Mountain", "lat": 44.04, "lon": -71.62, "state": "NH"},
    {"name": "Camelback", "lat": 41.05, "lon": -75.36, "state": "PA"},
    {"name": "Jackson Hole", "lat": 43.59, "lon": -110.85, "state": "WY"},
]


def _find_nearest_ski(lat: float, lon: float) -> dict | None:
    """Find the nearest ski resort from the static list."""
    nearest = None
    min_dist = float("inf")
    for ski in SKI_AREAS:
        d = _haversine_miles(lat, lon, ski["lat"], ski["lon"])
        if d < min_dist:
            min_dist = d
            nearest = {"name": ski["name"], "distance_miles": d}
    return nearest


def _get_county_data(state: str, county: str) -> dict | None:
    """Look up static county-level data by state abbreviation and county name."""
    return COUNTY_DATA.get((state, county))


def compute_match_score(score: ListingScore, acreage: float, price: int) -> int:
    """Compute a 0-100 match score based on user requirements.

    Weights:
      Water proximity: 10     Hospital proximity: 8      Big-box proximity: 8
      Trails: 7               Republican lean: 7         Acreage fit: 10
      Price fit: 10           Low taxes: 5               Military friendly: 5
      Snow: 5                 Sunshine: 5                Pop growth: 5
      Ski resort: 5           Young population: 3        County size: 2
      Offroad: 5              Schools: 7
    """
    points = 0
    max_points = 0

    # Acreage 3-5 acres (10 pts)
    max_points += 10
    if 3.0 <= acreage <= 5.5:
        points += 10
    elif 2.5 <= acreage <= 7.0:
        points += 5

    # Under $200K (10 pts) — price is stored in cents
    max_points += 10
    if price <= 20000000:
        points += 10

    # Water nearby (10 pts)
    max_points += 10
    if score.nearest_water_miles is not None:
        if score.nearest_water_miles < 1:
            points += 10
        elif score.nearest_water_miles < 3:
            points += 7
        elif score.nearest_water_miles < 5:
            points += 4

    # Hospital within 30 min (~25 miles) (8 pts)
    max_points += 8
    if score.nearest_hospital_miles is not None:
        if score.nearest_hospital_miles < 25:
            points += 8
        elif score.nearest_hospital_miles < 40:
            points += 4

    # Big box within 45 min (~35 miles) (8 pts)
    max_points += 8
    if score.nearest_bigbox_miles is not None:
        if score.nearest_bigbox_miles < 35:
            points += 8
        elif score.nearest_bigbox_miles < 50:
            points += 4

    # Hiking trails nearby (7 pts)
    max_points += 7
    if score.nearest_trail_miles is not None:
        if score.nearest_trail_miles < 5:
            points += 7
        elif score.nearest_trail_miles < 15:
            points += 4

    # Offroading (5 pts)
    max_points += 5
    if score.nearest_offroad_miles is not None:
        if score.nearest_offroad_miles < 15:
            points += 5
        elif score.nearest_offroad_miles < 30:
            points += 3

    # Republican (7 pts)
    max_points += 7
    if score.county_political_lean and score.county_political_lean.startswith("R"):
        points += 7

    # Low taxes (5 pts) — under 0.8% is great, under 1.2% is ok
    max_points += 5
    if score.county_property_tax_rate is not None:
        if score.county_property_tax_rate < 0.8:
            points += 5
        elif score.county_property_tax_rate < 1.2:
            points += 3

    # Military friendly (5 pts)
    max_points += 5
    if score.county_mil_discount:
        points += 5

    # Snow (5 pts) — need at least 20 inches
    max_points += 5
    if score.avg_annual_snowfall_inches is not None:
        if score.avg_annual_snowfall_inches >= 30:
            points += 5
        elif score.avg_annual_snowfall_inches >= 20:
            points += 3

    # Sunshine (5 pts) — need at least 170 sunny days
    max_points += 5
    if score.avg_sunny_days is not None:
        if score.avg_sunny_days >= 200:
            points += 5
        elif score.avg_sunny_days >= 170:
            points += 3

    # Growing population (5 pts) — 5yr growth > 5%
    max_points += 5
    if score.county_pop_growth_pct is not None:
        if score.county_pop_growth_pct > 10:
            points += 5
        elif score.county_pop_growth_pct > 5:
            points += 3

    # Young people (3 pts) — median age < 38
    max_points += 3
    if score.county_median_age is not None:
        if score.county_median_age < 35:
            points += 3
        elif score.county_median_age < 40:
            points += 2

    # Decent population for services (2 pts) — county pop > 40K
    max_points += 2
    if score.county_population is not None:
        if score.county_population > 100000:
            points += 2
        elif score.county_population > 40000:
            points += 1

    # Ski/snowboarding within a few hours (~150 miles) (5 pts)
    max_points += 5
    if score.nearest_ski_resort_miles is not None:
        if score.nearest_ski_resort_miles < 60:
            points += 5
        elif score.nearest_ski_resort_miles < 150:
            points += 3

    # Good schools (7 pts)
    max_points += 7
    if score.school_district_rating:
        if score.school_district_rating in ("Good", "Above Average"):
            points += 7
        elif score.school_district_rating == "Average":
            points += 4

    return round((points / max_points) * 100) if max_points > 0 else 0


async def enrich_listing(
    listing_id: uuid.UUID,
    lat: float,
    lon: float,
    state: str,
    county: str,
    acreage: float,
    price: int,
) -> ListingScore:
    """Enrich a listing with proximity and area data.

    Queries the Overpass API for nearby POIs (hospitals, big-box stores,
    water bodies, trails, offroad tracks) and merges in static county-level
    data for politics, taxes, climate, and demographics.  Computes a 0-100
    match score at the end.
    """
    score = ListingScore(listing_id=listing_id)

    async with httpx.AsyncClient() as client:
        # Run proximity checks with delays to be polite to Overpass API
        hospital = await find_nearest_hospital(client, lat, lon)
        await asyncio.sleep(1)

        bigbox = await find_nearest_bigbox(client, lat, lon)
        await asyncio.sleep(1)

        water = await find_nearest_water(client, lat, lon)
        await asyncio.sleep(1)

        trail = await find_nearest_trail(client, lat, lon)
        await asyncio.sleep(1)

        offroad = await find_nearest_offroad(client, lat, lon)
        await asyncio.sleep(1)

        school = await find_nearest_school(client, lat, lon)

    if hospital:
        score.nearest_hospital_miles = round(hospital["distance_miles"], 1)
        score.nearest_hospital_name = hospital["name"]

    if bigbox:
        score.nearest_bigbox_miles = round(bigbox["distance_miles"], 1)
        score.nearest_bigbox_name = bigbox["name"]

    if water:
        score.nearest_water_miles = round(water["distance_miles"], 1)
        score.nearest_water_type = water.get("name", "water body")

    if trail:
        score.nearest_trail_miles = round(trail["distance_miles"], 1)
        score.nearest_trail_name = trail["name"]

    if offroad:
        score.nearest_offroad_miles = round(offroad["distance_miles"], 1)

    if school:
        score.nearest_school_miles = round(school["distance_miles"], 1)
        score.nearest_school_name = school["name"]

    # Ski resort (from static data)
    ski = _find_nearest_ski(lat, lon)
    if ski:
        score.nearest_ski_resort_miles = round(ski["distance_miles"], 1)
        score.nearest_ski_resort_name = ski["name"]

    # County data (from static lookup)
    county_info = _get_county_data(state, county)
    if county_info:
        score.county_political_lean = county_info["lean"]
        score.county_property_tax_rate = county_info["tax"]
        score.county_mil_discount = county_info["mil"]
        score.county_population = county_info["pop"]
        score.county_pop_growth_pct = county_info["growth"]
        score.county_median_age = county_info["median_age"]
        score.avg_annual_snowfall_inches = county_info["snow"]
        score.avg_sunny_days = county_info["sunny"]
        score.school_district_rating = county_info.get("schools")

    score.match_score = compute_match_score(score, acreage, price)
    score.enriched_at = datetime.now(timezone.utc)

    return score
