from __future__ import annotations

import re
from typing import Any

from utils import http_get_json

US_STATE_CODES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "IA",
    "ID",
    "IL",
    "IN",
    "KS",
    "KY",
    "LA",
    "MA",
    "MD",
    "ME",
    "MI",
    "MN",
    "MO",
    "MS",
    "MT",
    "NC",
    "ND",
    "NE",
    "NH",
    "NJ",
    "NM",
    "NV",
    "NY",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VA",
    "VT",
    "WA",
    "WI",
    "WV",
    "WY",
}


def _looks_us_location(value: str) -> bool:
    text = value.strip()
    lower = text.lower()
    if not text:
        return False
    if "united states" in lower or lower.endswith(", us"):
        return True
    return bool(re.search(rf"\b({'|'.join(sorted(US_STATE_CODES))})\b", text))


def _office_location(office: dict[str, Any]) -> str:
    location = str(office.get("location") or "").strip()
    name = str(office.get("name") or "").strip()
    return location or name


def _job_locations(job: dict[str, Any]) -> list[str]:
    offices = job.get("offices")
    locations: list[str] = []
    if isinstance(offices, list):
        for office in offices:
            if not isinstance(office, dict):
                continue
            location = _office_location(office)
            if location and location not in locations:
                locations.append(location)

    if locations:
        return locations

    location = job.get("location") or {}
    location_name = str(location.get("name") if isinstance(location, dict) else "").strip()
    return [location_name] if location_name else []


def _primary_location(locations: list[str]) -> str:
    for location in locations:
        if _looks_us_location(location):
            return location
    return locations[0] if locations else ""


def _level_hint(job: dict[str, Any]) -> str:
    for field in job.get("metadata") or []:
        if str(field.get("name") or "").casefold() not in {"employment type", "job type", "career level"}:
            continue
        value = str(field.get("value") or "").casefold()
        if re.search(r"\bintern(?:ship)?\b|\bco-?op\b", value):
            return "Intern"
        if re.search(r"\bnew grad(?:uate)?\b|\buniversity grad(?:uate)?\b", value):
            return "New Grad"
    return ""


def _posting_key(job: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    # The same requisition can be published to both industry and campus boards
    # with different posting IDs and a different order of the same locations.
    locations = sorted({part.strip().casefold() for location in job.get("locations", []) for part in location.split(";")})
    return job["requisition_id"], tuple(locations)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    additional_keys = company_config.get("additional_source_keys") or []
    if additional_keys:
        results: list[dict[str, Any]] = []
        seen: set[tuple[str, tuple[str, ...]]] = set()
        for key in dict.fromkeys([company_config.get("source_key"), *additional_keys]):
            config = {**company_config, "source_key": key, "additional_source_keys": []}
            for job in fetch_company_jobs(config):
                key = _posting_key(job)
                if key not in seen:
                    seen.add(key)
                    results.append(job)
        return results
    source_key = company_config.get("source_key")
    if not source_key:
        return []

    url = f"https://boards-api.greenhouse.io/v1/boards/{source_key}/jobs"
    payload = http_get_json(url, params={"content": "true"})
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    results: list[dict[str, Any]] = []
    for job in jobs:
        locations = _job_locations(job)
        results.append(
            {
                "external_id": str(job.get("id") or ""),
                "requisition_id": str(job.get("internal_job_id") or job.get("id") or ""),
                "level_hint": _level_hint(job),
                "title": job.get("title") or "",
                "location_raw": _primary_location(locations),
                "locations": locations,
                "location_count": len(locations),
                "description": job.get("content") or "",
                "apply_url": job.get("absolute_url") or "",
                "source_url": job.get("absolute_url") or company_config.get("career_url", ""),
                "source_platform": "greenhouse",
            }
        )
    return results
