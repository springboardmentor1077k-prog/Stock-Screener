# import os

# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql://postgres:postgres@db:5432/stocks"
# )

# REDIS_URL = os.getenv(
#     "REDIS_URL",
#     "redis://redis:6379"
# )

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/stocks"
    REDIS_URL: str = "redis://redis:6379"
    SECRET_KEY: str = "supersecretkey"
    ALPHA_VANTAGE_API_KEY: str
    FINNHUB_API_KEY: str
    REDIS_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
settings = Settings()
settings.DATABASE_URL