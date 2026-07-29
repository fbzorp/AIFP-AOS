from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Application Settings
    APP_ENV: str = "development"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    HTTP_TIMEOUT_SECONDS: int = 20
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aifp:devpassword@localhost:5432/aifp_dev"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI / LLM
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: Optional[str] = None
    DEEPSEEK_PRIMARY_MODEL: Optional[str] = None
    DEEPSEEK_REASONING_MODEL: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DAILY_LLM_BUDGET_USD: float = 25.00
    
    # AiFinPay SDK
    AIFP_API_KEY: Optional[str] = None
    AIFP_BASE_URL: str = "https://api.aifinpay.com"
    
    # Moltbook / Social
    MOLTBOOK_BASE_URL: str = "https://www.moltbook.com"
    MOLTBOOK_API_KEY: Optional[str] = None
    MOLTBOOK_AGENT_API_KEY: Optional[str] = None
    MOLTBOOK_APP_KEY: Optional[str] = None
    MOLTBOOK_AUTOPUBLISH: bool = False
    MOLTBOOK_ALLOWED_SUBMOLTS: str = "general,aifintech,aiagents"
    
    # Other Social Media APIs
    X_API_KEY: Optional[str] = None
    X_API_SECRET: Optional[str] = None
    X_ACCESS_TOKEN: Optional[str] = None
    X_ACCESS_TOKEN_SECRET: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    
    # Blockchain
    SOLANA_RPC_URL: str = "https://api.devnet.solana.com"
    SOLANA_PRIVATE_KEY: Optional[str] = None
    EVM_RPC_URL: Optional[str] = None
    EVM_PRIVATE_KEY: Optional[str] = None
    
    # X402 Settings
    X402_ENABLED: bool = True
    X402_FACILITATOR_URL: str = "https://x402.aifinpay.com"
    PAYMENTS_NETWORK: str = "devnet"

    # Security / Limits
    DAILY_SPENDING_LIMIT: float = 100.00
    PER_TRANSACTION_LIMIT: float = 50.00
    HUMAN_APPROVAL_THRESHOLD: float = 25.00

    # X402 and Payments
    X402_ENABLED: bool = False
    X402_FACILITATOR_URL: Optional[str] = None
    PAYMENTS_NETWORK: str = "devnet"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True, 
        extra="ignore"
    )


settings = Settings()
