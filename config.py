from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    app_name: str = 'Solution Lab'
    app_version: str = '0.2.0'
    debug: bool = False
    host: str = '0.0.0.0'
    port: int = 8000
    log_level: str = 'INFO'

    default_max_cycles: int = 5
    max_candidates_per_cycle: int = 5
    allow_external_research_default: bool = True

    # External API keys
    firecrawl_api_key: str | None = None
    firecrawl_base_url: str = 'https://api.firecrawl.dev'
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Auth
    api_keys: str = ''  # Comma-separated list

    # Storage
    session_storage_path: Path = Field(default=Path('./data/sessions.db'))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
