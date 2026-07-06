from __future__ import annotations

from typing import Any

from utils import http_get_json


def _location_from_job(job: dict[str, Any]) -> str:
    postal_address = ((job.get("address") or {}).get("postalAddress") or {})
    country = str(postal_address.get("addressCountry") or "").strip()
    parts = [
        postal_address.get("addressLocality"),
        postal_address.get("addressRegion"),
        country,
    ]
    address_location = ", ".join(str(part).strip() for part in parts if str(part or "").strip())
    location = str(job.get("locationName") or job.get("location") or "").strip()

    if country.casefold() in {"united states", "usa", "us"}:
        if address_location and address_location != country:
            return address_location
        if bool(job.get("isRemote")):
            return "Remote, United States"
        return "United States"

    return location or address_location


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    source_key = company_config.get("source_key")
    if not source_key:
        return []

    url = f"https://api.ashbyhq.com/posting-api/job-board/{source_key}"
    payload = http_get_json(url, params={"includeCompensation": "true"})
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    results: list[dict[str, Any]] = []
    for job in jobs:
        results.append(
            {
                "external_id": str(job.get("id") or ""),
                "title": job.get("title") or "",
                "location_raw": _location_from_job(job),
                "description": job.get("descriptionPlain") or job.get("descriptionHtml") or "",
                "apply_url": job.get("jobUrl") or "",
                "source_url": job.get("jobUrl") or company_config.get("career_url", ""),
                "source_platform": "ashby",
            }
        )
    return results
