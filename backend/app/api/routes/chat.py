from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.services.openai_client import client

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat(
    message: str,
    current_user: User = Depends(get_current_user),
):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=message,
    )

    return {
        "reply": response.output_text,
        "user_id": current_user.id,
    }
