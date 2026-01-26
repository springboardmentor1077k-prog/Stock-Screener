from fastapi import FastAPI
from backend.auth import router as auth_router
from backend.ai.routes import router as ai_router

app = FastAPI(title="AI Stock Screener")

app.include_router(auth_router)
app.include_router(ai_router)
