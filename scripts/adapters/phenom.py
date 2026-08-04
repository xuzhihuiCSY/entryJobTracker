from __future__ import annotations

import json
from html import unescape
from typing import Any

from utils import http_get_text

TECH_SEARCH_TERMS = [
    "software engineer",
    "machine learning",
    "data scientist",
    "data engineer",
    "cloud engineer",
    "devops",
    "security engineer",
    "technology intern",
    "IT intern",
]


def _extract_jobs(page: str) -> list[dict[str, Any]]:
    marker = '"eagerLoadRefineSearch":'
    marker_index = page.find(marker)
    if marker_index < 0:
        return []
    try:
        payload, _ = json.JSONDecoder().raw_decode(page[marker_index + len(marker) :])
    except json.JSONDecodeError:
        return []
    jobs = payload.get("data", {}).get("jobs", []) if isinstance(payload, dict) else []
    if not isinstance(jobs, list):
        return []
    return [job for job in jobs if isinstance(job, dict)]


def _locations(job: dict[str, Any]) -> list[str]:
    multi_location = job.get("multi_location")
    if isinstance(multi_location, list):
        locations = [str(value).strip() for value in multi_location if str(value).strip()]
        if locations:
            return locations
    for key in ("address", "cityStateCountry", "location"):
        location = str(job.get(key) or "").strip()
        if location:
            return [location]
    return []


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    if not career_url:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        page = http_get_text(career_url, params={"keywords": term})
        for job in _extract_jobs(page):
            external_id = str(job.get("reqId") or job.get("jobId") or "").strip()
            if not external_id or external_id in seen:
                continue
            seen.add(external_id)
            locations = _locations(job)
            apply_url = unescape(str(job.get("applyUrl") or "").strip())
            results.append(
                {
                    "external_id": external_id,
                    "title": job.get("title") or "",
                    "location_raw": "; ".join(locations),
                    "locations": locations,
                    "location_count": len(locations),
                    "description": job.get("descriptionTeaser") or "",
                    "apply_url": apply_url,
                    "source_url": apply_url or career_url,
                    "source_platform": "phenom",
                }
            )
    return results
