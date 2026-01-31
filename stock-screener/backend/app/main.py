
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.routes import auth, screener, portfolio
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(screener.router, prefix=f"{settings.API_V1_STR}/screener", tags=["screener"])
app.include_router(portfolio.router, prefix=f"{settings.API_V1_STR}/portfolio", tags=["portfolio"])

@app.on_event("startup")
def create_initial_data():
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
