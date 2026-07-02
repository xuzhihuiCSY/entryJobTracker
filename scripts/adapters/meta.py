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
    return _dedupe(jobs)


def _raw_job(item: dict[str, Any], query: str) -> dict[str, Any]:
    title = item.get("title_exact") or ""
    location = item.get("location_exact") or _location_from_parts(item)
    reqid = item.get("reqid") or item.get("guid") or item.get("id") or ""
    detail_path = _detail_path(item)
    return {
        "external_id": _slug(f"{reqid}-{location}") or _slug(f"{title}-{location}"),
        "title": title,
        "location_raw": location,
        "description": item.get("description") or "",
        "apply_url": f"https://metacareers.dejobs.org{detail_path}" if detail_path else SOURCE_URL,
        "source_url": SOURCE_URL + f"?q={quote_plus(query)}",
        "source_platform": "custom_meta_jobsyn",
    }


def _location_from_parts(item: dict[str, Any]) -> str:
    parts = [item.get("city_exact"), item.get("state_short"), item.get("country_short_exact")]
    return ", ".join(str(part) for part in parts if part)


def _detail_path(item: dict[str, Any]) -> str:
    city = _slug(str(item.get("city_exact") or "remote"))
    state = _slug(str(item.get("state_short") or ""))
    title = item.get("title_slug") or _slug(item.get("title_exact") or "job")
    reqid = _slug(str(item.get("reqid") or item.get("guid") or item.get("id") or ""))
    if not reqid:
        return ""
    location = f"{city}-{state}" if state else city
    return f"/{location}/{title}/job/{reqid}/"


def _slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


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
