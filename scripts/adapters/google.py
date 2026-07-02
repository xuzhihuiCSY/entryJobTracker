from __future__ import annotations

from typing import Any

from .placeholder import fetch_company_jobs as _placeholder


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    return _placeholder(company_config)
