from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils import http_get_text

LOCATION_PAGES = [
    "https://careers.microsoft.com/v2/global/en/locations/seattle-area.html",
    "https://careers.microsoft.com/v2/global/en/locations/bay-area.html",
    "https://careers.microsoft.com/v2/global/en/locations/new-york.html",
    "https://careers.microsoft.com/v2/global/en/locations/dc-metro.html",
    "https://careers.microsoft.com/v2/global/en/locations/new-england.html",
]


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for page_url in LOCATION_PAGES:
        html = http_get_text(page_url)
        jobs.extend(_parse_location_page(html, page_url))
    return _dedupe(jobs)


def _parse_location_page(html: str, page_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict[str, Any]] = []
    for link in soup.select('a[href*="apply.careers.microsoft.com/careers/job/"]'):
        card = _nearest_job_card(link)
        if not card:
            continue
        text = card.get_text(" ", strip=True)
        href = link.get("href") or ""
        title = _extract_title(card, text)
        location = _extract_location(text)
        if not title:
            continue
        jobs.append(
            {
                "external_id": _external_id_from_url(href) or f"{title}-{location}",
                "title": title,
                "location_raw": location,
                "description": text,
                "apply_url": urljoin(page_url, href),
                "source_url": page_url,
                "source_platform": "custom_microsoft",
            }
        )
    return jobs


def _nearest_job_card(link: Any) -> Any:
    parent = link
    for _ in range(5):
        parent = parent.parent
        if not parent:
            return None
        classes = parent.get("class") or []
        if "careers-joblistResponsive-columnList" in classes:
            return parent
    return None


def _extract_title(card: Any, text: str) -> str:
    heading = card.find(["h2", "h3", "h4"])
    if heading:
        return heading.get_text(" ", strip=True)
    match = re.match(r"(.+?)\s+20\d{2}-\d{2}-\d{2}\s+", text)
    return match.group(1).strip() if match else ""


def _extract_location(text: str) -> str:
    match = re.search(r"20\d{2}-\d{2}-\d{2}\s+(.+?)(?:\s+\d+\s+days\s*/\s*week|<b>|Overview|Responsibilities)", text)
    if not match:
        return ""
    location = match.group(1).strip()
    return location.replace(" +", ", +")


def _external_id_from_url(url: str) -> str:
    match = re.search(r"/job/([^?/#]+)", url)
    return match.group(1) if match else ""


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
