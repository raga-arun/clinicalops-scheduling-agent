"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class InternalAPISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INTERNAL_", extra="ignore")

    scheduling_base_url: str = "http://scheduling-api.internal"
    patient_base_url: str = "http://patient-api.internal"
    availability_base_url: str = "http://availability-api.internal"

    timeout_seconds: float = 15.0
    max_connections: int = 100
    max_keepalive_connections: int = 20


class VaultSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VAULT_", extra="ignore")

    address: str = "http://vault.internal:8200"
    namespace: str | None = None
    timeout_seconds: float = 5.0


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    url: str = "redis://redis.internal:6379/0"
    timeout_seconds: float = 5.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "clinicalops-scheduling-agent"
    service_version: str = "0.1.0"
    environment: str = Field(default="local")
    log_level: str = "INFO"

    api_prefix: str = "/api/v1"
    docs_url: str | None = "/docs"
    openapi_url: str | None = "/openapi.json"

    tenant_header: str = "X-Tenant-ID"
    request_id_header: str = "X-Request-ID"
    require_tenant: bool = True

    internal: InternalAPISettings = Field(default_factory=InternalAPISettings)
    vault: VaultSettings = Field(default_factory=VaultSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
