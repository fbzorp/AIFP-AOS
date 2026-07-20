from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aifp:devpassword@localhost:5432/aifp_dev"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI / LLM API Keys
    DEEPSEEK_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # AiFinPay SDK
    AIFP_API_KEY: Optional[str] = None
    AIFP_BASE_URL: str = "https://api.aifinpay.com"
    
    # Social Media APIs
    X_API_KEY: Optional[str] = None
    X_API_SECRET: Optional[str] = None
    X_ACCESS_TOKEN: Optional[str] = None
    X_ACCESS_TOKEN_SECRET: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    MOLTBOOK_API_KEY: Optional[str] = None
    
    # Blockchain
    SOLANA_RPC_URL: str = "https://api.devnet.solana.com"
    SOLANA_PRIVATE_KEY: Optional[str] = None
    EVM_RPC_URL: Optional[str] = None
    EVM_PRIVATE_KEY: Optional[str] = None
    
    # Application Settings
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Security
    DAILY_SPENDING_LIMIT: float = 100.00
    PER_TRANSACTION_LIMIT: float = 50.00
    HUMAN_APPROVAL_THRESHOLD: float = 25.00
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
