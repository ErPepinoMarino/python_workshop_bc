from functools import lru_cache

from arq.connections import RedisSettings
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://postgres:bootcamp@127.0.0.1:5433/integrated"
    )
    redis_host: str = "127.0.0.1"
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_database: int = Field(default=0, ge=0)
    log_format: str = Field(default="console", pattern="^(console|json)$")

    def to_arq(self) -> RedisSettings:
        return RedisSettings(
            host=self.redis_host,
            port=self.redis_port,
            database=self.redis_database,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
