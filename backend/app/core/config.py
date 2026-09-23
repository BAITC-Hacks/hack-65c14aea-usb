from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Smart Contractor Match"
    app_version: str = "0.3.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    database_url: str = (
        "postgresql+asyncpg://contractors:contractors@localhost:5432/contractors"
    )
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300
    cache_request_timeout: float = 0.25
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "contractors-v1"
    elasticsearch_request_timeout: float = 4.0
    max_candidates: int = 500
    embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    embedding_dimensions: int = 384
    embedding_cache_dir: str = "/opt/fastembed-cache"
    semantic_search_weight: float = 0.7
    lexical_search_weight: float = 0.3

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

