#!/usr/bin/env python3
"""Set up search criteria for land search across target states."""
import uuid

from scraper.db import get_engine, get_session
from scraper.models import Base, SearchCriteria


def _build_criteria() -> list[SearchCriteria]:
    """Return the full list of regional search criteria."""
    return [
        SearchCriteria(
            id=uuid.uuid4(),
            name="Idaho - Boise Area",
            min_acreage=3.0,
            max_price=20000000,  # $200K in cents
            max_ppa=None,
            states=["ID"],
            counties=["Ada", "Canyon", "Gem", "Boise", "Elmore"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="Idaho - North (Coeur d'Alene)",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["ID"],
            counties=["Kootenai", "Bonner", "Boundary", "Shoshone"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="Idaho - East (Idaho Falls)",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["ID"],
            counties=["Bonneville", "Madison", "Jefferson", "Fremont"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="Colorado - Springs Area",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["CO"],
            counties=["El Paso", "Teller", "Park", "Fremont", "Douglas"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="Utah - Wasatch Front",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["UT"],
            counties=["Utah", "Wasatch", "Summit", "Cache", "Box Elder"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="Montana - West",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["MT"],
            counties=[
                "Flathead", "Gallatin", "Missoula", "Lewis and Clark", "Ravalli",
            ],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="Michigan - West",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["MI"],
            counties=["Grand Traverse", "Kalamazoo", "Allegan", "Kent", "Ottawa"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="New Hampshire",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["NH"],
            counties=["Grafton", "Carroll", "Coos", "Merrimack", "Belknap"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="Pennsylvania - Poconos",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["PA"],
            counties=["Monroe", "Pike", "Wayne", "Lackawanna", "Carbon"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="West Virginia - Eastern Panhandle",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["WV"],
            counties=["Jefferson", "Berkeley", "Morgan", "Hardy"],
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
        SearchCriteria(
            id=uuid.uuid4(),
            name="Wyoming",
            min_acreage=3.0,
            max_price=20000000,
            max_ppa=None,
            states=["WY"],
            counties=[],  # All counties
            require_water=False,
            require_utils=False,
            require_road=False,
            zoning_types=[],
            is_active=True,
        ),
    ]


def setup() -> None:
    """Create all search criteria in the database."""
    engine = get_engine()
    Base.metadata.create_all(engine)

    with get_session(engine) as session:
        # Clear existing criteria
        session.query(SearchCriteria).delete()

        criteria_list = _build_criteria()
        for criteria in criteria_list:
            session.add(criteria)

        print(f"Created {len(criteria_list)} search criteria")


if __name__ == "__main__":
    setup()
