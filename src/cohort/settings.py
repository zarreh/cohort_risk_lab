from functools import lru_cache

from pydantic_settings import SettingsConfigDict
from zarreh_agentkit.settings import AgentSettings


class Settings(AgentSettings):
    """Application configuration, sourced from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="COHORT_", extra="ignore")

    offline_mode: bool = False

    langsmith_project: str = "cohort-risk-lab"

    cohort_db_path: str = "data/cohort.db"
    queue_store_path: str = "data/queue.db"
    checkpoint_db_path: str = "data/checkpoints.db"
    registry_dir: str = "artifacts/registry"

    frontend_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
