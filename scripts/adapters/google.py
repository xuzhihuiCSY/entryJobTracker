from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils import http_get_text

BASE_URL = "https://www.google.com/about/careers/applications/"
SEARCH_URL = urljoin(BASE_URL, "jobs/results/")
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
                params={"q": query, "location": "United States", "page": page},
            )
            jobs.extend(_parse_jobs(html, query))
    return _dedupe(jobs)


def _parse_jobs(html: str, query: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict[str, Any]] = []
    for heading in soup.select("h3.QJPWVe"):
        card = heading.find_parent("li")
        if not card:
            continue
        link = card.select_one("a[href*='jobs/results/']")
        location_el = card.select_one("span.r0wTof")
        href = link.get("href") if link else ""
        apply_url = urljoin(BASE_URL, href)
        external_id = _external_id_from_url(href) or heading.get_text(" ", strip=True)
        description = card.get_text(" ", strip=True)
        jobs.append(
            {
                "external_id": external_id,
                "title": heading.get_text(" ", strip=True),
                "location_raw": location_el.get_text(" ", strip=True) if location_el else "",
                "description": description,
                "apply_url": apply_url,
                "source_url": SEARCH_URL + f"?q={query}&location=United%20States",
                "source_platform": "custom_google",
            }
        )
    return jobs


def _external_id_from_url(href: str) -> str:
    marker = "jobs/results/"
    if marker not in href:
        return ""
    value = href.split(marker, 1)[1].split("?", 1)[0].strip("/")
    return value.split("-", 1)[0]


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
