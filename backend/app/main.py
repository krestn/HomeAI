from fastapi import FastAPI
from app.api.api import api_router

app = FastAPI(title="HomeAI")

app.include_router(api_router)

@app.get("/")
def root():
    return {"status": "ok"}
