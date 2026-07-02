from __future__ import annotations

from typing import Any

import requests

from utils import DEFAULT_HEADERS, REQUEST_TIMEOUT_SECONDS

TENANT = "nvidia"
SITE = "NVIDIAExternalCareerSite"
BASE_URL = f"https://{TENANT}.wd5.myworkdayjobs.com/{SITE}"
API_URL = f"https://{TENANT}.wd5.myworkdayjobs.com/wday/cxs/{TENANT}/{SITE}/jobs"
SEARCH_TERMS = [
    "software engineer",
    "software engineer intern",
    "new college graduate software",
    "machine learning engineer",
    "data scientist",
    "data engineer",
]

def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    us_location_id = _find_us_location_id()
    jobs: list[dict[str, Any]] = []
    for query in SEARCH_TERMS:
        for offset in (0, 20, 40):
            payload: dict[str, Any] = {
                "appliedFacets": {},
                "limit": 20,
                "offset": offset,
                "searchText": query,
            }
            if us_location_id:
                payload["appliedFacets"] = {"locationHierarchy1": [us_location_id]}
            response = requests.post(
                API_URL,
                json=payload,
                headers={**DEFAULT_HEADERS, "Accept": "application/json", "Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            postings = data.get("jobPostings", [])
            for posting in postings:
                jobs.append(_raw_job(posting, query))
            if len(postings) < 20:
                break
    return _dedupe(jobs)


def _find_us_location_id() -> str:
    response = requests.post(
        API_URL,
        json={"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": "software engineer"},
        headers={**DEFAULT_HEADERS, "Accept": "application/json", "Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    for facet in data.get("facets", []):
        if facet.get("facetParameter") != "locationMainGroup":
            continue
        for group in facet.get("values", []):
            if group.get("facetParameter") != "locationHierarchy1":
                continue
            for value in group.get("values", []):
                if value.get("descriptor") == "United States":
                    return value.get("id", "")
    return ""


def _raw_job(posting: dict[str, Any], query: str) -> dict[str, Any]:
    external_path = posting.get("externalPath") or ""
    job_code = ""
    bullet_fields = posting.get("bulletFields") or []
    if bullet_fields:
        job_code = str(bullet_fields[0])
    apply_url = _apply_url(external_path)
    return {
        "external_id": job_code or external_path,
        "title": posting.get("title") or "",
        "location_raw": posting.get("locationsText") or "",
        "description": " ".join(str(field) for field in bullet_fields if field),
        "apply_url": apply_url,
        "source_url": BASE_URL + f"?q={query}",
        "source_platform": "custom_nvidia",
    }


def _apply_url(external_path: str) -> str:
    if not external_path:
        return BASE_URL
    return BASE_URL + (external_path if external_path.startswith("/") else f"/{external_path}")


def _dedupe(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for job in jobs:
        key = job.get("external_id") or job.get("apply_url")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(job)
    return deduped
