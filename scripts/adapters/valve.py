from __future__ import annotations

import logging
from html import unescape
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from utils import http_get_text

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.valvesoftware.com/en/jobs"
TECH_TITLE_PHRASES = ("software engineer", "software engineering", "database administrator")


def _clean_text(value: str) -> str:
    return " ".join(unescape(value).split())


def _job_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    return (parse_qs(parsed.query).get("job_id") or [""])[0].strip()


def _parse_listing(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict[str, str]] = []
    seen: set[str] = set()

    for link in soup.select(".job_opening a[href]"):
        href = urljoin(BASE_URL, str(link.get("href") or ""))
        external_id = _job_id_from_url(href)
        title = _clean_text(link.get_text(" ", strip=True))
        if not external_id or external_id in seen or not title:
            continue
        seen.add(external_id)
        jobs.append({"external_id": external_id, "title": title, "apply_url": href})

    return jobs


def _parse_detail(html: str, listing_job: dict[str, str]) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one(".job_opening_title h1")
    location_node = soup.select_one(".job_opening_location")
    title = _clean_text(title_node.get_text(" ", strip=True)) if title_node else listing_job["title"]
    location = _clean_text(location_node.get_text(" ", strip=True)) if location_node else "Bellevue, WA, USA"
    description_node = soup.select_one(".job_description")
    description = str(description_node) if description_node else ""
    apply_url = listing_job["apply_url"]

    return {
        "external_id": listing_job["external_id"],
        "title": title,
        "location_raw": location,
        "description": description,
        "apply_url": apply_url,
        "source_url": apply_url,
        "source_platform": "valve",
    }


def _is_technical_title(title: str) -> bool:
    title_text = title.lower()
    return any(phrase in title_text for phrase in TECH_TITLE_PHRASES)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, str]]:
    listing_url = str(company_config.get("career_url") or BASE_URL).strip() or BASE_URL
    listing_html = http_get_text(listing_url)
    listing_jobs = _parse_listing(listing_html)
    results: list[dict[str, str]] = []

    for listing_job in listing_jobs:
        if not _is_technical_title(listing_job["title"]):
            continue
        try:
            detail_html = http_get_text(listing_job["apply_url"])
        except Exception as exc:
            LOGGER.warning("Skipping Valve job %s after detail fetch failed: %s", listing_job["external_id"], exc)
            continue
        detail_job = _parse_detail(detail_html, listing_job)
        if detail_job.get("description"):
            results.append(detail_job)

    return results
