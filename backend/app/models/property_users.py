from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    DateTime,
    Boolean,
    func,
    UniqueConstraint,
    Index,
    text,
)
from app.core.database import Base


class PropertyUsers(Base):
    __tablename__ = "property_users"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # Role describes WHY the user is related to the property
    # Examples: owner, renter, service_provider, etc
    role = Column(String, nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        # Prevent duplicate users
        UniqueConstraint(
            "user_id",
            "property_id",
            "role",
            name="uq_property_user",
        ),
        # Indexes for fast authorization checks
        Index("ix_property_users_user_id", "user_id"),
        Index("ix_property_users_property_id", "property_id"),
        Index(
            "ix_property_users_active_only",
            "user_id",
            "property_id",
            postgresql_where=text("is_active = true"),
        ),
    )
