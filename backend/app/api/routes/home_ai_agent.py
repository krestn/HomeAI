from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.home_ai_agent import run_home_agent

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    message: str
    property_id: int | None = None


@router.post("/chat")
def chat_agent(
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent_result = run_home_agent(
        db=db,
        user_id=current_user.id,
        message=payload.message,
        property_id=payload.property_id,
    )

    return {
        "reply": agent_result["reply"],
        "user_id": current_user.id,
        "active_property": agent_result["active_property"],
        "available_properties": agent_result["available_properties"],
        "requires_property_selection": agent_result["requires_property_selection"],
    }
