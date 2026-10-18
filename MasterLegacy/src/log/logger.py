"""Lightweight logging setup for version_0.

Design goals:
- No side effects on import: logging is configured lazily when get_logger() is first called.
- Single configuration point for the "version_0" namespace so handlers aren't duplicated.
- Uses only the Python standard library (logging.handlers.RotatingFileHandler).
- Writes rotating logs to version_0/logs/app.log and emits to stderr for development.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_LOGGER_NAME = "version_0"
"""Base logger namespace. Child loggers are created as "version_0.<name>".
Configuring the base logger ensures consistent handlers for all child loggers."""

_configured = False
"""Module-level flag to ensure configuration runs only once."""


def _ensure_config(log_dir: Path | None = None, level: int = logging.INFO) -> None:
    """Configure the base logger exactly once.

    This function is intentionally not called at import time. get_logger() invokes it
    lazily so merely importing this module does not change global logging state.
    """
    global _configured
    if _configured:
        return

    base_logger = logging.getLogger(BASE_LOGGER_NAME)
    base_logger.setLevel(level)
    # Prevent messages from being propagated to the root logger to avoid duplicate output
    # when the root logger is configured elsewhere in the application.
    base_logger.propagate = False

    # Determine the logs directory inside version_0
    if log_dir is None:
        log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Rotating file handler: keep files bounded in size and retain a few backups.
    file_path = log_dir / "app.log"
    file_handler = RotatingFileHandler(
        filename=str(file_path), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(level)

    # Console handler for development (writes to stderr)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Shared formatter: ISO-like timestamp, level, logger name, and message.
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    base_logger.addHandler(file_handler)
    base_logger.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given name under the version_0 namespace.

    The first call to get_logger triggers lazy configuration of the base logger.

    Example:
        logger = get_logger("validators")
        logger.info("starting validation")
    """
    _ensure_config()
    return logging.getLogger(f"{BASE_LOGGER_NAME}.{name}")
