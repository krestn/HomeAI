from sqlalchemy.orm import Session
from app.models.property_users import PropertyUsers
from app.models.property import Property


def get_user_properties(db: Session, user_id: int) -> list[Property]:
    return (
        db.query(Property)
        .join(PropertyUsers, Property.id == PropertyUsers.property_id)
        .filter(
            PropertyUsers.user_id == user_id,
            PropertyUsers.is_active.is_(True),
        )
        .all()
    )