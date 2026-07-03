from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import quote_plus

import requests

from utils import DEFAULT_HEADERS, REQUEST_TIMEOUT_SECONDS

API_URL = "https://prod-search-api.jobsyn.org/api/v1/solr/search"
SOURCE_URL = "https://metacareers.dejobs.org/jobs/"
QUERY_TERMS = [
    "software engineer",
    "software engineering intern",
    "new grad software engineer",
    "data scientist",
    "data engineer",
    "machine learning engineer",
    "ai engineer",
]
LOGGER = logging.getLogger(__name__)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for query in QUERY_TERMS:
        for page in range(1, 4):
            try:
                response = requests.get(
                    API_URL,
                    params={"q": query, "page": page},
                    headers={
                        **DEFAULT_HEADERS,
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "Referer": "https://metacareers.dejobs.org/",
                        "x-origin": "metacareers.dejobs.org",
                    },
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                LOGGER.warning("Meta Jobsyn query failed for %r page %s: %s", query, page, exc)
                break
            data = response.json()
            page_jobs = data.get("jobs", [])
            for item in page_jobs:
                jobs.append(_raw_job(item, query))
            if not data.get("pagination", {}).get("has_more_pages"):
                break
    return _filter_active_official_jobs(_aggregate_locations(jobs))


def _raw_job(item: dict[str, Any], query: str) -> dict[str, Any]:
    title = item.get("title_exact") or ""
    location = item.get("location_exact") or _location_from_parts(item)
    reqid = item.get("reqid") or item.get("guid") or item.get("id") or ""
    return {
        "external_id": _slug(reqid) or _slug(f"{title}-{location}"),
        "title": title,
        "location_raw": location,
        "locations": [location] if location else [],
        "description": item.get("description") or "",
        "apply_url": f"https://www.metacareers.com/jobs/{reqid}/" if reqid else SOURCE_URL,
        "source_url": SOURCE_URL + f"?q={quote_plus(query)}",
        "source_platform": "custom_meta_jobsyn",
    }


def _location_from_parts(item: dict[str, Any]) -> str:
    parts = [item.get("city_exact"), item.get("state_short"), item.get("country_short_exact")]
    return ", ".join(str(part) for part in parts if part)


def _slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _aggregate_locations(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for job in jobs:
        key = str(job.get("apply_url") or job.get("external_id") or _slug(job.get("title", "")))
        if key not in grouped:
            grouped[key] = {**job, "locations": []}
        locations = grouped[key]["locations"]
        for location in job.get("locations", []):
            if location and location not in locations:
                locations.append(location)
        if not grouped[key].get("description") and job.get("description"):
            grouped[key]["description"] = job["description"]
    aggregated: list[dict[str, Any]] = []
    for job in grouped.values():
        locations = job.get("locations", [])
        if locations:
            job["location_raw"] = "; ".join(locations)
            job["location_count"] = len(locations)
        aggregated.append(job)
    return aggregated


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


def _filter_active_official_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_by_url: dict[str, bool] = {}
    active_jobs: list[dict[str, Any]] = []
    for job in jobs:
        apply_url = job.get("apply_url", "")
        if apply_url not in active_by_url:
            active_by_url[apply_url] = _is_active_official_url(apply_url)
        if active_by_url[apply_url]:
            active_jobs.append(job)
    return active_jobs


def _is_active_official_url(url: str) -> bool:
    try:
        response = requests.get(
            url,
            headers={**DEFAULT_HEADERS, "Accept": "text/html,text/plain,*/*"},
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        LOGGER.warning("Meta official job URL validation failed for %s: %s", url, exc)
        return False
    return response.status_code == 200 and "position-not-available" not in response.url
