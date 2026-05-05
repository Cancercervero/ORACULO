from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql+asyncpg://warren:warren@localhost/warren_core"
    llm_api_key: str = "sk-placeholder"
    llm_model: str = "gpt-4o-mini"
    prob_dampening: float = 0.15


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
