from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, sourced from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="COHORT_", extra="ignore")

    environment: str = "development"
    openai_api_key: str = ""
    offline_mode: bool = False

    langsmith_api_key: str = ""
    langsmith_project: str = "cohort-risk-lab"

    data_dir: str = "data"
    cohort_db_path: str = "data/cohort.db"
    queue_store_path: str = "data/queue.db"
    checkpoint_db_path: str = "data/checkpoints.db"
    registry_dir: str = "artifacts/registry"

    rate_limit_per_minute: int = 20
    max_request_body_bytes: int = 16_384


@lru_cache
def get_settings() -> Settings:
    return Settings()
