from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Algo Trading Bot"
    app_env: str = "development"
    api_prefix: str = "/api"
    cache_dir: Path = Path("backend/cache")
    default_period: str = "2y"
    default_interval: str = "1d"
    initial_cash: float = 100000.0
    transaction_cost: float = 0.001
    risk_free_rate: float = 0.02
    live_poll_interval_seconds: int = 5
    alpha_vantage_api_key: Optional[str] = None
    database_url: Optional[str] = None
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings
