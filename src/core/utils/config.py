"""
MAI Framework V2 - Configuration Management
Supports hybrid Docker + Host architecture
"""

from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MlxLmSettings(BaseSettings):
    """MLX-LM server configuration for hybrid architecture."""

    model_config = SettingsConfigDict(env_prefix="MLXLM__")

    # CRITICAL: When running in Docker, this MUST point to host.docker.internal
    base_url: str = Field(
        default="http://host.docker.internal:8081/v1",
        description="MLX-LM server URL. Use host.docker.internal from Docker."
    )
    api_key: str = Field(
        default="not-needed",
        description="API key (not required for local MLX server)"
    )
    model_name: str = Field(
        default="mlx-community/Qwen2.5-7B-Instruct-4bit",
        description="Model identifier"
    )
    max_tokens: int = Field(default=32768, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout: int = Field(default=120, ge=1)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Ensure base_url ends with /v1 for OpenAI compatibility."""
        v = v.rstrip("/")
        if not v.endswith("/v1"):
            v = f"{v}/v1"
        return v


class DatabaseSettings(BaseSettings):
    """Database configuration using Docker service names."""

    model_config = SettingsConfigDict(env_prefix="DATABASE__")

    # Docker service name 'postgres' resolves within the network
    url: str = Field(
        default="postgresql+asyncpg://mai:mai_secret@postgres:5432/mai_framework",
        description="Database URL using Docker service name"
    )
    pool_size: int = Field(default=20, ge=1)
    max_overflow: int = Field(default=10, ge=0)
    pool_timeout: int = Field(default=30, ge=1)
    echo: bool = Field(default=False)


class RedisSettings(BaseSettings):
    """Redis configuration using Docker service names."""

    model_config = SettingsConfigDict(env_prefix="REDIS__")

    # Docker service name 'redis' resolves within the network
    url: str = Field(
        default="redis://redis:6379/0",
        description="Redis URL using Docker service name"
    )
    max_connections: int = Field(default=50, ge=1)
    timeout: int = Field(default=5, ge=1)


class QdrantSettings(BaseSettings):
    """Qdrant configuration using Docker service names."""

    model_config = SettingsConfigDict(env_prefix="QDRANT__")

    # Docker service name 'qdrant' resolves within the network
    url: str = Field(
        default="http://qdrant:6333",
        description="Qdrant HTTP URL using Docker service name"
    )
    grpc_port: int = Field(default=6334)
    collection_name: str = Field(default="mai_memory")
    prefer_grpc: bool = Field(default=True)
    api_key: Optional[str] = Field(default=None)


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env.docker",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="mai-framework")
    environment: str = Field(default="production")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    cors_origins: List[str] = Field(
        default=["http://localhost", "http://localhost:80"]
    )

    # Nested settings
    mlxlm: MlxLmSettings = Field(default_factory=MlxLmSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)

    # JWT
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=30)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
