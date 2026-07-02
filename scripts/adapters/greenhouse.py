from __future__ import annotations

from typing import Any

from utils import http_get_json


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    source_key = company_config.get("source_key")
    if not source_key:
        return []

    url = f"https://boards-api.greenhouse.io/v1/boards/{source_key}/jobs"
    payload = http_get_json(url, params={"content": "true"})
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    results: list[dict[str, Any]] = []
    for job in jobs:
        location = job.get("location") or {}
        results.append(
            {
                "external_id": str(job.get("id") or ""),
                "title": job.get("title") or "",
                "location_raw": location.get("name") or "",
                "description": job.get("content") or "",
                "apply_url": job.get("absolute_url") or "",
                "source_url": job.get("absolute_url") or company_config.get("career_url", ""),
                "source_platform": "greenhouse",
            }
        )
    return results
