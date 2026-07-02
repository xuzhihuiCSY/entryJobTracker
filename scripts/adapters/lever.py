from __future__ import annotations

from typing import Any

from utils import http_get_json


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    source_key = company_config.get("source_key")
    if not source_key:
        return []

    url = f"https://api.lever.co/v0/postings/{source_key}"
    payload = http_get_json(url, params={"mode": "json"})
    postings = payload if isinstance(payload, list) else []
    results: list[dict[str, Any]] = []
    for post in postings:
        categories = post.get("categories") or {}
        results.append(
            {
                "external_id": str(post.get("id") or ""),
                "title": post.get("text") or "",
                "location_raw": categories.get("location") or "",
                "description": post.get("descriptionPlain") or post.get("description") or "",
                "apply_url": post.get("hostedUrl") or "",
                "source_url": post.get("hostedUrl") or company_config.get("career_url", ""),
                "source_platform": "lever",
            }
        )
    return results
