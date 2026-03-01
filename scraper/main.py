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
