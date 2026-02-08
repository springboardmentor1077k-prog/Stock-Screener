from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.routes import router
from app.core import settings, setup_logging
from app.db import init_db_pool, close_db_pool

# Setup logging
setup_logging()

app = FastAPI()

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
app.include_router(router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    """Initialize database connection pool on startup."""
    init_db_pool()

@app.on_event("shutdown")
def shutdown_event():
    """Close database connection pool on shutdown."""
    close_db_pool()
    