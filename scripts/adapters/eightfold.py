from __future__ import annotations

import json
from html import unescape
from typing import Any

from utils import http_get_text

TECH_SEARCH_TERMS = [
    "software",
    "machine learning",
    "data scientist",
    "data engineer",
    "frontend",
    "backend",
    "full stack",
    "security engineer",
    "site reliability",
    "cloud engineer",
    "devops",
    "ai engineer",
    "intern",
    "new grad",
]


def _extract_positions(page: str) -> list[dict[str, Any]]:
    decoded = unescape(page)
    marker = '"positions":'
    marker_index = decoded.find(marker)
    if marker_index < 0:
        return []

    payload_start = marker_index + len(marker)
    try:
        payload, _ = json.JSONDecoder().raw_decode(decoded[payload_start:].lstrip())
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [position for position in payload if isinstance(position, dict)]


def _locations(position: dict[str, Any]) -> list[str]:
    values = position.get("locations")
    if isinstance(values, list):
        locations = [str(value).strip() for value in values if str(value).strip()]
        if locations:
            return locations

    location = str(position.get("location") or "").strip()
    return [location] if location else []


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    if not career_url:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        page = http_get_text(career_url, params={"query": term, "location": "United States"})
        for position in _extract_positions(page):
            external_id = str(position.get("ats_job_id") or position.get("id") or "").strip()
            if not external_id or external_id in seen:
                continue
            seen.add(external_id)

            locations = _locations(position)
            apply_url = str(position.get("canonicalPositionUrl") or "").strip()
            results.append(
                {
                    "external_id": external_id,
                    "title": position.get("posting_name") or position.get("name") or "",
                    "location_raw": "; ".join(locations),
                    "locations": locations,
                    "location_count": len(locations),
                    "description": position.get("job_description") or "",
                    "apply_url": apply_url,
                    "source_url": apply_url or career_url,
                    "source_platform": "eightfold",
                }
            )

    return results
