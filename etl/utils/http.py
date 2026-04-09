"""HTTP helpers with retry logic for ETL scripts."""

from __future__ import annotations

import logging
import time

import requests

LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2
REQUEST_TIMEOUT = 10


def get_json(url: str, params: dict | None = None) -> dict | None:
    """GET a JSON endpoint with automatic retry on failure."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            LOGGER.warning("HTTP %s — %s (attempt %s)", resp.status_code, url, attempt)
        except requests.RequestException as exc:
            LOGGER.warning("Request failed: %s (attempt %s): %s", url, attempt, exc)

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    return None
