from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    LOGGER.warning(
        "Microsoft's current public careers site did not expose a stable unauthenticated jobs API during verification; skipping"
    )
    return []
