from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urlencode

import requests

from utils import DEFAULT_HEADERS, REQUEST_TIMEOUT_SECONDS

APP_ID = "6FNAX3TBEF"
SEARCH_API_KEY = "416caa4690f002ff6fe4a2097623640b"
DEFAULT_INDEX_NAME = "careers_en-US_production"
DEFAULT_DEPARTMENT = "Engineering"
QUERY_URL = f"https://{APP_ID}-dsn.algolia.net/1/indexes/*/queries"
SOURCE_URL = "https://www.rippling.com/careers/open-roles"
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
LOGGER = logging.getLogger(__name__)


def _algolia_params(page: int, department: str, hits_per_page: int) -> str:
    return urlencode(
        {
            "hitsPerPage": hits_per_page,
            "page": page,
            "facetFilters": json.dumps([[f"departmentName:{department}"]], separators=(",", ":")),
        }
    )


def _search_page(index_name: str, department: str, page: int, hits_per_page: int) -> dict[str, Any]:
    response = requests.post(
        QUERY_URL,
        params={"x-algolia-application-id": APP_ID, "x-algolia-api-key": SEARCH_API_KEY},
        json={
            "requests": [
                {
                    "indexName": index_name,
                    "params": _algolia_params(page, department, hits_per_page),
                }
            ]
        },
        headers={**DEFAULT_HEADERS, "Accept": "application/json,text/plain,*/*"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results:
        raise RuntimeError(f"Rippling Algolia returned unexpected response: {payload}")
    first = results[0]
    if not isinstance(first, dict):
        raise RuntimeError(f"Rippling Algolia returned unexpected result: {payload}")
    return first


def _looks_us_location_name(name: str) -> bool:
    value = name.strip()
    lower = value.lower()
    if not value:
        return False
    if "united states" in lower or lower.endswith(", us") or ", us)" in lower:
        return True
    return bool(re.search(rf"\b({'|'.join(sorted(US_STATE_CODES))})\b", value))


def _is_us_location(location: dict[str, Any]) -> bool:
    country_code = str(location.get("countryCode") or "").strip().upper()
    country = str(location.get("country") or "").strip().lower()
    name = str(location.get("name") or "").strip()
    return country_code == "US" or country in {"united states", "united states of america"} or _looks_us_location_name(name)


def _us_locations_from_hit(hit: dict[str, Any]) -> list[str]:
    locations = hit.get("locations")
    us_locations: list[str] = []
    if isinstance(locations, list):
        for location in locations:
            if not isinstance(location, dict) or not _is_us_location(location):
                continue
            name = str(location.get("name") or "").strip()
            if name and name not in us_locations:
                us_locations.append(name)

    if us_locations:
        return us_locations

    location_names = hit.get("locationNames")
    if isinstance(location_names, list):
        for location_name in location_names:
            name = str(location_name or "").strip()
            if _looks_us_location_name(name) and name not in us_locations:
                us_locations.append(name)
    return us_locations


def _description(department: str, is_remote: bool, locations: list[str]) -> str:
    workplace = "Remote" if is_remote else "On-site or hybrid"
    location_text = "; ".join(locations)
    return " | ".join(part for part in [department, workplace, location_text] if part)


def jobs_from_hits(hits: list[dict[str, Any]], department: str = DEFAULT_DEPARTMENT) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for hit in hits:
        if str(hit.get("departmentName") or "").strip() != department:
            continue
        us_locations = _us_locations_from_hit(hit)
        if not us_locations:
            continue

        external_id = str(hit.get("jobId") or hit.get("objectID") or "").split("__", 1)[0].strip()
        if not external_id:
            continue

        job = grouped.setdefault(
            external_id,
            {
                "external_id": external_id,
                "title": str(hit.get("name") or "").strip(),
                "location_raw": "",
                "locations": [],
                "description": "",
                "apply_url": str(hit.get("url") or "").strip(),
                "source_url": str(hit.get("url") or SOURCE_URL).strip(),
                "source_platform": "rippling_algolia",
                "_is_remote": bool(hit.get("isRemote")),
            },
        )
        job["_is_remote"] = bool(job.get("_is_remote")) or bool(hit.get("isRemote"))
        if not job.get("apply_url") and hit.get("url"):
            job["apply_url"] = str(hit["url"]).strip()
            job["source_url"] = str(hit["url"]).strip()
        for location in us_locations:
            if location not in job["locations"]:
                job["locations"].append(location)

    results: list[dict[str, Any]] = []
    for job in grouped.values():
        locations = sorted(job.get("locations") or [])
        if not locations:
            continue
        is_remote = bool(job.pop("_is_remote", False))
        job["locations"] = locations
        job["location_raw"] = locations[0]
        job["location_count"] = len(locations)
        job["description"] = _description(department, is_remote, locations)
        results.append(job)
    return sorted(results, key=lambda item: (item["title"].lower(), item["external_id"]))


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    index_name = str(company_config.get("source_key") or DEFAULT_INDEX_NAME).strip()
    department = str(company_config.get("department") or DEFAULT_DEPARTMENT).strip()
    hits_per_page = 100
    hits: list[dict[str, Any]] = []

    for page in range(20):
        result = _search_page(index_name, department, page, hits_per_page)
        page_hits = result.get("hits")
        if not isinstance(page_hits, list):
            raise RuntimeError(f"Rippling Algolia returned non-list hits on page {page}: {result}")
        hits.extend(hit for hit in page_hits if isinstance(hit, dict))

        nb_pages = int(result.get("nbPages") or 0)
        if page + 1 >= nb_pages or not page_hits:
            break
    else:
        LOGGER.warning("Rippling Algolia pagination stopped at hard page limit")

    return jobs_from_hits(hits, department=department)
