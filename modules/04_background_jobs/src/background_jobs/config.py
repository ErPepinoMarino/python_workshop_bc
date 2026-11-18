from functools import lru_cache

from arq.connections import RedisSettings
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="REDIS_",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = Field(default=6379, ge=1, le=65535)
    database: int = Field(default=0, ge=0)

    def to_arq(self) -> RedisSettings:
        return RedisSettings(host=self.host, port=self.port, database=self.database)


@lru_cache
def get_settings() -> Settings:
    return Settings()
