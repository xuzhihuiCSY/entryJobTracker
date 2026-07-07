from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from curl_cffi import requests as curl_requests

BASE_URL = "https://jobs.uber.com"
SEARCH_URL = f"{BASE_URL}/api/jobs/search"
SEARCH_TERMS = [
    "software",
    "machine learning",
    "data scientist",
    "data engineer",
    "security engineer",
    "frontend",
    "backend",
    "full stack",
    "site reliability",
    "cloud engineer",
    "devops",
    "intern",
    "new grad",
]


def _new_session() -> curl_requests.Session:
    session = curl_requests.Session(impersonate="chrome120")
    session.headers.update(
        {
            "Accept": "application/json,text/plain,*/*",
            "Referer": f"{BASE_URL}/en/jobs/",
        }
    )
    return session


def _location_text(location: dict[str, Any]) -> str:
    address = str(location.get("Address") or "").strip()
    if address:
        return address
    city = str(location.get("City") or "").strip()
    region = str(location.get("Region") or "").strip()
    country = str(location.get("Country") or "").strip()
    return ", ".join(part for part in (city, region, country) if part)


def _job_locations(job: dict[str, Any]) -> list[str]:
    locations = []
    for location in job.get("Locations") or []:
        if not isinstance(location, dict):
            continue
        text = _location_text(location)
        if text and text not in locations:
            locations.append(text)
    return locations


def _apply_url(job: dict[str, Any]) -> str:
    urls = job.get("Urls")
    if isinstance(urls, list):
        default_url = next((url for url in urls if isinstance(url, dict) and url.get("IsDefault")), None)
        selected = default_url or next((url for url in urls if isinstance(url, dict)), None)
        if selected:
            return urljoin(BASE_URL, str(selected.get("Url") or ""))
    job_id = str(job.get("Id") or "").strip()
    return f"{BASE_URL}/en/jobs/{job_id}/" if job_id else BASE_URL


def _raw_job(job: dict[str, Any]) -> dict[str, Any]:
    locations = _job_locations(job)
    apply_url = _apply_url(job)
    return {
        "external_id": str(job.get("Id") or job.get("Reference") or "").strip(),
        "title": job.get("Title") or "",
        "location_raw": locations[0] if locations else "",
        "locations": locations,
        "location_count": len(locations),
        "description": job.get("Description") or "",
        "apply_url": apply_url,
        "source_url": apply_url,
        "source_platform": "uber",
    }


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    session = _new_session()
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for term in SEARCH_TERMS:
        page = 1
        while page <= 20:
            response = session.get(
                SEARCH_URL,
                params={
                    "locale": "en",
                    "search": term,
                    "countries": "United States",
                    "page": page,
                },
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
            if not jobs:
                break

            for job in jobs:
                if not isinstance(job, dict):
                    continue
                external_id = str(job.get("Id") or job.get("Reference") or "").strip()
                if not external_id or external_id in seen:
                    continue
                seen.add(external_id)
                results.append(_raw_job(job))

            total_pages = int(payload.get("totalPages") or 1)
            if page >= total_pages:
                break
            page += 1

    return results
