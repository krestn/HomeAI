from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/home")
def health(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
    }
