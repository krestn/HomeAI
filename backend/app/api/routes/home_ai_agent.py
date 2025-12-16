from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.home_ai_agent import run_home_agent

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat")
def chat_agent(
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reply = run_home_agent(
        db=db,
        user_id=current_user.id,
        message=message,
    )

    return {
        "reply": reply,
        "user_id": current_user.id,
    }
