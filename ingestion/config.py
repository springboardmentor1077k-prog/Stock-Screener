import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

def get_env_var(key: str, required: bool = True, default: Any = None) -> str:
    value = os.getenv(key, default)
    if required and value is None:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value

ALPHA_API_KEY: str = get_env_var("ALPHA_VANTAGE_API_KEY")

DB_CONFIG: Dict[str, Any] = {
    "host": get_env_var("DB_HOST"),
    "user": get_env_var("DB_USER"),
    "password": get_env_var("DB_PASSWORD"),
    "database": get_env_var("DB_NAME"),
    "port": int(get_env_var("DB_PORT")),
}
