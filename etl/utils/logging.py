"""Centralized logging setup for all ETL scripts.

Usage:
    from etl.utils.logging import setup_logging

    LOGGER = setup_logging(__name__)

`setup_logging` is idempotent — it only configures the root logger on the
first call, so importing it from multiple scripts in the same process
(e.g. via the pipeline orchestrator) is safe.
"""

from __future__ import annotations

import logging

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_configured = False


def setup_logging(name: str | None = None, level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger once and return a named logger."""
    global _configured
    if not _configured:
        logging.basicConfig(level=level, format=_LOG_FORMAT)
        _configured = True
    return logging.getLogger(name)
