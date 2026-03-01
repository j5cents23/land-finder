import enum
import uuid
from datetime import datetime

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
