"""Batch enrich listings that don't have scores yet, with rate limiting."""
import asyncio
import logging
import sys

from scraper.db import get_engine, get_session
from scraper.models import Base, Listing, ListingScore
from scraper.pipeline.enricher import enrich_listing

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("enrich-batch")


async def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    engine = get_engine()
    Base.metadata.create_all(engine)

    with get_session(engine) as session:
        existing_ids = {
            row[0]
            for row in session.query(ListingScore.listing_id).all()
        }

        listings = (
            session.query(Listing)
            .filter(
                Listing.latitude.isnot(None),
                Listing.longitude.isnot(None),
                Listing.is_active == True,  # noqa: E712
            )
            .all()
        )

        unenriched = [l for l in listings if l.id not in existing_ids]
        batch = unenriched[:limit]
        logger.info(
            "Enriching %d of %d unenriched listings (of %d with coords)",
            len(batch),
            len(unenriched),
            len(listings),
        )

        enriched = 0
        for i, listing in enumerate(batch):
            try:
                score = await enrich_listing(
                    listing.id,
                    listing.latitude,
                    listing.longitude,
                    listing.state,
                    listing.county,
                    listing.acreage,
                    listing.price,
                )
                session.merge(score)
                session.commit()
                enriched += 1
                logger.info(
                    "[%d/%d] %s, %s — score: %s",
                    i + 1,
                    len(batch),
                    listing.city,
                    listing.state,
                    score.match_score,
                )
            except Exception as e:
                logger.warning("[%d/%d] Failed: %s", i + 1, len(batch), e)

            # 2-second delay between listings to avoid Overpass rate limits
            await asyncio.sleep(2)

        logger.info("Done. Enriched %d listings.", enriched)


if __name__ == "__main__":
    asyncio.run(main())
