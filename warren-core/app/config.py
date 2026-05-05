from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql+asyncpg://warren:warren@localhost/warren_core"
    llm_api_key: str = "ollama"
    llm_base_url: str = "http://host.docker.internal:11434/v1"
    llm_model: str = "qwen3:8b"
    prob_dampening: float = 0.15


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
