from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    LOGGER.warning(
        "No implemented parser for %s (%s); skipping without crashing",
        company_config.get("name", "unknown company"),
        company_config.get("source_type", "unknown source"),
    )
    return []
