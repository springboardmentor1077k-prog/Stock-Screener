from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import sqlite3
from utils.logging_config import logger

# Retry for transient DB errors
db_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((sqlite3.OperationalError, sqlite3.DatabaseError)),
    before_sleep=lambda retry_state: logger.warning(f"Retrying DB operation... Attempt {retry_state.attempt_number}")
)

# For external API calls (simulated)
external_api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    before_sleep=lambda retry_state: logger.warning(f"Retrying External API call... Attempt {retry_state.attempt_number}")
)
