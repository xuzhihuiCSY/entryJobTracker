from __future__ import annotations

import math
from typing import Any

from utils import http_get_json


def _us_locations(posting: dict[str, Any]) -> list[str]:
    cities = posting.get("cities") or []
    countries = posting.get("countries") or []
    locations: list[str] = []
    for city, country in zip(cities, countries):
        if str(country).strip().lower() != "united states":
            continue
        location = ", ".join(value for value in (str(city).strip(), "United States") if value)
        if location and location not in locations:
            locations.append(location)
    return locations


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip().rstrip("/")
    source_url = str(company_config.get("source_base_url") or "").strip()
    interests = company_config.get("source_interests") or ["Tech & AI", "Technology & Digital"]
    country = str(company_config.get("source_country") or "United States").strip()
    if not career_url or not source_url or not interests or not country:
        return []

    page_size = 100
    page = 1
    total_pages = 1
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.mckinsey.com",
        "Referer": f"{career_url}/",
    }
    while page <= total_pages:
        data = http_get_json(
            source_url,
            params={
                "pageSize": page_size,
                "start": page,
                "countries": country,
                "interest": ",".join(str(value) for value in interests),
                "lang": "en",
            },
            headers=headers,
        )
        postings = data.get("docs", []) if isinstance(data, dict) else []
        if page == 1:
            total = int(data.get("numFound") or 0) if isinstance(data, dict) else 0
            total_pages = max(1, math.ceil(total / page_size))
        if not postings:
            break
        for posting in postings:
            if not isinstance(posting, dict):
                continue
            external_id = str(posting.get("jobID") or "").strip()
            locations = _us_locations(posting)
            if not external_id or external_id in seen or not locations:
                continue
            seen.add(external_id)
            friendly_url = str(posting.get("friendlyURL") or "").strip().strip("/")
            detail_url = f"{career_url}/jobs/{friendly_url}" if friendly_url else career_url
            description = " ".join(
                str(posting.get(field) or "")
                for field in ("whatYouWillDo", "yourBackground", "whoYouWillWorkWith")
            )
            results.append(
                {
                    "external_id": external_id,
                    "title": posting.get("title") or "",
                    "location_raw": "; ".join(locations),
                    "locations": locations,
                    "location_count": len(locations),
                    "description": description,
                    "apply_url": posting.get("jobApplyURL") or detail_url,
                    "source_url": detail_url,
                    "source_platform": "mckinsey",
                }
            )
        page += 1
    return results
