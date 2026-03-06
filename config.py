"""
Environment-based configuration for Solution Lab.

All settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Solution Lab"
    debug: bool = False
    log_level: str = "INFO"

    # API
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM Configuration (stub for MVP - would integrate with actual providers)
    llm_provider: str = "openai"  # openai, anthropic, ollama
    llm_model: str = "gpt-4"
    llm_api_key: str | None = None
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4000

    # Firecrawl Configuration
    firecrawl_api_key: str | None = None
    firecrawl_base_url: str = "https://api.firecrawl.dev"

    # Session Storage
    session_storage_path: Path = Path("./sessions")
    max_sessions: int = 100
    session_ttl_hours: int = 24

    # Orchestrator Defaults
    default_max_cycles: int = 5
    default_allow_research: bool = True

    # Convergence Thresholds
    min_candidates_for_convergence: int = 2
    max_candidates_for_convergence: int = 5

    @property
    def session_storage_absolute(self) -> Path:
        """Return absolute path for session storage."""
        return self.session_storage_path.resolve()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export for convenience
settings = get_settings()
