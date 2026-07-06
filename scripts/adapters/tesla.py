from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import requests

STATE_URL = "https://www.tesla.com/cua-api/apps/careers/state"
CAREERS_URL = "https://www.tesla.com/careers/search/?site=US"
DETAIL_ROOT = "https://www.tesla.com/careers/search/job"
STATE_PATH_ENV = "ENTRYJOBTRACKER_TESLA_STATE_PATH"
DEFAULT_SITE = "US"

TYPE_LABELS = {
    "fulltime": "Full-Time",
    "parttime": "Part-Time",
    "intern": "Intern/Apprentice",
    "seasonal": "Seasonal",
}
BLOCKED_MARKERS = (
    "Access Denied",
    "AkamaiGHost",
    "You don't have permission to access",
)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    source_url = company_config.get("source_url") or f"{STATE_URL}?site={company_config.get('source_key') or DEFAULT_SITE}"
    site = _site_from_url(source_url)
    payload = _load_state_payload(source_url)
    return jobs_from_state(payload, site=site, source_url=source_url)


def jobs_from_state(payload: dict[str, Any], site: str = DEFAULT_SITE, source_url: str = STATE_URL) -> list[dict[str, Any]]:
    lookup = payload.get("lookup") if isinstance(payload.get("lookup"), dict) else {}
    departments = _string_keyed_lookup(lookup.get("departments"))
    locations = _string_keyed_lookup(lookup.get("locations"))
    types = _string_keyed_lookup(lookup.get("types"))
    location_ids = _location_ids_for_site(payload, site)
    if not location_ids:
        raise RuntimeError(f"Tesla state payload does not contain location ids for site={site!r}")

    jobs: list[dict[str, Any]] = []
    for row in payload.get("listings") or []:
        if not isinstance(row, dict):
            continue
        row_location_ids = _row_location_ids(row)
        if not row_location_ids or row_location_ids.isdisjoint(location_ids):
            continue
        job = _job_from_listing(row, departments, locations, types, source_url)
        if job:
            jobs.append(job)
    return jobs


def _load_state_payload(source_url: str) -> dict[str, Any]:
    state_path = os.environ.get(STATE_PATH_ENV, "").strip()
    if state_path:
        payload = json.loads(Path(state_path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"{STATE_PATH_ENV} must point to a Tesla state JSON object")
        return payload

    url = _state_fetch_url(source_url)
    response = _http_get_state(url)
    payload = _maybe_state_payload(response)
    if payload is None:
        snippet = re.sub(r"\s+", " ", (response.text or "")[:180]).strip()
        raise RuntimeError(f"Tesla careers state request was blocked or returned non-state payload: {response.status_code} {snippet}")
    return payload


def _http_get_state(url: str) -> requests.Response:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Referer": CAREERS_URL,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
    }
    try:
        import curl_cffi.requests as crequests

        return crequests.get(url, impersonate="chrome120", headers=headers, timeout=45)
    except Exception:
        return requests.get(url, headers=headers, timeout=45)


def _maybe_state_payload(response: Any) -> dict[str, Any] | None:
    text = response.text or ""
    if response.status_code != 200 or any(marker in text for marker in BLOCKED_MARKERS):
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    if "cpr_chlge" in payload or "listings" not in payload or "lookup" not in payload:
        return None
    return payload


def _state_fetch_url(source_url: str) -> str:
    parts = urlsplit(source_url or "")
    if parts.netloc == "www.tesla.com" and parts.path == "/cua-api/apps/careers/state":
        return source_url
    query = parts.query or f"site={DEFAULT_SITE}"
    return f"{STATE_URL}?{query}"


def _site_from_url(source_url: str) -> str:
    params = parse_qs(urlsplit(source_url or "").query, keep_blank_values=False)
    site = (params.get("site") or [DEFAULT_SITE])[0].strip()
    return site or DEFAULT_SITE


def _location_ids_for_site(payload: dict[str, Any], site: str = DEFAULT_SITE) -> set[str]:
    wanted = site.casefold()
    ids: set[str] = set()
    for region in payload.get("geo") or []:
        if not isinstance(region, dict):
            continue
        for site_node in region.get("sites") or []:
            if not isinstance(site_node, dict):
                continue
            if str(site_node.get("id") or "").casefold() == wanted:
                _collect_location_ids(site_node, ids)
    return ids


def _collect_location_ids(node: dict[str, Any], ids: set[str]) -> None:
    cities = node.get("cities") or {}
    if isinstance(cities, dict):
        for values in cities.values():
            ids.update(_as_id_set(values))
    for state in node.get("states") or []:
        if isinstance(state, dict):
            _collect_location_ids(state, ids)


def _row_location_ids(row: dict[str, Any]) -> set[str]:
    return _as_id_set(row.get("l"))


def _as_id_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip() for item in value if str(item).strip()}
    text = str(value).strip()
    return {text} if text else set()


def _job_from_listing(
    row: dict[str, Any],
    departments: dict[str, str],
    locations: dict[str, str],
    types: dict[str, str],
    source_url: str,
) -> dict[str, str] | None:
    title = _clean(row.get("t"))
    job_id = _clean(row.get("id"))
    location_id = next(iter(_row_location_ids(row)), "")
    if not title or not job_id:
        return None

    department = _clean(departments.get(str(row.get("dp")), ""))
    location = _clean(locations.get(location_id, ""))
    job_type_key = _clean(types.get(str(row.get("y")), ""))
    job_type = TYPE_LABELS.get(job_type_key.casefold(), _title_type(job_type_key))
    description = " | ".join(part for part in (department, job_type, location) if part)

    return {
        "external_id": job_id,
        "title": title,
        "location_raw": location,
        "description": description,
        "apply_url": _job_url(title, job_id),
        "source_url": source_url,
        "source_platform": "tesla",
    }


def _job_url(title: str, job_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-") or "job"
    return f"{DETAIL_ROOT}/{slug}-{job_id}"


def _string_keyed_lookup(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _clean(val) for key, val in value.items()}


def _title_type(value: str) -> str:
    if not value:
        return ""
    return value.replace("_", " ").replace("-", " ").title()


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())
