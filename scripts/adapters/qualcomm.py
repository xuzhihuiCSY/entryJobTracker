from __future__ import annotations

import re
from typing import Any

from curl_cffi import requests as curl_requests

BASE_URL = "https://careers.qualcomm.com"
CAREERS_URL = f"{BASE_URL}/careers"
SEARCH_URL = f"{BASE_URL}/api/pcsx/search"
SEARCH_TERMS = [
    "software engineer",
    "machine learning engineer",
    "data scientist",
    "data engineer",
    "security engineer",
    "software developer",
    "software architect",
    "firmware engineer",
    "devops engineer",
    "intern",
    "new grad",
]
PAGE_SIZE = 10


def _new_session() -> tuple[curl_requests.Session, dict[str, str]]:
    session = curl_requests.Session(impersonate="chrome120")
    page = session.get(CAREERS_URL, timeout=30)
    page.raise_for_status()
    csrf_match = re.search(r'<meta name="_csrf" content="([^"]+)"', page.text)
    csrf = csrf_match.group(1) if csrf_match else ""
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "Referer": CAREERS_URL,
        "X-Requested-With": "XMLHttpRequest",
    }
    if csrf:
        headers["X-CSRFToken"] = csrf
        headers["X-CSRF-Token"] = csrf
    return session, headers


def _us_locations(position: dict[str, Any]) -> list[str]:
    standardized = [
        str(location).strip()
        for location in position.get("standardizedLocations") or []
        if str(location).strip().endswith(", US")
    ]
    if standardized:
        return standardized
    return [
        str(location).strip()
        for location in position.get("locations") or []
        if "United States" in str(location)
    ]


def _description(position: dict[str, Any]) -> str:
    parts = [
        str(position.get("department") or ""),
        str(position.get("name") or ""),
        " ".join(str(location) for location in position.get("locations") or []),
    ]
    return " ".join(part for part in parts if part).strip()


def _title(position: dict[str, Any]) -> str:
    return str(position.get("name") or "").strip().lstrip("#").strip()


def _raw_job(position: dict[str, Any]) -> dict[str, Any] | None:
    external_id = str(position.get("displayJobId") or position.get("atsJobId") or position.get("id") or "").strip()
    locations = _us_locations(position)
    if not external_id or not locations:
        return None
    position_url = str(position.get("positionUrl") or "").strip()
    apply_url = f"{BASE_URL}{position_url}" if position_url.startswith("/") else position_url or f"{CAREERS_URL}/job/{position.get('id')}"
    return {
        "external_id": external_id,
        "title": _title(position),
        "location_raw": locations[0],
        "locations": locations,
        "location_count": len(locations),
        "description": _description(position),
        "apply_url": apply_url,
        "source_url": apply_url,
        "source_platform": "qualcomm",
    }


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    session, headers = _new_session()
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for term in SEARCH_TERMS:
        start = 0
        while start < 500:
            response = session.get(
                SEARCH_URL,
                params={
                    "domain": "qualcomm.com",
                    "query": term,
                    "location": "United States",
                    "start": start,
                    "num": PAGE_SIZE,
                },
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data", {}) if isinstance(payload, dict) else {}
            positions = data.get("positions", []) if isinstance(data, dict) else []
            if not positions:
                break

            for position in positions:
                if not isinstance(position, dict):
                    continue
                raw_job = _raw_job(position)
                if not raw_job or raw_job["external_id"] in seen:
                    continue
                seen.add(raw_job["external_id"])
                results.append(raw_job)

            count = int(data.get("count") or 0)
            start += PAGE_SIZE
            if start >= count:
                break

    return results
