import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
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
    REALTOR = "realtor"


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


class ListingScore(Base):
    __tablename__ = "listing_scores"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("listings.id"), primary_key=True
    )

    # Proximity scores (distance in miles, None = not checked yet)
    nearest_hospital_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_hospital_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    nearest_bigbox_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_bigbox_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nearest_water_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_water_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # lake, river, creek
    nearest_trail_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_trail_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nearest_offroad_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_ski_resort_miles: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    nearest_ski_resort_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    # Area data
    county_political_lean: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # R+15, D+5, etc
    county_property_tax_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # percentage
    county_mil_discount: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    county_population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    county_pop_growth_pct: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 5-year %
    county_median_age: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Climate
    avg_annual_snowfall_inches: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    avg_sunny_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # School quality
    nearest_school_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_school_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_district_rating: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "Above Average", "Average", etc.

    # Overall match score (0-100)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    enriched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
