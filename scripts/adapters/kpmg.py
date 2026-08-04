from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from utils import http_get_json

TECH_SEARCH_TERMS = [
    "software engineer",
    "machine learning",
    "data scientist",
    "data engineer",
    "cloud engineer",
    "security engineer",
    "technology intern",
    "IT intern",
]


def _parse_jobs(fragment: str, career_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(fragment, "html.parser")
    jobs: list[dict[str, Any]] = []
    for item in soup.select(".search--item"):
        job_link = item.select_one("a[href*='jobId=']")
        title = item.select_one(".list-view .h5")
        if job_link is None or title is None:
            continue
        apply_url = urljoin(career_url, str(job_link.get("href") or ""))
        external_id = parse_qs(urlparse(apply_url).query).get("jobId", [""])[0]
        if not external_id:
            continue
        location = item.select_one(".list-view .text-xs")
        location_raw = location.get_text(" ", strip=True) if location else ""
        if "|" in location_raw:
            location_raw = location_raw.split("|", 1)[1].strip()
        jobs.append(
            {
                "external_id": external_id,
                "title": title.get_text(" ", strip=True),
                "location_raw": location_raw,
                "description": "",
                "apply_url": apply_url,
                "source_url": apply_url,
                "source_platform": "kpmg",
            }
        )
    return jobs


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    source_url = str(company_config.get("source_base_url") or "").strip()
    if not career_url or not source_url:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        for page_number in range(1, 6):
            data = http_get_json(
                source_url,
                params={"ajax": "1", "keyword": term, "spage": page_number},
            )
            postings = data.get("postings", {}) if isinstance(data, dict) else {}
            fragment = postings.get("jobs", "") if isinstance(postings, dict) else ""
            jobs = _parse_jobs(str(fragment), career_url)
            if not jobs:
                break
            for job in jobs:
                external_id = job["external_id"]
                if external_id in seen:
                    continue
                seen.add(external_id)
                results.append(job)
    return results
