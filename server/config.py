"""Infrastructure configuration loaded from the local environment."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(min_length=1)
    redis_url: str = Field(min_length=1)
    minio_endpoint: str = Field(min_length=1)
    minio_access_key: str = Field(min_length=1)
    minio_secret_key: str = Field(min_length=1)
    minio_bucket: str = Field(min_length=1)
    minio_secure: bool = False
    ocr_device: Literal["cpu", "gpu:0"] = "cpu"


@lru_cache
def get_settings() -> Settings:
    return Settings()
