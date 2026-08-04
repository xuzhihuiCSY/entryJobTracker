from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils import http_get_text

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


def _parse_jobs(page: str, career_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(page, "html.parser")
    jobs: list[dict[str, Any]] = []
    for row in soup.select("tr.data-row"):
        title_link = row.select_one(".jobTitle.hidden-phone a[href]") or row.select_one(
            "a.jobTitle-link[href]"
        )
        if title_link is None:
            continue
        apply_url = urljoin(career_url, str(title_link.get("href") or ""))
        external_id = apply_url.rstrip("/").rsplit("/", 1)[-1]
        if not external_id.isdigit():
            continue
        location = row.select_one(".jobLocation")
        jobs.append(
            {
                "external_id": external_id,
                "title": title_link.get_text(" ", strip=True),
                "location_raw": location.get_text(" ", strip=True) if location else "",
                "description": "",
                "apply_url": apply_url,
                "source_url": apply_url,
                "source_platform": "successfactors",
            }
        )
    return jobs


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    search_url = str(company_config.get("source_base_url") or "").strip()
    if not career_url or not search_url:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        startrow = 0
        while startrow < 125:
            page = http_get_text(
                search_url,
                params={"q": term, "locationsearch": "", "startrow": startrow},
                headers={"Referer": career_url, "User-Agent": "Mozilla/5.0"},
            )
            jobs = _parse_jobs(page, career_url)
            if not jobs:
                break
            for job in jobs:
                external_id = job["external_id"]
                if external_id in seen:
                    continue
                seen.add(external_id)
                results.append(job)
            startrow += len(jobs)
            if len(jobs) < 25:
                break
    return results
