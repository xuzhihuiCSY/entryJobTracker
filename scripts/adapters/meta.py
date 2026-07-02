from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    LOGGER.warning(
        "Meta Careers search is currently rendered through client GraphQL without stable static results; skipping"
    )
    return []
