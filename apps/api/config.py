from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import model_validator


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

    # SEO / Multi-channel publishing
    SEO_MULTI_CHANNEL_AUTOPUBLISH: bool = False
    
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
    SEO_CONTENT_MULTI_CHANNEL_AUTOPUBLISH: bool = False
    
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

    @model_validator(mode="after")
    def validate_production_config(self) -> "Settings":
        """Validate that production environment has proper configuration."""
        if self.APP_ENV == "production":
            errors = []

            # Critical security settings
            if not self.SECRET_KEY or self.SECRET_KEY == "dev-secret-key-change-in-production":
                errors.append("SECRET_KEY must be set to a non-default value in production")

            # Critical LLM configuration
            if not self.DEEPSEEK_API_KEY:
                errors.append("DEEPSEEK_API_KEY is required in production")

            # Database password check
            if "prod_password" in self.DATABASE_URL:
                errors.append("Database password must not be the default 'prod_password' in production")

            # Conditional validation: only check credentials if autopublish is enabled
            if self.MOLTBOOK_AUTOPUBLISH:
                if not self.MOLTBOOK_API_KEY or not self.MOLTBOOK_AGENT_API_KEY or not self.MOLTBOOK_APP_KEY:
                    errors.append("Moltbook credentials are required when MOLTBOOK_AUTOPUBLISH is enabled in production")

            if self.X_AUTOPUBLISH:
                if not all([self.X_API_KEY, self.X_API_SECRET, self.X_ACCESS_TOKEN, self.X_ACCESS_TOKEN_SECRET]):
                    errors.append("X credentials are required when X_AUTOPUBLISH is enabled in production")

            if self.TELEGRAM_AUTOPUBLISH:
                if not self.TELEGRAM_BOT_TOKEN:
                    errors.append("Telegram bot token is required when TELEGRAM_AUTOPUBLISH is enabled in production")

            if self.SEO_MULTI_CHANNEL_AUTOPUBLISH:
                # SEO multi-channel publishing requires at least one platform configured
                if not (self.MOLTBOOK_AUTOPUBLISH or self.X_AUTOPUBLISH or self.TELEGRAM_AUTOPUBLISH):
                    errors.append("SEO multi-channel autopublish requires at least one platform (Moltbook, X, or Telegram) to have autopublish enabled")

            # Agent-specific autopublish validation
            for agent_prefix in ["FOUNDER_CONTENT", "TECHNICAL_CONTENT", "SEO_CONTENT"]:
                if getattr(self, f"{agent_prefix}_MOLTBOOK_AUTOPUBLISH", False):
                    if not all([
                        getattr(self, f"{agent_prefix}_MOLTBOOK_AGENT_API_KEY"),
                        getattr(self, f"{agent_prefix}_MOLTBOOK_APP_KEY")
                    ]):
                        errors.append(f"{agent_prefix} Moltbook credentials are required when autopublish is enabled in production")

                if getattr(self, f"{agent_prefix}_X_AUTOPUBLISH", False):
                    if not all([
                        getattr(self, f"{agent_prefix}_X_API_KEY"),
                        getattr(self, f"{agent_prefix}_X_API_SECRET"),
                        getattr(self, f"{agent_prefix}_X_ACCESS_TOKEN"),
                        getattr(self, f"{agent_prefix}_X_ACCESS_TOKEN_SECRET")
                    ]):
                        errors.append(f"{agent_prefix} X credentials are required when autopublish is enabled in production")

                if getattr(self, f"{agent_prefix}_TELEGRAM_AUTOPUBLISH", False):
                    if not all([
                        getattr(self, f"{agent_prefix}_TELEGRAM_BOT_TOKEN"),
                        getattr(self, f"{agent_prefix}_TELEGRAM_CHAT_ID")
                    ]):
                        errors.append(f"{agent_prefix} Telegram credentials are required when autopublish is enabled in production")

            if errors:
                self._production_validation_errors = errors
                # Don't raise here - let the lifespan handler decide
        else:
            self._production_validation_errors = None

        return self

    def validate_production_startup(self) -> list[str]:
        """
        Explicit validation method to be called at startup.
        Returns list of errors if production config is invalid, empty list otherwise.
        This allows audit event recording before raising the error.
        """
        if self.APP_ENV == "production":
            return getattr(self, "_production_validation_errors", [])
        return []


settings = Settings()
