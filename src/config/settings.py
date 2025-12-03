"""Configuration settings for the Deep Research Agent."""

from pathlib import Path
from typing import Optional
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="ignore",  # Ignore extra environment variables
    )
    
    # API Keys
    openai_api_key: str
    anthropic_api_key: str
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
    # Agent Configuration
    max_search_depth: int
    max_queries_per_depth: int # Max queries to generate per depth and execute per iteration
    min_confidence_threshold: float
    max_concurrent_searches: int
    
    # Model Configuration
    openai_search_model: str
    openai_extraction_model: str
    claude_model: str
    
    # Web Search Configuration
    web_search_external_access: bool = True  # Allow live web access (vs cached only)    
    # Logging
    log_level: str = "INFO"
    log_dir: Path = Path("logs")
    reports_dir: Path = Path("reports")
    
    # Development
    debug: bool = False
    
    def __repr__(self) -> str:
        """Hide sensitive data in logs."""
        return "Settings(**REDACTED**)"


# Global settings instance
settings = Settings()

# Ensure OPENAI_API_KEY is available via os.environ (for OpenAI SDKs)
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

