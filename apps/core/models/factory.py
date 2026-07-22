from google.adk.models.lite_llm import LiteLlm
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    deepseek_api_key: str
    deepseek_primary_model: str = "deepseek/deepseek-v4-flash"
    deepseek_reasoning_model: str = "deepseek/deepseek-v4-pro"
    deepseek_api_base: str = "https://api.deepseek.com"

settings = Settings()

def deepseek_fast() -> LiteLlm:
    return LiteLlm(model=settings.deepseek_primary_model, api_key=settings.deepseek_api_key, api_base=settings.deepseek_api_base, temperature=0.4)

def deepseek_reasoning() -> LiteLlm:
    return LiteLlm(model=settings.deepseek_reasoning_model, api_key=settings.deepseek_api_key, api_base=settings.deepseek_api_base, temperature=0.2)
