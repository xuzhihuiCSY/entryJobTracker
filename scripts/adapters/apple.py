from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils import http_get_text

BASE_URL = "https://jobs.apple.com"
SEARCH_URL = "https://jobs.apple.com/en-us/search"
SEARCH_TERMS = [
    "software engineer",
    "software engineer intern",
    "new grad software engineer",
    "machine learning engineer",
    "data scientist",
    "data engineer",
]


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for query in SEARCH_TERMS:
        for page in range(1, 3):
            html = http_get_text(
                SEARCH_URL,
                params={"search": query, "location": "united-states-USA", "page": page},
            )
            jobs.extend(_parse_jobs(html, query))
    return _dedupe(jobs)


def _parse_jobs(html: str, query: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict[str, Any]] = []
    for heading in soup.select("h3"):
        link = heading.select_one('a[href^="/en-us/details/"]')
        if not link:
            continue
        card = heading.find_parent("li")
        href = link.get("href") or ""
        location_el = card.select_one('[id^="search-store-name-container"]') if card else None
        description = card.get_text(" ", strip=True) if card else ""
        jobs.append(
            {
                "external_id": _external_id_from_url(href),
                "title": link.get_text(" ", strip=True),
                "location_raw": location_el.get_text(" ", strip=True) if location_el else "",
                "description": description,
                "apply_url": urljoin(BASE_URL, href),
                "source_url": SEARCH_URL + f"?search={query}&location=united-states-USA",
                "source_platform": "custom_apple",
            }
        )
    return jobs


def _external_id_from_url(href: str) -> str:
    parts = href.split("/")
    if "details" not in parts:
        return href
    index = parts.index("details")
    return parts[index + 1] if len(parts) > index + 1 else href


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
