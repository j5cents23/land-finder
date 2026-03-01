from scraper.db import get_engine, get_session
from scraper.models import Base, Listing


def test_get_engine_creates_tables():
    engine = get_engine(":memory:")
    Base.metadata.create_all(engine)
    with get_session(engine) as session:
        result = session.query(Listing).all()
        assert result == []


def test_get_session_is_usable():
    engine = get_engine(":memory:")
    Base.metadata.create_all(engine)
    with get_session(engine) as session:
        assert session.is_active
