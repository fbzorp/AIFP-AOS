from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Application Settings
    APP_ENV: str = "development"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    HTTP_TIMEOUT_SECONDS: int = 20
    
    # Embedding Model Settings
    EMBEDDING_MODEL_DIR: str = "/opt/models/all-MiniLM-L6-v2"
    
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
    AIFP_BASE_URL: str = "https://api.aifinpay.io"
    AIFINPAY_AGENT_SECRET: Optional[str] = None  # base58 Ed25519 secret key
    AIFINPAY_AGENT_PUBKEY: Optional[str] = None  # Ed25519 public key
    AIFINPAY_MAX_USD: float = 0.10  # per payable_fetch cap
    AIFINPAY_MCP_ENABLED: bool = False
    
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
    X_AUTOPUBLISH: bool = False
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_AUTOPUBLISH: bool = False
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_DEFAULT_CHANNEL: Optional[str] = None
    
    # News/Search APIs for Market Intelligence
    NEWS_API_KEY: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None
    
    # Agent-Specific Credentials (Single Source of Truth)
    # Founder Content Agent
    FOUNDER_CONTENT_X_API_KEY: Optional[str] = None
    FOUNDER_CONTENT_X_API_SECRET: Optional[str] = None
    FOUNDER_CONTENT_X_ACCESS_TOKEN: Optional[str] = None
    FOUNDER_CONTENT_X_ACCESS_TOKEN_SECRET: Optional[str] = None
    FOUNDER_CONTENT_X_AUTOPUBLISH: bool = False
    FOUNDER_CONTENT_TELEGRAM_BOT_TOKEN: Optional[str] = None
    FOUNDER_CONTENT_TELEGRAM_CHAT_ID: Optional[str] = None
    FOUNDER_CONTENT_TELEGRAM_AUTOPUBLISH: bool = False
    FOUNDER_CONTENT_TELEGRAM_DEFAULT_CHANNEL: Optional[str] = None
    FOUNDER_CONTENT_MOLTBOOK_AGENT_API_KEY: Optional[str] = None
    FOUNDER_CONTENT_MOLTBOOK_APP_KEY: Optional[str] = None
    FOUNDER_CONTENT_MOLTBOOK_AUTOPUBLISH: bool = False
    
    # Technical Content Agent
    TECHNICAL_CONTENT_X_API_KEY: Optional[str] = None
    TECHNICAL_CONTENT_X_API_SECRET: Optional[str] = None
    TECHNICAL_CONTENT_X_ACCESS_TOKEN: Optional[str] = None
    TECHNICAL_CONTENT_X_ACCESS_TOKEN_SECRET: Optional[str] = None
    TECHNICAL_CONTENT_X_AUTOPUBLISH: bool = False
    TECHNICAL_CONTENT_TELEGRAM_BOT_TOKEN: Optional[str] = None
    TECHNICAL_CONTENT_TELEGRAM_CHAT_ID: Optional[str] = None
    TECHNICAL_CONTENT_TELEGRAM_AUTOPUBLISH: bool = False
    TECHNICAL_CONTENT_TELEGRAM_DEFAULT_CHANNEL: Optional[str] = None
    TECHNICAL_CONTENT_MOLTBOOK_AGENT_API_KEY: Optional[str] = None
    TECHNICAL_CONTENT_MOLTBOOK_APP_KEY: Optional[str] = None
    TECHNICAL_CONTENT_MOLTBOOK_AUTOPUBLISH: bool = False
    
    # SEO Content Agent
    SEO_CONTENT_X_API_KEY: Optional[str] = None
    SEO_CONTENT_X_API_SECRET: Optional[str] = None
    SEO_CONTENT_X_ACCESS_TOKEN: Optional[str] = None
    SEO_CONTENT_X_ACCESS_TOKEN_SECRET: Optional[str] = None
    SEO_CONTENT_X_AUTOPUBLISH: bool = False
    SEO_CONTENT_TELEGRAM_BOT_TOKEN: Optional[str] = None
    SEO_CONTENT_TELEGRAM_CHAT_ID: Optional[str] = None
    SEO_CONTENT_TELEGRAM_AUTOPUBLISH: bool = False
    SEO_CONTENT_TELEGRAM_DEFAULT_CHANNEL: Optional[str] = None
    SEO_CONTENT_MOLTBOOK_AGENT_API_KEY: Optional[str] = None
    SEO_CONTENT_MOLTBOOK_APP_KEY: Optional[str] = None
    SEO_CONTENT_MOLTBOOK_AUTOPUBLISH: bool = False
    
    # Blockchain
    SOLANA_RPC_URL: str = "https://api.devnet.solana.com"
    SOLANA_PRIVATE_KEY: Optional[str] = None
    EVM_RPC_URL: Optional[str] = None
    EVM_PRIVATE_KEY: Optional[str] = None
    
    # X402 Settings
    X402_ENABLED: bool = True
    X402_FACILITATOR_URL: str = "https://api.aifinpay.io"
    PAYMENTS_NETWORK: str = "devnet"

    # Security / Limits
    DAILY_SPENDING_LIMIT: float = 100.00
    PER_TRANSACTION_LIMIT: float = 50.00
    HUMAN_APPROVAL_THRESHOLD: float = 25.00
    
    # Payment Security
    RECIPIENT_ALLOWLIST: str = "" # Comma-separated addresses
    PAYMENTS_KILL_SWITCH: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True, 
        extra="ignore"
    )


settings = Settings()
