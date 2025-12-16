from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.property import Property
from app.models.property_users import PropertyUsers
from app.core.security import hash_password


def seed():
    db: Session = SessionLocal()
    DEV_PASSWORD = "password123"

    try:
        # ---------- USERS ----------
        owner = User(
            first_name="John",
            last_name="Owner",
            phone_number="5551110001",
            email="owner@test.com",
            password_hash=hash_password(DEV_PASSWORD),
            is_admin=False,
        )

        renter = User(
            first_name="Jane",
            last_name="Renter",
            phone_number="5551110002",
            email="renter@test.com",
            password_hash=hash_password(DEV_PASSWORD),
            is_admin=False,
        )

        plumber = User(
            first_name="Paul",
            last_name="Plumber",
            phone_number="5551110003",
            email="plumber@test.com",
            password_hash=hash_password(DEV_PASSWORD),
            is_admin=False,
        )

        db.add_all([owner, renter, plumber])
        db.commit()

        db.refresh(owner)
        db.refresh(renter)
        db.refresh(plumber)

        # ---------- PROPERTY ----------
        property_1 = Property(
            street_address="129 Vernon Dr.",
            city="Bolingbrook",
            county="Will",
            state="IL",
            postal_code="60544",
            country="US",
            formatted_address="129 Vernon Dr. Bolingbrook, IL 60544",
        )
        property_2 = Property(
            street_address="704 Claremont Ave.",
            city="Chicago",
            county="Cook",
            state="IL",
            postal_code="60612",
            country="US",
            formatted_address="704 Claremont Ave. Chicago, IL 60612",
        )

        db.add_all([property_1, property_2]),
        db.commit()
        db.refresh(property_1)
        db.refresh(property_2)

        # ---------- PROPERTY RELATIONSHIPS ----------
        owner_relationship1 = PropertyUsers(
            user_id=owner.id,
            property_id=property_1.id,
            role="owner",
            start_date=datetime.utcnow(),
            is_active=True,
        )

        owner_relationship2 = PropertyUsers(
            user_id=owner.id,
            property_id=property_2.id,
            role="owner",
            start_date=datetime.utcnow(),
            is_active=True,
        )

        renter_relationship = PropertyUsers(
            user_id=renter.id,
            property_id=property_1.id,
            role="renter",
            start_date=datetime.utcnow(),
            is_active=True,
        )

        plumber_relationship = PropertyUsers(
            user_id=plumber.id,
            property_id=property_1.id,
            role="service_provider",
            start_date=datetime.utcnow(),
            is_active=True,
        )

        db.add_all(
            [
                owner_relationship1,
                owner_relationship2,
                renter_relationship,
                plumber_relationship,
            ]
        )
        db.commit()

        print("✅ Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print("❌ Seeding failed:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
