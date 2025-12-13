# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from app.core.database import SessionLocal
# from app.models.home import Home

# router = APIRouter()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# @router.post("/")
# def create_home(payload: dict, db: Session = Depends(get_db)):
#     home = Home(**payload)
#     db.add(home)
#     db.commit()
#     db.refresh(home)
#     return home
