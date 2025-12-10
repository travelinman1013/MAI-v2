"""
MAI Framework V2 - Intelligence Engine Configuration
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class EngineConfig(BaseSettings):
    """Configuration for the MLX Intelligence Engine."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env.host"),
        env_prefix="MLX_",
        case_sensitive=False,
        extra="ignore"  # Ignore extra env vars that don't match fields
    )

    # Server settings
    host: str = "0.0.0.0"  # Listen on all interfaces for Docker access
    port: int = 8081  # External port
    internal_port: int = 8082  # Internal MLX server port (MLX_INTERNAL_PORT)

    # Model settings - support both MLX_MODEL and MLX_DEFAULT_MODEL
    default_model: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    model: str = ""  # Alternative: MLX_MODEL (takes precedence if set)
    model_directory: str = "/Volumes/the-eagle/maxwell-ext/lmstudio/models/mlx-community"
    model_dir: str = ""  # Alternative: MLX_MODEL_DIR
    max_tokens: int = 32768

    # Performance
    use_metal: bool = True
    log_level: str = "INFO"

    @property
    def active_model(self) -> str:
        """Get the active model (prefers MLX_MODEL over MLX_DEFAULT_MODEL)."""
        return self.model if self.model else self.default_model

    @property
    def active_model_directory(self) -> str:
        """Get the active model directory."""
        return self.model_dir if self.model_dir else self.model_directory


_config: Optional[EngineConfig] = None


def get_config() -> EngineConfig:
    """Get cached configuration."""
    global _config
    if _config is None:
        _config = EngineConfig()
    return _config
