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
from scraper.spiders.facebook import FacebookSpider
from scraper.spiders.land_com import LandComSpider
from scraper.spiders.landwatch import LandWatchSpider
from scraper.spiders.zillow import ZillowSpider

logger = logging.getLogger("land-finder")

SPIDERS = {
    "craigslist": CraigslistSpider,
    "landwatch": LandWatchSpider,
    "land_com": LandComSpider,
    "zillow": ZillowSpider,
    "facebook": FacebookSpider,
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
    runs = runs[-100:]
    log_path.write_text(json.dumps(runs, indent=2))

    logger.info(f"Run complete: {run_summary['new_matches']} new matches from {run_summary['total_raw']} raw")
    return run_summary
