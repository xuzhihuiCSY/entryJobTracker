from __future__ import annotations

from typing import Any

from utils import http_get_json

API_BASE_URL = "https://api.smartrecruiters.com/v1/companies"
PAGE_SIZE = 100


def _location(posting: dict[str, Any]) -> str:
    location = posting.get("location")
    if not isinstance(location, dict):
        return ""
    return str(location.get("fullLocation") or "").strip()


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    company_identifier = str(company_config.get("source_key") or "").strip()
    if not company_identifier:
        return []

    url = f"{API_BASE_URL}/{company_identifier}/postings"
    results: list[dict[str, Any]] = []
    offset = 0
    while True:
        data = http_get_json(url, params={"limit": PAGE_SIZE, "offset": offset})
        postings = data.get("content", []) if isinstance(data, dict) else []
        if not isinstance(postings, list) or not postings:
            break

        for posting in postings:
            if not isinstance(posting, dict):
                continue
            external_id = str(posting.get("id") or "").strip()
            if not external_id:
                continue
            apply_url = f"https://jobs.smartrecruiters.com/{company_identifier}/{external_id}"
            results.append(
                {
                    "external_id": external_id,
                    "title": posting.get("name") or "",
                    "location_raw": _location(posting),
                    "description": "",
                    "apply_url": apply_url,
                    "source_url": apply_url,
                    "source_platform": "smartrecruiters",
                }
            )

        offset += len(postings)
        total = int(data.get("totalFound") or 0)
        if offset >= total:
            break

    return results
