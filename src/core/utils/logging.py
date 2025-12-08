"""
MAI Framework V2 - Logging Utilities
"""

import logging
import sys
from typing import Optional


def get_logger_with_context(module: str, level: Optional[str] = None) -> logging.Logger:
    """Get a logger with context."""
    logger = logging.getLogger(f"mai.{module}")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)

    logger.setLevel(level or logging.INFO)
    return logger
