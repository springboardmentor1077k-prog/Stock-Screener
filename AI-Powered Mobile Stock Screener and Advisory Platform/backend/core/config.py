# Core Configuration for Stock Screener
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://username:password@localhost/stock_screener")
    
    # JWT settings
    secret_key: str = os.getenv("SECRET_KEY")
    
    def __init__(self, **values):
        super().__init__(**values)
        # Validate that SECRET_KEY is set
        if not self.secret_key:
            raise ValueError("SECRET_KEY environment variable must be set. Please configure your .env file.")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # OpenAI settings
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_deployment: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    # Market data settings
    alpha_vantage_api_key: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    # Application settings
    app_name: str = "AI-Powered Stock Screener API"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API timeout settings
    api_request_timeout: int = int(os.getenv("API_REQUEST_TIMEOUT", "30"))  # Default 30 seconds
    
    class Config:
        # Load configuration from the main config directory so the app
        # picks up values from config/.env without extra setup.
        env_file = "config/.env"

settings = Settings()