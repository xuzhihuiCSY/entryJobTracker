from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from utils import http_get_json


def _clean(value: str | None) -> str:
    if not value:
        return ""
    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def _location(job: dict[str, Any]) -> str:
    normalized = job.get("normalized_location")
    if isinstance(normalized, list):
        return ", ".join(str(item) for item in normalized if item)
    if isinstance(normalized, str):
        return normalized
    return job.get("location") or ""


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    url = "https://www.amazon.jobs/en/search.json"
    payload = http_get_json(
        url,
        params={
            "offset": 0,
            "result_limit": 100,
            "sort": "recent",
            "category[]": "software-development",
        },
    )
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    results: list[dict[str, Any]] = []
    for job in jobs:
        location = _location(job)
        country_code = str(job.get("country_code") or "").upper()
        if country_code not in {"US", "USA"} and "united states" not in location.lower() and "usa" not in location.lower():
            continue
        job_path = job.get("job_path") or ""
        job_url = f"https://www.amazon.jobs{job_path}" if job_path.startswith("/") else job_path
        description = " ".join(
            [
                _clean(job.get("description")),
                _clean(job.get("basic_qualifications")),
                _clean(job.get("preferred_qualifications")),
            ]
        )
        results.append(
            {
                "external_id": str(job.get("id") or job.get("job_id") or ""),
                "title": job.get("title") or "",
                "location_raw": location,
                "description": description,
                "apply_url": job_url,
                "source_url": job_url or company_config.get("career_url", ""),
                "source_platform": "custom_amazon",
            }
        )
    return results
