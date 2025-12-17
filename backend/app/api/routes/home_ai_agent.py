from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.home_ai_agent import run_home_agent

WELCOME_TRIGGER_MESSAGE = "__homeai_welcome__"

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    message: str
    property_id: int | None = None


def build_welcome_response(user: User) -> dict:
    reply = (
        f"Hi {user.first_name}, I'm your HomeAI assistant. "
        "I'm here to help you with any questions or tasks related to your home. "
        "How can I assist you today?"
    )

    return {
        "reply": reply,
        "user_id": user.id,
        "user_name": f"{user.first_name} {user.last_name}",
        "active_property": None,
        "available_properties": [],
        "requires_property_selection": False,
    }


@router.post("/chat")
def chat_agent(
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.message == WELCOME_TRIGGER_MESSAGE:
        return build_welcome_response(current_user)

    agent_result = run_home_agent(
        db=db,
        user_id=current_user.id,
        message=payload.message,
        property_id=payload.property_id,
    )

    return {
        "reply": agent_result["reply"],
        "user_id": current_user.id,
        "user_name": f"{current_user.first_name} {current_user.last_name}",
        "active_property": agent_result["active_property"],
        "available_properties": agent_result["available_properties"],
        "requires_property_selection": agent_result["requires_property_selection"],
    }


@router.get("/welcome")
def welcome_message(current_user: User = Depends(get_current_user)):
    return build_welcome_response(current_user)
