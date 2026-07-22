from google.adk.models.lite_llm import LiteLlm
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field

class Settings(BaseSettings):
    deepseek_api_key: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    deepseek_primary_model: str = "deepseek/deepseek-v4-flash"
    deepseek_reasoning_model: str = "deepseek/deepseek-v4-pro"
    deepseek_api_base: str = "https://api.deepseek.com"

    class Config:
        env_file = ".env"
        extra = "ignore"

# Defer full instantiation or use lazy
settings = Settings()  # Will use defaults/env; no crash if key missing for imports

def deepseek_fast() -> LiteLlm:
    if not settings.deepseek_api_key:
        # Fallback for tests/Alembic
        return None  # or raise in production use
    return LiteLlm(model=settings.deepseek_primary_model, api_key=settings.deepseek_api_key, api_base=settings.deepseek_api_base, temperature=0.4)

def deepseek_reasoning() -> LiteLlm:
    if not settings.deepseek_api_key:
        return None
    return LiteLlm(model=settings.deepseek_reasoning_model, api_key=settings.deepseek_api_key, api_base=settings.deepseek_api_base, temperature=0.2)