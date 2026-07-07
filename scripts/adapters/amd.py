from __future__ import annotations

from typing import Any

from utils import http_get_json

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


def _location(job_data: dict[str, Any]) -> str:
    city = str(job_data.get("city") or "").strip()
    state = str(job_data.get("state") or "").strip()
    country = str(job_data.get("country") or "").strip()
    location_name = str(job_data.get("location_name") or "").strip()
    if city and state and country:
        return f"{city}, {state}, {country}"
    return location_name or country


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for term in TECH_SEARCH_TERMS:
        page = 1
        while page <= 3:
            payload = http_get_json(
                "https://careers.amd.com/api/jobs",
                params={"keywords": term, "page": page, "limit": 100},
            )
            jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
            if not jobs:
                break

            for job in jobs:
                job_data = job.get("data") if isinstance(job, dict) else None
                if not isinstance(job_data, dict):
                    continue
                external_id = str(job_data.get("req_id") or job_data.get("slug") or "").strip()
                if not external_id or external_id in seen:
                    continue
                seen.add(external_id)
                apply_url = f"https://careers.amd.com/careers-home/jobs/{external_id}"
                results.append(
                    {
                        "external_id": external_id,
                        "title": job_data.get("title") or "",
                        "location_raw": _location(job_data),
                        "description": " ".join(
                            str(job_data.get(field) or "")
                            for field in ("description", "responsibilities", "qualifications")
                        ).strip(),
                        "apply_url": apply_url,
                        "source_url": apply_url,
                        "source_platform": "amd",
                    }
                )

            total = int(payload.get("totalCount") or payload.get("count") or 0)
            page += 1
            if (page - 1) * len(jobs) >= total:
                break

    return results
