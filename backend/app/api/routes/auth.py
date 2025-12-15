from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.auth import oauth2_scheme


from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.user import User
from sqlalchemy import or_

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    identifier = form_data.username  # email OR phone

    user = (
        db.query(User)
        .filter(
            or_(
                User.email == identifier,
                User.phone_number == identifier,
            )
        )
        .first()
    )

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    # Stateless logout — client must discard token
    return {"message": "Logged out"}
