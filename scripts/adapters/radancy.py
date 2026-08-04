from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from utils import http_get_json

PAGE_SIZE = 100
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


def _api_url(company_config: dict[str, Any]) -> str:
    career_url = str(company_config.get("career_url") or "").strip()
    source_key = str(company_config.get("source_key") or "/api/jobs").strip()
    if source_key.startswith(("https://", "http://")):
        return source_key
    return urljoin(career_url.rstrip("/") + "/", source_key)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    url = _api_url(company_config)
    if not url:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        page = 1
        while True:
            payload = http_get_json(
                url,
                params={"keywords": term, "page": page, "limit": PAGE_SIZE},
            )
            wrappers = payload.get("jobs", []) if isinstance(payload, dict) else []
            if not isinstance(wrappers, list) or not wrappers:
                break

            for wrapper in wrappers:
                data = wrapper.get("data", {}) if isinstance(wrapper, dict) else {}
                if not isinstance(data, dict):
                    continue
                external_id = str(data.get("req_id") or data.get("ats_code") or data.get("slug") or "").strip()
                if not external_id or external_id in seen:
                    continue
                seen.add(external_id)

                apply_url = str(data.get("apply_url") or "").strip()
                description = " ".join(
                    str(data.get(key) or "").strip()
                    for key in ("description", "responsibilities", "qualifications")
                    if str(data.get(key) or "").strip()
                )
                results.append(
                    {
                        "external_id": external_id,
                        "title": data.get("title") or "",
                        "location_raw": data.get("full_location") or data.get("location_name") or "",
                        "description": description,
                        "apply_url": apply_url,
                        "source_url": apply_url or company_config.get("career_url", ""),
                        "source_platform": "radancy",
                    }
                )

            count = int(payload.get("count") or payload.get("totalCount") or 0)
            if page * PAGE_SIZE >= count or len(wrappers) < PAGE_SIZE:
                break
            page += 1

    return results
