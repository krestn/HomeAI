from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    UniqueConstraint,
    Index,
)
from app.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    __table_args__ = (
        # Prevent duplicate physical addresses
        UniqueConstraint(
            "street_address",
            "city",
            "state",
            "postal_code",
            name="uq_property_address",
        ),
        # Common lookup indexes
        Index("ix_properties_city_state", "city", "state"),
        Index("ix_properties_county_state", "county", "state"),
        Index("ix_properties_postal_code", "postal_code"),
        Index("ix_properties_formatted_address", "formatted_address"),
    )

    id = Column(Integer, primary_key=True)

    street_address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    county = Column(String, nullable=True)
    state = Column(String(2), nullable=False)
    postal_code = Column(String(10), nullable=False)

    country = Column(String(2), default="US")
    formatted_address = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
