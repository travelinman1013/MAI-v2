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
        case_sensitive=False
    )

    # Server settings
    host: str = "0.0.0.0"  # Listen on all interfaces for Docker access
    port: int = 8081  # External port
    mlx_internal_port: int = 8082  # Internal MLX server port

    # Model settings
    default_model: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    model_directory: str = "/Volumes/the-eagle/maxwell-ext/lmstudio/models/mlx-community"
    max_tokens: int = 32768

    # Performance
    use_metal: bool = True
    log_level: str = "INFO"


_config: Optional[EngineConfig] = None


def get_config() -> EngineConfig:
    """Get cached configuration."""
    global _config
    if _config is None:
        _config = EngineConfig()
    return _config
