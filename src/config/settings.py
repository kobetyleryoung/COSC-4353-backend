from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from config.logging_config import logger
from typing import List

# base pydantic settings class
class Settings(BaseSettings):
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
    AUTH0_AUDIENCE: str = os.getenv("AUTH0_AUDIENCE", "")
    AUTH0_ALGORITHM: str = "RS256"
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()

# filter out any formatting issues
# e.g. spaces after commas or empty strings
def cors_origins() -> List[str]:
    return [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()]