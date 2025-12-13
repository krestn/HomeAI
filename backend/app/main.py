from fastapi import FastAPI
from app.api.api import api_router

app = FastAPI(title="Homeowner AI")

app.include_router(api_router)

@app.get("/")
def root():
    return {"status": "ok"}
