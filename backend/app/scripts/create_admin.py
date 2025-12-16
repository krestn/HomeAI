from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

db = SessionLocal()

password = "homeai"  

admin = User(
    first_name="Kreston",
    last_name="Caldwell",
    phone_number="6308705588",
    email="kreston@homeai.com",
    password_hash=hash_password(password),
    is_admin=True,
)

db.add(admin)
db.commit()
db.refresh(admin)

print("Admin user created:", admin.id)
