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
