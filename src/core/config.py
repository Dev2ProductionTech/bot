"""Application configuration"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Environment
    ENVIRONMENT: str = Field(default="production")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    
    # Application
    APP_NAME: str = Field(default="Dev2Production Bot")
    SECRET_KEY: str = Field(..., min_length=32)
    
    # Database (Replit provides this automatically)
    DATABASE_URL: str = Field(default="")
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., min_length=40)
    TELEGRAM_WEBHOOK_SECRET: str = Field(..., min_length=32)
    TELEGRAM_WEBHOOK_URL: str = Field(...)
    AGENT_GROUP_CHAT_ID: Optional[int] = Field(default=None)
    
    # LongCat API
    LONGCAT_API_KEY: str = Field(..., min_length=20)
    LONGCAT_BASE_URL: str = Field(default="https://api.longcat.chat/v1")
    LONGCAT_MODEL: str = Field(default="gpt-4o-mini")
    LONGCAT_MAX_TOKENS: int = Field(default=500)
    LONGCAT_TIMEOUT: int = Field(default=30)
    
    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = Field(default=60)
    RATE_LIMIT_PER_DAY: int = Field(default=500)
    
    # LLM Quotas
    LLM_SESSION_LIMIT: int = Field(default=10)
    LLM_DAILY_LIMIT: int = Field(default=50)
    LLM_DAILY_BUDGET_USD: float = Field(default=100.0)
    
    @validator("TELEGRAM_BOT_TOKEN")
    def validate_telegram_token(cls, v):
        """Validate Telegram bot token format"""
        if not v or len(v) < 40:
            raise ValueError("Invalid Telegram bot token")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """Ensure secret key is strong"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
    
    @validator("DATABASE_URL", pre=True, always=True)
    def get_database_url(cls, v):
        """Get DATABASE_URL from Replit or environment"""
        if v:
            return v
        # Replit provides DATABASE_URL automatically
        return os.getenv("DATABASE_URL", "postgresql://localhost/dev2prod_bot")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
