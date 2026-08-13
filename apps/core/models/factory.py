from google.adk.models.lite_llm import LiteLlm
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import logging
from apps.api.config import settings as api_settings

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    deepseek_api_key: Optional[str] = None
    deepseek_primary_model: str = "deepseek/deepseek-v4-flash"
    deepseek_reasoning_model: str = "deepseek/deepseek-v4-pro"
    deepseek_api_base: str = "https://api.deepseek.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Defer full instantiation or use lazy
settings = Settings()  # Will use defaults/env; no crash if key missing for imports

def deepseek_fast() -> Optional[LiteLlm]:
    if not settings.deepseek_api_key:
        # Returns None for test/Alembic import safety
        # Production code should check for None and treat as error
        if api_settings.APP_ENV == "production":
            logger.error("DEEPSEEK_API_KEY is missing in production environment")
        return None
    return LiteLlm(model=settings.deepseek_primary_model, api_key=settings.deepseek_api_key, api_base=settings.deepseek_api_base, temperature=0.4)

def deepseek_reasoning() -> Optional[LiteLlm]:
    if not settings.deepseek_api_key:
        # Returns None for test/Alembic import safety
        # Production code should check for None and treat as error
        if api_settings.APP_ENV == "production":
            logger.error("DEEPSEEK_API_KEY is missing in production environment")
        return None
    return LiteLlm(model=settings.deepseek_reasoning_model, api_key=settings.deepseek_api_key, api_base=settings.deepseek_api_base, temperature=0.2)

def deepseek_fast_or_raise() -> LiteLlm:
    """
    Production-safe model instantiation that raises if credentials are missing.
    Use this in production code paths where a valid model is required.
    """
    model = deepseek_fast()
    if model is None:
        raise ValueError("DEEPSEEK_API_KEY is required in production")
    return model

def deepseek_reasoning_or_raise() -> LiteLlm:
    """
    Production-safe model instantiation that raises if credentials are missing.
    Use this in production code paths where a valid model is required.
    """
    model = deepseek_reasoning()
    if model is None:
        raise ValueError("DEEPSEEK_API_KEY is required in production")
    return model
