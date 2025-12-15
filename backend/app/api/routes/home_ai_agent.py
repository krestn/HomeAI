from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.services.home_ai_agent import run_home_agent

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/chat")
def chat_agent(
    message: str,
    current_user: User = Depends(get_current_user),
):
    reply = run_home_agent(message)

    return {
        "reply": reply,
        "user_id": current_user.id,
    }
