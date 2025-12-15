from fastapi import APIRouter
from app.api.routes import health, auth
from app.api.routes import home_ai_agent

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health")
api_router.include_router(auth.router)
api_router.include_router(home_ai_agent.router)


# api_router.include_router(homes.router, prefix="/homes")
